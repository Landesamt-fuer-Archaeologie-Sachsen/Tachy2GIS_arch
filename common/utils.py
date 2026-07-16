# -*- coding: utf-8 -*-
import ctypes
import logging
import os
import os.path
import re
import shutil
import webbrowser
import sqlite3
import subprocess

import sys
import uuid

import yaml
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication, QLocale, QRect, Qt, QUrl
from qgis.PyQt.QtGui import QPainter, QIcon

from qgis.PyQt.QtWidgets import QDesktopWidget, QDoubleSpinBox, QGridLayout, QLabel, QProgressBar, QTextBrowser, QWidget
from qgis.core import (
    QgsDefaultValue,
    QgsExpressionContextUtils,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    Qgis,
    QgsMapLayer,
    QgsMessageLog,
    QgsProject,
    QgsVectorLayer,
)
from qgis.utils import iface

from ..settings import PLUGIN_NAME, LANDINGPAGE

LOGGER = logging.getLogger(__name__)


def is_network_path(path):
    # Define the function prototype
    GetDriveTypeW = ctypes.windll.kernel32.GetDriveTypeW
    GetDriveTypeW.argtypes = [wintypes.LPCWSTR]
    GetDriveTypeW.restype = wintypes.UINT
    # Convert to absolute path
    full_path = os.path.abspath(path)
    # For UNC paths, use the server/share root
    if full_path.startswith("\\\\"):
        # UNC root would look like \\server\share
        # Typically extracting the first two path components after '\\'
        parts = full_path.strip("\\").split("\\")
        if len(parts) >= 2:
            unc_root = "\\\\" + parts[0] + "\\" + parts[1]
            drive_type = GetDriveTypeW(unc_root)
        else:
            # If we can't properly parse a UNC root, treat it carefully:
            return False
    else:
        # For normal paths (which might be mapped drives),
        # extract the drive letter and append '\\'
        drive, _ = os.path.splitdrive(full_path)
        if not drive:
            # No drive means it's relative or otherwise ambiguous
            return False
        # Ensure drive ends with a backslash
        drive_root = drive + "\\"
        drive_type = GetDriveTypeW(drive_root)

    return drive_type == 4  # DRIVE_REMOTE


def is_vsi_cached():
    return os.environ.get("SQLITE_USE_OGR_VFS", False)


def set_vsi_cached(activate: bool):
    """
    Set or unset env var SQLITE_USE_OGR_VFS [1] for file caching [2].
    This is used for opening and editing geopackage-based projects directly
        on windows network shared folders and accepting possible database corruption.
    Geopackage is based on SQLite and depends on file locking [3].
    [1] CTRL-F SQLITE_USE_OGR_VFS https://gdal.org/en/latest/drivers/vector/gpkg.html
    [2] https://gdal.org/en/latest/user/virtual_file_systems.html#vsicached-file-caching
    [3] https://www.sqlite.org/whentouse.html#situations_where_a_client_server_rdbms_may_work_better
    """
    if activate:
        LOGGER.info(
            "set SQLITE_USE_OGR_VFS (This is used for opening and editing geopackage-based projects directly"
            " on windows network shared folders and accepting possible database corruption.)"
        )
        os.environ["SQLITE_USE_OGR_VFS"] = "1"
    elif is_vsi_cached():
        LOGGER.info("unset SQLITE_USE_OGR_VFS")
        del os.environ["SQLITE_USE_OGR_VFS"]


def layers_not_in_edit_mode(list_of_layer_names: list[str]):
    project = QgsProject.instance()

    for layer_name in list_of_layer_names:
        layers = project.mapLayersByName(layer_name)
        if not layers:
            LOGGER.warning(f"Layer '{layer_name}' not found in the project.")
            return False

        if any([layer.isEditable() for layer in layers]):
            LOGGER.warning(f"Layer '{layer_name}' is in edit mode.")
            return False

    return True


def get_source_file_paths_of_layers(list_of_layer_names: list[str]):
    project = QgsProject.instance()

    paths_set = set()
    for layer_name in list_of_layer_names:
        layers = project.mapLayersByName(layer_name)
        if not layers:
            LOGGER.warning(f"Layer '{layer_name}' not found in the project.")
            return []

        for layer in layers:
            paths_set.add(str(layer.source()).split("|")[0])

    return list(paths_set)


def natural_sort_key(s, _nsre=re.compile("([0-9]+)")):
    return [int(text) if text.isdigit() else text.lower() for text in _nsre.split(s)]


def setCustomProjectVariable(variableName, variableWert):
    project = QgsProject.instance()
    QgsExpressionContextUtils.setProjectVariable(project, variableName, variableWert)


def getCustomProjectVariable(variableName):
    project = QgsProject.instance()
    variable = QgsExpressionContextUtils.projectScope(project).variable(variableName)
    if not variable:
        return ""
    else:
        return variable


def delCustomProjectVariable(variableName):
    project = QgsProject.instance()
    QgsExpressionContextUtils.removeProjectVariable(project, variableName)


def showAndHideWidgets(widgetsToShow, widgetsToHide):
    for wg in widgetsToShow:
        wg.show()
    for wg in widgetsToHide:
        wg.hide()


def enableAndDisableWidgets(enableWidgets, disableWidgets):
    for wg in enableWidgets:
        wg.setEnabled(True)
    for wg in disableWidgets:
        wg.setEnabled(False)


def project_backup(subfolder: str, keep_only_last_n_backups: int = None):
    """
    Creates a backup of a QGIS project and associated GeoPackage layers to a specified subfolder.
    This function ensures that the layers are not in edit mode, copies the project file and GeoPackage
    files to a timestamped backup folder, and optionally deletes the oldest backup folders.

    Parameters:
    - iface: An interface object used to interact with the QGIS application, including showing messages.
    - subfolder (str): The name of the subfolder within "_Sicherungen_" where backups will be stored.
    - keep_only_last_n_backups optional(int): The maximum number of backups to keep.

    Returns:
    - bool: True if the backup process was successful, False otherwise.
    """

    strftime_format_string = "%Y-%m-%d_%H_%M_%S"
    regex_pattern_for_format_string = r"\d{4}-\d{2}-\d{2}_\d{2}_\d{2}_\d{2}"
    sensible_layers = ["E_Point", "E_Line", "E_Polygon", "Messpunkte"]

    def delete_oldest_folders(directory, keep_num):
        pattern = re.compile(regex_pattern_for_format_string)

        folders = [
            os.path.join(directory, entry)
            for entry in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, entry)) and pattern.fullmatch(entry)
        ]
        folders.sort()
        num_to_delete = max(len(folders) - keep_num, 0)
        for folder in folders[:num_to_delete]:
            try:
                shutil.rmtree(folder)
                LOGGER.info(f"BACKUP: Deleted folder: {folder}")
            except Exception as e:
                LOGGER.error(f"BACKUP: ERROR deleting folder {folder}: {e}")

    def show_message(text, critical=False):
        iface.messageBar().pushMessage(
            title="T2G Archäologie Backup: ",
            text=text,
            level=(Qgis.MessageLevel.Warning if critical else Qgis.MessageLevel.Info),
            # duration=(0 if critical else -1)
            duration=(10 if critical else -1),
        )
        QgsMessageLog.logMessage(
            tag=PLUGIN_NAME,
            message="Backup: " + text,
            level=(Qgis.MessageLevel.Warning if critical else Qgis.MessageLevel.Info),
        )

    show_message("starting ... please wait")
    QCoreApplication.processEvents()  # give Qt the chance to process signals and show message

    project = QgsProject.instance()

    if not layers_not_in_edit_mode(sensible_layers) or project.isDirty():
        show_message(
            "Nicht möglich. Bitte den Editiermodus der Eingabelayer beenden und die Projektdatei speichern.", True
        )
        return False

    gpkg_paths = get_source_file_paths_of_layers(sensible_layers)
    if not gpkg_paths:
        show_message("Keine Quelle für Eingabelayer gefunden.", True)
        return False

    try:
        backup_folder_name = f"_Sicherungen_/{subfolder}"
        projectPath = project.readPath("..")  # from "Projekt" folder go one up
        target_folder = os.path.join(projectPath, backup_folder_name, datetime.now().strftime(strftime_format_string))
        LOGGER.info(f"BACKUP: creating target folder: {target_folder}")
        os.makedirs(target_folder)
    except Exception as e:
        show_message(f"Failed to create backup folder: {e}", True)
        return False

    try:
        projectFileName = project.fileName()
        newFileName = os.path.join(target_folder, Path(projectFileName).name)
        tmpFileName = str(projectFileName) + "_tmp.qgz"  # same folder or relative paths to layers will be wrong
        LOGGER.info(f"BACKUP: copying project file to: {newFileName}")
        # project.write()
        project.write(tmpFileName)
        project.write(projectFileName)
        shutil.move(tmpFileName, newFileName)
    except Exception as e:
        show_message(f"Failed to backup project file: {e}", True)
        return False

    try:
        for gpkg_path in gpkg_paths:
            if gpkg_path.endswith(".gpkg"):
                conn = sqlite3.connect(gpkg_path)
                cursor = conn.cursor()
                cursor.execute("VACUUM;")
                conn.commit()
                conn.close()

            LOGGER.info(f"BACKUP: copying GeoPackage {gpkg_path}")
            shutil.copy2(gpkg_path, target_folder)

    except Exception as e:
        show_message(f"Failed to backup GeoPackage: {e}", True)
        return False

    if keep_only_last_n_backups:
        delete_oldest_folders(os.path.join(projectPath, backup_folder_name), keep_num=keep_only_last_n_backups)

    iface.messageBar().popWidget()  # remove please wait message
    show_message("successful")
    return True


def addPoint3D(layer, point, attListe):
    referenceNumber = getCustomProjectVariable("aktcode")
    # geoarch = getCustomProjectVariable('geo-arch')

    # ToDo: should geo-arch be included as a field?
    dateFieldIndex = layer.fields().indexFromName("erf_datum")
    referenceFieldIndex = layer.fields().indexFromName("aktcode")
    # geoArchFieldIndex = layer.fields().indexFromName('geo-arch')

    attListe.update(
        {
            dateFieldIndex: str(datetime.now()),
            referenceFieldIndex: referenceNumber,
            # geoArchFieldIndex: geoarch
        }
    )

    feature = QgsFeature()
    fields = layer.fields()
    feature.setFields(fields)
    feature.setGeometry(QgsGeometry(point))
    _, addedFeatures = layer.dataProvider().addFeatures([feature])
    layer.updateExtents()

    layer.dataProvider().changeAttributeValues({addedFeatures[-1].id(): attListe})
    layer.featureAdded.emit(addedFeatures[-1].id())


# -------------------- Refactoring ----------------------------


class FileFunctions:
    @staticmethod
    def directory_del(path):
        # check if folder exists
        if os.path.exists(path):
            # remove if exists
            shutil.rmtree(path)

    @staticmethod
    def file_copy(quelle, ziel):
        if os.path.exists(quelle):
            shutil.copy(quelle, ziel)

    @staticmethod
    def file_del(path):
        if os.path.exists(path):
            os.remove(path)

    @staticmethod
    def directory_copy(source, destination, exclude_dirs_on_top_level=None):
        if exclude_dirs_on_top_level is None:
            exclude_dirs_on_top_level = []

        if os.path.exists(destination):
            LOGGER.warning(f"directory_copy() directory '{destination}' exists already.")
            return False

        try:
            os.makedirs(destination)

            for item in os.listdir(source):
                source_path = os.path.join(source, item)
                destination_path = os.path.join(destination, item)

                if os.path.isdir(source_path) and item in exclude_dirs_on_top_level:
                    # print(f"Skipping excluded directory: {item}")
                    continue

                if os.path.isdir(source_path):
                    shutil.copytree(source_path, destination_path)
                else:
                    shutil.copy2(source_path, destination_path)
            return True

        except Exception as e:
            LOGGER.error(f"directory_copy() failed: {e}")
            FileFunctions().directory_del(destination)
            return False


def isNumber(str):
    try:
        float(str)
        correct = True
    except:
        correct = False
    return correct


def any2bool(v):
    if v is None:
        pass
    elif isinstance(v, bool):
        return v
    elif isNumber(v):
        return bool(v)
    elif isinstance(v, str):
        if v.lower() in ("yes", "y", "ja", "j", "true", "t", "wahr", "on", "an", "1", "2"):
            return True
        elif v.lower() in ("no", "n", "nein", "false", "f", "falsch", "off", "aus", "0"):
            return False
    raise ValueError(f"invalid truth value: {v} (type {type(v)})")


def maxValue(layer, fieldname):
    values = []
    values.append(0)
    x = 0
    idField = layer.dataProvider().fieldNameIndex(fieldname)
    for feat in layer.getFeatures():
        attrs = feat.attributes()
        if attrs[idField] != None:
            x = x + 1
            try:
                if "_" in str(attrs[idField]):
                    continue
                # Attribute eine Zahl (bsp. 236)
                values.append(int(attrs[idField]))
            except ValueError:

                # list = [int(temp)for temp in str(attrs[idField]).split() if temp.isdigit()]
                # list = [int(s) for s in re.findall(r'-?\d+\.?\d*', str(attrs[idField]))]
                pattern = re.compile(r"\d+(?:;\.\d+)?")
                list = pattern.findall(str(attrs[idField]))
                for a in list:
                    values.append(int(a))
                pass
    return int(max(values))


def delSelectFeature():
    for layer in QgsProject.instance().mapLayers().values():
        if layer.type() == QgsMapLayer.VectorLayer:
            layer.removeSelection()


def fileLineCount(file):
    file = open(file)
    linecount = 0
    for line in file:
        linecount = linecount + 1
    file.close()
    return linecount


def delLayer(layername):
    if len([lyr for lyr in QgsProject.instance().mapLayers().values() if lyr.name() == layername]) != 0:
        templayer = QgsProject.instance().mapLayersByName(layername)[0]
        QgsProject.instance().removeMapLayers([templayer.id()])


def tableWidgetRemoveRows(widget):
    for row in reversed(range(widget.rowCount())):
        widget.removeRow(row)


class ProgressBar(QWidget):
    def __init__(self, titel):
        super().__init__()
        self.setWindowTitle(titel)
        self.move(QDesktopWidget().availableGeometry().center())
        self.progress = QProgressBar(self)
        self.progress.setGeometry(0, 0, 300, 25)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.value = 0
        self.close = False
        self.label = QLabel(self)
        self.label.setGeometry(0, 25, 300, 25)
        self.label.setAlignment(Qt.AlignCenter)
        self.show()

    def setValue(self, value):
        self.progress.setValue(value)

    def setMaximum(self, value):
        self.progress.setMaximum(value)

    def setText(self, value):
        self.label.setText(value)

    def closeEvent(self, event):
        self.close = True
        event.accept()


class HelpWindow(QWidget):

    def __init__(self, parent=None):
        super(HelpWindow, self).__init__(parent, Qt.WindowStaysOnTopHint)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.meldung = QTextBrowser()
        self.title = None
        self.text = None
        self.pfad = None
        self.layout().addWidget(self.meldung)  # ,0,0,1,2)

    def run(self, pfad, title, text, width, height):
        self.setWindowTitle(title)
        if pfad == None:
            self.meldung.setHtml(text)
        elif text == None:
            self.meldung.setSource(QUrl.fromLocalFile(pfad))
        self.resize(width, height)
        self.show()

    def setText(self, text):
        self.text = text

    def setPfad(self, pfad):
        self.pfad = pfad


class LocaleDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox that accepts both comma and period as decimal separator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLocale(QLocale.c())

    def validate(self, text, pos):
        return super().validate(text.replace(',', '.'), pos)

    def valueFromText(self, text):
        return super().valueFromText(text.replace(',', '.'))


# Define a metaclass SingletonMeta
class SingletonMeta(type):
    # Dictionary to store instances of classes
    _instances = {}

    # Override the __call__ method of the metaclass
    def __call__(cls, *args, **kwargs):
        # Check if the class is not already instantiated
        if cls not in cls._instances:
            # If not, create a new instance and store it in _instances dictionary
            cls._instances[cls] = super().__call__(*args, **kwargs)
        # Return the existing instance if already instantiated
        return cls._instances[cls]

    def clear(cls):
        # delete instance of provided class
        try:
            del cls._instances[cls]
        except KeyError:
            pass


class ArchProjectConfig(metaclass=SingletonMeta):
    CONFIG_FILE_NAME = "ArchProjectConfig.yaml"

    def __init__(self):
        self.config_data = None
        self.file_path = None

    def _resolve_file_path(self):
        projectFile = QgsProject.instance().fileName()
        if projectFile:
            return os.path.join(os.path.dirname(projectFile), self.CONFIG_FILE_NAME)
        return self.CONFIG_FILE_NAME

    def load_config(self):
        self.file_path = self._resolve_file_path()
        LOGGER.info(f"Tachy2GIS_arch plugin is loading config file {self.file_path}")

        try:
            with open(self.file_path, "r") as file:
                self.config_data = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")

        LOGGER.debug(f"Using following config data: {self.config_data}")

        if not isinstance(self.config_data, dict):
            raise ValueError("At top level the YAML file has to contain only variables.")

    def check_config(self):
        if self.config_data is None:
            self.load_config()

        mandatory_keys = [
            "Digitize_Befund_ObjTyp",
            "Digitize_display_points",
            "Digitize_Profil_ObjTyp",
            "GeoRef_Fotoentzerrpunkt_ObjArt",
            "GeoRef_Fotoentzerrpunkt_ObjTyp",
            "GeoRef_Profil_ColName",
            "GeoRef_Profil_ObjTyp",
            "ProfileTool_ProfilPP_ObjArt",
            "ProfileTool_ProfilPP_ObjSpez",
            "ProfileTool_ProfilPP_ObjTyp",
            "Transformation_colNameGcpSource",
        ]
        for key in mandatory_keys:
            if key not in self.config_data:
                raise ValueError(f"The key {key} is not present in the configuration file {self.file_path}.")

    def get(self, key, default=None):
        if self.config_data is None:
            self.load_config()

        return self.config_data.get(key, default)


def write_measurement_log(text):
    # a broken log path must never interrupt an ongoing measurement, so failures are only logged
    try:
        log_dir = QgsProject.instance().readPath(ArchProjectConfig().get("Log_directory", "."))
        os.makedirs(log_dir, exist_ok=True)

        aktcode = re.sub(r'[\\/:*?"<>|]', "_", getCustomProjectVariable("aktcode"))
        date_str = datetime.now().strftime("%Y%m%d")
        file_name = f"{aktcode}_{date_str}.txt" if aktcode else f"_{date_str}.txt"

        with open(os.path.join(log_dir, file_name), "a") as log_file:
            log_file.write(text)
    except Exception as e:
        LOGGER.warning(f"Could not write measurement log: {e}")


def color_shift_icon(source_icon, color):
    pixmap = source_icon.pixmap(64, 64)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
    painter.fillRect(pixmap.rect(), color)
    painter.end()
    return QIcon(pixmap)


def merge_icons(source_icon, small_icon):
    big = 64
    small = 32
    pixmap = source_icon.pixmap(big, big)
    small_pixmap = small_icon.pixmap(small, small)

    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    painter.drawPixmap(QRect(big - small, big - small, small, small), small_pixmap, small_pixmap.rect())
    painter.end()
    return QIcon(pixmap)


def openProjectFolder():
    # from "Projekt" folder go one up
    projectPath = QgsProject.instance().readPath("..")
    if sys.platform == "win32":
        os.startfile(projectPath.replace("/", "\\"))
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, projectPath])


def saveProject():
    project_backup("manuell")


def openManual():
    webbrowser.open(LANDINGPAGE)


def repairUuidsInLayers(layers: list[QgsVectorLayer]):
    QgsMessageLog.logMessage("Überprüfe UUID", PLUGIN_NAME, Qgis.Info)
    # obj_uuid erzeugen wenn Feld leer
    for layer in layers:
        fIndex = layer.dataProvider().fieldNameIndex("obj_uuid")
        if fIndex == -1:
            continue
        layer.startEditing()
        layer.setDefaultValueDefinition(fIndex, QgsDefaultValue("uuid()"))
        layer.updateFields()
        features_ohne_uuid = list(
            layer.getFeatures(QgsFeatureRequest().setFilterExpression('"obj_uuid" IS NULL'))
        )
        QgsMessageLog.logMessage(
            f"{len(features_ohne_uuid)} features ohne UUID in Layer {layer.name()}; Neugenerierung ...",
            PLUGIN_NAME,
            Qgis.Info,
        )
        attr_map = {f.id(): {fIndex: "{" + str(uuid.uuid4()) + "}"} for f in features_ohne_uuid}
        layer.dataProvider().changeAttributeValues(attr_map)
        layer.commitChanges()

        # Duplikatprüfung obj_uuid
        alle_uuids = [f["obj_uuid"] for f in layer.getFeatures()]
        if len(alle_uuids) != len(set(alle_uuids)):
            anzahl_duplikate = len(alle_uuids) - len(set(alle_uuids))
            QgsMessageLog.logMessage(
                f"WARNUNG: {anzahl_duplikate} doppelte obj_uuid in Layer {layer.name()}",
                PLUGIN_NAME,
                Qgis.Warning,
            )
