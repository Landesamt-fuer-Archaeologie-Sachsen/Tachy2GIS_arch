# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QWidget, QHBoxLayout, QLabel, QFrame, QSizePolicy, QToolBar, QAction, QComboBox, QLineEdit, QPushButton, QDoubleSpinBox

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

    def __init__(self, dialogInstance, canvasDigitize, toolIdentify, toolDigiPoint, toolDigiLine, toolDigiPolygon, toolEditPoint, toolEditLine, toolEditPolygon, rotationCoords):

        super(Parambar, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')
        self.dialogInstance = dialogInstance

        self.pup = Publisher()

        self.canvasDigitize = canvasDigitize
        self.toolDigiPoint = toolDigiPoint
        self.toolDigiLine = toolDigiLine
        self.toolDigiPolygon = toolDigiPolygon
        self.toolIdentify = toolIdentify

        self.toolEditPoint = toolEditPoint
        self.toolEditLine = toolEditLine
        self.toolEditPolygon = toolEditPolygon

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
        self.createIdentifyAction()

        self.createGetObjectsAction()

        self.createLayerauswahl()

        self.createSnapAction()
        self.createDigiPointAction()
        self.createDigiLineAction()
        self.createDigiPolygonAction()

        self.createEditPointAction()
        self.createEditLineAction()
        self.createEditPolygonAction()
        

        self.createTakeLayerAction()

        

        self.activatePan()

        #Koordinatenanzeige
        self.toolbarCoord = QToolBar("Coordinates", self)
        self.coordLineEdit = QLineEdit()
        self.coordLineEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.coordLineEdit.setAlignment(Qt.AlignCenter)
        self.coordLineEdit.setReadOnly(True)
        self.coordLineEditFm = self.coordLineEdit.fontMetrics()
        width_text = self.coordLineEditFm.width('xxxxxx.xxx,xxxxxxx.xxx,xxxx.xxx')
        self.coordLineEdit.setMinimumWidth(width_text + 20)
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
        #self.paramsBarLayout.addWidget(self.toolbarLayer)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.paramsBarLayout.addWidget(spacer)

        self.paramsBarLayout.addWidget(self.toolbarCoord)


    def createConnects(self):
        self.activeLayerCombo.currentIndexChanged.connect(self.__switchLayer)

        self.takeLayerButton.triggered.connect(self.takeLayerObjects)

    def takeLayerObjects(self):

        try:
            #layer_id = self.activeLayerCombo.currentData()
            #if self.refData['pointLayer'].id() == layer_id:
            self.toolDigiPoint.reverseRotation2Eingabelayer(self.refData['pointLayer'].id())
            #if self.refData['lineLayer'].id() == layer_id:
            self.toolDigiLine.reverseRotation2Eingabelayer(self.refData['lineLayer'].id())
            #if self.refData['polygonLayer'].id() == layer_id:
            self.toolDigiPolygon.reverseRotation2Eingabelayer(self.refData['polygonLayer'].id())

            infoText = "Objekte wurden erfolgreich in die Eingabelayer geschrieben."
            titleText = "Info"

        except Exception as e:
            infoText = f"Achtung! Die Daten wurden nicht in die Eingabelayer geschrieben. ({e})"
            titleText = "Fehler"

        #Info message
        self.__openInfoMessageBox(infoText, titleText)

    def getOriginalObjects(self):

        if self.getObjectsAction.isChecked():

            iconImport = QIcon(os.path.join(self.iconpath, 'Sichtbar_an.gif'))
            self.getObjectsAction.setIcon(iconImport)
            bufferGeometry = self.rotationCoords.profileBuffer(self.bufferSpin.value())

            self.toolDigiPoint.getFeaturesFromEingabelayer(bufferGeometry, 'tachy')
            self.toolDigiLine.getFeaturesFromEingabelayer(bufferGeometry, 'tachy')
            self.toolDigiPolygon.getFeaturesFromEingabelayer(bufferGeometry, 'tachy')
        else:
            iconImport = QIcon(os.path.join(self.iconpath, 'Sichtbar_aus.gif'))
            self.getObjectsAction.setIcon(iconImport)

            self.toolDigiPoint.removeNoneProfileFeatures()
            self.toolDigiLine.removeNoneProfileFeatures()
            self.toolDigiPolygon.removeNoneProfileFeatures()


    def __switchLayer(self, ix):

        combo = self.sender()
        layer_id = combo.currentData()

        if self.refData['pointLayer'].id() == layer_id:
            self.enableDigiPointAction()
            self.disableDigiLineAction()
            self.disableDigiPolygonAction()
            self.activateDigiPoint()

        if self.refData['lineLayer'].id() == layer_id:
            self.enableDigiLineAction()
            self.disableDigiPointAction()
            self.disableDigiPolygonAction()
            self.activateDigiLine()

        if self.refData['polygonLayer'].id() == layer_id:
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

    ## \brief Create identify action
    #
    def activateIdentify(self):
        self.canvasDigitize.setMapTool(self.toolIdentify)

    ## \brief Create snap action
    #
    def activateSnap(self):

        if self.actionSnap.isChecked():
            print('snapping on')

            self.toolDigiPoint.setSnapping(True)
            self.toolDigiLine.setSnapping(True)
            self.toolDigiPolygon.setSnapping(True)
            self.toolEditPoint.setSnapping(True)
            self.toolEditLine.setSnapping(True)
            self.toolEditPolygon.setSnapping(True)

        else:
            print('snapping off')
            self.toolDigiPoint.setSnapping(False)
            self.toolDigiLine.setSnapping(False)
            self.toolDigiPolygon.setSnapping(False)
            self.toolEditPoint.setSnapping(False)
            self.toolEditLine.setSnapping(False)
            self.toolEditPolygon.setSnapping(False)


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

    ## \brief Create point action
    #
    def activateEditPoint(self):
        self.canvasDigitize.setMapTool(self.toolEditPoint)
        self.toolDigiPoint.clearVertexMarker()

    ## \brief Create line action
    #
    def activateEditLine(self):
        self.canvasDigitize.setMapTool(self.toolEditLine)
        self.toolDigiLine.clearRubberband()

    ## \brief Create polygon action
    #
    def activateEditPolygon(self):
        self.canvasDigitize.setMapTool(self.toolEditPolygon)
        self.toolDigiPolygon.clearRubberband()

    ## \brief Create take layer action
    #
    def createTakeLayerAction(self):

        #Button in Eingabelayer übernehmen
        self.canvasToolbar.addSeparator()
        iconPan = QIcon(os.path.join(self.iconpath, 'export2eingabelayer.png'))
        self.takeLayerButton = QAction(iconPan, "Objekte in Eingabelayer schreiben", self)
        self.canvasToolbar.addAction(self.takeLayerButton)


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

    ## \brief Create identify action
    #
    def createIdentifyAction(self):

        #Point
        iconIdentify = QIcon(os.path.join(self.iconpath, 'mActionIdentify.png'))
        self.actionIdentify = QAction(iconIdentify, "Objekte abfragen", self)
        self.actionIdentify.setCheckable(True)

        self.toolIdentify.setAction(self.actionIdentify)

        self.canvasToolbar.addAction(self.actionIdentify)
        print('toolIdentify.type():', type(self.toolIdentify))
        self.canvasDigitize.setMapTool(self.toolIdentify)
        self.actionIdentify.triggered.connect(self.activateIdentify)


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

    def createSnapAction(self):

        iconSnap = QIcon(os.path.join(self.iconpath, 'mIconSnapping.png'))
        self.actionSnap = QAction(iconSnap, "Snapping", self)
        self.actionSnap.setCheckable(True)

        self.canvasToolbar.addAction(self.actionSnap)
  
        self.actionSnap.triggered.connect(self.activateSnap)


    ## \brief Create point action
    #
    def createDigiPointAction(self):

        #Point
        iconDigiPoint = QIcon(os.path.join(self.iconpath, 'mActionCapturePoint.png'))
        self.actionDigiPoint = QAction(iconDigiPoint, "Digitalisieren - Punkt", self)
        self.actionDigiPoint.setCheckable(True)

        self.toolDigiPoint.setAction(self.actionDigiPoint)

        self.canvasToolbar.addAction(self.actionDigiPoint)
        print('toolDigiPoint.type():', type(self.toolDigiPoint))
        self.canvasDigitize.setMapTool(self.toolDigiPoint)
        self.actionDigiPoint.triggered.connect(self.activateDigiPoint)

    ## \brief Create line action
    #
    def createDigiLineAction(self):

        #Line
        iconDigiLine = QIcon(os.path.join(self.iconpath, 'mActionCaptureLine.png'))
        self.actionDigiLine = QAction(iconDigiLine, "Digitalisieren - Linie", self)
        self.actionDigiLine.setCheckable(True)

        self.toolDigiLine.setAction(self.actionDigiLine)

        self.canvasToolbar.addAction(self.actionDigiLine)
        self.canvasDigitize.setMapTool(self.toolDigiLine)
        self.actionDigiLine.triggered.connect(self.activateDigiLine)

    ## \brief Create polygon action
    #
    def createDigiPolygonAction(self):

        #Polygon
        iconDigiPolygon = QIcon(os.path.join(self.iconpath, 'mActionCapturePolygon.png'))
        self.actionDigiPolygon = QAction(iconDigiPolygon, "Digitalisieren - Polygon", self)
        self.actionDigiPolygon.setCheckable(True)

        self.toolDigiPolygon.setAction(self.actionDigiPolygon)

        self.canvasToolbar.addAction(self.actionDigiPolygon)
        self.canvasDigitize.setMapTool(self.toolDigiPolygon)
        self.actionDigiPolygon.triggered.connect(self.activateDigiPolygon)


    ## \brief Create point action
    #
    def createGetObjectsAction(self):

        #Button Objekte aus Layer anzeigen
        iconImport = QIcon(os.path.join(self.iconpath, 'Sichtbar_aus.gif'))
        self.getObjectsAction = QAction(iconImport, "Objekte aus Eingabelayer", self)
        self.getObjectsAction.setCheckable(True)
        self.getObjectsAction.triggered.connect(self.getOriginalObjects)
        self.canvasToolbar.addSeparator()
        self.canvasToolbar.addAction(self.getObjectsAction)

        #Buffer Spinbox
        self.bufferSpin = QDoubleSpinBox(self)
        self.bufferSpin.setMinimum(0)
        self.bufferSpin.setMaximum(5)
        self.bufferSpin.setSingleStep(0.01)
        self.bufferSpin.setValue(1)
        self.bufferSpin.setToolTip('Max. Abstand [m] der Eingabelayerobjekte von der Profillinie')  
        self.canvasToolbar.addWidget(self.bufferSpin)


    ## \brief Create Layerauswahl
    #
    def createLayerauswahl(self):

        #Layerauswahl
        self.canvasToolbar.addSeparator()
        self.labelActiveLayerCombo = QLabel('Aktiver Layer')
        self.labelActiveLayerCombo.setAlignment(Qt.AlignVCenter)
        self.labelActiveLayerCombo.setStyleSheet("padding-right: 4px; padding-left: 4px")
        
        self.activeLayerCombo = QComboBox()
        self.canvasToolbar.addWidget(self.labelActiveLayerCombo)
        self.canvasToolbar.addWidget(self.activeLayerCombo)
        self.canvasToolbar.addSeparator()



    ## \brief Create point action
    #
    def createEditPointAction(self):

        iconEditPoint = QIcon(os.path.join(self.iconpath, 'mActionNodeTool.png'))
        self.actionEditPoint = QAction(iconEditPoint, "Knotenwerkzeug - Punkt", self)
        self.actionEditPoint.setCheckable(True)

        self.toolEditPoint.setAction(self.actionEditPoint)

        self.canvasToolbar.addAction(self.actionEditPoint)
        self.canvasDigitize.setMapTool(self.toolEditPoint)
        self.actionEditPoint.triggered.connect(self.activateEditPoint)

    ## \brief Create line action
    #
    def createEditLineAction(self):

        #Line
        iconEditLine = QIcon(os.path.join(self.iconpath, 'mActionNodeTool.png'))
        self.actionEditLine = QAction(iconEditLine, "Knotenwerkzeug - Linie", self)
        self.actionEditLine.setCheckable(True)

        self.toolEditLine.setAction(self.actionEditLine)

        self.canvasToolbar.addAction(self.actionEditLine)
        self.canvasDigitize.setMapTool(self.toolEditLine)
        self.actionEditLine.triggered.connect(self.activateEditLine)

    ## \brief Create polygon action
    #
    def createEditPolygonAction(self):

        #Line
        iconEditPolygon = QIcon(os.path.join(self.iconpath, 'mActionNodeTool.png'))
        self.actionEditPolygon = QAction(iconEditPolygon, "Knotenwerkzeug - Polygon", self)
        self.actionEditPolygon.setCheckable(True)

        self.toolEditPolygon.setAction(self.actionEditPolygon)

        self.canvasToolbar.addAction(self.actionEditPolygon)
        self.canvasDigitize.setMapTool(self.toolEditPolygon)
        self.actionEditPolygon.triggered.connect(self.activateEditPolygon)

    def activateMapToolMove(self, linkObj):
        self.actionMove.activate(0)


    def enableDigiPointAction(self):
        self.actionDigiPoint.setVisible(True)
        self.actionEditPoint.setVisible(True)

    #def enableIdentifyAction(self):
    #    self.actionIdentify.setVisible(True)

    def enableDigiLineAction(self):
        self.actionDigiLine.setVisible(True)
        self.actionEditLine.setVisible(True)

    def enableDigiPolygonAction(self):
        self.actionDigiPolygon.setVisible(True)
        self.actionEditPolygon.setVisible(True)

    def disableDigiPointAction(self):
        self.actionDigiPoint.setVisible(False)
        self.actionEditPoint.setVisible(False)
        self.toolDigiPoint.clearVertexMarker()

    #def disableIdentifyAction(self):
    #    self.actionIdentify.setVisible(False)

    def disableDigiLineAction(self):
        self.actionDigiLine.setVisible(False)
        self.actionEditLine.setVisible(False)
        self.toolDigiLine.clearRubberband()

    def disableDigiPolygonAction(self):
        self.actionDigiPolygon.setVisible(False)
        self.actionEditPolygon.setVisible(False)
        self.toolDigiPolygon.clearRubberband()
    ## \brief Update parambar element
    #
    # \param refData

    def update(self, refData):

        #self.createComponents()
        #self.createLayout()
        #self.createConnects()

        self.refData = refData

        self.activeLayerCombo.clear()
        self.activeLayerCombo.addItem(self.refData['pointLayer'].sourceName(), self.refData['pointLayer'].id())
        self.activeLayerCombo.addItem(self.refData['lineLayer'].sourceName(), self.refData['lineLayer'].id())
        self.activeLayerCombo.addItem(self.refData['polygonLayer'].sourceName(), self.refData['polygonLayer'].id())

        self.activeLayerCombo.resize(self.activeLayerCombo.sizeHint())

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def updateCoordinate(self, coordObj):

        retObj = self.rotationCoords.rotationReverse(coordObj['x'], coordObj['y'], True)

        self.coordLineEdit.setText(str('{:.3f}'.format(round(retObj['x_trans'], 3)))+','+str('{:.3f}'.format(round(retObj['y_trans'], 3)))+','+str('{:.3f}'.format(round(retObj['z_trans'], 3))))

    ## \brief Create a splitter (vertical line to separate labels in the parambar)
    #
    def createSplitter(self):
        vSplit = QFrame()
        vSplit.setFrameShape(QFrame.VLine|QFrame.Sunken)

        return vSplit


    ## \brief Opens a message box with background informations
    #

    def __openInfoMessageBox(self, infoText, titleText):

        self.__infoTranssformMsgBox = QMessageBox()
        self.__infoTranssformMsgBox.setText(infoText)
        self.__infoTranssformMsgBox.setWindowTitle(titleText)
        self.__infoTranssformMsgBox.setStandardButtons((QMessageBox.Ok))
        self.__infoTranssformMsgBox.exec_()