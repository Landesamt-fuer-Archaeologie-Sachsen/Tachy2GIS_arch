# -*- coding: utf-8 -*-
import os
import processing
from PyQt5.QtCore import Qt
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsMarkerSymbol, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer, QgsLineSymbol, QgsFillSymbol, QgsSingleSymbolRenderer, QgsPoint, QgsCoordinateReferenceSystem
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom

from ..publisher import Publisher



## @brief With the ProfileImageCanvas class a map canvas element is realized. It should be used in the profile dialog
#
# Inherits from QgsMapCanvas
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-05-26

class DigitizeCanvas(QgsMapCanvas):

    ## The constructor.
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self, dialogInstance, iFace):

        super(DigitizeCanvas, self).__init__()

        self.__iface = iFace

        self.pup = Publisher()

        self.iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')

        self.dialogInstance = dialogInstance

        self.imageLayer = None

        self.digiPointLayer = None
        self.digiLineLayer = None
        self.digiPolygonLayer = None

        self.createMapToolPan()
        self.createMapToolZoomIn()
        self.createMapToolZoomOut()
        #self.createMapToolDigiPoint()
        #self.createMapToolDigiLine()
        #self.createMapToolDigiPolygon()

        self.createConnects()

    def createDigiPointLayer(self, refData):
        refData['pointLayer'].selectAll()
        self.digiPointLayer = processing.run("native:saveselectedfeatures", {'INPUT': refData['pointLayer'], 'OUTPUT': 'memory:'})['OUTPUT']
        refData['pointLayer'].removeSelection()

        #Layer leeren
        pr = self.digiPointLayer.dataProvider()
        pr.truncate()

        symbol = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'green', 'size': '2'})

        self.digiPointLayer.setRenderer(QgsSingleSymbolRenderer(symbol))

        #crs = QgsCoordinateReferenceSystem(31468)

        crs = refData['pointLayer'].sourceCrs()

        self.digiPointLayer.setCrs(crs)

    def createDigiLineLayer(self, refData):

        refData['lineLayer'].selectAll()
        self.digiLineLayer = processing.run("native:saveselectedfeatures", {'INPUT': refData['lineLayer'], 'OUTPUT': 'memory:'})['OUTPUT']
        refData['lineLayer'].removeSelection()

        #Layer leeren
        pr = self.digiLineLayer.dataProvider()
        pr.truncate()

        symbol = QgsLineSymbol.createSimple({'line_style': 'solid', 'color': 'green', 'width': '1'})

        symbol_layer_vertex = QgsMarkerLineSymbolLayer()
        symbol_layer_vertex.setSubSymbol(QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'red'}))
        symbol_layer_vertex.setPlacement(1)

        symbol.appendSymbolLayer(symbol_layer_vertex)

        self.digiLineLayer.renderer().setUsingSymbolLevels(True)
        self.digiLineLayer.renderer().setSymbol(symbol)

        crs = refData['lineLayer'].sourceCrs()

        self.digiLineLayer.setCrs(crs)


    def createDigiPolygonLayer(self, refData):

        refData['polygonLayer'].selectAll()
        self.digiPolygonLayer = processing.run("native:saveselectedfeatures", {'INPUT': refData['polygonLayer'], 'OUTPUT': 'memory:'})['OUTPUT']
        refData['polygonLayer'].removeSelection()

        #Layer leeren
        pr = self.digiPolygonLayer.dataProvider()
        pr.truncate()

        symbol = QgsFillSymbol.createSimple({'style':'no', 'outline_style': 'solid', 'outline_color': 'green', 'outline_width': '1'})

        symbol_layer_vertex = QgsMarkerLineSymbolLayer()
        symbol_layer_vertex.setSubSymbol(QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'red'}))
        symbol_layer_vertex.setPlacement(1)

        symbol.appendSymbolLayer(symbol_layer_vertex)

        self.digiPolygonLayer.renderer().setUsingSymbolLevels(True)
        self.digiPolygonLayer.renderer().setSymbol(symbol)

        crs = refData['lineLayer'].sourceCrs()

        self.digiPolygonLayer.setCrs(crs)

    ## \brief Set coordinates on the statusbar in dialog instance TransformationDialog.setCoordinatesOnStatusBar() . Depends on mouse move on the map element
    #
    def canvasMoveEvent(self, event):
        x = event.x()
        y = event.y()
        self.pup.publish('moveCoordinate', {'x': x, 'y': y})
        #self.dialogInstance.setCoordinatesOnStatusBar(x, y)

    ## \brief Event connections
    #
    def createConnects(self):

        #Koordinatenanzeige
        self.xyCoordinates.connect(self.canvasMoveEvent)



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

    ## \brief Create action to digitalize points
    #def createMapToolDigiPoint(self):
    #    self.toolDigiPoint = MapToolDigiPoint(self, self.__iface)

    ## \brief Create action to digitalize lines
    #def createMapToolDigiLine(self):
    #    self.toolDigiLine = MapToolDigiLine(self, self.__iface)

    ## \brief Create action to digitalize polygons
    #def createMapToolDigiPolygon(self):
    #    self.toolDigiPolygon = MapToolDigiPolygon(self, self.__iface)


    ## \brief Set extent of the map by extent of the source layer
    #
    def setExtentByImageLayer(self):

        self.setExtent(self.imageLayer.extent())
        self.refresh()


    def removeFeatureByUuid(self, uuid):
        featuresPoly = self.digiPolygonLayer.getFeatures()

        for feature in featuresPoly:
            if feature['uuid'] == uuid:
                self.digiPolygonLayer.startEditing()
                self.digiPolygonLayer.deleteFeature(feature.id())
                self.digiPolygonLayer.commitChanges()

        featuresLine = self.digiLineLayer.getFeatures()

        for feature in featuresLine:
            if feature['uuid'] == uuid:
                self.digiLineLayer.startEditing()
                self.digiLineLayer.deleteFeature(feature.id())
                self.digiLineLayer.commitChanges()

        featuresPoint = self.digiPointLayer.getFeatures()

        for feature in featuresPoint:
            if feature['uuid'] == uuid:
                self.digiPointLayer.startEditing()
                self.digiPointLayer.deleteFeature(feature.id())
                self.digiPointLayer.commitChanges()

                #layer.dataProvider().deleteFeatures([5, 10])
    ## \brief Update canvas map element
    #
    # - Clear canvas element
    # - Validation of the source layer
    # - Show subset of the source layer - col obj_type = TransformationDialog.colNameGcpSource
    # - Marker symbol
    # - Label lyer with Id of the feature
    # - Additional display other input layers
    #
    # \param imageLayerPath

    def update(self, refData):

        #canvas leeren

        imageLayerPath = refData['profilePath']

        self.clearCache()
        self.refresh()

        self.imageLayer = QgsRasterLayer(imageLayerPath, "Profile image")
        if not self.imageLayer.isValid():
            print("Layer failed to load!")

        sourceCrs = self.imageLayer.crs()

        #Sets canvas CRS
        self.setDestinationCrs(sourceCrs)

        # set extent to the extent of Layer E_Point
        self.setExtentByImageLayer()
        listLayers = []

        self.createDigiPointLayer(refData)
        self.createDigiLineLayer(refData)
        self.createDigiPolygonLayer(refData)

        listLayers.append(self.digiPointLayer)
        listLayers.append(self.digiLineLayer)
        listLayers.append(self.digiPolygonLayer)

        listLayers.append(self.imageLayer)

        self.setLayers(listLayers)

        self.pup.publish('setDigiPointLayer', self.digiPointLayer)
        self.pup.publish('setDigiLineLayer', self.digiLineLayer)
        self.pup.publish('setDigiPolygonLayer', self.digiPolygonLayer)


        #self.toolDigiPoint.setDigiPointLayer(self.digiPointLayer)
        #self.toolDigiLine.setDigiLineLayer(self.digiLineLayer)
        #self.toolDigiPolygon.setDigiPolygonLayer(self.digiPolygonLayer)
