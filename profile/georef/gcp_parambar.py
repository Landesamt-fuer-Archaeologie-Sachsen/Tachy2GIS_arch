# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy, QToolBar, QAction, QLineEdit

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

    def __init__(self, dialogInstance, canvasGcp, rotationCoords):

        super(GcpParambar, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')

        self.dialogInstance = dialogInstance

        self.canvasGcp = canvasGcp

        self.rotationCoords = rotationCoords

        self.createComponents()
        self.createLayout()

    ## \brief Create components
    #
    def createComponents(self):

        self.gcpToolbar = QToolBar("Edit", self)

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
        width_text = self.coordLineEditFm.width('xxxxxx.xxx,xxxxxxx.xxx,xxxx.xxx')
        self.coordLineEdit.setMinimumWidth(width_text + 10)

        self.toolbarCoord.addWidget(self.coordLineEdit)    


    ## \brief Create Layout
    #
    def createLayout(self):

        self.paramsBarLayout = QHBoxLayout()
        self.setLayout(self.paramsBarLayout)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.paramsBarLayout.setContentsMargins(0, 0, 0, 0)
        self.paramsBarLayout.setSpacing(0)
        self.paramsBarLayout.addWidget(self.gcpToolbar)

        spacer = QWidget();
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.paramsBarLayout.addWidget(spacer)

        self.paramsBarLayout.addWidget(self.toolbarCoord)

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

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def updateCoordinate(self, coordObj):
        #self.coordLineEdit.setText(str(round(coordObj['x'], 2))+','+str(round(coordObj['y'], 2)))

        retObj = self.rotationCoords.rotationReverse(coordObj['x'], coordObj['y'], True)

        self.coordLineEdit.setText(str(round(retObj['x_trans'], 3))+','+str(round(retObj['y_trans'], 3))+','+str(round(retObj['z_trans'], 3)))

