# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon, QFont, QColor
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling, QgsPointXY
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom, QgsHighlight, QgsVertexMarker

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

    def __init__(self, dialogInstance):

        super(DigitizeCanvas, self).__init__()

        self.pup = Publisher()

        self.iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')

        self.dialogInstance = dialogInstance

        self.imageLayer = None

        self.createMapToolPan()
        self.createMapToolZoomIn()
        self.createMapToolZoomOut()

        self.createConnects()


    ## \brief Set coordinates on the statusbar in dialog instance TransformationDialog.setCoordinatesOnStatusBar() . Depends on mouse move on the map element
    #
    def canvasMoveEvent(self, event):
        x = event.x()
        y = event.y()
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

    def updateCanvas(self, imageLayerPath):

        #canvas leeren

        self.clearCache()
        self.refresh()

        self.imageLayer = QgsRasterLayer(imageLayerPath, "Profile image")
        if not self.imageLayer.isValid():
            print("Layer failed to load!")


        sourceCrs = self.imageLayer.crs()

        #Sets canvas CRS
        #my_crs = QgsCoordinateReferenceSystem(31469, QgsCoordinateReferenceSystem.EpsgCrsId)
        self.setDestinationCrs(sourceCrs)

        # set extent to the extent of Layer E_Point
        self.setExtentByImageLayer()
        listLayers = []
        listLayers.append(self.imageLayer)

        self.setLayers(listLayers)
