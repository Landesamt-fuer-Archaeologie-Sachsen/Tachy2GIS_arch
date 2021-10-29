# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy, QToolBar, QAction, QComboBox, QLineEdit, QPushButton

from ..publisher import Publisher

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

    def __init__(self, dialogInstance, canvasDigitize, toolDigiPoint, toolDigiLine, toolDigiPolygon, toolEditLine, rotationCoords):

        super(Parambar, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')
        self.dialogInstance = dialogInstance

        self.pup = Publisher()

        self.canvasDigitize = canvasDigitize
        self.toolDigiPoint = toolDigiPoint
        self.toolDigiLine = toolDigiLine
        self.toolDigiPolygon = toolDigiPolygon

        self.toolEditLine = toolEditLine

        self.rotationCoords = rotationCoords

        self.refData = None

        self.createComponents()
        self.createLayout()
        self.createConnects()


    ## \brief Create components
    #
    def createComponents(self):

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

        #self.activeLayerCombo.wheelEvent = lambda event: None
        #self.activeLayerCombo.currentTextChanged.connect(self.activeLayerChanged)

        self.toolbarLayer.addWidget(self.labelActiveLayerCombo)
        self.toolbarLayer.addWidget(self.activeLayerCombo)
        self.createDigiPointAction()
        self.createDigiLineAction()
        self.createDigiPolygonAction()

        self.createEditLineAction()

        #Button in Eingabelayer übernehmen
        self.takeLayerButton = QPushButton(self)
        self.takeLayerButton.setText("Objekte in Eingabelayerschreiben")
        self.takeLayerButton.setStyleSheet("background-color: green; width: 200px")
        self.toolbarLayer.addWidget(self.takeLayerButton)

        #Button Objekte aus Layer anzeigen
        self.getObjectsButton = QPushButton(self)
        self.getObjectsButton.setText("Objekte aus Eingabelayer")
        self.getObjectsButton.setStyleSheet("background-color: yellow; width: 150px")
        self.toolbarLayer.addWidget(self.getObjectsButton)

        #Koordinatenanzeige
        self.toolbarCoord = QToolBar("Coordinates", self)
        self.coordLabel = QLabel("Koordinate ")
        self.coordLineEdit = QLineEdit()
        self.coordLineEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.coordLineEdit.setReadOnly(True)
        self.coordLineEdit.setMinimumWidth(200);
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

        spacer = QWidget();
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred);
        self.paramsBarLayout.addWidget(spacer);

        self.paramsBarLayout.addWidget(self.toolbarCoord)


    def createConnects(self):
        self.activeLayerCombo.currentIndexChanged.connect(self.__switchLayer)

        self.takeLayerButton.clicked.connect(self.takeLayerObjects)

        self.getObjectsButton.clicked.connect(self.getOriginalObjects)



    def takeLayerObjects(self):
        layer_id = self.activeLayerCombo.currentData()
        if self.refData['pointLayer'].id() == layer_id:
            self.toolDigiPoint.reverseRotation2Eingabelayer(layer_id)
        if self.refData['lineLayer'].id() == layer_id:
            self.toolDigiLine.reverseRotation2Eingabelayer(layer_id)
        if self.refData['polygonLayer'].id() == layer_id:
            self.toolDigiPolygon.reverseRotation2Eingabelayer(layer_id)

    def getOriginalObjects(self):
        layer_id = self.activeLayerCombo.currentData()
        bufferGeometry = self.rotationCoords.profileBuffer(1)

        #if self.refData['pointLayer'].id() == layer_id:
        self.toolDigiPoint.rotationFromEingabelayer(bufferGeometry)
        self.toolDigiLine.rotationFromEingabelayer(bufferGeometry)
        self.toolDigiPolygon.rotationFromEingabelayer(bufferGeometry)

    def __switchLayer(self, ix):
        print('__switchLayer')
        combo = self.sender()
        layer_id = combo.currentData()

        if self.refData['pointLayer'].id() == layer_id:
            print('point')
            self.enableDigiPointAction()
            self.disableDigiLineAction()
            self.disableDigiPolygonAction()
            self.activateDigiPoint()

        if self.refData['lineLayer'].id() == layer_id:
            print('line')
            self.enableDigiLineAction()
            self.disableDigiPointAction()
            self.disableDigiPolygonAction()
            self.activateDigiLine()
            self.activateEditLine()

        if self.refData['polygonLayer'].id() == layer_id:
            print('polygon')
            self.disableDigiLineAction()
            self.disableDigiPointAction()
            self.enableDigiPolygonAction()
            self.activateDigiPolygon()

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

    ## \brief Create point action
    #
    def activateDigiPoint(self):
        self.canvasDigitize.setMapTool(self.toolDigiPoint)

    ## \brief Create line action
    #
    def activateDigiLine(self):
        self.canvasDigitize.setMapTool(self.toolDigiLine)

    ## \brief Create polygon action
    #
    def activateDigiPolygon(self):
        self.canvasDigitize.setMapTool(self.toolDigiPolygon)

    ## \brief Create line action
    #
    def activateEditLine(self):
        self.canvasDigitize.setMapTool(self.toolEditLine)

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

    ## \brief Create point action
    #
    def createDigiPointAction(self):

        #Point
        iconDigiPoint = QIcon(os.path.join(self.iconpath, 'mActionCapturePoint.png'))
        self.actionDigiPoint = QAction(iconDigiPoint, "Digitalisieren - Punkt", self)
        self.actionDigiPoint.setCheckable(False)

        self.toolDigiPoint.setAction(self.actionDigiPoint)

        self.toolbarLayer.addAction(self.actionDigiPoint)
        self.canvasDigitize.setMapTool(self.toolDigiPoint)
        self.actionDigiPoint.triggered.connect(self.activateDigiPoint)

    ## \brief Create line action
    #
    def createDigiLineAction(self):

        #Line
        iconDigiLine = QIcon(os.path.join(self.iconpath, 'mActionCaptureLine.png'))
        self.actionDigiLine = QAction(iconDigiLine, "Digitalisieren - Linie", self)
        self.actionDigiLine.setCheckable(False)

        self.toolDigiLine.setAction(self.actionDigiLine)

        self.toolbarLayer.addAction(self.actionDigiLine)
        self.canvasDigitize.setMapTool(self.toolDigiLine)
        self.actionDigiLine.triggered.connect(self.activateDigiLine)

    ## \brief Create polygon action
    #
    def createDigiPolygonAction(self):

        #Polygon
        iconDigiPolygon = QIcon(os.path.join(self.iconpath, 'mActionCapturePolygon.png'))
        self.actionDigiPolygon = QAction(iconDigiPolygon, "Digitalisieren - Polygon", self)
        self.actionDigiPolygon.setCheckable(False)

        self.toolDigiPolygon.setAction(self.actionDigiPolygon)

        self.toolbarLayer.addAction(self.actionDigiPolygon)
        self.canvasDigitize.setMapTool(self.toolDigiPolygon)
        self.actionDigiPolygon.triggered.connect(self.activateDigiPolygon)

    ## \brief Create line action
    #
    def createEditLineAction(self):

        #Line
        iconEditLine = QIcon(os.path.join(self.iconpath, 'mActionCaptureLine.png'))
        self.actionEditLine = QAction(iconEditLine, "Knotenwerkzeug - Linie", self)
        self.actionEditLine.setCheckable(False)

        self.toolEditLine.setAction(self.actionEditLine)

        self.toolbarLayer.addAction(self.actionEditLine)
        self.canvasDigitize.setMapTool(self.toolEditLine)
        self.actionEditLine.triggered.connect(self.activateEditLine)

    def activateMapToolMove(self, linkObj):
        self.actionMove.activate(0)


    def enableDigiPointAction(self):
        self.actionDigiPoint.setVisible(True)

    def enableDigiLineAction(self):
        self.actionDigiLine.setVisible(True)
        self.actionEditLine.setVisible(True)

    def enableDigiPolygonAction(self):
        self.actionDigiPolygon.setVisible(True)

    def disableDigiPointAction(self):
        self.actionDigiPoint.setVisible(False)
        self.toolDigiPoint.clearVertexMarker()

    def disableDigiLineAction(self):
        self.actionDigiLine.setVisible(False)
        self.actionEditLine.setVisible(False)
        self.toolDigiLine.clearRubberband()

    def disableDigiPolygonAction(self):
        self.actionDigiPolygon.setVisible(False)
        self.toolDigiPolygon.clearRubberband()
    ## \brief Update parambar element
    #
    # \param refData

    def update(self, refData):

        self.refData = refData

        self.activeLayerCombo.clear()
        self.activeLayerCombo.addItem(self.refData['pointLayer'].sourceName(), self.refData['pointLayer'].id())
        self.activeLayerCombo.addItem(self.refData['lineLayer'].sourceName(), self.refData['lineLayer'].id())
        self.activeLayerCombo.addItem(self.refData['polygonLayer'].sourceName(), self.refData['polygonLayer'].id())

        self.activeLayerCombo.resize(self.activeLayerCombo.sizeHint())

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def updateCoordinate(self, coordObj):

        #self.pup.publish('triggerAarTransformationParams', {})

        #self.rotationCoords = self.rotationCoords(self.transformationParams)

        retObj = self.rotationCoords.rotationReverse(coordObj['x'], coordObj['y'], True)

        self.coordLineEdit.setText(str(round(retObj['x_trans'], 3))+','+str(round(retObj['y_trans'], 3))+','+str(round(retObj['z_trans'], 3)))

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def createSplitter(self):
        vSplit = QFrame()
        vSplit.setFrameShape(QFrame.VLine|QFrame.Sunken)

        return vSplit