# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPainter, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QToolBar, QAction, QLineEdit, QActionGroup
from qgis.core import QgsApplication

from .map_tool_draw_polygon import PolygonMapTool


class ImageParambar(QWidget):
    """!
    @brief toolbar based on QWidget for map tools

    Inherits from QWidget

    @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
    @date 2020-11-09
    """

    def __init__(self, canvasImage):
        """!
        @param canvasImage ref to the canvas to use with map tools
        """
        super().__init__()
        self.canvasImage = canvasImage

        icon_path = os.path.join(os.path.dirname(__file__), "..", "Icons")

        self.imageToolbar = QToolBar("Edit", self)
        self.action_group = QActionGroup(self)

        # create component move:
        iconMove = QIcon(os.path.join(icon_path, "mActionAddGCPPoint.png"))
        self.actionMove = QAction(iconMove, "Move", self)
        self.actionMove.setCheckable(True)
        self.canvasImage.toolMove.setAction(self.actionMove)
        self.action_group.addAction(self.actionMove)
        self.imageToolbar.addAction(self.actionMove)
        self.actionMove.triggered.connect(self.activateMove)

        # create component pan:
        iconPan = QIcon(os.path.join(icon_path, "mActionPan.png"))
        self.actionPan = QAction(iconPan, "Pan", self)
        self.actionPan.setCheckable(True)
        self.canvasImage.toolPan.setAction(self.actionPan)
        self.action_group.addAction(self.actionPan)
        self.imageToolbar.addAction(self.actionPan)
        self.actionPan.triggered.connect(self.activatePan)

        # create component zoom in:
        iconZoomIn = QIcon(os.path.join(icon_path, "mActionZoomIn.png"))
        self.actionZoomIn = QAction(iconZoomIn, "Zoom in", self)
        self.actionZoomIn.setCheckable(True)
        self.canvasImage.toolZoomIn.setAction(self.actionZoomIn)
        self.action_group.addAction(self.actionZoomIn)
        self.imageToolbar.addAction(self.actionZoomIn)
        self.actionZoomIn.triggered.connect(self.activateZoomIn)

        # create component zoom out:
        iconZoomOut = QIcon(os.path.join(icon_path, "mActionZoomOut.png"))
        self.actionZoomOut = QAction(iconZoomOut, "Zoom out", self)
        self.actionZoomOut.setCheckable(True)
        self.canvasImage.toolZoomOut.setAction(self.actionZoomOut)
        self.action_group.addAction(self.actionZoomOut)
        self.imageToolbar.addAction(self.actionZoomOut)
        self.actionZoomOut.triggered.connect(self.activateZoomOut)

        # create component zoom to extent:
        iconExtent = QIcon(os.path.join(icon_path, "mActionZoomToLayer.png"))
        self.actionExtent = QAction(iconExtent, "Zoom to layer", self)
        self.action_group.addAction(self.actionExtent)
        self.imageToolbar.addAction(self.actionExtent)
        self.actionExtent.triggered.connect(self.canvasImage.setExtentByImageLayer)

        # create component coordinates:
        self.toolbarCoord = QToolBar("Coordinates", self)
        self.coordLineEdit = QLineEdit()
        self.coordLineEdit.setAlignment(Qt.AlignCenter)
        self.coordLineEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.coordLineEdit.setReadOnly(True)
        self.coordLineEditFm = self.coordLineEdit.fontMetrics()
        width_text = self.coordLineEditFm.width("xxxxxx.xx,xxxxxx.xx")
        self.coordLineEdit.setMinimumWidth(width_text + 30)
        self.toolbarCoord.addWidget(self.coordLineEdit)

        # create Layout
        self.paramsBarLayout = QHBoxLayout()
        self.paramsBarLayout.setContentsMargins(0, 0, 0, 0)
        self.paramsBarLayout.setSpacing(0)
        self.setLayout(self.paramsBarLayout)
        self.paramsBarLayout.addWidget(self.imageToolbar)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.paramsBarLayout.addWidget(spacer)
        self.paramsBarLayout.addWidget(self.toolbarCoord)

        # Polygon vvvvvvvvvvvvvvvvvvvvvvvvvv
        self.toolDrawPolygon = PolygonMapTool(self.canvasImage)
        self.action_group_polygon = QActionGroup(self)
        self.imageToolbar.addSeparator()

        def color_shift_icon(original_icon, color):
            pixmap = original_icon.pixmap(64, 64)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.fillRect(pixmap.rect(), color)
            painter.end()
            return QIcon(pixmap)

        # createAction_tool_polygon
        icon4 = QIcon(QgsApplication.iconPath("mActionAddNodesItem.svg"))
        self.action_tool_polygon = QAction(
            icon4, "Polygon: Zeichnen (zum Beschneiden)\n-> [STRG] halten für Snapping", self
        )
        self.action_tool_polygon.setCheckable(True)
        self.action_group.addAction(self.action_tool_polygon)
        self.imageToolbar.addAction(self.action_tool_polygon)
        self.action_tool_polygon.toggled.connect(self.polygon_set_map_tool)

        # createAction_tool_polygon_undo
        icon3 = QIcon(QgsApplication.iconPath("mActionRollbackEdits.svg"))
        self.action_tool_polygon_undo = QAction(icon3, "Polygon: vorhergehenden Punkt entfernen [ESC]", self)
        self.action_group_polygon.addAction(self.action_tool_polygon_undo)
        self.imageToolbar.addAction(self.action_tool_polygon_undo)
        self.action_tool_polygon_undo.triggered.connect(self.polygon_undo)

        # createAction_tool_polygon_finish
        icon1 = color_shift_icon(QIcon(QgsApplication.iconPath("mLayoutItemPolygon.svg")), QColor(0, 190, 0, 80))
        self.action_tool_polygon_finish = QAction(icon1, "Polygon: Editieren beenden [R-MOUSE]", self)
        self.action_group_polygon.addAction(self.action_tool_polygon_finish)
        self.imageToolbar.addAction(self.action_tool_polygon_finish)
        self.action_tool_polygon_finish.triggered.connect(self.polygon_finish)

        # createAction_tool_polygon_edit
        icon2 = QIcon(QgsApplication.iconPath("mActionEditNodesItem.svg"))
        self.action_tool_polygon_edit = QAction(icon2, "Polygon: Punkt auswählen zum erneuten Editieren", self)
        self.action_group_polygon.addAction(self.action_tool_polygon_edit)
        self.imageToolbar.addAction(self.action_tool_polygon_edit)
        self.action_tool_polygon_edit.triggered.connect(self.polygon_edit)

        # createAction_tool_polygon_reset
        icon = QIcon(QgsApplication.iconPath("mActionDeleteSelected.svg"))
        self.action_tool_polygon_reset = QAction(icon, "Polygon: alles löschen", self)
        self.action_group_polygon.addAction(self.action_tool_polygon_reset)
        self.imageToolbar.addAction(self.action_tool_polygon_reset)
        self.action_tool_polygon_reset.triggered.connect(self.polygon_reset)

        self.action_group_polygon.setEnabled(False)

    def activateMove(self):
        self.canvasImage.setMapTool(self.canvasImage.toolMove)

    def activatePan(self):
        self.canvasImage.setMapTool(self.canvasImage.toolPan)

    def activateZoomIn(self):
        self.canvasImage.setMapTool(self.canvasImage.toolZoomIn)

    def activateZoomOut(self):
        self.canvasImage.setMapTool(self.canvasImage.toolZoomOut)

    def activateMapToolMove(self, _):
        self.actionMove.activate(0)

    def polygon_set_map_tool(self, checked):
        self.action_group_polygon.setEnabled(checked)
        if checked:
            self.canvasImage.setMapTool(self.toolDrawPolygon)
        else:
            self.toolDrawPolygon.recover_to_normal_mode()

    def polygon_undo(self):
        self.toolDrawPolygon.undo_last_point()

    def polygon_finish(self):
        self.toolDrawPolygon.recover_to_normal_mode()

    def polygon_edit(self):
        self.toolDrawPolygon.select_mode()

    def polygon_reset(self):
        self.toolDrawPolygon.reset_polygon()

    def updateCoordinate(self, coordObj):
        self.coordLineEdit.setText(str(round(coordObj["x"], 2)) + "," + str(round(coordObj["y"], 2)))
