import uuid
import math
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QPushButton, QDialogButtonBox, QVBoxLayout
from qgis.gui import QgsMapToolIdentify, QgsMapToolIdentifyFeature, QgsRubberBand, QgsVertexMarker, QgsAttributeDialog, QgsAttributeEditorContext
from qgis.core import QgsExpression, QgsWkbTypes, QgsPointXY, QgsFeature, QgsGeometry, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsVectorLayerUtils, QgsFeatureRequest

from ..publisher import Publisher

class MapToolEditLine(QgsMapToolIdentifyFeature):
    def __init__(self, canvas, iFace, rotationCoords):
        self.__iface = iFace

        self.pup = Publisher()

        #self.setCursor(Qt.CrossCursor)
        self.digiLineLayer = None
        #self.onGeometryChanged = onGeometryChanged
        self.dragging = False
        self.feature = None
        self.vertex = None

        self.rotationCoords = rotationCoords

        self.canvas = canvas

        QgsMapToolIdentifyFeature.__init__(self, self.canvas)

    def canvasPressEvent(self, event):

        found_features = self.identify(event.x(), event.y(), [self.digiLineLayer], QgsMapToolIdentify.TopDownAll)
        identified_features = [f.mFeature for f in found_features]

        click_point = self.canvas.getCoordinateTransform().toMapCoordinates(event.x(), event.y())
        print('click_point', click_point)

        for feature in identified_features:

            feat_geom = feature.geometry()

            vertexCoord,vertex,prevVertex,nextVertex,distSquared = feat_geom.closestVertex(click_point)
            distance = math.sqrt(distSquared)

            print('event', event)
            print('feat_geom', feat_geom)
            print('vertexCoord', vertexCoord)
            print('vertex', vertex)
            print('prevVertex', prevVertex)
            print('nextVertex', nextVertex)
            print('distSquared', distSquared)
            print('distance', distance)

            tolerance = self.calcTolerance(event.pos())
            print('tolerance', tolerance)

            if distance > tolerance:
                return

            if event.button() == Qt.LeftButton:
                # Left click -> move vertex.
                self.dragging = True
                self.feature = feature
                self.vertex = vertex
                self.moveVertexTo(event.pos())
                self.canvas().refresh()
            elif event.button() == Qt.RightButton:
                # Right click -> delete vertex.
                self.deleteVertex(feature, vertex)
                self.canvas().refresh()

    def canvasMoveEvent(self, event):
        if self.dragging:
            self.moveVertexTo(event.pos())
            self.canvas().refresh()

    def canvasReleaseEvent(self, event):
        if self.dragging:
            self.moveVertexTo(event.pos())
            self.layer.updateExtents()
            self.canvas().refresh()
            self.dragging = False
            self.feature = None
            self.vertex = None

    """
    def canvasDoubleClickEvent(self, event):

        feature = self.findFeatureAt(event.pos())
        if feature == None:
            return
        mapPt,layerPt = self.transformCoordinates(event.pos())
        geometry = feature.geometry()
        distSquared,closestPt,beforeVertex = \
        geometry.closestSegmentWithContext(layerPt)
        distance = math.sqrt(distSquared)
        tolerance = self.calcTolerance(event.pos())
        if distance > tolerance:
            return
    """
    def calcTolerance(self, pos):
        layerPt1 = self.canvas.getCoordinateTransform().toMapCoordinates(pos.x(), pos.y())
        layerPt2 = self.canvas.getCoordinateTransform().toMapCoordinates(pos.x() + 10, pos.y())
        tolerance = layerPt2.x() - layerPt1.x()
        return tolerance

    """
    def findFeatureAt(self, pos):
        mapPt,layerPt = self.transformCoordinates(pos)
        tolerance = self.calcTolerance(pos)
        searchRect = QgsRectangle(layerPt.x() - tolerance,
        layerPt.y() - tolerance,
        layerPt.x() + tolerance,
        layerPt.y() + tolerance)
        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)

        for feature in self.layer.getFeatures(request):
            return feature
        return None
    """

    def setDigiLineLayer(self, digiLineLayer):
        self.digiLineLayer = digiLineLayer
