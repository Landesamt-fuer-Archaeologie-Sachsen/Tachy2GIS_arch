import math
import operator
import os

from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton, QMessageBox, QFileDialog, QInputDialog
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis._core import (
    QgsProject,
    QgsMessageLog,
    QgsPoint,
    Qgis,
    QgsFeatureRequest,
    QgsExpression,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsLayerTreeLayer,
    QgsWkbTypes,
)
from qgis.core import QgsApplication
from qgis.utils import iface

from ..common.config_file import Configfile, get_config_ini_path
from ..common.layers import T2gLayers, findLayerInProject
from ..common.utils import (
    openProjectFolder,
    saveProject,
    merge_icons,
    color_shift_icon,
    openManual,
    ProgressBar,
    fileLineCount,
    addPoint3D,
    delSelectFeature,
    delLayer,
)
from ..icons import ICON_PATHS
from ..settings import PLUGIN_NAME


class OpenProjectFolderAction(QAction):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Projektverzeichnis öffnen")
        self.setIcon(QIcon(ICON_PATHS["ordner-open"]))
        self.setEnabled(False)
        self.triggered.connect(self.callback)

    def callback(self):
        openProjectFolder()


class BackupProjectAction(QAction):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Backup erstellen")
        self.setIcon(QIcon(QgsApplication.iconPath("mActionFileSave.svg")))
        self.setEnabled(False)
        self.triggered.connect(self.callback)

    def callback(self):
        saveProject()


class AutoBackupProjectAction(QAction):
    def __init__(self, autosave_manager, parent=None):
        super().__init__(parent)
        self._autosave_manager = autosave_manager
        self.setText("Auto-Backup")
        self.setIcon(self.getIcon())
        self.setCheckable(True)
        self.setChecked(False)
        self.setEnabled(False)
        self.triggered.connect(self._autosave_manager.enable)

    def getIcon(self):
        icon_save_on = merge_icons(
            QIcon(QgsApplication.iconPath("mActionFileSave.svg")),
            QIcon(QgsApplication.iconPath("mIconHistory.svg")),
        )
        icon_save_off = color_shift_icon(icon_save_on, QColor(128, 128, 128, 170))
        icon_auto_backup = QIcon()
        icon_auto_backup.addPixmap(icon_save_on.pixmap(64, 64), QIcon.Normal, QIcon.On)
        icon_auto_backup.addPixmap(icon_save_off.pixmap(64, 64), QIcon.Normal, QIcon.Off)
        return icon_auto_backup


class SettingsAction(QAction):
    def __init__(self, autosave_manager, parent=None):
        super().__init__(QIcon(ICON_PATHS["Einstellungen"]), "Einstellungen", parent)
        self._autosave_manager = autosave_manager
        self._dialog = None
        self.setEnabled(False)
        self.triggered.connect(self._open)

    def _open(self):
        from .widgets import DlgSettings  # local import to avoid circular dependency

        config = Configfile(get_config_ini_path())
        self._dialog = DlgSettings(config, self._autosave_manager)
        self._dialog.setup()
        self._dialog.show()


class AboutAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["Frage"]), "Über dieses Plugin", parent)
        self._dialog = None
        self.triggered.connect(self._open)

    def _open(self):
        from .widgets import AboutDialog  # local import to avoid circular dependency

        self._dialog = AboutDialog(self.parent())
        self._dialog.exec()


class ManualAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["Formular"]), "Dokumentation", parent)
        self.triggered.connect(openManual)


class ImportPointsAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["points_import"]), "Punkt Import", parent)
        self.triggered.connect(importPoints)


class ExportPointsAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["points_export"]), "Punkt Export", parent)
        self.triggered.connect(exportPoints)


class ExportProfilePointsAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["points_export_profile"]), "Profilentzerrpunkte Export", parent)
        self.triggered.connect(exportProfilePoints)


class MenuPointsImportAction(QToolButton):
    """A toolbar button that opens a dropdown menu with point import/export actions."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.action_import = ImportPointsAction(self)
        self.action_export = ExportPointsAction(self)
        self.action_export_profile = ExportProfilePointsAction(self)

        menu = QMenu(self)
        menu.addActions([self.action_import, self.action_export, self.action_export_profile])

        self.setMenu(menu)
        self.setDefaultAction(self.action_import)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setEnabled(False)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.action_import.setEnabled(enabled)
        self.action_export.setEnabled(enabled)
        self.action_export_profile.setEnabled(enabled)


def importPoints():
    importPath = Configfile(get_config_ini_path()).getValue("Punkte Import", "pfad Importordner", "./../Jobs")
    pointsLayer = T2gLayers.getPointLayer()
    if not pointsLayer:
        return
    result = QMessageBox.information(
        None,
        "WICHTIG",
        "Dateiformat:\nptnr  x  y  z\n\nMöchten Sie fortfahren?",
        QMessageBox.Ok | QMessageBox.Cancel,
    )
    if result == QMessageBox.Ok:
        inputFile = QFileDialog.getOpenFileName(
            None,
            "Quellpfad",
            QgsProject.instance().readPath(importPath),
            "Vermessung (*.txt);;Text mit Komma (*.txt);;Text mit Tab (*.txt);;Excel (*.csv);;Alle Dateien (*.*)",
        )

        dateiFormat = os.path.splitext(inputFile[0])[-1].lower()
        if inputFile[0] != "":
            progress = ProgressBar("Fortschritt")
            QCoreApplication.processEvents()

            if dateiFormat == ".csv":
                QgsMessageLog.logMessage("Point import- read data from .csv", PLUGIN_NAME, Qgis.Info)
                with open(inputFile[0]) as file:
                    lineCount = fileLineCount(inputFile[0])
                    progress.setText(f"{lineCount} Punkte werden importiert")
                    progress.setMaximum(lineCount)
                    pointNumber = 0
                    objCount = 0
                    for line in file:
                        progress.setValue(pointNumber)
                        lineList = line.split(",")
                        try:
                            a = lineList[0].strip()
                            b = lineList[1].strip()
                            c = lineList[2].strip()
                            d = lineList[3].strip()
                            pt = QgsPoint(float(b), float(c), float(d))
                            attL = {"pt_nr": a}
                            addPoint3D(pointsLayer, pt, attL)
                            objCount += 1
                        except:
                            QgsMessageLog.logMessage(
                                f"Point import: Could not read point in line {pointNumber}",
                                PLUGIN_NAME,
                                Qgis.Info,
                            )
                        pointNumber += 1
            elif dateiFormat == ".txt":
                QgsMessageLog.logMessage("Point import- read data from .txt", PLUGIN_NAME, Qgis.Info)
                with open(inputFile[0]) as file:
                    lines = file.readlines()
                    lineCount = len(lines)
                    progress.setText(f"{lineCount} Punkte werden importiert")
                    progress.setMaximum(lineCount)
                    pointNumber = 0
                    objCount = 0
                    if "Komma" in inputFile[1]:
                        sep = ","
                    if "Tab" in inputFile[1]:
                        sep = "\t"
                    if "Vermessung" in inputFile[1]:
                        sep = "V"
                    for line in lines:
                        progress.setValue(pointNumber)
                        if sep != "V" and "." in line:
                            if "." in line:
                                try:
                                    a = str(line).split(sep)[0].lstrip()
                                    b = str(line).split(sep)[1].lstrip()
                                    c = str(line).split(sep)[2].lstrip()
                                    d = str(line).split(sep)[3].lstrip()
                                    pt = QgsPoint(float(b), float(c), float(d))
                                    attL = {"pt_nr": a}
                                    addPoint3D(pointsLayer, pt, attL)
                                    objCount += 1
                                except:
                                    QgsMessageLog.logMessage(
                                        f"Point import: Could not read point in line {pointNumber}",
                                        PLUGIN_NAME,
                                        Qgis.Info,
                                    )
                            else:
                                iface.messageBar().pushMessage(
                                    PLUGIN_NAME,
                                    f"Fehler! Falscher Spaltentrenner oder vorhandene Kopfzeile in Zeile {pointNumber}.",
                                    level=Qgis.Critical,
                                )
                        else:
                            try:
                                a = str(line)[0:15].lstrip()
                                b = str(line)[16:32].lstrip()
                                c = str(line)[33:44].lstrip()
                                d = str(line)[45:53].lstrip()
                                pt = QgsPoint(float(b), float(c), float(d))
                                attL = {"pt_nr": a}
                                addPoint3D(pointsLayer, pt, attL)
                                objCount += 1
                            except:
                                QgsMessageLog.logMessage(
                                    f"Point import: Could not read point in line {pointNumber}",
                                    PLUGIN_NAME,
                                    Qgis.Info,
                                )

                        pointNumber += 1

            if objCount > 0:
                iface.messageBar().pushMessage(PLUGIN_NAME, f"{objCount} Punkte eingetragen.", level=Qgis.Info)
            else:
                iface.messageBar().pushMessage(PLUGIN_NAME, "Keine Punkte eingetragen.", level=Qgis.Critical)


def exportPoints():
    exportPath = Configfile(get_config_ini_path()).getValue("Punkte Export", "pfad Exportordner", "./../Jobs")
    # Should be: layer "Messpunkte" or layer 'E_Point'
    layer = iface.activeLayer()

    if layer.selectedFeatureCount() == 0 or layer.geometryType() != QgsWkbTypes.PointGeometry:
        QMessageBox.critical(
            None,
            "Meldung",
            "Es sind keine Punkte selektiert oder es ist kein Punktlayer ausgewählt!",
            QMessageBox.Abort,
        )
    else:
        outputFile = QFileDialog.getSaveFileName(
            None,
            "Speicherpfad",
            QgsProject.instance().readPath(exportPath),
            "Text (*.txt);;Excel (*.csv);;Alle Dateien (*.*)",
        )
        if outputFile[0] != "":
            with open(outputFile[0], "w") as outputFile:
                feats = []
                for feat in layer.selectedFeatures():
                    pt = feat.geometry().constGet()
                    x = pt.x()
                    y = pt.y()
                    z = pt.z()
                    msgout = f'{feat["pt_nr"]}, {x}, {y}, {z}\n'
                    feats.append(msgout)

                box = QMessageBox()
                box.setIcon(QMessageBox.Question)
                box.setWindowTitle("Frage")
                box.setText("Wie soll sortiert werden?")
                box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                buttonY = box.button(QMessageBox.Yes)
                buttonY.setText("Punkt Nr")
                buttonN = box.button(QMessageBox.No)
                buttonN.setText("Datum")
                box.exec_()

                if box.clickedButton() == buttonY:
                    s_feats = sorted(feats, key=operator.itemgetter(0))
                elif box.clickedButton() == buttonN:
                    s_feats = sorted(feats, key=operator.itemgetter(1))

                # write to csv
                for item in s_feats:
                    outputFile.write(item.replace(" ", ""))
                outputFile.close()
                QMessageBox.information(None, "Meldung", "Fertig!")


def exportProfilePoints():
    config = Configfile(get_config_ini_path())
    exportpfad = config.getValue("Profilentzerrung", "pfad Exportordner", "./../Jobs")
    FN_PROFILNUMMER = config.getValue("Profilentzerrung", "feldNProfNr", "prof_nr")
    FN_DEF_FOTOENTZERRPUNKT = config.getValue("Profilentzerrung", "feldNFEP", "obj_typ")
    AW_FOTOENTZERRPUNKT = config.getValue("Profilentzerrung", "attFEP", "Fotoentzerrpunkt")
    profnr, ok = QInputDialog.getText(None, "Profil", "Profilnummer eingeben")
    if ok != True:
        return

    # Linien-Layer für Profillinie aussuchen
    profLayer = T2gLayers.getLineLayer()
    profPointLayer = T2gLayers.getPointLayer()
    if not profLayer or not profPointLayer:
        return

    suchstr = '"' + FN_PROFILNUMMER + '"=' + "'" + profnr + "'"
    it = profLayer.getFeatures(QgsFeatureRequest(QgsExpression(suchstr)))
    ids = [i.id() for i in it]
    profLayer.selectByIds(ids)

    if str(profLayer.selectedFeatureCount()) == "0":
        QMessageBox.information(None, "Meldung", "Kein Profil gefunden!")
        return
    elif profLayer.selectedFeatureCount() > 1:
        QMessageBox.information(None, "Meldung", f"{profLayer.selectedFeatureCount()} Profile gefunden! Abbruch")
        return

    # Anfang Blickrichtung bestimmen
    view = None
    koordlist = []
    for feat in profLayer.selectedFeatures():
        if feat.geometry().isMultipart():
            # Multipart
            parts = feat.geometry().asGeometryCollection()
            for part in parts:
                for vertex in part.vertices():
                    koordlist.append({"x": vertex.x(), "y": vertex.y()})
            QgsMessageLog.logMessage(str(koordlist[0]["x"]), PLUGIN_NAME, Qgis.Info)
            pointAx = koordlist[0]["x"]
            pointAy = koordlist[0]["y"]
            pointBx = koordlist[-0]["x"]
            pointBy = koordlist[-0]["y"]
        else:
            # Singlepart
            pointA = feat.geometry().get()[0]
            pointB = feat.geometry().get()[-1]
            pointAx = pointA.x()
            pointAy = pointA.y()
            pointBx = pointB.x()
            pointBy = pointB.y()

        dx = pointBx - pointAx
        dy = pointBy - pointAy
        vp = [dx, dy]
        v0 = [-1, 1]
        # Lösung von hier: https://stackoverflow.com/questions/14066933/direct-way-of-computing-clockwise-angle-between-2-vectors/16544330#16544330, angepasst auf Berechnung ohne numpy
        dot = v0[0] * vp[0] + v0[1] * vp[1]  # dot product: x1*x2 + y1*y2
        det = v0[0] * vp[1] - vp[0] * v0[1]  # determinant: x1*y2 - y1*x2

        radians = math.atan2(det, dot)
        angle = math.degrees(radians)
        # negative Winkelwerte (3. und 4. Quadrant, Laufrichtung entgegen Uhrzeigersinn) in fortlaufenden Wert (181 bis 360) umrechnen
        if angle < 0:
            angle *= -1
            angle = 180 - angle + 180

        if angle <= 90:
            view = "N"
        elif angle <= 180:
            view = "W"
        elif angle <= 270:
            view = "S"
        elif angle > 270:
            view = "E"
    # Ende Blickrichtung bestimmen

    feats = []
    ok = True
    # such2 = '"obj_art"=\'Fotoentzerrpunkt\' and '
    # such2 = '"obj_typ"=\'V_Referenzierungspunkt\' and '
    # such2 = '"obj_typ"='+ '\''+ AW_FOTOENTZERRPUNKT + '\' and '
    such2 = '"' + FN_DEF_FOTOENTZERRPUNKT + '"=' + "'" + AW_FOTOENTZERRPUNKT + "' and "
    it = profPointLayer.getFeatures(QgsFeatureRequest(QgsExpression(str(such2 + suchstr))))
    QgsMessageLog.logMessage(str(such2 + suchstr), PLUGIN_NAME, Qgis.Info)
    ids = [i.id() for i in it]
    profPointLayer.selectByIds(ids)
    if profPointLayer.selectedFeatureCount() == 0:
        QMessageBox.information(None, "Meldung", "Keine Profilentzerrpunkte gefunden!")
        return

    #######
    msgout = "%s, %s, %s, %s, %s, %s, %s\n" % ("punktnr", "x", "y", "z", "profnr", "view", "pointsused")
    feats.append(msgout)
    for feat in profPointLayer.selectedFeatures():
        koordlist = []
        if feat.geometry().isMultipart():
            # Multipart
            parts = feat.geometry().asGeometryCollection()
            for part in parts:
                for vertex in part.vertices():
                    koordlist.append({"x": vertex.x(), "y": vertex.y(), "z": vertex.z()})
                    QgsMessageLog.logMessage(str(vertex.z()), PLUGIN_NAME, Qgis.Info)
            x = koordlist[0]["x"]
            y = koordlist[0]["y"]
            z = koordlist[0]["z"]
        else:
            # Singlepart
            x = feat.geometry().get().x()
            y = feat.geometry().get().y()
            z = feat.geometry().get().z()
        value = "---"
        try:
            value = str(feat["aktcode"]) + "_" + str(feat["pt_nr"])  # Fehler
        except Exception as e:
            QgsMessageLog.logMessage(str(e), PLUGIN_NAME, Qgis.Info)
            pass
        ###
        msgout = "%s, %s, %s, %s, %s, %s, %s\n" % (value, x, y, z, profnr, view, 1)
        # if feat["obj_typ"] != 'Fotoentzerrpunkt' or feat["prof_nr"] == '':
        if feat[FN_DEF_FOTOENTZERRPUNKT] != AW_FOTOENTZERRPUNKT or feat[FN_PROFILNUMMER] == "":
            ok = False
        feats.append(msgout)
    delLayer("Prof Entzerrpunkte AAR-Tool")
    box = QMessageBox()
    # ToDo: change following in: if not ok:
    if ok == False:
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Frage")
        box.setText("Manche Punkte sind keine Profilentzerrpunkte!")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        buttonY = box.button(QMessageBox.Yes)
        buttonY.setText("OK")
        buttonN = box.button(QMessageBox.No)
        buttonN.setText("Abbruch")
        box.exec_()
        if box.clickedButton() == buttonY:
            ok = True
        elif box.clickedButton() == buttonN:
            ok = False

    else:
        box = QMessageBox()
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Frage")
        box.setText("Export als ...?")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Abort)
        buttonY = box.button(QMessageBox.Yes)
        buttonY.setText("Templayer")
        buttonY.setToolTip("Erzeugt einen temporären Layer.")
        buttonN = box.button(QMessageBox.No)
        buttonN.setText("CSV-Datei")
        buttonN.setToolTip("Erzeugt eine CSV Datei.")
        buttonA = box.button(QMessageBox.Abort)
        buttonA.setText("Beides")
        buttonA.setToolTip("Erzeugt einen temporären Layer und eine CSV-Datei.")
        buttonY.setFocus()
        box.exec_()

        if box.clickedButton() == buttonN or box.clickedButton() == buttonA:
            # csv-Datei
            output_file = QFileDialog.getSaveFileName(
                None,
                "Speicherpfad",
                QgsProject.instance().readPath(exportpfad),
                "Excel (*.csv);;Excel (*.txt);;Alle Dateien (*.*)",
            )
            if output_file[0] != "":
                # write to csv
                output_file = open(output_file[0], "w")
                for item in feats:
                    output_file.write(item.replace(" ", ""))
                output_file.close()
        vl = None
        if box.clickedButton() == buttonY or box.clickedButton() == buttonA:
            # templayer erzeugen
            vl = QgsVectorLayer("Point", "Prof Entzerrpunkte AAR-Tool", "memory")
            # change memorylayer crs to layer crs
            vl.setCrs(profPointLayer.crs())
            pr = vl.dataProvider()
            pr.addAttributes(
                [
                    QgsField("punktnr", QVariant.String, "text"),
                    QgsField("x", QVariant.Double, "double"),
                    QgsField("y", QVariant.Double, "double"),
                    QgsField("z", QVariant.Double, "double"),
                    QgsField("profilnr", QVariant.Int, "integer"),
                    QgsField("view", QVariant.String, "text"),
                    QgsField("points used", QVariant.Int, "integer"),
                ]
            )
            vl.updateFields()
            feat = QgsFeature()
            for item in feats:
                it = item.split(",")
                point = QgsPoint(float(it[1]), float(it[2]), float(it[3]))
                feat.setGeometry(QgsGeometry(point))
                feat.setAttributes([str(it[0]), point.x(), point.y(), point.z(), int(it[4]), str(it[5]), int(it[6])])
                pr.addFeatures([feat])
                # QgsMessageLog.logMessage(str(it[1]), 'T2G Archäologie', Qgis.Info)
            # add memorylayer to canvas
            QgsProject.instance().addMapLayer(vl, False)
            root = QgsProject.instance().layerTreeRoot()
            g = root.findGroup("Vermessung")
            if g is None:
                g = root.addGroup("Vermessung")
            g.insertChildNode(0, QgsLayerTreeLayer(vl))
        delSelectFeature()
