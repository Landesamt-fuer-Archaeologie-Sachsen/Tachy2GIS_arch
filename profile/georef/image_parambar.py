# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFrame, QSizePolicy, QToolBar, QAction, QLineEdit
from qgis.core import QgsApplication

from .map_tool_draw_polygon import PolygonMapTool


## @brief With the TransformationDialogParambar class a bar based on QWidget is realized
#
# Inherits from QWidget
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09


class ImageParambar(QWidget):
    def __init__(self, dialogInstance, canvasImage):
        ## The constructor.
        # Creates labels with styles
        # @param dialogInstance pointer to the dialogInstance

        super(ImageParambar, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), "..", "Icons")
        print("iconpath", self.iconpath)
        self.dialogInstance = dialogInstance

        self.canvasImage = canvasImage

        self.createComponents()
        self.createLayout()

    ## \brief Create components
    #
    def createComponents(self):
        self.imageToolbar = QToolBar("Edit", self)

        self.createMoveAction()
        self.createPanAction()
        self.createActionZoomIn()
        self.createActionZoomOut()
        self.createActionExtent()

        self.toolbarCoord = QToolBar("Coordinates", self)
        self.coordLineEdit = QLineEdit()
        self.coordLineEdit.setAlignment(Qt.AlignCenter)
        self.coordLineEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.coordLineEdit.setReadOnly(True)
        self.coordLineEditFm = self.coordLineEdit.fontMetrics()
        width_text = self.coordLineEditFm.width("xxxxxx.xx,xxxxxx.xx")
        self.coordLineEdit.setMinimumWidth(width_text + 30)

        self.toolbarCoord.addWidget(self.coordLineEdit)

    ## \brief Create Layout
    #
    def createLayout(self):
        self.paramsBarLayout = QHBoxLayout()
        self.paramsBarLayout.setContentsMargins(0, 0, 0, 0)
        self.paramsBarLayout.setSpacing(0)
        self.setLayout(self.paramsBarLayout)
        self.paramsBarLayout.addWidget(self.imageToolbar)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.paramsBarLayout.addWidget(spacer)

        self.paramsBarLayout.addWidget(self.toolbarCoord)

    ## \brief Create move action
    #
    def activateMove(self):
        self.canvasImage.setMapTool(self.canvasImage.toolMove)

    ## \brief Create pan action
    #
    def activatePan(self):
        self.canvasImage.setMapTool(self.canvasImage.toolPan)

    ## \brief Create pan action
    #
    def activateZoomIn(self):
        self.canvasImage.setMapTool(self.canvasImage.toolZoomIn)

    ## \brief Create pan action
    #
    def activateZoomOut(self):
        self.canvasImage.setMapTool(self.canvasImage.toolZoomOut)

    ## \brief Create move action
    #
    def createMoveAction(self):
        # move
        iconMove = QIcon(os.path.join(self.iconpath, "mActionAddGCPPoint.png"))
        self.actionMove = QAction(iconMove, "Move", self)
        self.actionMove.setCheckable(True)

        self.canvasImage.toolMove.setAction(self.actionMove)

        self.imageToolbar.addAction(self.actionMove)
        self.canvasImage.setMapTool(self.canvasImage.toolMove)
        self.actionMove.triggered.connect(self.activateMove)

    ## \brief Create pan action
    #
    def createPanAction(self):
        # Pan
        iconPan = QIcon(os.path.join(self.iconpath, "mActionPan.png"))
        self.actionPan = QAction(iconPan, "Pan", self)
        self.actionPan.setCheckable(True)

        self.canvasImage.toolPan.setAction(self.actionPan)

        self.imageToolbar.addAction(self.actionPan)
        self.canvasImage.setMapTool(self.canvasImage.toolPan)
        self.actionPan.triggered.connect(self.activatePan)

    def createActionZoomIn(self):
        iconZoomIn = QIcon(os.path.join(self.iconpath, "mActionZoomIn.png"))
        self.actionZoomIn = QAction(iconZoomIn, "Zoom in", self)
        self.actionZoomIn.setCheckable(True)

        self.canvasImage.toolZoomIn.setAction(self.actionZoomIn)

        self.imageToolbar.addAction(self.actionZoomIn)
        self.canvasImage.setMapTool(self.canvasImage.toolZoomIn)

        self.actionZoomIn.triggered.connect(self.activateZoomIn)

    def createActionZoomOut(self):
        iconZoomOut = QIcon(os.path.join(self.iconpath, "mActionZoomOut.png"))
        self.actionZoomOut = QAction(iconZoomOut, "Zoom out", self)
        self.actionZoomOut.setCheckable(True)

        self.canvasImage.toolZoomOut.setAction(self.actionZoomOut)

        self.imageToolbar.addAction(self.actionZoomOut)
        self.canvasImage.setMapTool(self.canvasImage.toolZoomOut)

        self.actionZoomOut.triggered.connect(self.activateZoomOut)

    def createActionExtent(self):
        iconExtent = QIcon(os.path.join(self.iconpath, "mActionZoomToLayer.png"))
        self.actionExtent = QAction(iconExtent, "Zoom to layer", self)

        self.imageToolbar.addAction(self.actionExtent)

        self.actionExtent.triggered.connect(self.canvasImage.setExtentByImageLayer)

    def createAction_tool_polygon(self):
        icon = QIcon(QgsApplication.iconPath("mActionAddNodesItem.svg"))
        self.action_tool_polygon = QAction(icon, "Zeichne Polygon zum Beschneiden", self)
        self.action_tool_polygon.setCheckable(True)
        self.imageToolbar.addAction(self.action_tool_polygon)
        self.action_tool_polygon.triggered.connect(self.polygon_set_map_tool)

    def polygon_set_map_tool(self):
        self.canvasImage.setMapTool(self.toolDrawPolygon)

    def createAction_tool_polygon_finish(self):
        icon = QIcon(QgsApplication.iconPath("mLayoutItemPolygon.svg"))
        self.action_tool_polygon_finish = QAction(icon, "Linienzug schließen", self)
        self.imageToolbar.addAction(self.action_tool_polygon_finish)
        self.action_tool_polygon_finish.triggered.connect(self.polygon_finish)

    def polygon_finish(self):
        self.toolDrawPolygon.finishPolygon()

    def createAction_tool_polygon_reset(self):
        icon = QIcon(QgsApplication.iconPath("mActionRefresh.svg"))
        self.action_tool_polygon_reset = QAction(icon, "Polygon zurücksetzen", self)
        self.imageToolbar.addAction(self.action_tool_polygon_reset)
        self.action_tool_polygon_reset.triggered.connect(self.polygon_reset)

    def polygon_reset(self):
        self.toolDrawPolygon.reset()

    def set_for_kreuzprofil(self):
        self.toolDrawPolygon = PolygonMapTool(self.canvasImage)
        self.imageToolbar.addSeparator()
        self.createAction_tool_polygon()
        self.createAction_tool_polygon_finish()
        self.createAction_tool_polygon_reset()

    def activateMapToolMove(self, linkObj):
        self.actionMove.activate(0)

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def createSplitter(self):
        vSplit = QFrame()
        vSplit.setFrameShape(QFrame.VLine | QFrame.Sunken)

        return vSplit

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def updateCoordinate(self, coordObj):
        self.coordLineEdit.setText(str(round(coordObj["x"], 2)) + "," + str(round(coordObj["y"], 2)))
