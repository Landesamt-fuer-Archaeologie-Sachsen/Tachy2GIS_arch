# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy, QToolBar, QAction, QComboBox, QLineEdit

from .rotation_coords import RotationCoords

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

    def __init__(self, dialogInstance, canvasDigitize, dataStore):

        super(Parambar, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')
        self.dialogInstance = dialogInstance

        self.canvasDigitize = canvasDigitize
        self.dataStore = dataStore

        self.createComponents()
        self.createLayout()
        #self.createConnects()


    ## \brief Create components
    #
    def createComponents(self):

        self.rotationCoords = RotationCoords(self.dataStore)

        #MapEdits
        self.canvasToolbar = QToolBar("Edit", self)
        self.createPanAction()
        self.createActionZoomIn()
        self.createActionZoomOut()
        self.createActionExtent()

        #Layerauswahl
        self.toolbarLayer = QToolBar("Layer", self)
        self.labelActiveLayerCombo = QLabel('Activer Layer')
        self.labelActiveLayerCombo.setAlignment(Qt.AlignVCenter)
        self.activeLayerCombo = QComboBox()
        #self.activeLayerCombo.setAlignment(Qt.AlignLeft)

        self.activeLayerCombo.wheelEvent = lambda event: None
        #self.activeLayerCombo.currentTextChanged.connect(self.onComboboxChanged)

        self.toolbarLayer.addWidget(self.labelActiveLayerCombo)
        self.toolbarLayer.addWidget(self.activeLayerCombo)

        #Koordinatenanzeige
        self.toolbarCoord = QToolBar("Coordinates", self)
        self.coordLabel = QLabel("Koordinate ")
        self.coordLineEdit = QLineEdit()
        self.coordLineEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.coordLineEdit.setReadOnly(True)
        self.coordLineEdit.setMinimumWidth(150);
        self.toolbarCoord.addWidget(self.coordLabel)
        self.toolbarCoord.addWidget(self.coordLineEdit)


    ## \brief Create Layout
    #
    def createLayout(self):

        self.paramsBarLayout = QHBoxLayout()
        self.paramsBarLayout.setContentsMargins(0, 0, 0, 0)
        self.paramsBarLayout.setSpacing(0)
        self.setLayout(self.paramsBarLayout)
        #self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.paramsBarLayout.addWidget(self.canvasToolbar)
        self.paramsBarLayout.addWidget(self.toolbarLayer)
        self.paramsBarLayout.addWidget(self.toolbarCoord)

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


    ## \brief Update parambar element
    #
    # \param refData

    def update(self, refData):

        self.activeLayerCombo.addItem(refData['pointLayer'].sourceName(), refData['pointLayer'])
        self.activeLayerCombo.addItem(refData['lineLayer'].sourceName(), refData['lineLayer'])
        self.activeLayerCombo.addItem(refData['polygonLayer'].sourceName(), refData['polygonLayer'])

        self.activeLayerCombo.resize(self.activeLayerCombo.sizeHint())

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def updateCoordinate(self, coordObj):

        retObj = self.rotationCoords.rotationReverse(coordObj['x'], coordObj['y'], coordObj['y'], True)

        print('orginal', coordObj['x'], coordObj['y'], 10)
        print('transform', retObj['x_trans'], retObj['y_trans'], retObj['z_trans'])

        self.coordLineEdit.setText(str(round(retObj['x_trans'], 2))+','+str(round(retObj['z_trans'], 2)))

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def createSplitter(self):
        vSplit = QFrame()
        vSplit.setFrameShape(QFrame.VLine|QFrame.Sunken)

        return vSplit
