# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon, QFont, QColor
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling, QgsPointXY
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom, QgsHighlight, QgsVertexMarker

from .publisher import Publisher
from .maptool_move import MapToolMove

## @brief With the ProfileImageCanvas class a map canvas element is realized. It should be used in the profile dialog
#
# Inherits from QgsMapCanvas
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-05-26

class ProfileImageCanvas(QgsMapCanvas):

    ## The constructor.
    # @param dialogInstance pointer to the dialogInstance

    def __init__(self, dialogInstance):

        super(ProfileImageCanvas, self).__init__()

        self.pup = Publisher()

        self.iconpath = os.path.join(os.path.dirname(__file__), 'Icons')

        self.dialogInstance = dialogInstance

        self.imageLayer = None

        self.activePoint = None

        self.markerPoints = []

        self.setCanvasColor(Qt.white)

        self.createMapToolPan()
        self.createMapToolZoomIn()
        self.createMapToolZoomOut()
        #self.createMapToolClick()
        self.createMapToolMoveMarker()

        self.createConnects()


    def __delete_marker(self, uuid):

        for mark in self.markerPoints:
            if uuid == mark["uuid"]:
                self.scene().removeItem(mark["marker"])
        self.refresh()

    def display_point(self, pointData ):

        if self.activePoint:
            self.__delete_marker(self.activePoint)

            m = QgsVertexMarker(self)
            m.setCenter(QgsPointXY(pointData[0], pointData[1]))

            m.setColor(QColor(0, 255, 0))
            m.setIconSize(5)
            m.setIconType(QgsVertexMarker.ICON_CIRCLE) # or ICON_CROSS, ICON_X
            m.setPenWidth(3)

            self.markerPoints.append({"uuid": self.activePoint, "marker": m})

            self.pup.publish('imagePointCoordinates', {'uuid': self.activePoint, 'x': pointData[0], 'z': abs(pointData[1])})


    def press_point(self, pointData ):

        print('press_point', pointData)

        if self.activePoint:
            self.__delete_marker(self.activePoint)

            m = QgsVertexMarker(self)
            m.setCenter(QgsPointXY(pointData[0], pointData[1]))

            m.setColor(QColor(0, 255, 0))
            m.setIconSize(5)
            m.setIconType(QgsVertexMarker.ICON_CIRCLE) # or ICON_CROSS, ICON_X
            m.setPenWidth(3)

            self.markerPoints.append({"uuid": self.activePoint, "marker": m})

            self.pup.publish('imagePointCoordinates', {'uuid': self.activePoint, 'x': pointData[0], 'z': abs(pointData[1])})

    def release_point(self, pointData ):

        print('release_point', pointData)

        if self.activePoint:
            self.__delete_marker(self.activePoint)

            m = QgsVertexMarker(self)
            m.setCenter(QgsPointXY(pointData[0], pointData[1]))

            m.setColor(QColor(0, 255, 0))
            m.setIconSize(5)
            m.setIconType(QgsVertexMarker.ICON_CIRCLE) # or ICON_CROSS, ICON_X
            m.setPenWidth(3)

            self.markerPoints.append({"uuid": self.activePoint, "marker": m})

            self.pup.publish('imagePointCoordinates', {'uuid': self.activePoint, 'x': pointData[0], 'z': abs(pointData[1])})

    def move_point(self, pointData ):

        print('move_point', pointData)

        if self.activePoint:
            self.__delete_marker(self.activePoint)

            m = QgsVertexMarker(self)
            m.setCenter(QgsPointXY(pointData[0], pointData[1]))

            m.setColor(QColor(0, 255, 0))
            m.setIconSize(5)
            m.setIconType(QgsVertexMarker.ICON_CIRCLE) # or ICON_CROSS, ICON_X
            m.setPenWidth(3)

            self.markerPoints.append({"uuid": self.activePoint, "marker": m})

            #self.pup.publish('imagePointCoordinates', {'uuid': self.activePoint, 'x': pointData[0], 'z': pointData[1]})

    def setActivePoint(self, linkObj):
        print('setActivePoint image')
        #print(linkObj['uuid'])
        self.activePoint = linkObj['uuid']

    ## \brief Event connections
    #
    def createConnects(self):

        #Koordinatenanzeige
        self.xyCoordinates.connect(self.canvasMoveEvent)

    '''
    ## \brief Create action to click on the map
    #
    def createMapToolClick(self):
        self.toolClick = QgsMapToolEmitPoint(self)

        self.click()'''

    ## \brief Create action to drag a marker on the map
    #
    def createMapToolMoveMarker(self):
        #self.toolMove = QgsMapToolEmitPoint(self)

        self.toolMove = MapToolMove(self)

        self.move()

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

    '''
    ## \brief Set map tool click
    #
    def click(self):
        self.setMapTool(self.toolClick)
        self.toolClick.canvasClicked.connect( self.display_point )'''

    ## \brief Set map tool move Vertex
    #
    def move(self):
        self.setMapTool(self.toolMove)
        self.toolMove.pressSignal.connect( self.press_point )
        self.toolMove.releaseSignal.connect( self.release_point )
        self.toolMove.moveSignal.connect( self.move_point )

    ## \brief Set coordinates on the statusbar in dialog instance TransformationDialog.setCoordinatesOnStatusBar() . Depends on mouse move on the map element
    #
    def canvasMoveEvent(self, event):
        x = event.x()
        y = event.y()
        #self.dialogInstance.setCoordinatesOnStatusBar(x, y)

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
