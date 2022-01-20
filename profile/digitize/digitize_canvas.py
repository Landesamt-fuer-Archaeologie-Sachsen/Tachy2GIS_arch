# -*- coding: utf-8 -*-
import os
import processing
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsMarkerSymbol, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer, QgsSimpleLineSymbolLayer, QgsLineSymbol, QgsFillSymbol, QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsPoint, QgsCoordinateReferenceSystem
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

        self.createConnects()

    def createDigiPointLayer(self, refData):
        refData['pointLayer'].selectAll()
        self.digiPointLayer = processing.run("native:saveselectedfeatures", {'INPUT': refData['pointLayer'], 'OUTPUT': 'memory:'})['OUTPUT']
        refData['pointLayer'].removeSelection()

        #Layer leeren
        pr = self.digiPointLayer.dataProvider()
        pr.truncate()

        #Renderer
        symbol_profile = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'green', 'size': '2'})
        symbol_tachy = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'grey', 'size': '2'})

        #self.digiPointLayer.setRenderer(QgsSingleSymbolRenderer(symbol))

        categorized_renderer = QgsCategorizedSymbolRenderer()

        categorized_renderer.setClassAttribute('geo_quelle')

        field = self.digiPointLayer.fields().lookupField('geo_quelle')
        unique_values = self.digiPointLayer.uniqueValues(field)
        # Add a few categories
        cat1 = QgsRendererCategory('profile_object', symbol_profile, 'profile')
        cat2 = QgsRendererCategory(None, symbol_tachy, 'tachy')
        categorized_renderer.addCategory(cat1)
        categorized_renderer.addCategory(cat2)

        self.digiPointLayer.setRenderer(categorized_renderer)

        #Projection
        crs = refData['pointLayer'].sourceCrs()
        self.digiPointLayer.setCrs(crs)

        #Label Layer
        palSettings  = QgsPalLayerSettings()
        textFormat = QgsTextFormat()
        textFormat.setFont(QFont("Arial", 10))
        textFormat.setSize(10)
        palSettings.setFormat(textFormat)

        palSettings.fieldName = "id"
        palSettings.placement = 4
        palSettings.enabled = True

        labelSettings = QgsVectorLayerSimpleLabeling(palSettings)
        self.digiPointLayer.setLabelsEnabled(True)
        self.digiPointLayer.setLabeling(labelSettings)

    def createDigiLineLayer(self, refData):

        refData['lineLayer'].selectAll()
        self.digiLineLayer = processing.run("native:saveselectedfeatures", {'INPUT': refData['lineLayer'], 'OUTPUT': 'memory:'})['OUTPUT']
        refData['lineLayer'].removeSelection()

        #Layer leeren
        pr = self.digiLineLayer.dataProvider()
        pr.truncate()

        #Renderer
        symbol_profile = QgsLineSymbol.createSimple({'line_style': 'solid', 'color': 'green', 'width': '1'})
        symbol_tachy = QgsLineSymbol.createSimple({'line_style': 'solid', 'color': 'grey', 'width': '1'})

        symbol_tachy_vertex = QgsMarkerLineSymbolLayer()
        symbol_tachy_vertex.setSubSymbol(QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'grey'}))
        symbol_tachy_vertex.setPlacement(1)

        symbol_profile_vertex = QgsMarkerLineSymbolLayer()
        symbol_profile_vertex.setSubSymbol(QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'red'}))
        symbol_profile_vertex.setPlacement(1)

        symbol_profile.appendSymbolLayer(symbol_profile_vertex)
        symbol_tachy.appendSymbolLayer(symbol_tachy_vertex)

        # Add a few categories
        categorized_renderer = QgsCategorizedSymbolRenderer()
        categorized_renderer.setClassAttribute('geo_quelle')
        cat1 = QgsRendererCategory('profile_object', symbol_profile, 'profile')
        cat2 = QgsRendererCategory(None, symbol_tachy, 'tachy')
        categorized_renderer.addCategory(cat1)
        categorized_renderer.addCategory(cat2)

        self.digiLineLayer.renderer().setUsingSymbolLevels(True)
        self.digiLineLayer.setRenderer(categorized_renderer)

        crs = refData['lineLayer'].sourceCrs()

        self.digiLineLayer.setCrs(crs)

        #Label Layer
        palSettings  = QgsPalLayerSettings()
        textFormat = QgsTextFormat()

        textFormat.setFont(QFont("Arial", 10))
        textFormat.setSize(10)
        palSettings.setFormat(textFormat)

        palSettings.fieldName = "id"
        palSettings.placement = 4
        palSettings.enabled = True

        labelSettings = QgsVectorLayerSimpleLabeling(palSettings)
        self.digiLineLayer.setLabelsEnabled(True)
        self.digiLineLayer.setLabeling(labelSettings)


    def createDigiPolygonLayer(self, refData):

        refData['polygonLayer'].selectAll()
        self.digiPolygonLayer = processing.run("native:saveselectedfeatures", {'INPUT': refData['polygonLayer'], 'OUTPUT': 'memory:'})['OUTPUT']
        refData['polygonLayer'].removeSelection()

        #Layer leeren
        pr = self.digiPolygonLayer.dataProvider()
        pr.truncate()

        #Renderer
        symbol_profile = QgsFillSymbol.createSimple({'style':'no', 'outline_style': 'solid', 'outline_color': 'green', 'outline_width': '1'})
        symbol_tachy = QgsFillSymbol.createSimple({'style':'no', 'outline_style': 'solid', 'outline_color': 'grey', 'outline_width': '1'})

        symbol_tachy_vertex = QgsMarkerLineSymbolLayer()
        symbol_tachy_vertex.setSubSymbol(QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'grey'}))
        symbol_tachy_vertex.setPlacement(1)

        symbol_profile_vertex = QgsMarkerLineSymbolLayer()
        symbol_profile_vertex.setSubSymbol(QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'red'}))
        symbol_profile_vertex.setPlacement(1)

        symbol_profile.appendSymbolLayer(symbol_profile_vertex)
        symbol_tachy.appendSymbolLayer(symbol_tachy_vertex)

        # Add a few categories
        categorized_renderer = QgsCategorizedSymbolRenderer()
        categorized_renderer.setClassAttribute('geo_quelle')
        cat1 = QgsRendererCategory('profile_object', symbol_profile, 'profile')
        cat2 = QgsRendererCategory(None, symbol_tachy, 'tachy')
        categorized_renderer.addCategory(cat1)
        categorized_renderer.addCategory(cat2)

        self.digiPolygonLayer.renderer().setUsingSymbolLevels(True)
        self.digiPolygonLayer.setRenderer(categorized_renderer)

        crs = refData['polygonLayer'].sourceCrs()

        self.digiPolygonLayer.setCrs(crs)

        #Label Layer
        palSettings  = QgsPalLayerSettings()
        textFormat = QgsTextFormat()

        textFormat.setFont(QFont("Arial", 10))
        textFormat.setSize(10)
        palSettings.setFormat(textFormat)

        palSettings.fieldName = "id"
        palSettings.placement = 4
        palSettings.enabled = True

        labelSettings = QgsVectorLayerSimpleLabeling(palSettings)
        self.digiPolygonLayer.setLabelsEnabled(True)
        self.digiPolygonLayer.setLabeling(labelSettings)

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
