# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtCore import Qt, QSizeF, QPointF
from qgis.PyQt.QtGui import QColor, QTextDocument
from qgis.core import (
    QgsRasterLayer,
    QgsFillSymbol,
    QgsPointXY,
    QgsTextAnnotation,
)
from qgis.gui import (
    QgsMapCanvas,
    QgsMapToolPan,
    QgsMapToolZoom,
    QgsVertexMarker,
    QgsMapCanvasAnnotationItem,
)

from ..publisher import Publisher
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
        super().__init__()

        self.pup = Publisher()

        self.iconpath = os.path.join(os.path.dirname(__file__), "Icons")

        self.dialogInstance = dialogInstance

        self.imageLayer = None

        self.activePoint = None

        self.aarPoints = []

        self.markerPoints = []

        self.setCanvasColor(Qt.white)

        self.createMapToolPan()
        self.createMapToolZoomIn()
        self.createMapToolZoomOut()
        self.createMapToolMoveMarker()
        self.createConnects()

    def __delete_marker(self, obj_uuid):
        for mark in self.markerPoints:
            if obj_uuid == mark["obj_uuid"]:
                self.scene().removeItem(mark["marker"])
                self.scene().removeItem(mark["annotation"])
        self.refresh()

    def __createMarker(self, pointData):
        pnt = QgsPointXY(pointData[0], pointData[1])

        ptnr = ""
        if len(self.activePoint["ptnr"]) > 0 and self.activePoint["ptnr"] != "NULL":
            ptnr = str(self.activePoint["ptnr"])

        # Annotation
        txt = QTextDocument()
        txt.setHtml('<span style="font-family: Arial; font-size: 13px"><b>' + ptnr + "</b></span>")
        lbl = QgsTextAnnotation(self)
        lbl.setDocument(txt)
        lbl.setMapPosition(pnt)
        lbl.setFrameSize(QSizeF(txt.size().width(), txt.size().height()))
        lbl.setFrameOffsetFromReferencePoint(QPointF(2, -20))
        sym1 = QgsFillSymbol.createSimple({"color": "0,0,0,0", "outline_color": "0,0,0,0"})
        lbl.setFillSymbol(sym1)

        ann = QgsMapCanvasAnnotationItem(lbl, self)

        # Marker
        mark = QgsVertexMarker(self)
        mark.setCenter(pnt)
        # mark.setColor(QColor(0, 255, 0))
        mark.setIconSize(5)
        mark.setIconType(QgsVertexMarker.ICON_CIRCLE)
        mark.setPenWidth(3)

        return mark, ann

    def updateAarPoints(self, aarPoints):
        self.aarPoints = aarPoints

        self.updateMarkerPoints()

    def updateMarkerPoints(self):
        for point in self.aarPoints:
            for mark in self.markerPoints:
                if point["obj_uuid"] == mark["obj_uuid"]:
                    if point["usage"] == 1:
                        mark["marker"].setColor(QColor(0, 255, 0))
                    if point["usage"] == 0:
                        mark["marker"].setColor(QColor(100, 100, 100))

            self.refresh()

    def press_point(self, pointData):
        if self.activePoint:
            self.__delete_marker(self.activePoint["obj_uuid"])

            mark, ann = self.__createMarker(pointData)

            self.markerPoints.append({"obj_uuid": self.activePoint["obj_uuid"], "marker": mark, "annotation": ann})

            self.updateMarkerPoints()

    def release_point(self, pointData):
        if self.activePoint:
            self.__delete_marker(self.activePoint["obj_uuid"])

            mark, ann = self.__createMarker(pointData)

            self.markerPoints.append({"obj_uuid": self.activePoint["obj_uuid"], "marker": mark, "annotation": ann})

            self.updateMarkerPoints()

            self.pup.publish(
                "imagePointCoordinates",
                {
                    "obj_uuid": self.activePoint["obj_uuid"],
                    "x": pointData[0],
                    "z": abs(pointData[1]),
                },
            )

    def move_point(self, pointData):
        if self.activePoint:
            self.__delete_marker(self.activePoint["obj_uuid"])

            mark, ann = self.__createMarker(pointData)

            self.markerPoints.append({"obj_uuid": self.activePoint["obj_uuid"], "marker": mark, "annotation": ann})

            self.updateMarkerPoints()

    def setActivePoint(self, linkObj):
        self.activePoint = linkObj

    ## \brief Event connections
    #
    def createConnects(self):
        # Koordinatenanzeige
        self.xyCoordinates.connect(self.canvasMoveEvent)

    """
    ## \brief Create action to click on the map
    #
    def createMapToolClick(self):
        self.toolClick = QgsMapToolEmitPoint(self)

        self.click()"""

    ## \brief Create action to drag a marker on the map
    #
    def createMapToolMoveMarker(self):
        # self.toolMove = QgsMapToolEmitPoint(self)

        self.toolMove = MapToolMove(self)

        self.set_map_tool_move_vertex()

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
        self.toolZoomOut = QgsMapToolZoom(self, True)  # true = out

    """
    ## \brief Set map tool click
    #
    def click(self):
        self.setMapTool(self.toolClick)
        self.toolClick.canvasClicked.connect( self.display_point )"""

    ## \brief Set map tool move Vertex
    #
    def set_map_tool_move_vertex(self):
        self.setMapTool(self.toolMove)
        self.toolMove.pressSignal.connect(self.press_point)
        self.toolMove.releaseSignal.connect(self.release_point)
        self.toolMove.moveSignal.connect(self.move_point)

    ## \brief Set coordinates on the statusbar in dialog instance TransformationDialog.setCoordinatesOnStatusBar() .
    # Depends on mouse move on the map element
    #
    def canvasMoveEvent(self, event):
        x = event.x()
        y = event.y()
        self.pup.publish("moveCoordinate", {"x": x, "y": y})

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
        # canvas leeren

        self.clearCache()
        self.refresh()
        checker = False

        self.imageLayer = QgsRasterLayer(imageLayerPath, "Profile image")
        if not self.imageLayer.isValid():
            print("Layer failed to load!")
            checker = False
        else:
            checker = True
            print("Layer is loaded!")

            sourceCrs = self.imageLayer.crs()

            # Sets canvas CRS
            # my_crs = QgsCoordinateReferenceSystem(31469, QgsCoordinateReferenceSystem.EpsgCrsId)
            self.setDestinationCrs(sourceCrs)

            # set extent to the extent of Layer E_Point
            self.setExtentByImageLayer()
            listLayers = [self.imageLayer]

            self.setLayers(listLayers)

        return checker
