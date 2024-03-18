from datetime import date, datetime
import os
from functools import partial
import math
import uuid
import winsound


from qgis.core import (Qgis,
                       QgsFeatureRequest,
                       QgsGeometry,
                       QgsLineString,
                       QgsMessageLog,
                       QgsSnappingUtils,
                       QgsPoint,
                       QgsPointXY,
                       QgsPolygon,
                       QgsProject,
                       QgsRectangle,
                       QgsVectorLayerUtils,
                       QgsWkbTypes)
from qgis.gui import (QgsMapTool,
                      QgsSnapIndicator,
                      QgsRubberBand,
                      QgsVertexMarker)
from qgis.utils import (iface,
                        plugins)

from qgis.PyQt import uic
from qgis.PyQt.QtCore import (Qt,
                          QTimer,
                          QVariant)
from qgis.PyQt.QtGui import (QColor,
                         QCursor,
                         QIcon,
                         QKeySequence)
from qgis.PyQt.QtWidgets import (QAction,
                             QComboBox,
                             QLineEdit,
                             QMenu,
                             QMessageBox,
                             QHeaderView,
                             QTableWidgetItem,
                             QShortcut)

from ..functions import (enableAndDisableWidgets,
                         getCustomProjectVariable,
                         getLookupDict,
                         HelpWindow,
                         findLayerInProject,
                         layerHasPendingChanges,
                         setCustomProjectVariable,
                         showAndHideWidgets)
from ..toolbar_functions import (saveProject)


iconPaths = {
    'free': 'Icons/Frei.gif',
    'circle_2_points_radius': 'Icons/Circle2PR',
    'circle_2_points_diameter': 'Icons/Circle2P',
    'delete_vertex': 'Icons/delVertex.png',
    'rectangle': 'Icons/Rectangle.gif',
    'polygons': 'Icons/mActionCapturePolygon.png',
    'lines': 'Icons/mActionCaptureLine.png',
    'points': 'Icons/mActionCapturePoint.png',
    'tachy2gis_visible': 'Icons/Sichtbar_an.gif',
    'tachy2gis_not_visible': 'Icons/Sichtbar_aus.gif',
    'add_vertex': 'Icons/addVertex.png'
}
for iconDescription, iconPath in iconPaths.items():
    iconPaths[iconDescription] = os.path.join(
        os.path.dirname(__file__), iconPath)


polygonsLayerName = 'E_Polygon'
linesLayerName = 'E_Line'
pointsLayerName = 'E_Point'

layers = {
    'polygons': polygonsLayerName,
    'lines': linesLayerName,
    'points': pointsLayerName
}

connectedSignalsDict = {}


WIDGET, BASE = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'messen.ui'))

projectVariables = [
    'obj_typ_polygons',
    'obj_art_polygons',
    'obj_spez_polygons',
    'obj_typ_lines',
    'obj_art_lines',
    'obj_typ_points',
    'obj_art_points',
    'schnitt_nr',
    'planum_nr',
    'zbs',
    'prof_nr',
    'pt_nr',
    'fund_nr',
    'probe_nr',
]


class MeasurementTab(BASE, WIDGET):
    cmbLayerType: QComboBox
    schnitt_nr: QLineEdit
    planum_nr: QLineEdit
    zbs: QLineEdit
    prof_nr: QLineEdit
    pt_nr: QLineEdit
    fund_nr: QLineEdit
    probe_nr: QLineEdit

    def __init__(self):

        super().__init__(iface.mainWindow())
        self.setupUi(self)

        self.tachy2GisVisible = False
        self.tachy2GisPlugin = None
        self.tachyWatchActive = False
        self.firstTachyStart = True

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

        self.setGuiContent()
        self.connectSignals()

        self.keys = []
        self.createKeys()

        self.helpWindow = HelpWindow()

    def setupUi(self, dialog):
        super().setupUi(dialog)

        def ignoreWheelEvent(event):
            event.ignore()

        self.cmbLayerType.wheelEvent = ignoreWheelEvent

    def createKeys(self):

        self.createKey(QKeySequence(Qt.Key_Return),
                       iface.mapCanvas(), self.saveGeometry)
        self.createKey(QKeySequence(Qt.Key_Return), self, self.saveGeometry)
        self.createKey(QKeySequence(Qt.Key_Enter),
                       iface.mapCanvas(), self.saveGeometry)
        self.createKey(QKeySequence(Qt.Key_Enter), self, self.saveGeometry)

        self.createKey(QKeySequence("Shift+L"), iface.mapCanvas(),
                       self.deleteCurrentDigitizing)
        self.createKey(QKeySequence("Shift+L"), self,
                       self.deleteCurrentDigitizing)

        self.createKey(QKeySequence("Shift+Z"), iface.mapCanvas(),
                       self.deleteLastVertexFromCoordsTable)
        self.createKey(QKeySequence("Shift+Z"), self,
                       self.deleteLastVertexFromCoordsTable)

        self.createKey(QKeySequence("Shift+K"), iface.mapCanvas(),
                       self.openCloseCoordinatesGroupBox)
        self.createKey(QKeySequence("Shift+K"), self,
                       self.openCloseCoordinatesGroupBox)

        self.createKey(QKeySequence("Shift+A"), iface.mapCanvas(),
                       self.openCloseAttributesGroupBox)
        self.createKey(QKeySequence("Shift+A"), self,
                       self.openCloseAttributesGroupBox)

        self.createKey(QKeySequence("Shift+N"), iface.mapCanvas(),
                       self.openCloseNumberGroupBox)
        self.createKey(QKeySequence("Shift+N"), self,
                       self.openCloseNumberGroupBox)

        self.createKey(QKeySequence("Shift+M"), iface.mapCanvas(),
                       self.openCloseMeasurementPointsGroupBox)
        self.createKey(QKeySequence("Shift+M"), self,
                       self.openCloseMeasurementPointsGroupBox)

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
        self.cbFixTxtReference.stateChanged.connect(
            self.setReferenceNumberProjectVariable)
        self.cmbLayerType.currentIndexChanged.connect(
            self.adjustDigitizingToGeometryType)
        iface.mapCanvas().mapToolSet.connect(self.setDigitizeAction)
        connectedSignalsDict['setDigitizeAction'] = self.setDigitizeAction
        self.actionDigitize.triggered.connect(self.activateDigitizeTool)
        self.butT2GShow.clicked.connect(
            lambda: self.showHideTachy2GisInstance(True))
        self.btnClear.clicked.connect(self.deleteCurrentDigitizing)
        self.coordsTableWidget.cellChanged.connect(self.setNewCoordinate)
        self.coordsTableWidget.customContextMenuRequested.connect(
            self.openCoordsTableMenu)
        self.coordsTableWidget.itemSelectionChanged.connect(
            self.highlightMarker)
        self.measurementsTableWidget.cellClicked.connect(
            self.zoomToAndSelectFeature)
        self.btnCreateFeature.clicked.connect(self.saveGeometry)
        self.cmbObjectType_1.currentIndexChanged.connect(
            self.comboObjectTypeChanged)
        self.cmbObjectType_2.currentIndexChanged.connect(
            self.comboObjectArtChanged)
        self.cmbObjectType_3.currentIndexChanged.connect(
            self.comboObjectSpezChanged)
        self.btnResetAutoAttributes.clicked.connect(
            self.resetAutoAttributeValues)
        self.cbActivateAutoAttributes.stateChanged.connect(
            self.setAutoAttributeMode)
        self.schnitt_nr.editingFinished.connect(
            partial(self.onLineEditingFinished, self.schnitt_nr))
        self.planum_nr.editingFinished.connect(
            partial(self.onLineEditingFinished, self.planum_nr))
        self.zbs.editingFinished.connect(
            partial(self.onLineEditingFinished, self.zbs))
        self.prof_nr.editingFinished.connect(
            partial(self.onLineEditingFinished, self.prof_nr))
        self.pt_nr.editingFinished.connect(
            partial(self.onLineEditingFinished, self.pt_nr))
        self.fund_nr.editingFinished.connect(
            partial(self.onLineEditingFinished, self.fund_nr))
        self.probe_nr.editingFinished.connect(
            partial(self.onLineEditingFinished, self.probe_nr))
        self.btnSaveProject.clicked.connect(saveProject)
        self.btnHelp.clicked.connect(self.showHelp)

    def resetMeasurementTab(self):
        self.showHideTachy2GisInstance(False)
        self.leaveDigitizingMode()
        self.resetTabToBeginning()
        self.disconnectSignals()
        self.deactivateKeys()

    def closeMeasurementTab(self):
        self.showHideTachy2GisInstance(False)
        self.leaveDigitizingMode()
        self.resetTabToBeginning()
        self.deactivateKeys()

    def disconnectSignals(self):
        signal = connectedSignalsDict.get('setDigitizeAction')
        if signal:
            iface.mapCanvas().mapToolSet.disconnect(signal)
            connectedSignalsDict.pop('setDigitizeAction')
        signal = connectedSignalsDict.get('resetToNewProject')

    def fillCmbLayerType(self):

        cmbLayerTypeDict = {

            'no_layer': {
                'description': 'Keine Auswahl',
                'icon': QIcon()
            },
            'polygons': {
                'description': 'Polygone',
                'icon': QIcon(iconPaths['polygons'])
            },
            'lines': {
                'description': 'Linien',
                'icon': QIcon(iconPaths['lines'])
            },
            'points': {
                'description': 'Punkte',
                'icon': QIcon(iconPaths['points'])
            }

        }

        for editingTypeValue, editingTypeInfo in cmbLayerTypeDict.items():
            self.cmbLayerType.addItem(
                editingTypeInfo['icon'], editingTypeInfo['description'], editingTypeValue)

    def createCoordsTable(self):
        self.coordsTableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.coordsTableWidget.horizontalHeader().setStretchLastSection(True)
        self.coordsTableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def createMeasurementPointsTable(self):
        self.measurementsTableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.measurementsTableWidget.horizontalHeader().setStretchLastSection(True)
        self.measurementsTableWidget.horizontalHeader(
        ).setSectionResizeMode(QHeaderView.Stretch)

    def setDigitizeAction(self, e):
        try:
            if e.toolName() not in ['digitizepolygons_tachy2gis',
                                    'digitizelines_tachy2gis',
                                    'digitizepoints_tachy2gis']:
                self.actionDigitize.setChecked(False)
        except:
            QgsMessageLog.logMessage(message='MeasurementTab->setDigitizeAction: exception', tag='T2G Archäologie', level=Qgis.MessageLevel.Warning)
            return

    def findLayerToEdit(self, geometryType):
        mapLayers = QgsProject.instance().mapLayers()
        for geomType, layerName in layers.items():
            if geometryType == geomType:
                for lyr in mapLayers.values():
                    if lyr.name() == layerName:
                        iface.setActiveLayer(lyr)
                        return lyr

    def adjustElementsAtStart(self):
        self.cbFixTxtReference.setCheckState(0)

        self.cmbLayerType.setCurrentIndex(0)

        self.cmbLayerType.setEnabled(False)

        widgetsToShow = []

        widgetsToHide = [
            self.widgetDigitizingTools,
            self.qgsGroupBoxAttributes,
            self.qgsGroupBoxSettings,
            self.qgsGroupBoxCoordinates,
            self.widgetCmbPolygonDigitizingMode,
            self.widgetDigitizingButtons,
            self.qgsGroupBoxNextValues,
            self.qgsGroupBoxMeasurementPoints
        ]

        showAndHideWidgets(widgetsToShow, widgetsToHide)

    def fillTxtReference(self):
        referenceNumber = getCustomProjectVariable('aktcode')
        if referenceNumber != QVariant():
            self.txtReference.setText(referenceNumber)

    def fillCmbPolygonDigitizingMode(self):

        cmbPolygonDigitizingMode = {

            'free': {
                'description': 'Frei',
                'icon': QIcon(iconPaths['free'])
            },
            'circle_2_points_radius': {
                'description': 'Kreis mit 2 Punkten (Radius)',
                'icon': QIcon(iconPaths['circle_2_points_radius'])
            },
            'circle_2_points_diameter': {
                'description': 'Kreis mit 2 Punkten (Durchmesser)',
                'icon': QIcon(iconPaths['circle_2_points_diameter'])
            },
            'rectangle': {
                'description': 'Rechteck',
                'icon': QIcon(iconPaths['rectangle'])
            }

        }

        for editingTypeValue, editingTypeInfo in cmbPolygonDigitizingMode.items():
            self.cmbPolygonDigitizingMode.addItem(
                editingTypeInfo['icon'], editingTypeInfo['description'], editingTypeValue)

    def setReferenceNumberProjectVariable(self):

        if self.cbFixTxtReference.isChecked():
            referenceNumber = self.txtReference.text()
            if referenceNumber == '':
                iface.messageBar().pushMessage("T2G Archäologie",
                                               "Bitte eine Maßnahmennummer angeben")
                self.cbFixTxtReference.setCheckState(0)
                return
            if not self.tachy2GisPlugin:
                self.tachy2GisPlugin = self.getTachy2GisInstance()
                if not self.tachy2GisPlugin:
                    iface.messageBar().pushMessage("T2G Archäologie",
                                                   "Bitte Tachy2GIS-3DViewer installieren und aktivieren", Qgis.Warning)
                    self.cbFixTxtReference.setCheckState(0)
                    return
                self.tachy2GisPlugin.dlg.closingPlugin.connect(
                    self.resetOnTachy2GisClose)

            self.startTachy2GisInstance()
            self.createObjectsForTachy2GisWatch()

            setCustomProjectVariable('aktcode', referenceNumber)
            enableAndDisableWidgets(
                [self.cmbLayerType], [self.txtReference])
            self.activateKeys()
        else:
            self.resetTabToBeginning()
            self.deactivateKeys()

    def resetTabToBeginning(self):
        enableAndDisableWidgets([self.txtReference], [self.cmbLayerType])
        self.adjustElementsAtStart()
        iface.actionPan().trigger()

    def resetOnTachy2GisClose(self):
        self.cbFixTxtReference.setCheckState(0)
        iface.messageBar().pushMessage("T2G Archäologie",
                                       "Tachy2GIS-3DViewer wurde gestoppt, Digitalisierung abgebrochen", Qgis.Warning)
        self.setReferenceNumberProjectVariable()
        self.tachy2GisVisible = False

    def getTachy2GisInstance(self):
        for pluginName, plugin in plugins.items():
            if pluginName.lower() == 'tachy2gis':
                return plugin

    def startTachy2GisInstance(self):
        if self.firstTachyStart:
            self.tachy2GisPlugin.run()
            self.tachy2GisVisible = True
            self.firstTachyStart = False
        else:
            self.showHideTachy2GisInstance()

    def setTachy2GisToGeometry(self, geometryType):
        if geometryType == 'polygons':
            self.tachy2GisPlugin.dlg.targetLayerComboBox.setCurrentText(
                'E_Polygon')
            self.tachy2GisPlugin.dlg.sourceLayerComboBox.setCurrentText(
                'E_Polygon')
        elif geometryType == 'lines':
            self.tachy2GisPlugin.dlg.targetLayerComboBox.setCurrentText(
                'E_Line')
            self.tachy2GisPlugin.dlg.sourceLayerComboBox.setCurrentText(
                'E_Line')
        elif geometryType == 'points':
            self.tachy2GisPlugin.dlg.targetLayerComboBox.setCurrentText(
                'E_Point')
            self.tachy2GisPlugin.dlg.sourceLayerComboBox.setCurrentText(
                'E_Point')
        self.tachy2GisPlugin.setPickable()

    def showHideTachy2GisInstance(self, open=True):
        if self.tachy2GisVisible:
            if self.tachy2GisPlugin.dlg.isVisible():
                iface.removeDockWidget(self.tachy2GisPlugin.dlg)

            self.tachy2GisVisible = False
            self.butT2GShow.setIcon(QIcon(iconPaths['tachy2gis_not_visible']))
        else:
            if open:
                if not self.tachy2GisPlugin.dlg.isVisible():
                    iface.addDockWidget(Qt.BottomDockWidgetArea,
                                        self.tachy2GisPlugin.dlg)
                self.tachy2GisVisible = True
                self.butT2GShow.setIcon(QIcon(iconPaths['tachy2gis_visible']))

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

        if geometryType == 'no_layer':
            showAndHideWidgets([], [self.widgetDigitizingTools,
                                    self.qgsGroupBoxAttributes,
                                    self.widgetCmbPolygonDigitizingMode,
                                    self.qgsGroupBoxSettings,
                                    self.widgetDigitizingButtons,
                                    self.qgsGroupBoxNextValues,
                                    self.qgsGroupBoxCoordinates,
                                    self.qgsGroupBoxMeasurementPoints])
            if self.digitizeTool:
                self.digitizeTool = None
            if self.markersAndRubberBand:
                self.markersAndRubberBand = None
            self.geometryType = None
            return

        self.layerToEdit = self.findLayerToEdit(geometryType)
        if not self.layerToEdit:
            iface.messageBar().pushMessage("T2G Archäologie",
                                           f"Bitte den Layer {layers[geometryType]} ins Projekt laden", Qgis.Warning)
            self.cmbLayerType.setCurrentIndex(0)
            return
        if layerHasPendingChanges(self.layerToEdit):
            iface.messageBar().pushMessage("T2G Archäologie",
                                           f"Der Layer {layers[geometryType]} ist im Editiermodus. Bitte das Editieren beenden.", Qgis.Warning)
            self.cmbLayerType.setCurrentIndex(0)
            return

        showAndHideWidgets([self.widgetDigitizingTools,
                            self.qgsGroupBoxSettings,
                            self.qgsGroupBoxCoordinates,
                            self.qgsGroupBoxNextValues,
                            self.qgsGroupBoxMeasurementPoints,
                            self.widgetDigitizingButtons], [])

        self.markersAndRubberBand = self.createMarkersAndRubberBand(
            geometryType)

        self.actionDigitize.setIcon(QIcon(iconPaths[geometryType]))
        self.digitizeTool = DigitizeTool(geometryType,
                                         self)
        self.btnDigitizeTool.setDefaultAction(self.actionDigitize)

        self.setTachy2GisToGeometry(geometryType)

        if geometryType == 'polygons':
            self.actionDigitize.setText('Polygone zeichnen')
            showAndHideWidgets([self.qgsGroupBoxAttributes,
                                self.widgetCmbPolygonDigitizingMode],
                               [])

        elif geometryType == 'lines':
            self.actionDigitize.setText('Linien zeichnen')
            showAndHideWidgets([self.qgsGroupBoxAttributes],
                               [self.widgetCmbPolygonDigitizingMode])

        elif geometryType == 'points':
            self.actionDigitize.setText('Punkte zeichnen')
            showAndHideWidgets([self.qgsGroupBoxAttributes],
                               [self.widgetCmbPolygonDigitizingMode])
        self.geometryType = geometryType
        self.setAttributes()
        self.startTachyWatch()

    def setAutoAttributeMode(self):
        if self.cbActivateAutoAttributes.isChecked():
            setCustomProjectVariable('autoAttribute', True)
        else:
            setCustomProjectVariable('autoAttribute', False)

    def clearObjectCombos(self):
        self.cmbObjectType_1.blockSignals(True)
        self.cmbObjectType_2.blockSignals(True)
        self.cmbObjectType_3.blockSignals(True)
        self.cmbObjectType_1.clear()
        self.cmbObjectType_2.clear()
        self.cmbObjectType_3.clear()
        self.cmbObjectType_1.blockSignals(False)
        self.cmbObjectType_2.blockSignals(False)
        self.cmbObjectType_3.blockSignals(False)

    def setAttributes(self):
        self.clearObjectCombos()
        self.fillComboObjectType()

        if self.geometryType != 'polygons':
            self.cmbObjectType_3.hide()
        else:
            self.cmbObjectType_3.show()

        objTypeGeometry = getCustomProjectVariable(
            f"obj_typ_{self.geometryType}")
        if objTypeGeometry:
            self.cmbObjectType_1.setCurrentIndex(
                self.cmbObjectType_1.findData(objTypeGeometry))

    def comboObjectTypeChanged(self):
        self.fillComboObjectArt()
        setCustomProjectVariable(
            f"obj_typ_{self.geometryType}", self.cmbObjectType_1.currentData())

        objArtGeometry = getCustomProjectVariable(
            f"obj_art_{self.geometryType}")
        if objArtGeometry:
            self.cmbObjectType_2.setCurrentIndex(
                self.cmbObjectType_2.findData(objArtGeometry))

    def comboObjectArtChanged(self):
        setCustomProjectVariable(
            f'obj_art_{self.geometryType}', self.cmbObjectType_2.currentData())
        if self.geometryType != 'polygons':
            return

        self.fillComboObjectSpez()

        objSpezGeometry = getCustomProjectVariable(
            f"obj_spez_{self.geometryType}")
        if objSpezGeometry:
            self.cmbObjectType_3.setCurrentIndex(
                self.cmbObjectType_3.findData(objSpezGeometry))

    def comboObjectSpezChanged(self):
        setCustomProjectVariable(
            f'obj_spez_{self.geometryType}', self.cmbObjectType_3.currentData())

    def resetAutoAttributeValues(self):
        for variable in projectVariables:
            setCustomProjectVariable(variable, '')
        self.cmbObjectType_1.setCurrentIndex(0)
        self.cmbObjectType_2.setCurrentIndex(0)
        self.cmbObjectType_3.setCurrentIndex(0)
        self.schnitt_nr.clear()
        self.planum_nr.clear()
        self.zbs.clear()
        self.prof_nr.clear()
        self.pt_nr.clear()
        self.fund_nr.clear()
        self.probe_nr.clear()

    def fillComboObjectType(self):
        self.cmbObjectType_1.blockSignals(True)
        self.cmbObjectType_1.clear()
        self.cmbObjectType_2.clear()
        self.cmbObjectType_3.clear()
        geom_typ = int(self.layerToEdit.geometryType())
        s1_layer = QgsProject.instance().mapLayersByName('obj_type_s1')[0]
        obj_types = getLookupDict(
            s1_layer, 'class_id', 's1', f'geom_typ = {geom_typ}')
        self.cmbObjectType_1.addItem('', None)
        for fid, description in obj_types.items():
            self.cmbObjectType_1.addItem(description, fid)
        self.cmbObjectType_1.blockSignals(False)

    def fillComboObjectArt(self):
        self.cmbObjectType_2.blockSignals(True)
        self.cmbObjectType_2.clear()
        self.cmbObjectType_3.clear()
        s1_fid = self.cmbObjectType_1.currentData()
        s2_layer = QgsProject.instance().mapLayersByName('obj_type_s2')[0]
        obj_types = getLookupDict(
            s2_layer, 'fid', 's2', f'obj_type_relation_s1_s2_s1_class_id = {s1_fid}')
        self.cmbObjectType_2.addItem('', None)
        for fid, description in obj_types.items():
            self.cmbObjectType_2.addItem(description, fid)
        self.cmbObjectType_2.blockSignals(False)

    def fillComboObjectSpez(self):
        self.cmbObjectType_3.blockSignals(True)
        self.cmbObjectType_3.clear()
        s2_fid = self.cmbObjectType_2.currentData()
        s3_layer = QgsProject.instance().mapLayersByName('obj_type_s3')[0]
        obj_types = getLookupDict(
            s3_layer, 'fid', 's3', f'obj_type_relation_s2_s3_fid_s2 = {s2_fid}')
        self.cmbObjectType_3.addItem('', None)
        for fid, description in obj_types.items():
            self.cmbObjectType_3.addItem(description, fid)
        self.cmbObjectType_3.blockSignals(False)

    def createMarkersAndRubberBand(self, geometryType):
        if geometryType == 'polygons':
            geom = QgsWkbTypes.PolygonGeometry
        elif geometryType == 'lines':
            geom = QgsWkbTypes.LineGeometry
        elif geometryType == 'points':
            geom = QgsWkbTypes.PointGeometry
        return MarkersAndRubberBand(geom)

    def createObjectsForTachy2GisWatch(self):
        self.vertices = self.tachy2GisPlugin.vtk_mouse_interactor_style.vertices
        self.watch = QTimer()
        self.verticesCount = 0
        self.watch.timeout.connect(self.watchevent)

    def resetObjectsForTachy2GisWatch(self):
        if self.vertices:
            self.vertices.clear()
        if self.tachy2GisPlugin:
            self.stopTachyWatch()
            self.tachy2GisPlugin.vtk_mouse_interactor_style.draw()
        self.verticesCount = 0

    def deleteCurrentDigitizing(self):
        self.resetObjectsForTachy2GisWatch()
        self.resetDigitizing()

    def startTachyWatch(self):
        iface.messageBar().pushMessage("Tachy2GisArch",
                                       f"Verbindung zu Tachy2Gis aufgebaut. Punkte für {layers[self.geometryType]} können erfasst werden.", duration=10)
        QgsMessageLog.logMessage(
            'Tachy2Gis watch started', 'T2G Archäologie', Qgis.Info)
        self.watch.start(150)
        self.tachyWatchActive = True

    def stopTachyWatch(self):
        if self.tachyWatchActive:
            QgsMessageLog.logMessage(
                'Tachy2Gis watch stopped', 'T2G Archäologie', Qgis.Info)
        self.watch.stop()
        self.tachyWatchActive = True

    def watchevent(self):
        # Check for new points in 3D viewer
        pointsInTachy2Gis3D = len(self.vertices)
        if pointsInTachy2Gis3D > self.verticesCount:
            self.verticesCount += 1
            x, y, z = self.vertices[-1][0], self.vertices[-1][1], self.vertices[-1][2]
            self.addRowToTable(x, y, z)
            self.markersAndRubberBand.updateVertex(x, y, z)
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
            newCoordinate = float(
                self.coordsTableWidget.item(row, column).text())
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
                self.tachy2GisPlugin.vtk_mouse_interactor_style.draw()
                self.markersAndRubberBand.updateVertex(x, y, row, False)
                self.markersAndRubberBand.setHightlightMarkers([(x, y)])
        except:
            self.coordsTableWidget.setItem(row, column, oldCoordinate)

    def openCoordsTableMenu(self, pos):
        coordsTableMenu = QMenu()
        delVertex = coordsTableMenu.addAction(
            QIcon(iconPaths['delete_vertex']), " Vertex löschen")
        delVertex.triggered.connect(self.deleteVertexFromCoordsTable)
        addVertex = coordsTableMenu.addAction(
            QIcon(iconPaths['add_vertex']), " Vertex hinzufügen")
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
        self.tachy2GisPlugin.vtk_mouse_interactor_style.draw()

    def deleteLastVertexFromCoordsTable(self):
        if self.verticesCount >= 1:
            self.verticesCount -= 1
            self.coordsTableWidget.removeRow(self.verticesCount)
            self.coordsTableRowCount -= 1
            self.markersAndRubberBand.deleteVertex(self.verticesCount)
            self.updatePointCount()

            self.vertices.pop(self.verticesCount)
            self.tachy2GisPlugin.vtk_mouse_interactor_style.draw()

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
        qgsPoints = []
        for vertex in self.vertices:
            point = QgsPoint(vertex[0], vertex[1], vertex[2])
            qgsPoints.append(point)
        if self.geometryType == 'polygons':
            polygonGeometryType = self.cmbPolygonDigitizingMode.currentData()
            if polygonGeometryType == 'free':
                return QgsPolygon(QgsLineString(qgsPoints))
            elif polygonGeometryType == 'circle_2_points_radius':
                return self.createCircleRadiusGeometry()
            elif polygonGeometryType == 'circle_2_points_diameter':
                return self.createCircleDiameterGeometry()
            elif polygonGeometryType == 'rectangle':
                return self.createRectangleGeometry()

        elif self.geometryType == 'lines':
            return QgsLineString(qgsPoints)
        elif self.geometryType == 'points':
            return qgsPoints

    def createCircleRadiusGeometry(self):
        if self.verticesCount > 2:
            iface.messageBar().pushMessage("T2G Archäologie",
                                           f"Nur zwei Punkte erlaubt (Modus: Kreis mit 2 Punkten (Radius))", Qgis.Warning)
            return False
        point1 = QgsPoint(float(self.vertices[0][0]), float(
            self.vertices[0][1]), float(self.vertices[0][2]))
        point2 = QgsPoint(float(self.vertices[1][0]), float(
            self.vertices[1][1]), float(self.vertices[1][2]))
        radius = point1.distance3D(point2)
        geom = self.createCircleGeometry(point1, radius, 30)
        return geom

    def createCircleDiameterGeometry(self):
        if self.verticesCount > 2:
            iface.messageBar().pushMessage("T2G Archäologie",
                                           f"Nur zwei Punkte erlaubt (Modus: Kreis mit 2 Punkten (Durchmesser))", Qgis.Warning)
            return False
        point1 = QgsPoint(float(self.vertices[0][0]), float(
            self.vertices[0][1]), float(self.vertices[0][2]))
        point2 = QgsPoint(float(self.vertices[1][0]), float(
            self.vertices[1][1]), float(self.vertices[1][2]))
        x = (point1.x()+point2.x())/2
        y = (point1.y()+point2.y())/2
        center = QgsPoint((point1.x()+point2.x())/2,
                          (point1.y()+point2.y())/2, float(self.vertices[1][2]))
        radius = point1.distance3D(center)
        geom = self.createCircleGeometry(center, radius, 30)
        return geom

    def createRectangleGeometry(self):
        if self.verticesCount > 2:
            iface.messageBar().pushMessage("T2G Archäologie",
                                           f"Nur zwei Punkte erlaubt (Modus: Rechteck))", Qgis.Warning)
            return False
        point1 = QgsPoint(float(self.vertices[0][0]), float(
            self.vertices[0][1]), float(self.vertices[0][2]))
        point2 = QgsPoint(float(self.vertices[1][0]), float(
            self.vertices[1][1]), float(self.vertices[1][2]))
        rect = QgsRectangle(point1.x(), point1.y(), point2.x(), point2.y())
        geom = QgsGeometry.fromRect(rect)
        return geom

    def createCircleGeometry(self, point, radius, segments):
        pts = []
        for i in range(segments):
            theta = i * (2.0 * math.pi / segments)
            p = QgsPoint(point.x() + radius * math.cos(theta),
                         point.y() + radius * math.sin(theta), point.z())
            pts.append(p)
        pts.append(pts[0])
        return QgsGeometry.fromPolyline(pts)

    def checkGeometry(self, geom):
        if self.geometryType == 'polygons' or self.geometryType == 'lines':
            if isinstance(geom, QgsPolygon) or isinstance(geom, QgsLineString):
                geomClone = geom.clone()
                return QgsGeometry(geomClone).isGeosValid()
            elif isinstance(geom, QgsGeometry):
                return geom.isGeosValid()
            else:
                return False

    def createFeatureFromGeometry(self, geom):
        uuidFeature = self.layerToEdit.dataProvider().fieldNameIndex('obj_uuid')
        if self.geometryType == 'polygons' or self.geometryType == 'lines':
            attr = {uuidFeature: '{' + str(uuid.uuid4())+'}'}
            feature = QgsVectorLayerUtils.createFeature(layer=self.layerToEdit,
                                                        geometry=QgsGeometry(
                                                            geom),
                                                        attributes=attr)
            return feature
        elif self.geometryType == 'points':
            features = []
            for pt in geom:
                attr = {uuidFeature: '{' + str(uuid.uuid4())+'}'}
                feature = QgsVectorLayerUtils.createFeature(layer=self.layerToEdit,
                                                            geometry=QgsGeometry(
                                                                pt),
                                                            attributes=attr)

                features.append(feature)
            return features

    def openAttributeForm(self, feature):
        if self.cbAttributeFormular.isChecked():
            self.layerToEdit.startEditing()
            query = "fid >= " + str(feature.id())
            box = iface.showAttributeTable(self.layerToEdit, query)
            box.exec_()

    def saveGeometry(self):
        if not self.layerToEdit:
            return

        if layerHasPendingChanges(self.layerToEdit):
            iface.messageBar().pushMessage("T2G Archäologie",
                                           f"Der Layer {layers[self.geometryType]} ist im Editiermodus. Bitte das Editieren beenden.", Qgis.Warning)
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
        if geom == False:
            return

        if self.geometryType == 'polygons' or self.geometryType == 'lines':
            if self.checkGeometry(geom):
                feature = self.createFeatureFromGeometry(geom)
                _, features = self.layerToEdit.dataProvider().addFeatures([
                    feature])
            else:
                iface.messageBar().pushMessage("T2G Archäologie",
                                               f"Die Geometrie ist ungültig. Bitte korrigieren oder löschen", Qgis.Warning)
                return
        elif self.geometryType == 'points':
            features = self.createFeatureFromGeometry(geom)
            _, features = self.layerToEdit.dataProvider().addFeatures(features)

        if features:
            addedFeature = features[0]
            self.addMeasurementPoints()
            self.addLastMeasurementsToTable(features)
            self.deleteCurrentDigitizing()
            iface.mapCanvas().refreshAllLayers()
            self.tachy2GisPlugin.vtk_mouse_interactor_style.draw()
            self.openAttributeForm(addedFeature)
            self.beepSound()

    def addMeasurementPoints(self):
        measurementPointsLayer = findLayerInProject('Messpunkte')
        if not measurementPointsLayer:
            return
        measurementPointsLayer.startEditing()
        dateOfMeasurement = str(date.today())
        features = []

        for i in range(len(self.vertices)):
            x = self.vertices[i][0]
            y = self.vertices[i][1]
            z = self.vertices[i][2]
            uuidPoint = '{' + str(uuid.uuid4()) + '}'
            attL = {1: dateOfMeasurement, 4: str(
                x), 5: str(y), 6: str(z), 8: uuidPoint}
            pt = QgsPoint(float(x), float(y), float(z))
            features.append(QgsVectorLayerUtils.createFeature(measurementPointsLayer,
                                                              QgsGeometry(pt),
                                                              attL,
                                                              measurementPointsLayer.createExpressionContext()))

        for feat in features:
            measurementPointsLayer.dataProvider().addFeatures([feat])
            QgsMessageLog.logMessage(
                str(x)+'|'+str(y)+'|'+str(z), 'Messpunkte', Qgis.Info)

        measurementPointsLayer.commitChanges()



    def addLastMeasurementsToTable(self, features):
        for feat in features:
            timeOfMeasurement = str(datetime.now().strftime("%H:%M:%S"))
            row = self.measurementsTableWidget.rowCount()
            self.measurementsTableWidget.insertRow(row)
            self.measurementsTableWidget.setItem(
                row, 0, QTableWidgetItem(str(timeOfMeasurement)))
            self.measurementsTableWidget.setItem(
                row, 1, QTableWidgetItem(self.layerToEdit.name()))
            self.measurementsTableWidget.setItem(
                row, 2, QTableWidgetItem(str(feat.id())))

    def zoomToAndSelectFeature(self, row, column):
        layerName = self.measurementsTableWidget.item(row, 1).text()
        fid = int(self.measurementsTableWidget.item(row, 2).text())
        layer = findLayerInProject(layerName)
        if layer:
            layer.selectByExpression(f"fid = {fid}")
            iface.actionZoomToSelected().trigger()

    # ToDo: refactoring
    def nextValues(self):
        if self.zbs.text() != '':
            try:
                if int(self.zbs.text()) >= int(self.txtNextBef.text()) and not '_' in self.zbs.text():
                    self.txtNextBef.setText(str(int(self.zbs.text())+1))
            except:
                QgsMessageLog.logMessage(message='MeasurementTab->nextValues: no setText', tag='T2G Archäologie', level=Qgis.MessageLevel.Warning)
        if self.fund_nr.txtFundNr.text() != '':
            try:
                if int(self.fund_nr.text()) >= int(self.txtNextFund.text() and not '_' in self.fund_nr.text()):
                    self.txtNextFund.setText(str(int(self.fund_nr.text())+1))
            except:
                QgsMessageLog.logMessage(message='MeasurementTab->nextValues: no setText', tag='T2G Archäologie', level=Qgis.MessageLevel.Warning)
        if self.prof_nr.text() != '':
            try:
                if int(self.prof_nr.text()) >= int(self.txtNextProf.text() and not '_' in self.prof_nr.text()):
                    self.txtNextProf.setText(str(int(self.prof_nr.text())+1))
            except:
                QgsMessageLog.logMessage(message='MeasurementTab->nextValues: no setText', tag='T2G Archäologie', level=Qgis.MessageLevel.Warning)
        if self.probe_nr.text() != '':
            try:
                if int(self.probe_nr.text()) >= int(self.txtNextProb.text() and not '_' in self.probe_nr.text()):
                    self.txtNextProb.setText(str(int(self.probe_nr.text())+1))
            except:
                QgsMessageLog.logMessage(message='MeasurementTab->nextValues: no setText', tag='T2G Archäologie', level=Qgis.MessageLevel.Warning)

    def showHelp(self):
        helpHtmPath = os.path.join(os.path.dirname(__file__), 'Tips.htm')
        self.helpWindow.run(helpHtmPath, None, 280, 300)

    def updatePointCount(self):
        if self.verticesCount == 1:
            self.lblPointCount.setText("1 Punkt")
        else:
            self.lblPointCount.setText(f"{self.verticesCount} Punkte")

    def onLineEditingFinished(self, widget: QLineEdit):
        if self.geometryType == 'no_layer':
            return
        setCustomProjectVariable(f'{widget.objectName()}', widget.text())
        self.nextValues()

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
            winsound.Beep(1000, 100)


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

        self.tachy2GisPlugin = measurementGui.tachy2GisPlugin
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
        connectedSignalsDict['adjustSnappingToNewConfig'] = self.adjustSnappingToNewConfig

    def disconnectSignals(self):
        if connectedSignalsDict.get('adjustSnappingToNewConfig'):
            QgsProject.instance().snappingConfigChanged.disconnect(
                self.adjustSnappingToNewConfig)
            connectedSignalsDict.pop('adjustSnappingToNewConfig')

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
            coordsTable.setItem(
                numberRows, 0, QTableWidgetItem(str(point.x())))
            coordsTable.setItem(
                numberRows, 1, QTableWidgetItem(str(point.y())))
            coordsTable.setItem(numberRows, 2, QTableWidgetItem(str(zValue)))
        else:
            numberRows = self.measurementGui.insertAtIndex
            self.vertices.insert(numberRows, (point.x(), point.y(), zValue))
            coordsTable.insertRow(numberRows)
            coordsTable.setItem(
                numberRows, 0, QTableWidgetItem(str(point.x())))
            coordsTable.setItem(
                numberRows, 1, QTableWidgetItem(str(point.y())))
            coordsTable.setItem(numberRows, 2, QTableWidgetItem(str(zValue)))
            self.measurementGui.insertAtIndex = -1

        self.measurementGui.updatePointCount()
        self.tachy2GisPlugin.vtk_mouse_interactor_style.draw()
