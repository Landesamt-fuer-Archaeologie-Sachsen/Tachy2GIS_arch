# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtCore import Qt, QRect
from qgis.PyQt.QtGui import QIcon, QPainter, QColor
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QToolBar, QAction, QLineEdit, QActionGroup
from qgis.core import QgsApplication

from ..digitize.map_tools import PolygonMapTool


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

        icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "Icons")

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
        iconPan = QIcon(QgsApplication.iconPath("mActionPan"))
        self.actionPan = QAction(iconPan, "Pan", self)
        self.actionPan.setCheckable(True)
        self.canvasImage.toolPan.setAction(self.actionPan)
        self.action_group.addAction(self.actionPan)
        self.imageToolbar.addAction(self.actionPan)
        self.actionPan.triggered.connect(self.activatePan)

        # create component zoom in:
        iconZoomIn = QIcon(QgsApplication.iconPath("mActionZoomIn"))
        self.actionZoomIn = QAction(iconZoomIn, "Zoom in", self)
        self.actionZoomIn.setCheckable(True)
        self.canvasImage.toolZoomIn.setAction(self.actionZoomIn)
        self.action_group.addAction(self.actionZoomIn)
        self.imageToolbar.addAction(self.actionZoomIn)
        self.actionZoomIn.triggered.connect(self.activateZoomIn)

        # create component zoom out:
        iconZoomOut = QIcon(QgsApplication.iconPath("mActionZoomOut"))
        self.actionZoomOut = QAction(iconZoomOut, "Zoom out", self)
        self.actionZoomOut.setCheckable(True)
        self.canvasImage.toolZoomOut.setAction(self.actionZoomOut)
        self.action_group.addAction(self.actionZoomOut)
        self.imageToolbar.addAction(self.actionZoomOut)
        self.actionZoomOut.triggered.connect(self.activateZoomOut)

        # create component zoom to extent:
        iconExtent = QIcon(QgsApplication.iconPath("mActionZoomToLayer"))
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
            painter.setCompositionMode(QPainter.CompositionMode_DestinationOver)
            painter.drawPixmap(QRect(big - small, big - small, small, small), small_pixmap, small_pixmap.rect())
            painter.end()
            return QIcon(pixmap)

        # createAction_tool_polygon
        icon_geom = QIcon(QgsApplication.iconPath("mLayoutItemPolygon.svg"))
        icon_add = merge_icons(
            icon_geom,
            QIcon(QgsApplication.iconPath("mActionAdd.svg")),
        )
        self.action_tool_polygon = QAction(
            icon_add,
            (
                "Polygon zeichnen (zum Beschneiden)\n"
                "-> [L-MAUS] Punkt setzen\n"
                "-> [Z] vorhergehenden Punkt entfernen\n"
                "-> [R] Reihenfolge der Punkte umkehren\n"
                "-> [R-MAUS] Editieren beenden"
            ),
            self,
        )
        self.action_tool_polygon.setCheckable(True)
        self.action_group.addAction(self.action_tool_polygon)
        self.imageToolbar.addAction(self.action_tool_polygon)
        self.action_tool_polygon.toggled.connect(self.polygon_set_map_tool)

        # createAction_tool_polygon_edit
        icon_edit = merge_icons(
            color_shift_icon(icon_geom, QColor(0, 160, 255, 80)),
            QIcon(QgsApplication.iconPath("mActionToggleEditing.svg")),
        )
        self.action_tool_polygon_edit = QAction(icon_edit, "Polygon editieren\n(1) Punkt auswählen", self)
        self.action_group_polygon.addAction(self.action_tool_polygon_edit)
        self.imageToolbar.addAction(self.action_tool_polygon_edit)
        self.action_tool_polygon_edit.triggered.connect(self.polygon_edit)

        # createAction_tool_polygon_reset
        icon_reset = merge_icons(
            color_shift_icon(icon_geom, QColor(190, 0, 0, 60)),
            QIcon(QgsApplication.iconPath("mActionDeleteSelected.svg")),
        )
        self.action_tool_polygon_reset = QAction(icon_reset, "Polygon entfernen", self)
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

    def polygon_edit(self):
        self.toolDrawPolygon.select_mode()

    def polygon_reset(self):
        self.toolDrawPolygon.reset_geometry()

    def updateCoordinate(self, coordObj):
        self.coordLineEdit.setText(str(round(coordObj["x"], 2)) + "," + str(round(coordObj["y"], 2)))
