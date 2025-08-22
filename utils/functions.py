# -*- coding: utf-8 -*-
import csv
import ctypes
import os
import os.path
import re
import shutil
import sqlite3
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

import yaml
from qgis.PyQt.QtCore import pyqtSignal, QCoreApplication, QRect, Qt, QUrl
from qgis.PyQt.QtGui import QColor, QPainter, QIcon, QImage, QPixmap
from qgis.PyQt.QtWidgets import QDesktopWidget, QGridLayout, QMessageBox, QLabel, QProgressBar, QTextBrowser, QWidget
from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.core import (
    QgsExpressionContextUtils,
    QgsFeature,
    QgsField,
    QgsGeometry,
    Qgis,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsMapLayer,
    QgsMessageLog,
    QgsPoint,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker
from qgis.utils import iface


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
        print(
            "set SQLITE_USE_OGR_VFS (This is used for opening and editing geopackage-based projects directly"
            " on windows network shared folders and accepting possible database corruption.)"
        )
        os.environ["SQLITE_USE_OGR_VFS"] = "1"
    elif is_vsi_cached():
        print("unset SQLITE_USE_OGR_VFS")
        del os.environ["SQLITE_USE_OGR_VFS"]


def layers_not_in_edit_mode(list_of_layer_names: list[str]):
    project = QgsProject.instance()

    for layer_name in list_of_layer_names:
        layers = project.mapLayersByName(layer_name)
        if not layers:
            print(f"Layer '{layer_name}' not found in the project.")
            return False

        if any([layer.isEditable() for layer in layers]):
            print(f"Layer '{layer_name}' is in edit mode.")
            return False

    return True


def commit_changes_in_layers(list_of_layer_names: list[str] = None):
    project = QgsProject.instance()

    for layer_name in list_of_layer_names:
        layers = project.mapLayersByName(layer_name)
        if not layers:
            print(f"Layer '{layer_name}' not found in the project.")
            return False

        for layer in layers:
            if layer.isEditable() and layer.isModified():
                layer.commitChanges()
                layer.startEditing()

    return True


def get_source_file_paths_of_layers(list_of_layer_names: list[str]):
    project = QgsProject.instance()

    paths_set = set()
    for layer_name in list_of_layer_names:
        layers = project.mapLayersByName(layer_name)
        if not layers:
            print(f"Layer '{layer_name}' not found in the project.")
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


def layerHasPendingChanges(layer: QgsVectorLayer):
    buffer = layer.editBuffer()
    if not buffer:
        return False
    return bool(len(buffer.changedGeometries()) + len(buffer.changedAttributeValues()))


def findLayerInProject(name):
    mapLayers = QgsProject.instance().mapLayers()
    for lyr in mapLayers.values():
        if lyr.name() == name:
            return lyr


def project_backup(iface, subfolder: str, keep_only_last_n_backups: int = None):
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
                print(f"BACKUP: Deleted folder: {folder}")
            except Exception as e:
                print(f"BACKUP: ERROR deleting folder {folder}: {e}")

    def show_message(text, critical=False):
        iface.messageBar().pushMessage(
            title="T2G Archäologie Backup: ",
            text=text,
            level=(Qgis.MessageLevel.Warning if critical else Qgis.MessageLevel.Info),
            # duration=(0 if critical else -1)
            duration=(10 if critical else -1),
        )
        QgsMessageLog.logMessage(
            tag="T2G Archäologie",
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
        print("BACKUP: creating target folder: " + target_folder)
        os.makedirs(target_folder)
    except Exception as e:
        show_message(f"Failed to create backup folder: {e}", True)
        return False

    try:
        projectFileName = project.fileName()
        newFileName = os.path.join(target_folder, Path(projectFileName).name)
        tmpFileName = str(projectFileName) + "_tmp.qgz"  # same folder or relative paths to layers will be wrong
        print("BACKUP: copying project file to: " + newFileName)
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

            print(f"BACKUP: copying GeoPackage {gpkg_path}")
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
            print(f"directory_copy() directory '{destination}' exists already.")
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
            print(e)
            FileFunctions().directory_del(destination)
            return False


class makerAndRubberbands:
    def __init__(self):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.lMakers = []
        self.lRabberbands = []
        self.makerTyp = QgsVertexMarker.ICON_BOX
        self.color = QColor(255, 0, 0)

    def setMakerType(self, vertexMaker):
        self.makerTyp = vertexMaker

    def setColor(self, QColor):
        self.color = QColor

    def setMarker(self, x, y, size, penwidth):
        m = QgsVertexMarker(self.canvas)
        m.setCenter(QgsPointXY(float(x), float(y)))
        m.setColor(self.color)
        m.setIconSize(size)
        m.setIconType(self.makerTyp)
        m.setPenWidth(penwidth)
        m.show()
        self.lMakers.append(m)

    def setRubberBandPoly(self, ptList, penwidth):
        ptL = []
        for a in ptList:
            item = QgsPoint(float(a[0]), float(a[1]), float(a[2]))
            ptL.append(item)
        # ersten Punkt als letzten einfügen
        # ptList.append(ptList[0])
        r = QgsRubberBand(self.canvas)
        r.setToGeometry(QgsGeometry.fromPolyline(ptL), None)
        r.setColor(self.color)
        # r.fillColor()
        r.setWidth(penwidth)
        r.show()
        self.lRabberbands.append(r)

    def makerClean(self):
        for maker in self.lMakers:
            self.canvas.scene().removeItem(maker)

    def rubberBandClean(self):
        for maker in self.lRabberbands:
            self.canvas.scene().removeItem(maker)


def isDate(datum, spl):
    correctDate = None
    year = int(datum.split(spl)[0])
    month = int(datum.split(spl)[1])
    day = int(datum.split(spl)[2])
    try:
        newDate = datetime(year, month, day)
        correctDate = True
    except ValueError:
        correctDate = False
    return correctDate


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


def maxValueInt(layer, fieldname):
    idx = layer.dataProvider().fieldNameIndex(fieldname)
    if layer.maximumValue(idx) == None:
        max = 0
    else:
        max = layer.maximumValue(idx)
    return int(max)


def ValueList(layer, fieldname):
    befnr = []

    for field in layer.fields():
        if field.name() == fieldname:
            idField = layer.dataProvider().fieldNameIndex(fieldname)
            for feat in layer.selectedFeatures():
                attrs = feat.attributes()
                if attrs[idField] != None:
                    try:
                        befnr.append(int(attrs[idField]))
                    except ValueError:
                        pass
    try:
        return befnr
    except ValueError:
        befnr.append(0)
        return befnr


def mapCanvasRefresh():
    cachingEnabled = iface.mapCanvas().isCachingEnabled()
    for layer in iface.mapCanvas().layers():
        if cachingEnabled:
            layer.triggerRepaint()
    iface.mapCanvas().refresh()


def setColumnVisibility(layer, columnName, visible):
    config = layer.attributeTableConfig()
    columns = config.columns()
    for column in columns:
        if column.name == columnName:
            column.hidden = not visible
            break
    config.setColumns(columns)
    layer.setAttributeTableConfig(config)


def setColumnSort(layer, columnName, sort):
    config = layer.attributeTableConfig()


def csvListfilter(pfad, spalte, suchspalte, suchwert, vergleich):
    path = os.path.join(pfad)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        d = list(reader)
        w = Listfilter(d, spalte, suchspalte, suchwert, vergleich)
    f.close()
    return w


def csvToList(pfad):
    path = os.path.join(pfad)
    with open(path, "r") as f:
        reader = csv.reader(f, delimiter=";")
        d = list(reader)
    f.close()
    return d


def Listfilter(liste, spalte, suchspalte, suchwert, vergleich):
    w = []
    for i in range(len(liste)):
        if vergleich == "genau":
            if suchwert == (liste[i][suchspalte]):
                w.append(liste[i][spalte])
        else:
            if suchwert in (liste[i][suchspalte]):
                w.append(liste[i][spalte])
    return w


def getListfilterIndex(liste, suchspalte, suchwert, vergleich):
    w = None
    for i in range(len(liste)):
        if vergleich == "genau":
            if suchwert == (liste[i][suchspalte]):
                w = i
                return w
        else:
            if suchwert in (liste[i][suchspalte]):
                w = i
                return w
    return w


def csvWriter(pfad, list):
    output_file = open(pfad, "w")
    row2 = ""
    for row in range(len(list)):
        for i in range(len(list[row])):
            row2 = row2 + list[row][i] + ";"
        row2 = row2[:-1] + "\n"
    output_file.write(row2.strip())
    output_file.close()


def featureAttributEdit(layer, feature, attList):
    for item in attList:
        fIndex = layer.dataProvider().fieldNameIndex(item)
        layer.changeAttributeValue(feature.id(), fIndex, attList[item])


def addAttributField(layer, fieldname, typ, length):
    layer.startEditing()
    if layer.dataProvider().fieldNameIndex(fieldname) == -1:
        layer.dataProvider().addAttributes([QgsField(fieldname, typ, len=length)])
        layer.updateFields()


def setSelectAllFeatures(layer):
    meldung = True
    it = layer.getFeatures()
    ids = [i.id() for i in it]
    layer.selectByIds(ids)

    if layer.selectedFeatureCount() > 0:
        iface.mapCanvas().zoomToSelected(layer)
        if not layer.geometryType() == QgsWkbTypes.PointGeometry:
            iface.mapCanvas().zoomByFactor(5)
        # iface.mapCanvas().refresh()
        meldung = False
    else:
        meldung = True
    if meldung == True:
        QMessageBox.warning(None, "Meldung", "Keine Objekte gefunden!")


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


def getlayerSelectedFeatures():
    for layer in QgsProject.instance().mapLayers().values():
        if layer.type() == QgsMapLayer.VectorLayer:
            if layer.selectedFeatureCount() > 0:
                layer
                break
    return layer


def delLayer(layername):
    if len([lyr for lyr in QgsProject.instance().mapLayers().values() if lyr.name() == layername]) != 0:
        templayer = QgsProject.instance().mapLayersByName(layername)[0]
        QgsProject.instance().removeMapLayers([templayer.id()])


def tableWidgetRemoveRows(widget):
    for row in reversed(range(widget.rowCount())):
        widget.removeRow(row)


class LayerTree:
    def __init__(self, objekt=QgsProject.instance().layerTreeRoot()):
        self.tree = objekt
        self.visible = True
        self.expanded = True

    def allChildsVisible(self, value):
        self.setVisible(value)
        for child in self.tree.children():
            self.layerTreeVisible(child)

    def allGroupsVisible(self, value):
        self.setVisible(value)
        for child in self.tree.children():
            self.layerGroupVisible(child)

    def allGroupsExpanded(self, value):
        self.setExpanded(value)
        for child in self.tree.children():
            self.layerGroupExpanded(child)

    def childVisible(self):
        pass

    def setVisible(self, value):
        self.visible = value

    def setExpanded(self, value):
        self.expanded = value

    # ---------------------------------------------------------------------------------------------------------------------

    def layerTreeVisible(self, child):
        child.setItemVisibilityChecked(self.visible)
        for child in child.children():
            # QgsMessageLog.logMessage(str(child.dump()), 'T2G Archäologie', Qgis.Info)
            if isinstance(child, QgsLayerTreeGroup):
                self.layerTreeVisible(child)
                pass
            elif isinstance(child, QgsLayerTreeLayer):
                child.setItemVisibilityChecked(self.visible)

    def layerGroupVisible(self, child):
        if isinstance(child, QgsLayerTreeGroup):
            child.setItemVisibilityChecked(self.visible)
        for child in child.children():
            # QgsMessageLog.logMessage(str(child.dump()), 'T2G Archäologie', Qgis.Info)
            if isinstance(child, QgsLayerTreeGroup):
                # child.setItemVisibilityChecked(self.visible)
                self.layerGroupVisible(child)

    def layerGroupExpanded(self, child):
        if isinstance(child, QgsLayerTreeGroup):
            child.setExpanded(self.expanded)
        elif isinstance(child, QgsLayerTreeLayer):
            child.setExpanded(False)
        for child in child.children():
            if isinstance(child, QgsLayerTreeGroup):
                child.setExpanded(self.expanded)
                self.layerGroupExpanded(child)
            elif isinstance(child, QgsLayerTreeLayer):
                child.setExpanded(False)

    def layerExpanded(self, child):
        if isinstance(child, QgsLayerTreeLayer):
            child.setExpanded(self.expanded)
        for child in child.children():
            if isinstance(child, QgsLayerTreeLayer):
                child.setExpanded(self.expanded)
        pass


def setAliasName():
    # >Alias Namen erzeugen
    for layer in QgsProject.instance().mapLayers().values():
        if layer.type() == QgsMapLayer.VectorLayer:
            a = 0
            for field in layer.fields():
                if field.name() == "messatum":
                    layer.setFieldAlias(a, "Aufnamedatum")
                elif field.name() == "aktcode":
                    layer.setFieldAlias(a, "Grabung")
                elif field.name() == "obj_typ":
                    layer.setFieldAlias(a, "Objekttyp")
                elif field.name() == "obj_art":
                    layer.setFieldAlias(a, "Objektart")
                elif field.name() == "schnitt_nr":
                    layer.setFieldAlias(a, "Schnitt-Nr")
                elif field.name() == "planum":
                    layer.setFieldAlias(a, "Planum")
                elif field.name() == "material":
                    layer.setFieldAlias(a, "Material")
                elif field.name() == "bemerkung":
                    layer.setFieldAlias(a, "Bemerkung")
                elif field.name() == "bef_nr":
                    layer.setFieldAlias(a, "Befund-Nr")
                elif field.name() == "fund_nr":
                    layer.setFieldAlias(a, "Fund-Nr")
                elif field.name() == "geo-arch":
                    layer.setFieldAlias(a, "Geo/Arch")
                elif field.name() == "prob_nr":
                    layer.setFieldAlias(a, "Probe-Nr")
                a = a + 1
    # <Alias Namen erzeugen


class progressBar(QWidget):
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
        self.lab = QLabel(self)
        self.lab.setGeometry(0, 25, 300, 25)
        self.lab.setAlignment(Qt.AlignCenter)
        self.show()

    def setValue(self, value):
        self.progress.setValue(value)

    def setMaximum(self, value):
        self.progress.setMaximum(value)

    def setText(self, value):
        # self.lab.styleSheet("{Background-color : rgb(240, 240, 240) ; font: 75 7pt ;}")
        self.lab.setText(value)

    def closeEvent(self, event):
        # self.opacity = self.ui.mOpacityWidget.opacity
        self.close = True
        event.accept()


class PrintClickedPoint(QgsMapToolEmitPoint):
    geomPoint = pyqtSignal()

    def __init__(self, canvas, dlg):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.dlg = dlg

    def canvasMoveEvent(self, e):
        try:
            # point = self.toMapCoordinates(self.canvas.mouseLastXY())
            # point = e.originalMapPoint()
            # point = e.snapPoint()
            # self.dlg.activateWindow()
            # self.dlg.txtPoint_2.setText(str(point.x())+','+str(point.y()))
            pass
        except:
            pass

    def canvasPressEvent(self, e):
        # try:
        point = e.snapPoint()
        # point = self.asWkb(e.snapPoint())
        self.dlg.activateWindow()
        self.dlg.txtPointTemp.setText(str(point.x()) + "," + str(point.y()))
        # except:
        #    pass


class ClickedPoint(QgsMapToolEmitPoint):
    geomPoint = pyqtSignal()
    tempPoint = pyqtSignal()

    def __init__(self, canvas, dlg):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.dlg = dlg

    def canvasMoveEvent(self, e):
        try:
            point = self.toMapCoordinates(self.canvas.mouseLastXY())
            point = e.originalMapPoint()
            point = e.snapPoint()
            self.geomPoint.emit()
            self.dlg.activateWindow()
        except:
            pass

    def canvasPressEvent(self, e):
        # try:
        point = e.snapPoint()

        # point = self.asWkb(e.snapPoint())
        self.dlg.activateWindow()
        self.tempPoint.emit()


class xml:
    def __init__(self, file):
        self.file = file

    def getValue(self, element, key):
        import xml.etree.ElementTree as ElementTree

        tree = ElementTree.parse(self.file)
        root = tree.getroot()

        for elem in root:
            if elem.tag == element:
                for child in elem:
                    if child.attrib["name"] == key:
                        return child.text

    def setValue(self, element, key, wert):
        import xml.etree.ElementTree as ElementTree

        tree = ElementTree.parse(self.file)
        root = tree.getroot()

        for elem in root:
            if elem.tag == element:
                for child in elem:
                    if child.attrib["name"] == key:
                        child.text = wert
        tree.write(self.file)


class HelpWindow(QWidget):

    def __init__(self, parent=None):
        super(HelpWindow, self).__init__(parent, Qt.WindowStaysOnTopHint)
        self.setLayout(QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.meldung = QTextBrowser()
        self.text = None
        self.pfad = None
        self.layout().addWidget(self.meldung)  # ,0,0,1,2)

    def run(self, pfad, text, width, height):
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
    def __init__(self):
        self.config_data = None
        self.file_path = "ArchProjectConfig.yaml"
        projectFile = QgsProject.instance().fileName()
        if projectFile and projectFile != "":
            project_dir = os.path.dirname(projectFile)
            self.file_path = os.path.join(project_dir, self.file_path)

    def load_config(self):
        print(f"Tachy2GIS_arch plugin is loading config file {self.file_path}", flush=True)

        try:
            with open(self.file_path, "r") as file:
                self.config_data = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")

        print(f"Using following config data: {self.config_data}")

        if not isinstance(self.config_data, dict):
            raise ValueError("At top level the YAML file has to contain only variables.")

    def check_config(self):
        if self.config_data is None:
            self.load_config()

        mandatory_keys = [
            "AutoSave_enabled",
            "AutoSave_interval_in_min",
            "AutoSave_keep_last_n_backups",
            "default_exportordner",
            "default_importordner",
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
