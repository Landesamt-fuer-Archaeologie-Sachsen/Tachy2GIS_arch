# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon, QFont, QColor
from qgis.core import QgsVectorLayer, QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom, QgsHighlight

## @brief With the ProfileGcpCanvas class a map canvas element is realized. It should be used in the profile dialog
#
# Inherits from QgsMapCanvas
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-26-05

class ProfileGcpCanvas(QgsMapCanvas):

    ## The constructor.
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self, dialogInstance):

        super(ProfileGcpCanvas, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), 'Icons')

        self.dialogInstance = dialogInstance

        self.activePoint = None

        self.gcpLayer = None

        self.setCanvasColor(Qt.white)

        self.createMapToolPan()
        self.createMapToolZoomIn()
        self.createMapToolZoomOut()

        self.createConnects()


    ## \brief Event connections
    #
    def createConnects(self):

        #Koordinatenanzeige
        self.xyCoordinates.connect(self.canvasMoveEvent)

    ## \brief Set coordinates on the statusbar in dialog instance TransformationDialog.setCoordinatesOnStatusBar() . Depends on mouse move on the map element
    #
    def canvasMoveEvent(self, event):
        x = event.x()
        y = event.y()
        #self.dialogInstance.setCoordinatesOnStatusBar(x, y)

    ## \brief Create action to pan on the map
    #
    def createMapToolPan(self):
        self.toolPan = QgsMapToolPan(self)

    ## \brief Create action to zoom in on the map
    #
    def createMapToolZoomIn(self):
        self.toolZoomIn = QgsMapToolZoom(self, False)

    ## \brief Create action to zoom out on the map
    #
    def createMapToolZoomOut(self):
        self.toolZoomOut = QgsMapToolZoom(self, True) # true = out

    ## \brief Set extent of the map by extent of the source layer
    #
    def setExtentByGcpLayer(self):

        self.setExtent(self.gcpLayer.extent())
        self.refresh()

    def setActivePoint(self, linkObj):
        print('setActivePoint image')
        #print(linkObj['uuid'])
        self.activePoint = linkObj['uuid']

    ## \brief Update canvas map element
    #
    # - Clear canvas element
    # - Validation of the source layer
    # - Show subset of the source layer - col obj_type = TransformationDialog.colNameGcpSource
    # - Marker symbol
    # - Label lyer with Id of the feature
    # - Additional display other input layers
    #
    # \param gcpLayer

    def updateCanvas(self, refData):

        #canvas leeren

        self.clearCache()
        self.refresh()

        self.gcpLayer = refData['pointLayer']

        #check validation of Layers
        if not self.gcpLayer.isValid():
            self.messageBar.pushMessage("Error", "Layer "+self.gcpLayer.name()+" failed to load!", level=1, duration=5)

        sourceCrs = self.gcpLayer.crs()

        #self.gcpLayer.setSubsetString("obj_type = '"+self.dialogInstance.colNameGcpSource+"'")

        #renderer = layer.renderer()

        symbol = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'red', 'size': '2'})

        self.gcpLayer.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol()))
        self.gcpLayer.renderer().setSymbol(symbol)
        # show the change
        self.gcpLayer.triggerRepaint()

        #Sets canvas CRS
        self.setDestinationCrs(sourceCrs)

        # set extent to the extent of Layer E_Point
        self.setExtentByGcpLayer()

        #Label Source Layer
        sourcelayerSettings  = QgsPalLayerSettings()
        textFormat = QgsTextFormat()

        textFormat.setFont(QFont("Arial", 12))
        textFormat.setSize(12)

        bufferSettings = QgsTextBufferSettings()
        bufferSettings.setEnabled(True)
        bufferSettings.setSize(0.10)
        bufferSettings.setColor(QColor("black"))

        textFormat.setBuffer(bufferSettings)
        sourcelayerSettings.setFormat(textFormat)

        sourcelayerSettings.fieldName = "ptnr"
        sourcelayerSettings.placement = 4
        sourcelayerSettings.enabled = True

        sourcelayerSettings = QgsVectorLayerSimpleLabeling(sourcelayerSettings)
        self.gcpLayer.setLabelsEnabled(True)
        self.gcpLayer.setLabeling(sourcelayerSettings)
        self.gcpLayer.triggerRepaint()

        listLayers = []
        listLayers.append(self.gcpLayer)

        self.setLayers(listLayers)

    ## \brief Short highlighting of a feature by uuid
    #
    # \param uuidValue

    def highlightSourceLayer(self, uuidValue):

        for feature in self.gcpLayer.getFeatures():
            uuidFeat = feature.attribute("uuid")
            if uuidFeat == uuidValue:
                self.flashFeatureIds(self.gcpLayer, [feature.id()], startColor = QColor(Qt.green), endColor = QColor(Qt.green), flashes = 5, duration = 500)
