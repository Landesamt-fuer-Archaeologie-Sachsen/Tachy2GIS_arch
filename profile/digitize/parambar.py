# -*- coding: utf-8 -*-

from qgis.PyQt.QtCore import Qt, QRect
from qgis.PyQt.QtGui import QIcon, QPainter, QColor
from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QWidget,
    QHBoxLayout,
    QLabel,
    QFrame,
    QSizePolicy,
    QToolBar,
    QAction,
    QComboBox,
    QLineEdit,
    QDoubleSpinBox,
    QActionGroup,
)
from qgis.core import QgsApplication
from qgis.utils import iface

from ..publisher import Publisher
from ...Icons import ICON_PATHS
from ...utils.functions import layers_not_in_edit_mode


## @brief With the TransformationDialogParambar class a bar based on QWidget is realized
#
# Inherits from QWidget
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09


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


class Parambar(QWidget):
    ## The constructor.
    # Creates labels with styles
    # @param dialogInstance pointer to the dialogInstance

    def __init__(
        self,
        dialogInstance,
        canvasDigitize,
        toolIdentify,
        toolDigiPoint,
        toolDigiLine,
        toolDigiPolygon,
        rotationCoords,
        aar_direction,
    ):
        super(Parambar, self).__init__()

        self.dialogInstance = dialogInstance

        self.aar_direction = aar_direction

        self.pup = Publisher()

        self.canvasDigitize = canvasDigitize
        self.toolDigiPoint = toolDigiPoint
        self.toolDigiLine = toolDigiLine
        self.toolDigiPolygon = toolDigiPolygon
        self.toolIdentify = toolIdentify

        self.rotationCoords = rotationCoords

        self.refData = None

        self.createComponents()
        self.createLayout()
        self.createConnects()

    def createComponents(self):
        # MapEdits
        self.canvasToolbar = QToolBar("Edit", self)
        self.createPanAction()
        self.createActionZoomIn()
        self.createActionZoomOut()
        self.createActionExtent()
        self.createIdentifyAction()

        self.createGetObjectsAction()

        self.createLayerauswahl()

        self.createActionGroupPolygon()
        self.createActionGroupLine()
        self.createActionGroupPoint()

        self.createTakeLayerAction()

        self.activatePan()

        # Koordinatenanzeige
        self.toolbarCoord = QToolBar("Coordinates", self)
        self.coordLineEdit = QLineEdit()
        self.coordLineEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.coordLineEdit.setAlignment(Qt.AlignCenter)
        self.coordLineEdit.setReadOnly(True)
        self.coordLineEditFm = self.coordLineEdit.fontMetrics()
        width_text = self.coordLineEditFm.width("xxxxxx.xxx,xxxxxxx.xxx,xxxx.xxx")
        self.coordLineEdit.setMinimumWidth(width_text + 30)
        self.toolbarCoord.addWidget(self.coordLineEdit)

    def createLayout(self):
        self.paramsBarLayout = QHBoxLayout()
        self.paramsBarLayout.setContentsMargins(0, 0, 0, 0)
        self.paramsBarLayout.setSpacing(0)
        self.setLayout(self.paramsBarLayout)
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.paramsBarLayout.addWidget(self.canvasToolbar)
        # self.paramsBarLayout.addWidget(self.toolbarLayer)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.paramsBarLayout.addWidget(spacer)

        self.paramsBarLayout.addWidget(self.toolbarCoord)

    def createConnects(self):
        self.activeLayerCombo.currentIndexChanged.connect(self.switchLayer)

        self.takeLayerButton.triggered.connect(self.takeLayerObjects)

    def takeLayerObjects(self):

        if not layers_not_in_edit_mode(["E_Point", "E_Line", "E_Polygon", "Messpunkte"]):
            iface.messageBar().pushMessage(
                "Error", "Bitte den Editiermodus der Eingabelayer beenden.", level=1, duration=3
            )
            return
        try:
            # layer_id = self.activeLayerCombo.currentData()
            # if self.refData['pointLayer'].id() == layer_id:
            self.toolDigiPoint.reverseRotation2Eingabelayer(self.refData["pointLayer"].id(), self.aar_direction)
            # if self.refData['lineLayer'].id() == layer_id:
            self.toolDigiLine.reverseRotation2Eingabelayer(self.refData["lineLayer"].id(), self.aar_direction)
            # if self.refData['polygonLayer'].id() == layer_id:
            self.toolDigiPolygon.reverseRotation2Eingabelayer(self.refData["polygonLayer"].id(), self.aar_direction)

            infoText = "Objekte wurden erfolgreich in die Eingabelayer geschrieben."
            titleText = "Info"

        except Exception as e:
            infoText = f"Achtung! Die Daten wurden nicht in die Eingabelayer geschrieben. ({type(e)}: {e})"
            titleText = "Fehler"

        self.__openInfoMessageBox(infoText, titleText)

    def getOriginalObjects(self):
        if self.getObjectsAction.isChecked():
            iconImport = QIcon(ICON_PATHS["Sichtbar_an"])
            self.getObjectsAction.setIcon(iconImport)
            bufferGeometry = self.rotationCoords.profileBuffer(self.bufferSpin.value(), self.aar_direction)

            self.toolDigiPoint.getFeaturesFromEingabelayer(bufferGeometry, "tachy", self.aar_direction)
            self.toolDigiLine.getFeaturesFromEingabelayer(bufferGeometry, "tachy", self.aar_direction)
            self.toolDigiPolygon.getFeaturesFromEingabelayer(bufferGeometry, "tachy", self.aar_direction)
        else:
            iconImport = QIcon(ICON_PATHS["Sichtbar_aus"])
            self.getObjectsAction.setIcon(iconImport)

            self.toolDigiPoint.removeNoneProfileFeatures()
            self.toolDigiLine.removeNoneProfileFeatures()
            self.toolDigiPolygon.removeNoneProfileFeatures()

    def switchLayer(self, ix):
        combo = self.sender()
        layer_id = combo.currentData()

        if self.refData["pointLayer"].id() == layer_id:
            self.enableDigiPointAction()
            self.disableDigiLineAction()
            self.disableDigiPolygonAction()
            self.activateDigiPoint()
            self.action_tool_point.setChecked(True)

        if self.refData["lineLayer"].id() == layer_id:
            self.disableDigiPointAction()
            self.enableDigiLineAction()
            self.disableDigiPolygonAction()
            self.activateDigiLine()
            self.action_tool_line.setChecked(True)

        if self.refData["polygonLayer"].id() == layer_id:
            self.disableDigiLineAction()
            self.disableDigiPointAction()
            self.enableDigiPolygonAction()
            self.activateDigiPolygon()
            self.action_tool_polygon.setChecked(True)

        self.canvasDigitize.setFocus()  # so that keyboard events reach this without click

    def activatePan(self):
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolPan)

    def activateZoomIn(self):
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolZoomIn)

    def activateIdentify(self):
        self.action_tool_point.setChecked(False)
        self.action_tool_point_edit.setChecked(False)
        self.action_tool_line.setChecked(False)
        self.action_tool_line_edit.setChecked(False)
        self.action_tool_polygon.setChecked(False)
        self.action_tool_polygon_edit.setChecked(False)
        self.toolIdentify.set_for_feat_form()
        self.canvasDigitize.setMouseTracking(True)
        self.canvasDigitize.setMapTool(self.toolIdentify)
        self.actionIdentify.setChecked(True)

    def activateZoomOut(self):
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolZoomOut)

    def activateDigiPoint(self):
        self.canvasDigitize.setMapTool(self.toolDigiPoint)

    def activateDigiLine(self):
        self.canvasDigitize.setMapTool(self.toolDigiLine)

    def activateDigiPolygon(self):
        self.canvasDigitize.setMapTool(self.toolDigiPolygon)

    def createTakeLayerAction(self):
        # Button in Eingabelayer übernehmen
        self.canvasToolbar.addSeparator()
        iconPan = merge_icons(
            QIcon(QgsApplication.iconPath("mActionDuplicateLayer.svg")),
            QIcon(QgsApplication.iconPath("mActionFileSave.svg")),
        )
        self.takeLayerButton = QAction(iconPan, "Objekte in Eingabelayer schreiben", self)
        self.canvasToolbar.addAction(self.takeLayerButton)

    def createPanAction(self):
        # Pan
        iconPan = QIcon(QgsApplication.iconPath("mActionPan"))
        self.actionPan = QAction(iconPan, "Pan", self)
        self.actionPan.setCheckable(True)

        self.canvasDigitize.toolPan.setAction(self.actionPan)

        self.canvasToolbar.addAction(self.actionPan)
        # self.canvasDigitize.setMapTool(self.canvasDigitize.toolPan)
        self.actionPan.triggered.connect(self.activatePan)

    def createIdentifyAction(self):
        # Point
        iconIdentify = QIcon(QgsApplication.iconPath("mActionIdentify"))
        self.actionIdentify = QAction(iconIdentify, "Objekte abfragen", self)
        self.actionIdentify.setCheckable(True)

        # self.toolIdentify.setAction(self.actionIdentify)

        self.canvasToolbar.addAction(self.actionIdentify)
        # self.canvasDigitize.setMapTool(self.toolIdentify)
        self.actionIdentify.triggered.connect(self.activateIdentify)

    def createActionZoomIn(self):
        iconZoomIn = QIcon(QgsApplication.iconPath("mActionZoomIn"))
        self.actionZoomIn = QAction(iconZoomIn, "Zoom in", self)
        self.actionZoomIn.setCheckable(True)

        self.canvasDigitize.toolZoomIn.setAction(self.actionZoomIn)

        self.canvasToolbar.addAction(self.actionZoomIn)
        # self.canvasDigitize.setMapTool(self.canvasDigitize.toolZoomIn)

        self.actionZoomIn.triggered.connect(self.activateZoomIn)

    def createActionZoomOut(self):
        iconZoomOut = QIcon(QgsApplication.iconPath("mActionZoomOut"))
        self.actionZoomOut = QAction(iconZoomOut, "Zoom out", self)
        self.actionZoomOut.setCheckable(True)

        self.canvasDigitize.toolZoomOut.setAction(self.actionZoomOut)

        self.canvasToolbar.addAction(self.actionZoomOut)
        # self.canvasDigitize.setMapTool(self.canvasDigitize.toolZoomOut)

        self.actionZoomOut.triggered.connect(self.activateZoomOut)

    def createActionExtent(self):
        iconExtent = QIcon(QgsApplication.iconPath("mActionZoomToLayer"))
        self.actionExtent = QAction(iconExtent, "Zoom to layer", self)

        self.canvasToolbar.addAction(self.actionExtent)

        self.actionExtent.triggered.connect(self.canvasDigitize.setExtentByImageLayer)

    def createGetObjectsAction(self):
        # Button Objekte aus Layer anzeigen
        iconImport = QIcon(ICON_PATHS["Sichtbar_aus"])
        self.getObjectsAction = QAction(iconImport, "Objekte aus Eingabelayer", self)
        self.getObjectsAction.setCheckable(True)
        self.getObjectsAction.triggered.connect(self.getOriginalObjects)
        self.canvasToolbar.addSeparator()
        self.canvasToolbar.addAction(self.getObjectsAction)

        # Buffer Spinbox
        self.bufferSpin = QDoubleSpinBox(self)
        self.bufferSpin.setMinimum(0)
        self.bufferSpin.setMaximum(5)
        self.bufferSpin.setSingleStep(0.01)
        self.bufferSpin.setValue(1)
        self.bufferSpin.setToolTip("Max. Abstand [m] der Eingabelayerobjekte von der Profillinie")
        self.canvasToolbar.addWidget(self.bufferSpin)

    def createLayerauswahl(self):
        # Layerauswahl
        self.canvasToolbar.addSeparator()
        self.labelActiveLayerCombo = QLabel("aktiver\nLayer:")
        self.labelActiveLayerCombo.setAlignment(Qt.AlignVCenter)
        self.labelActiveLayerCombo.setStyleSheet("padding-right: 4px; padding-left: 4px")

        self.activeLayerCombo = QComboBox()
        self.canvasToolbar.addWidget(self.labelActiveLayerCombo)
        self.canvasToolbar.addWidget(self.activeLayerCombo)
        self.canvasToolbar.addSeparator()

    def createActionGroupPolygon(self):
        self.action_group_polygon = QActionGroup(self)

        # createAction_tool_polygon
        icon_geom = QIcon(QgsApplication.iconPath("mLayoutItemPolygon.svg"))
        icon_add = merge_icons(
            icon_geom,
            QIcon(QgsApplication.iconPath("mActionAdd.svg")),
        )
        self.action_tool_polygon = QAction(
            icon_add,
            (
                "Polygon zeichnen\n"
                "-> [L-MAUS] Punkt setzen\n"
                "-> [STRG] halten für Snapping\n"
                "-> [Z] vorhergehenden Punkt entfernen\n"
                "-> [R] Reihenfolge der Punkte umkehren\n"
                "-> [R-MAUS] Editieren beenden"
            ),
            self,
        )
        self.action_tool_polygon.setCheckable(True)
        self.action_group_polygon.addAction(self.action_tool_polygon)
        self.canvasToolbar.addAction(self.action_tool_polygon)
        self.action_tool_polygon.toggled.connect(self.polygon_set_map_tool)

        # createAction_tool_polygon_edit
        icon_edit = merge_icons(
            color_shift_icon(icon_geom, QColor(0, 160, 255, 80)),
            QIcon(QgsApplication.iconPath("mActionToggleEditing.svg")),
        )
        self.action_tool_polygon_edit = QAction(
            icon_edit, "Polygon editieren\n(1) Polygon und (2) Punkt auswählen", self
        )
        self.action_tool_polygon_edit.setCheckable(True)
        self.action_group_polygon.addAction(self.action_tool_polygon_edit)
        self.canvasToolbar.addAction(self.action_tool_polygon_edit)
        self.action_tool_polygon_edit.triggered.connect(self.polygon_set_edit_tool)

    def polygon_set_map_tool(self, checked):
        if not isinstance(checked, bool):
            checked = True

        self.action_tool_polygon_edit.setChecked(not checked)
        self.action_tool_polygon.setChecked(checked)
        self.actionIdentify.setChecked(False)
        if checked:
            self.canvasDigitize.setMapTool(self.toolDigiPolygon)
        else:
            self.toolDigiPolygon.recover_to_normal_mode()

    def polygon_set_edit_tool(self, checked):
        if not isinstance(checked, bool):
            checked = True

        self.action_tool_polygon.setChecked(not checked)
        self.action_tool_polygon_edit.setChecked(checked)
        self.actionIdentify.setChecked(False)
        if checked:
            self.toolIdentify.set_for_select_action("polygons")
            self.canvasDigitize.setMapTool(self.toolIdentify)
        else:
            self.toolDigiPolygon.recover_to_normal_mode()

    def createActionGroupLine(self):
        self.action_group_line = QActionGroup(self)

        # createAction_tool_line
        icon_geom = QIcon(QgsApplication.iconPath("mLayoutItemPolyline.svg"))
        icon_add = merge_icons(
            icon_geom,
            QIcon(QgsApplication.iconPath("mActionAdd.svg")),
        )
        self.action_tool_line = QAction(
            icon_add,
            (
                "Linie zeichnen\n"
                "-> [L-MAUS] Punkt setzen\n"
                "-> [STRG] halten für Snapping\n"
                "-> [Z] vorhergehenden Punkt entfernen\n"
                "-> [R] Reihenfolge der Punkte umkehren\n"
                "-> [R-MAUS] Editieren beenden"
            ),
            self,
        )
        self.action_tool_line.setCheckable(True)
        self.action_group_line.addAction(self.action_tool_line)
        self.canvasToolbar.addAction(self.action_tool_line)
        self.action_tool_line.toggled.connect(self.line_set_map_tool)

        # createAction_tool_line_edit
        icon_edit = merge_icons(
            color_shift_icon(icon_geom, QColor(0, 160, 255, 80)),
            QIcon(QgsApplication.iconPath("mActionToggleEditing.svg")),
        )
        self.action_tool_line_edit = QAction(icon_edit, "Linie editieren\n(1) Linie und (2) Punkt auswählen", self)
        self.action_tool_line_edit.setCheckable(True)
        self.action_group_line.addAction(self.action_tool_line_edit)
        self.canvasToolbar.addAction(self.action_tool_line_edit)
        self.action_tool_line_edit.triggered.connect(self.line_set_edit_tool)

    def line_set_map_tool(self, checked):
        if not isinstance(checked, bool):
            checked = True

        self.action_tool_line_edit.setChecked(not checked)
        self.action_tool_line.setChecked(checked)
        self.actionIdentify.setChecked(False)
        if checked:
            self.canvasDigitize.setMapTool(self.toolDigiLine)
        else:
            self.toolDigiLine.recover_to_normal_mode()

    def line_set_edit_tool(self, checked):
        if not isinstance(checked, bool):
            checked = True

        self.action_tool_line.setChecked(not checked)
        self.action_tool_line_edit.setChecked(checked)
        self.actionIdentify.setChecked(False)
        if checked:
            self.toolIdentify.set_for_select_action("lines")
            self.canvasDigitize.setMapTool(self.toolIdentify)
        else:
            self.toolDigiLine.recover_to_normal_mode()

    def createActionGroupPoint(self):
        self.action_group_point = QActionGroup(self)

        # createAction_tool_point
        icon_geom = QIcon(QgsApplication.iconPath("mIconPointLayer.svg"))
        icon_add = merge_icons(
            icon_geom,
            QIcon(QgsApplication.iconPath("mActionAdd.svg")),
        )
        self.action_tool_point = QAction(
            icon_add,
            (
                "Punkt zeichnen\n"
                "-> [L-MAUS] Punkt setzen\n"
                "-> [STRG] halten für Snapping\n"
                "-> [Z] vorhergehenden Punkt entfernen\n"
                "-> [R-MAUS] Editieren beenden"
            ),
            self,
        )
        self.action_tool_point.setCheckable(True)
        self.action_group_point.addAction(self.action_tool_point)
        self.canvasToolbar.addAction(self.action_tool_point)
        self.action_tool_point.toggled.connect(self.point_set_map_tool)

        # createAction_tool_point_edit
        icon_edit = merge_icons(
            color_shift_icon(icon_geom, QColor(0, 160, 255, 80)),
            QIcon(QgsApplication.iconPath("mActionToggleEditing.svg")),
        )
        self.action_tool_point_edit = QAction(icon_edit, "Punkt auswählen\nzum erneuten Editieren", self)
        self.action_tool_point_edit.setCheckable(True)
        self.action_group_point.addAction(self.action_tool_point_edit)
        self.canvasToolbar.addAction(self.action_tool_point_edit)
        self.action_tool_point_edit.triggered.connect(self.point_set_edit_tool)

    def point_set_map_tool(self, checked):
        if not isinstance(checked, bool):
            checked = True

        self.action_tool_point_edit.setChecked(not checked)
        self.action_tool_point.setChecked(checked)
        self.actionIdentify.setChecked(False)
        if checked:
            self.canvasDigitize.setMapTool(self.toolDigiPoint)
        else:
            self.toolDigiPoint.recover_to_normal_mode()

    def point_set_edit_tool(self, checked):
        if not isinstance(checked, bool):
            checked = True

        self.action_tool_point.setChecked(not checked)
        self.action_tool_point_edit.setChecked(checked)
        self.actionIdentify.setChecked(False)
        if checked:
            self.toolIdentify.set_for_select_action("points")
            self.canvasDigitize.setMapTool(self.toolIdentify)
        else:
            self.toolDigiPoint.recover_to_normal_mode()

    def enableDigiPointAction(self):
        self.action_group_point.setVisible(True)

    def disableDigiPointAction(self):
        self.action_group_point.setVisible(False)
        self.toolDigiPoint.clear_map_tool()

    def enableDigiLineAction(self):
        self.action_group_line.setVisible(True)

    def disableDigiLineAction(self):
        self.action_group_line.setVisible(False)
        self.toolDigiLine.clear_map_tool()

    def enableDigiPolygonAction(self):
        self.action_group_polygon.setVisible(True)

    def disableDigiPolygonAction(self):
        self.action_group_polygon.setVisible(False)
        self.toolDigiPolygon.clear_map_tool()

    def update(self, refData):
        # self.createComponents()
        # self.createLayout()
        # self.createConnects()

        self.refData = refData

        self.activeLayerCombo.clear()
        self.activeLayerCombo.addItem(self.refData["pointLayer"].sourceName(), self.refData["pointLayer"].id())
        self.activeLayerCombo.addItem(self.refData["lineLayer"].sourceName(), self.refData["lineLayer"].id())
        self.activeLayerCombo.addItem(self.refData["polygonLayer"].sourceName(), self.refData["polygonLayer"].id())

        # select lineLayer per default:
        self.activeLayerCombo.setCurrentIndex(1)

        self.activeLayerCombo.resize(self.activeLayerCombo.sizeHint())

    def updateCoordinate(self, coordObj):
        retObj = self.rotationCoords.rotationReverse(coordObj["x"], coordObj["y"], True, self.aar_direction)

        self.coordLineEdit.setText(
            str("{:.3f}".format(round(retObj["x_trans"], 3)))
            + ","
            + str("{:.3f}".format(round(retObj["y_trans"], 3)))
            + ","
            + str("{:.3f}".format(round(retObj["z_trans"], 3)))
        )

    def createSplitter(self):
        vSplit = QFrame()
        vSplit.setFrameShape(QFrame.VLine | QFrame.Sunken)

        return vSplit

    def __openInfoMessageBox(self, infoText, titleText):
        self.__infoTranssformMsgBox = QMessageBox()
        self.__infoTranssformMsgBox.setText(infoText)
        self.__infoTranssformMsgBox.setWindowTitle(titleText)
        self.__infoTranssformMsgBox.setStandardButtons((QMessageBox.Ok))
        self.__infoTranssformMsgBox.exec_()
