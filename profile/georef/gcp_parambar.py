# -*- coding: utf-8 -*-
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy, QToolBar, QAction

## @brief With the TransformationDialogParambar class a bar based on QWidget is realized
#
# Inherits from QWidget
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09

class GcpParambar(QWidget):

    ## The constructor.
    # Creates labels with styles
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self, dialogInstance, canvasGcp):

        super(GcpParambar, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')

        self.dialogInstance = dialogInstance

        self.canvasGcp = canvasGcp

        self.gcpToolbar = QToolBar("Edit", self)

        self.paramsBarLayout = QHBoxLayout()
        self.setLayout(self.paramsBarLayout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.paramsBarLayout.addWidget(self.gcpToolbar)

        self.createPanAction()
        self.createActionZoomIn()
        self.createActionZoomOut()
        self.createActionExtent()

    ## \brief Create pan action
    #
    def activatePan(self):
        self.canvasGcp.setMapTool(self.canvasGcp.toolPan)

    ## \brief Create pan action
    #
    def activateZoomIn(self):
        self.canvasGcp.setMapTool(self.canvasGcp.toolZoomIn)

    ## \brief Create pan action
    #
    def activateZoomOut(self):
        self.canvasGcp.setMapTool(self.canvasGcp.toolZoomOut)

    ## \brief Create pan action
    #
    def createPanAction(self):

        #Pan
        iconPan = QIcon(os.path.join(self.iconpath, 'mActionPan.png'))
        self.actionPan = QAction(iconPan, "Pan", self)
        self.actionPan.setCheckable(True)

        self.canvasGcp.toolPan.setAction(self.actionPan)

        self.gcpToolbar.addAction(self.actionPan)
        self.canvasGcp.setMapTool(self.canvasGcp.toolPan)
        self.actionPan.triggered.connect(self.activatePan)

    def createActionZoomIn(self):

        iconZoomIn = QIcon(os.path.join(self.iconpath, 'mActionZoomIn.png'))
        self.actionZoomIn = QAction(iconZoomIn, "Zoom in", self)
        self.actionZoomIn.setCheckable(True)

        self.canvasGcp.toolZoomIn.setAction(self.actionZoomIn)

        self.gcpToolbar.addAction(self.actionZoomIn)
        self.canvasGcp.setMapTool(self.canvasGcp.toolZoomIn)

        self.actionZoomIn.triggered.connect(self.activateZoomIn)

    def createActionZoomOut(self):

        iconZoomOut = QIcon(os.path.join(self.iconpath, 'mActionZoomOut.png'))
        self.actionZoomOut = QAction(iconZoomOut, "Zoom out", self)
        self.actionZoomOut.setCheckable(True)

        self.canvasGcp.toolZoomOut.setAction(self.actionZoomOut)

        self.gcpToolbar.addAction(self.actionZoomOut)
        self.canvasGcp.setMapTool(self.canvasGcp.toolZoomOut)

        self.actionZoomOut.triggered.connect(self.activateZoomOut)

    def createActionExtent(self):

        iconExtent = QIcon(os.path.join(self.iconpath, 'mActionZoomToLayer.png'))
        self.actionExtent = QAction(iconExtent, "Zoom to layer", self)

        self.gcpToolbar.addAction(self.actionExtent)

        self.actionExtent.triggered.connect(self.canvasGcp.setExtentByGcpLayer)



    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def createSplitter(self):
        vSplit = QFrame()
        vSplit.setFrameShape(QFrame.VLine|QFrame.Sunken)

        return vSplit
