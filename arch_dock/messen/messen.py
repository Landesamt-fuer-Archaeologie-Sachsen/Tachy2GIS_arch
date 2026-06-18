import logging
import math
import os
import uuid
from contextlib import contextmanager
from datetime import date, datetime

from qgis.PyQt import uic, sip
from qgis.PyQt.QtCore import Qt, QTimer, QVariant, QEvent, QObject
from qgis.PyQt.QtGui import QColor, QCursor, QIcon, QKeySequence
from qgis.PyQt.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QLineEdit,
    QMenu,
    QMessageBox,
    QHeaderView,
    QTableWidgetItem,
    QShortcut,
    QWidget,
)
from qgis.core import (
    Qgis,
    QgsFeature,
    QgsGeometry,
    QgsLineString,
    QgsMessageLog,
    QgsSnappingUtils,
    QgsPoint,
    QgsPointXY,
    QgsPolygon,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
    QgsVectorLayerUtils,
    QgsWkbTypes,
    QgsApplication,
)
from qgis.gui import QgsMapTool, QgsSnapIndicator, QgsRubberBand, QgsVertexMarker
from qgis.utils import iface

from ...settings import PLUGIN_NAME
from .autoattributes import getComboboxModelFromLayerConfig, clearAutoAttributeProjectVariables
from ...icons import ICON_PATHS
from ...common.utils import (
    enableAndDisableWidgets,
    getCustomProjectVariable,
    HelpWindow,
    isNumber,
    maxValue,
    setCustomProjectVariable,
    showAndHideWidgets,
)
from ...common.layers import T2gLayers, findLayerInProject, layerHasPendingChanges


LOGGER = logging.getLogger(__name__)

layers = {"polygons": T2gLayers.Polygon.value, "lines": T2gLayers.Line.value, "points": T2gLayers.Point.value}

connectedSignalsDict = {}

WIDGET, BASE = uic.loadUiType(os.path.join(os.path.dirname(__file__), "forms", "messen.ui"))


class MeasurementTab(BASE, WIDGET):
    cmbLayerType: QComboBox
    schnitt_nr: QLineEdit
    planum_nr: QLineEdit
    bef_nr: QLineEdit
    prof_nr: QLineEdit
    pt_nr: QLineEdit
    fund_nr: QLineEdit
    probe_nr: QLineEdit

    def __init__(self):

        super().__init__(iface.mainWindow())
        self.setupUi(self)

        self.insertAtIndex = -1
        self.coordsTableRowCount = 0
        self.vertices = None
        self.geometryType = None
        self.verticesCount = 0

        self.actionDigitize = QAction()
        self.actionDigitize.setCheckable(True)
        self.digitizeTool = None
        self.markersAndRubberBand = None
        self.layerToEdit = None

        self.nextIdUpdater = None
        self._tachyDock = None

        self.setGuiContent()
        self.cbAttributeFormular.setIcon(QIcon(QgsApplication.iconPath("mActionOpenTableEdited.svg")))
        self.cbStartEditing.setIcon(QIcon(QgsApplication.iconPath("mActionToggleEditing.svg")))
        self.cbSound.setIcon(QIcon(ICON_PATHS["Sound"]))
        self.connectSignals()

        self.keys = []
        self.createKeys()

        self.helpWindow = HelpWindow()

    @property
    def tachyDock(self):
        if not self._tachyDock:
            self._tachyDock = iface.mainWindow().findChild(QWidget, "VtkViewer")
        if not self._tachyDock:
            LOGGER.warning("Could not find VtkViewer dock widget in the main window.")
        return self._tachyDock

    def setupUi(self, dialog):
        super().setupUi(dialog)
        for cmb in self.findChildren(QComboBox):
            cmb.installEventFilter(self)

    def createKeys(self):

        self.createKey(QKeySequence(Qt.Key_Return), iface.mapCanvas(), self.saveGeometry)
        self.createKey(QKeySequence(Qt.Key_Return), self, self.saveGeometry)
        self.createKey(QKeySequence(Qt.Key_Enter), iface.mapCanvas(), self.saveGeometry)
        self.createKey(QKeySequence(Qt.Key_Enter), self, self.saveGeometry)

        self.createKey(QKeySequence("Shift+L"), iface.mapCanvas(), self.deleteCurrentDigitizing)
        self.createKey(QKeySequence("Shift+L"), self, self.deleteCurrentDigitizing)

        self.createKey(QKeySequence("Shift+Z"), iface.mapCanvas(), self.deleteLastVertexFromCoordsTable)
        self.createKey(QKeySequence("Shift+Z"), self, self.deleteLastVertexFromCoordsTable)

        self.createKey(QKeySequence("Shift+K"), iface.mapCanvas(), self.openCloseCoordinatesGroupBox)
        self.createKey(QKeySequence("Shift+K"), self, self.openCloseCoordinatesGroupBox)

        self.createKey(QKeySequence("Shift+A"), iface.mapCanvas(), self.openCloseAttributesGroupBox)
        self.createKey(QKeySequence("Shift+A"), self, self.openCloseAttributesGroupBox)

        self.createKey(QKeySequence("Shift+N"), iface.mapCanvas(), self.openCloseNumberGroupBox)
        self.createKey(QKeySequence("Shift+N"), self, self.openCloseNumberGroupBox)

        self.createKey(QKeySequence("Shift+M"), iface.mapCanvas(), self.openCloseMeasurementPointsGroupBox)
        self.createKey(QKeySequence("Shift+M"), self, self.openCloseMeasurementPointsGroupBox)

    def createKey(self, sequence, parent, slot):
        shortcut = QShortcut(sequence, parent)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(slot)
        self.keys.append(shortcut)

    def activateKeys(self):
        for key in self.keys:
            key.setEnabled(True)

    def deactivateKeys(self):
        for key in self.keys:
            key.setEnabled(False)

    def setGuiContent(self):
        self.adjustElementsAtStart()
        self.fillTxtReference()
        self.fillCmbLayerType()
        self.fillCmbPolygonDigitizingMode()
        self.createCoordsTable()
        self.createMeasurementPointsTable()

    def connectSignals(self):
        self.cbFixTxtReference.stateChanged.connect(self.setReferenceNumberProjectVariable)
        self.cmbLayerType.currentIndexChanged.connect(self.adjustDigitizingToGeometryType)
        iface.mapCanvas().mapToolSet.connect(self.setDigitizeAction)
        connectedSignalsDict["setDigitizeAction"] = self.setDigitizeAction
        self.actionDigitize.triggered.connect(self.activateDigitizeTool)
        self.btnClear.clicked.connect(self.deleteCurrentDigitizing)
        self.coordsTableWidget.cellChanged.connect(self.setNewCoordinate)
        self.coordsTableWidget.customContextMenuRequested.connect(self.openCoordsTableMenu)
        self.coordsTableWidget.itemSelectionChanged.connect(self.highlightMarker)
        self.measurementsTableWidget.cellClicked.connect(self.zoomToAndSelectFeature)
        self.btnCreateFeature.clicked.connect(self.saveGeometry)
        self.cmbObjectType_1.currentIndexChanged.connect(self.comboObjectTypeChanged)
        self.cmbObjectType_2.currentIndexChanged.connect(self.comboObjectArtChanged)
        self.cmbObjectType_3.currentIndexChanged.connect(self.comboObjectSpezChanged)
        self.cmbMaterial.currentIndexChanged.connect(self.comboMaterialChanged)
        self.cmbMaterial2.currentIndexChanged.connect(self.comboMaterial2Changed)
        self.cmbZeit.currentIndexChanged.connect(self.comboZeitChanged)
        self.cmbZeit2.currentIndexChanged.connect(self.comboZeit2Changed)
        self.btnResetAutoAttributes.clicked.connect(self.resetAutoAttributeValues)
        self.cbActivateAutoAttributes.stateChanged.connect(self.setAutoAttributeMode)
        self.schnitt_nr.editingFinished.connect(self.onLineEditingFinished)
        self.planum_nr.editingFinished.connect(self.onLineEditingFinished)
        self.bef_nr.editingFinished.connect(self.onLineEditingFinished)
        self.prof_nr.editingFinished.connect(self.onLineEditingFinished)
        self.pt_nr.editingFinished.connect(self.onLineEditingFinished)
        self.fund_nr.editingFinished.connect(self.onLineEditingFinished)
        self.probe_nr.editingFinished.connect(self.onLineEditingFinished)
        self.btnHelp.clicked.connect(self.showHelp)

    def resetMeasurementTab(self):
        self.leaveDigitizingMode()
        self.resetTabToBeginning()
        self.fillTxtReference()
        self.reconnectSignals()

    def closeMeasurementTab(self):
        self.leaveDigitizingMode()
        self.resetTabToBeginning()
        self.disconnectSignals()
        self.deactivateKeys()
        if self.nextIdUpdater:
            self.nextIdUpdater.stop()

    def reconnectSignals(self):
        iface.mapCanvas().mapToolSet.connect(self.setDigitizeAction)
        connectedSignalsDict["setDigitizeAction"] = self.setDigitizeAction

    def disconnectSignals(self):
        signal = connectedSignalsDict.get("setDigitizeAction")
        if signal:
            iface.mapCanvas().mapToolSet.disconnect(signal)
            connectedSignalsDict.pop("setDigitizeAction")

    def fillCmbLayerType(self):
        cmbLayerTypeDict = {
            "no_layer": {"description": "Keine Auswahl", "icon": QIcon()},
            "polygons": {"description": "Polygone", "icon": QIcon(QgsApplication.iconPath("mActionCapturePolygon"))},
            "lines": {"description": "Linien", "icon": QIcon(QgsApplication.iconPath("mActionCaptureLine"))},
            "points": {"description": "Punkte", "icon": QIcon(QgsApplication.iconPath("mActionCapturePoint"))},
        }

        for editingTypeValue, editingTypeInfo in cmbLayerTypeDict.items():
            self.cmbLayerType.addItem(editingTypeInfo["icon"], editingTypeInfo["description"], editingTypeValue)

    def createCoordsTable(self):
        self.coordsTableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.coordsTableWidget.horizontalHeader().setStretchLastSection(True)
        self.coordsTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def createMeasurementPointsTable(self):
        self.measurementsTableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.measurementsTableWidget.horizontalHeader().setStretchLastSection(True)
        self.measurementsTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def setDigitizeAction(self, e):
        try:
            if e.toolName() not in [
                "digitizepolygons_tachy2gis",
                "digitizelines_tachy2gis",
                "digitizepoints_tachy2gis",
            ]:
                self.actionDigitize.setChecked(False)
        except Exception as e:
            QgsMessageLog.logMessage(
                message="MeasurementTab->setDigitizeAction: " + str(e),
                tag=PLUGIN_NAME,
                level=Qgis.MessageLevel.Warning,
            )
            return

    def findLayerToEdit(self, geometryType):
        mapLayers = QgsProject.instance().mapLayers()
        for geomType, layerName in layers.items():
            if geometryType == geomType:
                for lyr in mapLayers.values():
                    if lyr.name() == layerName:
                        iface.setActiveLayer(lyr)
                        return lyr
        return None

    def adjustElementsAtStart(self):
        self.cbFixTxtReference.setCheckState(0)

        self.cmbLayerType.setCurrentIndex(0)

        self.cmbLayerType.setEnabled(False)

        widgetsToShow = []

        widgetsToHide = [
            self.btnDigitizeTool,
            self.qgsGroupBoxAttributes,
            self.qgsGroupBoxCoordinates,
            self.cmbPolygonDigitizingMode,
            self.widgetDigitizingButtons,
            self.qgsGroupBoxNextValues,
            self.qgsGroupBoxMeasurementPoints,
        ]

        showAndHideWidgets(widgetsToShow, widgetsToHide)

    def fillTxtReference(self):
        referenceNumber = getCustomProjectVariable("aktcode")
        if referenceNumber != QVariant():
            self.txtReference.setText(referenceNumber)

    def fillCmbPolygonDigitizingMode(self):

        cmbPolygonDigitizingMode = {
            "free": {"description": "Frei", "icon": QIcon(ICON_PATHS["free"])},
            "circle_2_points_radius": {
                "description": "Kreis mit 2 Punkten (Radius)",
                "icon": QIcon(ICON_PATHS["circle_2_points_radius"]),
            },
            "circle_2_points_diameter": {
                "description": "Kreis mit 2 Punkten (Durchmesser)",
                "icon": QIcon(ICON_PATHS["circle_2_points_diameter"]),
            },
            "rectangle": {"description": "Rechteck", "icon": QIcon(ICON_PATHS["rectangle"])},
        }

        for editingTypeValue, editingTypeInfo in cmbPolygonDigitizingMode.items():
            self.cmbPolygonDigitizingMode.addItem(
                editingTypeInfo["icon"], editingTypeInfo["description"], editingTypeValue
            )

    def setReferenceNumberProjectVariable(self):
        if not self.cbFixTxtReference.isChecked():
            self.resetTabToBeginning()
            self.deactivateKeys()
            return

        referenceNumber = self.txtReference.text()
        if referenceNumber == "":
            iface.messageBar().pushMessage(PLUGIN_NAME, "Bitte eine Maßnahmennummer angeben")
            self.cbFixTxtReference.setCheckState(0)
            return

        self.createObjectsForTachy2GisWatch()

        setCustomProjectVariable("aktcode", referenceNumber)
        enableAndDisableWidgets([self.cmbLayerType], [self.txtReference])
        self.activateKeys()
        self.nextIdUpdater = NextIdUpdater(
            layers=T2gLayers.getEditLayers(),
            widgets={
                "bef_nr": self.txtNextBef,
                "prof_nr": self.txtNextProf,
                "fund_nr": self.txtNextFund,
                "probe_nr": self.txtNextProb,
            },
            parent=self,
        )
        self.nextIdUpdater.start()

    def resetTabToBeginning(self):
        enableAndDisableWidgets([self.txtReference], [self.cmbLayerType])
        self.adjustElementsAtStart()
        iface.actionPan().trigger()

    def setTachy2GisToGeometry(self, geometryType):
        if geometryType == "polygons":
            self.tachyDock.targetLayerComboBox.setCurrentText("E_Polygon")
            self.tachyDock.sourceLayerComboBox.setCurrentText("E_Polygon")
        elif geometryType == "lines":
            self.tachyDock.targetLayerComboBox.setCurrentText("E_Line")
            self.tachyDock.sourceLayerComboBox.setCurrentText("E_Line")
        elif geometryType == "points":
            self.tachyDock.targetLayerComboBox.setCurrentText("E_Point")
            self.tachyDock.sourceLayerComboBox.setCurrentText("E_Point")
        self.tachyDock.setPickable()

    def activateDigitizeTool(self):
        if self.actionDigitize.isChecked():
            iface.mapCanvas().setMapTool(self.digitizeTool)
        else:
            iface.actionPan().trigger()

    def resetDigitizing(self):
        self.updatePointCount()
        self.coordsTableWidget.setRowCount(0)
        self.insertAtIndex = -1
        self.coordsTableRowCount = 0
        if self.markersAndRubberBand:
            self.markersAndRubberBand.removeMarkersAndRubberBand()

    def leaveDigitizingMode(self):
        self.cmbLayerType.setCurrentIndex(0)

    def adjustDigitizingToGeometryType(self):

        iface.actionPan().trigger()
        geometryType = self.cmbLayerType.currentData()

        self.resetObjectsForTachy2GisWatch()
        self.resetDigitizing()

        if geometryType == "no_layer":
            showAndHideWidgets(
                [],
                [
                    self.btnDigitizeTool,
                    self.qgsGroupBoxAttributes,
                    self.cmbPolygonDigitizingMode,
                    self.widgetDigitizingButtons,
                    self.qgsGroupBoxNextValues,
                    self.qgsGroupBoxCoordinates,
                    self.qgsGroupBoxMeasurementPoints,
                ],
            )
            if self.digitizeTool:
                self.digitizeTool = None
            if self.markersAndRubberBand:
                self.markersAndRubberBand = None
            self.geometryType = None
            return

        self.layerToEdit = self.findLayerToEdit(geometryType)
        if not self.layerToEdit:
            iface.messageBar().pushMessage(
                PLUGIN_NAME, f"Bitte den Layer {layers[geometryType]} ins Projekt laden", Qgis.Warning
            )
            self.cmbLayerType.setCurrentIndex(0)
            return
        if layerHasPendingChanges(self.layerToEdit):
            iface.messageBar().pushMessage(
                PLUGIN_NAME,
                f"Der Layer {layers[geometryType]} ist im Editiermodus. Bitte das Editieren beenden.",
                Qgis.Warning,
            )
            self.cmbLayerType.setCurrentIndex(0)
            return

        showAndHideWidgets(
            [
                self.btnDigitizeTool,
                self.qgsGroupBoxCoordinates,
                self.qgsGroupBoxNextValues,
                self.qgsGroupBoxMeasurementPoints,
                self.widgetDigitizingButtons,
            ],
            [],
        )

        self.markersAndRubberBand = self.createMarkersAndRubberBand(geometryType)

        self.actionDigitize.setIcon(self.cmbLayerType.itemIcon(self.cmbLayerType.currentIndex()))
        self.digitizeTool = DigitizeTool(geometryType, self)
        self.btnDigitizeTool.setDefaultAction(self.actionDigitize)

        self.setTachy2GisToGeometry(geometryType)

        if geometryType == "polygons":
            self.actionDigitize.setText("Polygone zeichnen")
            showAndHideWidgets([self.qgsGroupBoxAttributes, self.cmbPolygonDigitizingMode], [])

        elif geometryType == "lines":
            self.actionDigitize.setText("Linien zeichnen")
            showAndHideWidgets([self.qgsGroupBoxAttributes], [self.cmbPolygonDigitizingMode])

        elif geometryType == "points":
            self.actionDigitize.setText("Punkte zeichnen")
            showAndHideWidgets([self.qgsGroupBoxAttributes], [self.cmbPolygonDigitizingMode])
        self.geometryType = geometryType
        self.adjustAutoAttributes()
        self.startTachyWatch()

    def setAutoAttributeMode(self, state: int):
        setCustomProjectVariable("autoAttribute", bool(state))

    def adjustAutoAttributes(self):
        self.fillComboObjectType()
        if not self.cmbMaterial.count():
            self.fillComboMaterial()
        if not self.cmbZeit.count():
            self.fillComboZeit()

        self.cmbObjectType_3.setEnabled(self.geometryType == "polygons")

        self.resetAutoAttributeValues()

    def comboObjectTypeChanged(self):
        self.fillComboObjectArt()
        setCustomProjectVariable(f"obj_typ_{self.geometryType}", self.cmbObjectType_1.currentData())

        objArtGeometry = getCustomProjectVariable(f"obj_art_{self.geometryType}")
        if objArtGeometry:
            self.cmbObjectType_2.setCurrentIndex(self.cmbObjectType_2.findData(objArtGeometry))

    def comboObjectArtChanged(self):
        setCustomProjectVariable(f"obj_art_{self.geometryType}", self.cmbObjectType_2.currentData())
        if self.geometryType != "polygons":
            return

        self.fillComboObjectSpez()

        objSpezGeometry = getCustomProjectVariable(f"obj_spez_{self.geometryType}")
        if objSpezGeometry:
            self.cmbObjectType_3.setCurrentIndex(self.cmbObjectType_3.findData(objSpezGeometry))

    def comboObjectSpezChanged(self):
        setCustomProjectVariable(f"obj_spez_{self.geometryType}", self.cmbObjectType_3.currentData())

    def comboMaterialChanged(self):
        setCustomProjectVariable("material", self.cmbMaterial.currentData())
        self.fillComboMaterial2()

        material2 = getCustomProjectVariable("material_zwei")
        if material2:
            self.cmbMaterial2.setCurrentIndex(self.cmbMaterial2.findData(material2))

    def comboMaterial2Changed(self):
        setCustomProjectVariable("material_zwei", self.cmbMaterial2.currentData())

    def comboZeitChanged(self):
        setCustomProjectVariable("zeit", self.cmbZeit.currentData())
        self.fillComboZeit2()

        zeit2 = getCustomProjectVariable("zeit_zwei")
        if zeit2:
            self.cmbZeit2.setCurrentIndex(self.cmbZeit2.findData(zeit2))

    def comboZeit2Changed(self):
        setCustomProjectVariable("zeit_zwei", self.cmbZeit2.currentData())

    def resetAutoAttributeValues(self):
        self.cmbObjectType_1.setCurrentIndex(0)
        self.cmbObjectType_2.setCurrentIndex(0)
        self.cmbObjectType_3.setCurrentIndex(0)
        self.schnitt_nr.clear()
        self.planum_nr.clear()
        self.bef_nr.clear()
        self.prof_nr.clear()
        self.pt_nr.clear()
        self.fund_nr.clear()
        self.probe_nr.clear()
        self.cmbMaterial.setCurrentIndex(0)
        self.cmbMaterial2.setCurrentIndex(0)
        self.cmbZeit.setCurrentIndex(0)
        self.cmbZeit2.setCurrentIndex(0)

        clearAutoAttributeProjectVariables()

    def _incrementValue(self, text):
        for sep in ('_', '.'):
            if sep in text:
                prefix, suffix = text.rsplit(sep, 1)
                try:
                    return prefix + sep + str(int(suffix) + 1)
                except ValueError:
                    continue
        try:
            return str(int(text) + 1)
        except ValueError:
            return text

    def incrementAutoAttributes(self):
        fields = [
            (self.cbIncrementBef, self.bef_nr),
            (self.cbIncrementProf, self.prof_nr),
            (self.cbIncrementPt, self.pt_nr),
            (self.cbIncrementFund, self.fund_nr),
            (self.cbIncrementProbe, self.probe_nr),
        ]
        for checkbox, lineEdit in fields:
            if checkbox.isChecked() and lineEdit.text():
                newValue = self._incrementValue(lineEdit.text())
                lineEdit.setText(newValue)
                setCustomProjectVariable(lineEdit.objectName(), newValue)

    @contextmanager
    def blockSignalsObjTypes(self):
        self.cmbObjectType_1.blockSignals(True)
        self.cmbObjectType_2.blockSignals(True)
        self.cmbObjectType_3.blockSignals(True)
        try:
            yield
        finally:
            self.cmbObjectType_1.blockSignals(False)
            self.cmbObjectType_2.blockSignals(False)
            self.cmbObjectType_3.blockSignals(False)

    def fillComboObjectType(self):
        with self.blockSignalsObjTypes():
            self.cmbObjectType_1.clear()
            self.cmbObjectType_2.clear()
            self.cmbObjectType_3.clear()
            obj_types = getComboboxModelFromLayerConfig(self.layerToEdit, "obj_typ")
            self.cmbObjectType_1.addItem("", None)
            for fid, description in obj_types.items():
                self.cmbObjectType_1.addItem(description, fid)

    def fillComboObjectArt(self):
        with self.blockSignalsObjTypes():
            self.cmbObjectType_2.clear()
            self.cmbObjectType_3.clear()
            obj_types = getComboboxModelFromLayerConfig(
                self.layerToEdit, "obj_art", {"obj_typ": self.cmbObjectType_1.currentData()}
            )
            self.cmbObjectType_2.addItem("", None)
            for fid, description in obj_types.items():
                self.cmbObjectType_2.addItem(description, fid)

    def fillComboObjectSpez(self):
        with self.blockSignalsObjTypes():
            self.cmbObjectType_3.clear()

            obj_types = getComboboxModelFromLayerConfig(
                self.layerToEdit,
                "obj_spez",
                {"obj_typ": self.cmbObjectType_1.currentData(), "obj_art": self.cmbObjectType_2.currentData()},
            )
            self.cmbObjectType_3.addItem("", None)
            for fid, description in obj_types.items():
                self.cmbObjectType_3.addItem(description, fid)

    def fillComboMaterial(self):
        self.cmbMaterial.blockSignals(True)
        self.cmbMaterial2.clear()
        self.cmbMaterial.clear()
        materials = getComboboxModelFromLayerConfig(self.layerToEdit, "material")
        self.cmbMaterial.addItem("", None)
        for fid, description in materials.items():
            if all((fid, description)):
                self.cmbMaterial.addItem(description, fid)
        self.cmbMaterial.blockSignals(False)

    def fillComboMaterial2(self):
        self.cmbMaterial2.blockSignals(True)
        self.cmbMaterial2.clear()
        materials = getComboboxModelFromLayerConfig(
            self.layerToEdit,
            "material_zwei",
            {"material": self.cmbMaterial.currentData()},
        )
        self.cmbMaterial2.addItem("", None)
        for fid, description in materials.items():
            if all((fid, description)):
                self.cmbMaterial2.addItem(description, fid)
        self.cmbMaterial2.blockSignals(False)

    def fillComboZeit(self):
        self.cmbZeit.blockSignals(True)
        self.cmbZeit2.clear()
        self.cmbZeit.clear()
        epochen = getComboboxModelFromLayerConfig(self.layerToEdit, "zeit")
        self.cmbZeit.addItem("", None)
        for fid, description in epochen.items():
            if all((fid, description)):
                self.cmbZeit.addItem(description, fid)
        self.cmbZeit.blockSignals(False)

    def fillComboZeit2(self):
        self.cmbZeit2.blockSignals(True)
        self.cmbZeit2.clear()
        epochen = getComboboxModelFromLayerConfig(
            self.layerToEdit,
            "zeit_zwei",
            {"zeit": self.cmbZeit.currentData()},
        )
        self.cmbZeit2.addItem("", None)
        for fid, description in epochen.items():
            if all((fid, description)):
                self.cmbZeit2.addItem(description, fid)
        self.cmbZeit2.blockSignals(False)

    def createMarkersAndRubberBand(self, geometryType):
        if geometryType == "polygons":
            geom = QgsWkbTypes.PolygonGeometry
        elif geometryType == "lines":
            geom = QgsWkbTypes.LineGeometry
        elif geometryType == "points":
            geom = QgsWkbTypes.PointGeometry
        return MarkersAndRubberBand(geom)

    def createObjectsForTachy2GisWatch(self):
        self.vertices = self.tachyDock.vtk_mouse_interactor_style.vertices
        self.watch = QTimer(self)
        self.verticesCount = 0
        self.watch.timeout.connect(self.watchevent)

    def resetObjectsForTachy2GisWatch(self):
        if self.vertices:
            self.vertices.clear()
        self.stopTachyWatch()
        self.tachyDock.vtk_mouse_interactor_style.draw()
        self.verticesCount = 0

    def deleteCurrentDigitizing(self):
        self.resetObjectsForTachy2GisWatch()
        self.resetDigitizing()

    def startTachyWatch(self):
        self.watch.start(150)

    def stopTachyWatch(self):
        self.watch.stop()

    def watchevent(self):
        # Check for new points in 3D viewer
        pointsInTachy2Gis3D = len(self.vertices)
        if pointsInTachy2Gis3D > self.verticesCount:
            self.verticesCount += 1
            x, y, z = self.vertices[-1][0], self.vertices[-1][1], self.vertices[-1][2]
            self.addRowToTable(x, y, z)
            self.markersAndRubberBand.updateVertex(x, y)
            self.beepSound()

    def addRowToTable(self, x, y, z):
        coordsTable = self.coordsTableWidget
        numberRows = coordsTable.rowCount()
        coordsTable.insertRow(numberRows)
        coordsTable.setItem(numberRows, 0, QTableWidgetItem(str(x)))
        coordsTable.setItem(numberRows, 1, QTableWidgetItem(str(y)))
        coordsTable.setItem(numberRows, 2, QTableWidgetItem(str(z)))
        self.updatePointCount()

    def setNewCoordinate(self, row, column):
        if self.coordsTableWidget.rowCount() != self.coordsTableRowCount:
            if column == 2:
                self.coordsTableRowCount = self.coordsTableWidget.rowCount()
            return
        oldCoordinate = self.vertices[row][column]
        try:
            newCoordinate = float(self.coordsTableWidget.item(row, column).text().replace(',', '.'))
            if oldCoordinate != newCoordinate:
                self.markersAndRubberBand.removeHighlightMarkers()
                x, y, z = self.vertices[row]
                if column == 0:
                    x = newCoordinate
                elif column == 1:
                    y = newCoordinate
                elif column == 2:
                    z = newCoordinate
                self.vertices[row] = (x, y, z)
                self.tachyDock.vtk_mouse_interactor_style.draw()
                self.markersAndRubberBand.updateVertex(x, y, row, False)
                self.markersAndRubberBand.setHightlightMarkers([(x, y)])
        except:
            self.coordsTableWidget.setItem(row, column, oldCoordinate)

    def openCoordsTableMenu(self, pos):
        coordsTableMenu = QMenu()
        delVertex = coordsTableMenu.addAction(QIcon(ICON_PATHS["delete_vertex"]), " Vertex löschen")
        delVertex.triggered.connect(self.deleteVertexFromCoordsTable)
        addVertex = coordsTableMenu.addAction(QIcon(ICON_PATHS["add_vertex"]), " Vertex hinzufügen")
        addVertex.triggered.connect(self.setInsertAtIndex)
        coordsTableMenu.exec_(QCursor.pos())

    def deleteVertexFromCoordsTable(self):
        self.verticesCount -= 1
        vertexIndex = self.coordsTableWidget.currentRow()
        self.coordsTableWidget.removeRow(vertexIndex)
        self.coordsTableRowCount -= 1
        self.markersAndRubberBand.deleteVertex(vertexIndex)
        self.updatePointCount()

        self.vertices.pop(vertexIndex)
        self.tachyDock.vtk_mouse_interactor_style.draw()

    def deleteLastVertexFromCoordsTable(self):
        if self.verticesCount >= 1:
            self.verticesCount -= 1
            self.coordsTableWidget.removeRow(self.verticesCount)
            self.coordsTableRowCount -= 1
            self.markersAndRubberBand.deleteVertex(self.verticesCount)
            self.updatePointCount()

            self.vertices.pop(self.verticesCount)
            self.tachyDock.vtk_mouse_interactor_style.draw()

    def setInsertAtIndex(self):
        self.insertAtIndex = self.coordsTableWidget.currentRow() + 1

    def highlightMarker(self):
        if self.markersAndRubberBand:
            selectedCoords = []
            for item in self.coordsTableWidget.selectedItems():
                row = item.row()
                x = self.vertices[row][0]
                y = self.vertices[row][1]
                selectedCoords.append((x, y))

            self.markersAndRubberBand.setHightlightMarkers(selectedCoords)

    def createGeometry(self):
        qgsPoints = [QgsPoint(vertex[0], vertex[1], vertex[2]) for vertex in self.vertices]

        if self.geometryType == "polygons":
            polygonGeometryType = self.cmbPolygonDigitizingMode.currentData()
            if polygonGeometryType == "free":
                return QgsPolygon(QgsLineString(qgsPoints))
            elif polygonGeometryType == "circle_2_points_radius":
                return self.createCircleRadiusGeometry()
            elif polygonGeometryType == "circle_2_points_diameter":
                return self.createCircleDiameterGeometry()
            elif polygonGeometryType == "rectangle":
                return self.createRectangleGeometry()
        elif self.geometryType == "lines":
            return QgsLineString(qgsPoints)
        elif self.geometryType == "points":
            return qgsPoints
        return None

    def createCircleRadiusGeometry(self):
        if self.verticesCount > 2:
            iface.messageBar().pushMessage(
                PLUGIN_NAME, f"Nur zwei Punkte erlaubt (Modus: Kreis mit 2 Punkten (Radius))", Qgis.Warning
            )
            return False
        point1 = QgsPoint(float(self.vertices[0][0]), float(self.vertices[0][1]), float(self.vertices[0][2]))
        point2 = QgsPoint(float(self.vertices[1][0]), float(self.vertices[1][1]), float(self.vertices[1][2]))
        radius = point1.distance3D(point2)
        geom = self.createCircleGeometry(point1, radius, 30)
        return geom

    def createCircleDiameterGeometry(self):
        if self.verticesCount > 2:
            iface.messageBar().pushMessage(
                PLUGIN_NAME, f"Nur zwei Punkte erlaubt (Modus: Kreis mit 2 Punkten (Durchmesser))", Qgis.Warning
            )
            return False
        point1 = QgsPoint(float(self.vertices[0][0]), float(self.vertices[0][1]), float(self.vertices[0][2]))
        point2 = QgsPoint(float(self.vertices[1][0]), float(self.vertices[1][1]), float(self.vertices[1][2]))
        x = (point1.x() + point2.x()) / 2
        y = (point1.y() + point2.y()) / 2
        center = QgsPoint((point1.x() + point2.x()) / 2, (point1.y() + point2.y()) / 2, float(self.vertices[1][2]))
        radius = point1.distance3D(center)
        geom = self.createCircleGeometry(center, radius, 30)
        return geom

    def createRectangleGeometry(self):
        if self.verticesCount > 2:
            iface.messageBar().pushMessage(PLUGIN_NAME, f"Nur zwei Punkte erlaubt (Modus: Rechteck))", Qgis.Warning)
            return False
        point1 = QgsPoint(float(self.vertices[0][0]), float(self.vertices[0][1]), float(self.vertices[0][2]))
        point2 = QgsPoint(float(self.vertices[1][0]), float(self.vertices[1][1]), float(self.vertices[1][2]))
        rect = QgsRectangle(point1.x(), point1.y(), point2.x(), point2.y())
        geom = QgsGeometry.fromRect(rect)
        return geom

    def createCircleGeometry(self, point, radius, segments):
        pts = []
        for i in range(segments):
            theta = i * (2.0 * math.pi / segments)
            p = QgsPoint(point.x() + radius * math.cos(theta), point.y() + radius * math.sin(theta), point.z())
            pts.append(p)
        pts.append(pts[0])
        return QgsGeometry.fromPolyline(pts)

    def checkGeometry(self, geom):
        if self.geometryType == "polygons" or self.geometryType == "lines":
            if isinstance(geom, QgsPolygon) or isinstance(geom, QgsLineString):
                geomClone = geom.clone()
                return QgsGeometry(geomClone).isGeosValid()
            elif isinstance(geom, QgsGeometry):
                return geom.isGeosValid()
            else:
                return False

    def createFeatureFromGeometry(self, geom: QgsGeometry):
        uuidFieldIndex = self.layerToEdit.dataProvider().fieldNameIndex("obj_uuid")
        attr = {uuidFieldIndex: "{" + str(uuid.uuid4()) + "}"}
        feature = QgsVectorLayerUtils.createFeature(layer=self.layerToEdit, geometry=QgsGeometry(geom), attributes=attr)
        return feature

    def createFeaturesFromPoints(self, points: list[QgsPoint]):
        uuidFieldIndex = self.layerToEdit.dataProvider().fieldNameIndex("obj_uuid")
        featuresData = [
            QgsVectorLayerUtils.QgsFeatureData(
                geometry=QgsGeometry(pt), attributes={uuidFieldIndex: "{" + str(uuid.uuid4()) + "}"}
            )
            for pt in points
        ]
        features = QgsVectorLayerUtils.createFeatures(self.layerToEdit, featuresData)
        return features

    def openAttributeForm(self, features):
        if not self.cbAttributeFormular.isChecked():
            return
        if not features:
            return
        feature = features[0]
        if len(features) == 1:
            iface.openFeatureForm(self.layerToEdit, feature)
        else:
            query = "fid >= " + str(feature.id())
            iface.showAttributeTable(self.layerToEdit, query)

    def saveGeometry(self):
        if not self.layerToEdit:
            return

        if layerHasPendingChanges(self.layerToEdit):
            iface.messageBar().pushMessage(
                PLUGIN_NAME,
                f"Der Layer {layers[self.geometryType]} ist im Editiermodus. Bitte das Editieren beenden.",
                Qgis.Warning,
            )
            return
        for point in self.vertices:
            if point[2] == 0:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setText("Geometrie enthält Nullhöhen. Fortfahren?")
                msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                returnValue = msgBox.exec()
                if returnValue != QMessageBox.Ok:
                    return
                break

        geom = self.createGeometry()
        if not geom:
            return

        if self.geometryType == "polygons" or self.geometryType == "lines":
            if self.checkGeometry(geom):
                feature = self.createFeatureFromGeometry(geom)
                _, features = self.layerToEdit.dataProvider().addFeatures([feature])
                self.layerToEdit.featureAdded.emit(feature.id())
            else:
                iface.messageBar().pushMessage(
                    PLUGIN_NAME, f"Die Geometrie ist ungültig. Bitte korrigieren oder löschen", Qgis.Warning
                )
                return
        elif self.geometryType == "points":
            features = []
            for i, point in enumerate(geom):
                _, added = self.layerToEdit.dataProvider().addFeatures(self.createFeaturesFromPoints([point]))
                features.extend(added)
                if i < len(geom) - 1:
                    self.incrementAutoAttributes()
            self.layerToEdit.featureAdded.emit(features[0].id())

        if features:
            self.addMeasurementPoints()
            self.addLastMeasurementsToTable(features)
            self.deleteCurrentDigitizing()
            self.startTachyWatch()
            iface.mapCanvas().refreshAllLayers()
            self.tachyDock.vtk_mouse_interactor_style.draw()
            if self.cbStartEditing.isChecked():
                self.layerToEdit.startEditing()
            self.openAttributeForm(features)
            self.incrementAutoAttributes()
            self.beepSound()

    def addMeasurementPoints(self):
        measurementPointsLayer = T2gLayers.getMesspunkteLayer()
        if not measurementPointsLayer:
            return
        measurementPointsLayer.startEditing()
        dateOfMeasurement = str(date.today())
        features = []

        for i in range(len(self.vertices)):
            x = self.vertices[i][0]
            y = self.vertices[i][1]
            z = self.vertices[i][2]
            uuidPoint = "{" + str(uuid.uuid4()) + "}"
            attL = {1: dateOfMeasurement, 4: str(x), 5: str(y), 6: str(z), 8: uuidPoint}
            pt = QgsPoint(float(x), float(y), float(z))
            features.append(
                QgsVectorLayerUtils.createFeature(
                    measurementPointsLayer, QgsGeometry(pt), attL, measurementPointsLayer.createExpressionContext()
                )
            )

        for feat in features:
            measurementPointsLayer.dataProvider().addFeatures([feat])
            QgsMessageLog.logMessage(str(x) + "|" + str(y) + "|" + str(z), "Messpunkte", Qgis.Info)

        measurementPointsLayer.commitChanges()

    def addLastMeasurementsToTable(self, features):
        for feat in features:
            timeOfMeasurement = str(datetime.now().strftime("%H:%M:%S"))
            row = self.measurementsTableWidget.rowCount()
            self.measurementsTableWidget.insertRow(row)
            self.measurementsTableWidget.setItem(row, 0, QTableWidgetItem(str(timeOfMeasurement)))
            self.measurementsTableWidget.setItem(row, 1, QTableWidgetItem(self.layerToEdit.name()))
            self.measurementsTableWidget.setItem(row, 2, QTableWidgetItem(str(feat.id())))

    def zoomToAndSelectFeature(self, row, column):
        layerName = self.measurementsTableWidget.item(row, 1).text()
        fid = int(self.measurementsTableWidget.item(row, 2).text())
        layer = findLayerInProject(layerName)
        if layer:
            layer.selectByExpression(f"fid = {fid}")
            iface.actionZoomToSelected().trigger()

    def showHelp(self):
        helpHtmPath = os.path.join(os.path.dirname(__file__), "Tips.htm")
        self.helpWindow.run(helpHtmPath, "Vermessung Kurzbefehle", None, 400, 300)

    def updatePointCount(self):
        if self.verticesCount == 1:
            self.lblPointCount.setText("1 Punkt")
        else:
            self.lblPointCount.setText(f"{self.verticesCount} Punkte")

    def onLineEditingFinished(self):
        if self.geometryType == "no_layer":
            return
        widget = self.sender()
        setCustomProjectVariable(f"{widget.objectName()}", widget.text() or None)

    def openCloseCoordinatesGroupBox(self):
        collapsed = self.qgsGroupBoxCoordinates.isCollapsed()
        self.qgsGroupBoxCoordinates.setCollapsed(not collapsed)

    def openCloseAttributesGroupBox(self):
        collapsed = self.qgsGroupBoxAttributes.isCollapsed()
        self.qgsGroupBoxAttributes.setCollapsed(not collapsed)

    def openCloseNumberGroupBox(self):
        collapsed = self.qgsGroupBoxNextValues.isCollapsed()
        self.qgsGroupBoxNextValues.setCollapsed(not collapsed)

    def openCloseMeasurementPointsGroupBox(self):
        collapsed = self.qgsGroupBoxMeasurementPoints.isCollapsed()
        self.qgsGroupBoxMeasurementPoints.setCollapsed(not collapsed)

    def beepSound(self):
        if self.cbSound.isChecked():
            QApplication.beep()

    def eventFilter(self, obj, event) -> bool:
        if isinstance(obj, QComboBox) and event.type() == QEvent.Wheel:
            event.ignore()
            return True
        return False


class NextIdUpdater(QObject):
    def __init__(self, layers: list[QgsVectorLayer], widgets: dict[str, QLineEdit], parent: QWidget = None):
        """
        Keeps the display widgets up to date with the next available IDs for the given attributes.
        This class monitors changes of all attributes (keys in the "widgets" dict) in the provided layers and updates
        the corresponding widgets when features are added, deleted, or modified.

        Args:
            layers (list[QgsVectorLayer]): List of layers to monitor.
            widgets (dict[str, QWidget]): Dictionary of widgets to update, keyed by attribute name.
                Example: {bef_nr: QLineEdit, fund_nr: QLineEdit, prof_nr: QLineEdit, probe_nr: QLineEdit}
        """
        super().__init__(parent)
        self.layers = layers
        self.widgets = widgets
        self._connected_layers: set[QgsVectorLayer] = set()

    def start(self):
        self._connectSignals()
        self._updateFromFilters()

    def stop(self):
        self.clear()
        self._disconnectSignals()

    def clear(self):
        for widget in self.widgets.values():
            widget.clear()

    def setMaxValues(self):
        for attributeName, widget in self.widgets.items():
            maxId = 0
            for layer in self._connected_layers:
                maxId = max(maxId, maxValue(layer, attributeName))
            widget.setText(str(maxId + 1))

    def _updateFromFilters(self):
        if any([layer.subsetString() for layer in self.layers]):
            for widget in self.widgets.values():
                widget.setText("xxxxx")
        else:
            self.setMaxValues()

    def _connectSignals(self):
        for layer in self.layers:
            if sip.isdeleted(layer) or layer in self._connected_layers:
                continue
            layer.editingStarted.connect(self._onEditingStarted)
            layer.featureAdded.connect(self._onFeatureAdded)
            layer.featuresDeleted.connect(self._onFeaturesDeleted)
            layer.subsetStringChanged.connect(self._onSubsetStringChanged)
            layer.attributeValueChanged.connect(self._onAttributeValueChanged)
            layer.committedFeaturesAdded.connect(self._onCommittedFeaturesAdded)
            layer.committedFeaturesRemoved.connect(self._onCommittedFeaturesRemoved)
            layer.committedAttributeValuesChanges.connect(self._onCommittedAttributeValuesChanges)
            self._connected_layers.add(layer)

    def _disconnectSignals(self):
        for layer in list(self._connected_layers):
            if sip.isdeleted(layer):
                self._connected_layers.discard(layer)
                continue
            layer.editingStarted.disconnect(self._onEditingStarted)
            layer.featureAdded.disconnect(self._onFeatureAdded)
            layer.featuresDeleted.disconnect(self._onFeaturesDeleted)
            layer.subsetStringChanged.disconnect(self._onSubsetStringChanged)
            layer.attributeValueChanged.disconnect(self._onAttributeValueChanged)
            layer.committedFeaturesAdded.disconnect(self._onCommittedFeaturesAdded)
            layer.committedFeaturesRemoved.disconnect(self._onCommittedFeaturesRemoved)
            layer.committedAttributeValuesChanges.disconnect(self._onCommittedAttributeValuesChanges)
            self._connected_layers.discard(layer)

    def _onEditingStarted(self):
        self.setMaxValues()

    def _onFeatureAdded(self, fid):
        self.setMaxValues()

    def _onFeaturesDeleted(self, fid):
        self.setMaxValues()

    def _onAttributeValueChanged(self, fid, idx, value):
        layer = self.sender()
        if not layer or sip.isdeleted(layer):
            return
        field = layer.fields()[idx]
        if not field:
            return
        if field.name() not in self.widgets:
            return
        if not isNumber(str(value)):
            return
        self.setMaxValues()

    def _onSubsetStringChanged(self):
        self._updateFromFilters()

    def _onCommittedFeaturesAdded(self, layerId: str, added: list[QgsFeature]):
        self.setMaxValues()

    def _onCommittedFeaturesRemoved(self, layerId: str, removed: set[int]):
        self.setMaxValues()

    def _onCommittedAttributeValuesChanges(self, layerId: str, changes: dict[int, dict[int, QVariant]]):
        relevant = False
        for _fid, by_idx in changes.items():
            if relevant:
                break
            # by_idx: {field_index: new_value}
            for idx in by_idx.keys():
                field = None
                layer = self.sender()
                if not layer or sip.isdeleted(layer):
                    continue
                field = layer.fields()[idx]
                if field and field.name() in self.widgets:
                    relevant = True
                    break
        if relevant:
            self.setMaxValues()


MARKERSIZE = 10
PENWIDTH = 1
MARKERTYPE = QgsVertexMarker.ICON_BOX
COLOR = QColor(255, 0, 0)
HIGHLIGHTCOLOR = QColor(0, 255, 0)
RUBBERBANDCOLOR = QColor(255, 0, 0, 50)


class MarkersAndRubberBand(QgsRubberBand):

    def __init__(self, geometryType):

        self.geometryType = geometryType
        super().__init__(iface.mapCanvas(), self.geometryType)
        self.setWidth(PENWIDTH)
        self.setColor(COLOR)
        self.setFillColor(RUBBERBANDCOLOR)
        self.setLineStyle(Qt.DashLine)
        self.points = []

        self.markerList = []
        self.highlightMarkers = []

    def removeHighlightMarkers(self):
        for marker in self.highlightMarkers:
            iface.mapCanvas().scene().removeItem(marker)
        self.highlightMarkers.clear()

    def setHightlightMarkers(self, selectedCoords):
        self.removeHighlightMarkers()
        for coords in selectedCoords:
            hightlightMarker = QgsVertexMarker(iface.mapCanvas())
            hightlightMarker.setCenter(QgsPointXY(coords[0], coords[1]))
            hightlightMarker.setColor(HIGHLIGHTCOLOR)
            hightlightMarker.setIconSize(MARKERSIZE)
            hightlightMarker.setIconType(MARKERTYPE)
            hightlightMarker.setPenWidth(PENWIDTH)
            self.highlightMarkers.append(hightlightMarker)

    def updateVertex(self, x, y, index=-1, new=True):
        self.setMarker(x, y, index, new)
        self.setRubberBandGeometry(x, y, index, new)

    def setMarker(self, x, y, index=-1, new=True):
        m = QgsVertexMarker(iface.mapCanvas())
        m.setCenter(QgsPointXY(float(x), float(y)))
        m.setColor(COLOR)
        m.setIconSize(MARKERSIZE)
        m.setIconType(MARKERTYPE)
        m.setPenWidth(PENWIDTH)
        if index != -1:
            if new:
                self.markerList.insert(index, m)
            else:
                iface.mapCanvas().scene().removeItem(self.markerList[index])
                self.markerList[index] = m
        else:
            self.markerList.append(m)

    def removeMarkersAndRubberBand(self):
        for marker in self.markerList:
            iface.mapCanvas().scene().removeItem(marker)
        self.reset(self.geometryType)
        self.points.clear()
        self.markerList.clear()

    def deleteVertex(self, vertexIndex):
        self.points.pop(vertexIndex)
        if self.geometryType == QgsWkbTypes.PolygonGeometry:
            self.setToGeometry(QgsGeometry.fromPolygonXY([self.points]))
        elif self.geometryType == QgsWkbTypes.LineGeometry:
            self.setToGeometry(QgsGeometry.fromPolylineXY(self.points))
        elif self.geometryType == QgsWkbTypes.PointGeometry:
            self.setToGeometry(QgsGeometry.fromMultiPointXY(self.points))
        markerToDelete = self.markerList[vertexIndex]
        iface.mapCanvas().scene().removeItem(markerToDelete)
        self.markerList.pop(vertexIndex)

    def setRubberBandGeometry(self, x, y, index=-1, new=True):
        point = QgsPointXY(float(x), float(y))
        if index == -1:
            if new:
                self.points.append(point)
            else:
                self.points[-1] = point
        else:
            if new:
                self.points.insert(index, point)
            else:
                self.points[index] = point
        self.reset(self.geometryType)
        if self.geometryType == QgsWkbTypes.PolygonGeometry:
            self.setToGeometry(QgsGeometry.fromPolygonXY([self.points]))
        elif self.geometryType == QgsWkbTypes.LineGeometry:
            self.setToGeometry(QgsGeometry.fromPolylineXY(self.points))
        elif self.geometryType == QgsWkbTypes.PointGeometry:
            self.setToGeometry(QgsGeometry.fromMultiPointXY(self.points))


class DigitizeTool(QgsMapTool):

    def __init__(self, geometryName, measurementGui: MeasurementTab):

        QgsMapTool.__init__(self, iface.mapCanvas())

        toolName = f"digitize{geometryName}_tachy2gis"
        self.setToolName(toolName)

        self.tachy2GisPlugin = measurementGui.tachyDock
        self.vertices = self.tachy2GisPlugin.vtk_mouse_interactor_style.vertices

        self.measurementGui = measurementGui

        self.geometryName = geometryName

        self.markersAndRubberBand = self.measurementGui.markersAndRubberBand

        self.setSnapping()

        self.connectSignals()

    def setSnapping(self):
        self.snapConfig = QgsProject.instance().snappingConfig()
        self.snapUtils = QgsSnappingUtils(iface.mapCanvas())
        self.snapUtils.setConfig(self.snapConfig)
        self.snapUtils.setMapSettings(iface.mapCanvas().mapSettings())
        self.snapIndicator = QgsSnapIndicator(iface.mapCanvas())

    def connectSignals(self):
        QgsProject.instance().snappingConfigChanged.connect(self.adjustSnappingToNewConfig)
        connectedSignalsDict["adjustSnappingToNewConfig"] = self.adjustSnappingToNewConfig

    def disconnectSignals(self):
        if connectedSignalsDict.get("adjustSnappingToNewConfig"):
            QgsProject.instance().snappingConfigChanged.disconnect(self.adjustSnappingToNewConfig)
            connectedSignalsDict.pop("adjustSnappingToNewConfig")

    def adjustSnappingToNewConfig(self):
        self.snapConfig = QgsProject.instance().snappingConfig()
        self.snapUtils.setConfig(self.snapConfig)

    def canvasMoveEvent(self, e):
        e.snapPoint()
        matchedPoint = e.mapPointMatch()
        if self.snapConfig.enabled():
            self.snapIndicator.setMatch(matchedPoint)

    def canvasPressEvent(self, e):
        point = e.snapPoint()
        index = self.measurementGui.insertAtIndex
        self.markersAndRubberBand.updateVertex(point.x(), point.y(), index)
        self.addRowToTable(point)

    def addRowToTable(self, point):
        coordsTable = self.measurementGui.coordsTableWidget
        zValue = self.measurementGui.spZValue.value()
        self.measurementGui.verticesCount += 1

        if self.measurementGui.insertAtIndex == -1:
            numberRows = coordsTable.rowCount()
            self.vertices.append((point.x(), point.y(), zValue))
            coordsTable.insertRow(numberRows)
            coordsTable.setItem(numberRows, 0, QTableWidgetItem(str(point.x())))
            coordsTable.setItem(numberRows, 1, QTableWidgetItem(str(point.y())))
            coordsTable.setItem(numberRows, 2, QTableWidgetItem(str(zValue)))
        else:
            numberRows = self.measurementGui.insertAtIndex
            self.vertices.insert(numberRows, (point.x(), point.y(), zValue))
            coordsTable.insertRow(numberRows)
            coordsTable.setItem(numberRows, 0, QTableWidgetItem(str(point.x())))
            coordsTable.setItem(numberRows, 1, QTableWidgetItem(str(point.y())))
            coordsTable.setItem(numberRows, 2, QTableWidgetItem(str(zValue)))
            self.measurementGui.insertAtIndex = -1

        self.measurementGui.updatePointCount()
        self.tachy2GisPlugin.vtk_mouse_interactor_style.draw()
