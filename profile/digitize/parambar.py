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

class Parambar(QWidget):

    ## The constructor.
    # Creates labels with styles
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self, dialogInstance, canvasDigitize):

        super(Parambar, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')
        print('iconpath', self.iconpath)
        self.dialogInstance = dialogInstance

        self.canvasDigitize = canvasDigitize

        self.canvasToolbar = QToolBar("Edit", self)

        self.paramsBarLayout = QHBoxLayout()
        self.setLayout(self.paramsBarLayout)
        #self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.paramsBarLayout.addWidget(self.canvasToolbar)

        self.createPanAction()
        self.createActionZoomIn()
        self.createActionZoomOut()
        self.createActionExtent()

    '''
    ## \brief Create click action
    #
    def activateClick(self):
        print('activateClick')
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolClick)'''


    ## \brief Create pan action
    #
    def activatePan(self):
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolPan)

    ## \brief Create pan action
    #
    def activateZoomIn(self):
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolZoomIn)

    ## \brief Create pan action
    #
    def activateZoomOut(self):
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolZoomOut)

    '''
    ## \brief Create click action
    #
    def createClickAction(self):

        #Click
        iconClick = QIcon(os.path.join(self.iconpath, 'mActionAddGCPPoint.png'))
        self.actionClick = QAction(iconClick, "Click", self)
        self.actionClick.setCheckable(True)

        self.canvasDigitize.toolClick.setAction(self.actionClick)

        self.canvasToolbar.addAction(self.actionClick)
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolClick)
        self.actionClick.triggered.connect(self.activateClick)'''


    ## \brief Create pan action
    #
    def createPanAction(self):

        #Pan
        iconPan = QIcon(os.path.join(self.iconpath, 'mActionPan.png'))
        self.actionPan = QAction(iconPan, "Pan", self)
        self.actionPan.setCheckable(True)

        self.canvasDigitize.toolPan.setAction(self.actionPan)

        self.canvasToolbar.addAction(self.actionPan)
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolPan)
        self.actionPan.triggered.connect(self.activatePan)


    def createActionZoomIn(self):

        iconZoomIn = QIcon(os.path.join(self.iconpath, 'mActionZoomIn.png'))
        self.actionZoomIn = QAction(iconZoomIn, "Zoom in", self)
        self.actionZoomIn.setCheckable(True)

        self.canvasDigitize.toolZoomIn.setAction(self.actionZoomIn)

        self.canvasToolbar.addAction(self.actionZoomIn)
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolZoomIn)

        self.actionZoomIn.triggered.connect(self.activateZoomIn)

    def createActionZoomOut(self):

        iconZoomOut = QIcon(os.path.join(self.iconpath, 'mActionZoomOut.png'))
        self.actionZoomOut = QAction(iconZoomOut, "Zoom out", self)
        self.actionZoomOut.setCheckable(True)

        self.canvasDigitize.toolZoomOut.setAction(self.actionZoomOut)

        self.canvasToolbar.addAction(self.actionZoomOut)
        self.canvasDigitize.setMapTool(self.canvasDigitize.toolZoomOut)

        self.actionZoomOut.triggered.connect(self.activateZoomOut)

    def createActionExtent(self):

        iconExtent = QIcon(os.path.join(self.iconpath, 'mActionZoomToLayer.png'))
        self.actionExtent = QAction(iconExtent, "Zoom to layer", self)

        self.canvasToolbar.addAction(self.actionExtent)

        self.actionExtent.triggered.connect(self.canvasDigitize.setExtentByImageLayer)

    def activateMapToolMove(self, linkObj):
        self.actionMove.activate(0)


    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def createSplitter(self):
        vSplit = QFrame()
        vSplit.setFrameShape(QFrame.VLine|QFrame.Sunken)

        return vSplit
