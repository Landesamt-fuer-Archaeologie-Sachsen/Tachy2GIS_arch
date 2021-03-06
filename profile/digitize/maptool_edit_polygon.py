import math
from PyQt5.QtCore import Qt
from qgis.gui import QgsMapToolIdentify, QgsMapToolIdentifyFeature, QgsVertexMarker
from qgis.core import QgsWkbTypes

from ..publisher import Publisher
from .maptool_mixin import MapToolMixin

class MapToolEditPolygon(QgsMapToolIdentifyFeature, MapToolMixin):
    def __init__(self, canvas, iFace, rotationCoords):
        self.__iface = iFace

        self.pup = Publisher()

        #self.setCursor(Qt.CrossCursor)
        self.digiPolygonLayer = None
        #self.onGeometryChanged = onGeometryChanged
        self.dragging = False
        self.feature = None
        self.vertex = None
        self.vertexMarker = None

        self.snapping = False

        self.rotationCoords = rotationCoords

        self.canvas = canvas

        QgsMapToolIdentifyFeature.__init__(self, self.canvas)

        self.deactivated.connect(self.deactivateLayer)

    def deactivateLayer(self):
        if self.digiPolygonLayer != None:
            self.digiPolygonLayer.commitChanges()
            self.digiPolygonLayer.updateExtents()
            self.digiPolygonLayer.endEditCommand()

    def canvasPressEvent(self, event):

        found_features = self.identify(event.x(), event.y(), [self.digiPolygonLayer], QgsMapToolIdentify.TopDownAll)
        identified_features = [f.mFeature for f in found_features]
        
        pointXY = self.canvas.getCoordinateTransform().toMapCoordinates(event.x(), event.y())

        self.clearVertexMarker()

        for feature in identified_features:

            if feature['geo_quelle'] == 'profile_object':

                self.digiPolygonLayer.startEditing()

                feat_geom = feature.geometry()

                vertexCoord,vertex,prevVertex,nextVertex,distSquared = feat_geom.closestVertex(pointXY)

                distance = math.sqrt(distSquared)

                tolerance = self.calcTolerance(self.canvas, event.pos())

                if distance > tolerance:
                    return

                if event.button() == Qt.LeftButton:
                    # Left click -> move vertex.
                    self.dragging = True
                    self.feature = feature
                    self.vertex = vertex
                    layerPt = self.moveVertexTo(event.pos())

                    self.clearVertexMarker()
                    self.vertexMarker = self.createVertexMarker(self.canvas, layerPt, Qt.red, 5, QgsVertexMarker.ICON_BOX, 3)

                    self.canvas.refresh()
                elif event.button() == Qt.RightButton:
                    # Right click -> delete vertex.
                    self.deleteVertex(feature, vertex)
                    self.canvas.refresh()

    def clearVertexMarker(self):
        self.canvas.scene().removeItem(self.vertexMarker)

    def findFeatureAt(self, pos):

        found_features = self.identify(pos.x(), pos.y(), [self.digiPolygonLayer], QgsMapToolIdentify.TopDownAll)
        identified_features = [f.mFeature for f in found_features]

        for feature in identified_features:
            return feature
        return None


    def canvasMoveEvent(self, event):
        if self.dragging:

            layerPt = self.moveVertexTo(event.pos())
            self.clearVertexMarker()
            self.vertexMarker = self.createVertexMarker(self.canvas, layerPt, Qt.red, 5, QgsVertexMarker.ICON_BOX, 3)

            self.canvas.refresh()


    def canvasReleaseEvent(self, event):
        if self.dragging:

            if self.snapping is True:
                pointXY, position = self.snapToNearestVertex(self.canvas, event.pos(), self.feature)
                self.moveVertexToSnap(pointXY)
            else:
                pointXY = self.moveVertexTo(event.pos())

            self.digiPolygonLayer.updateExtents()
            self.clearVertexMarker()
            self.vertexMarker = self.createVertexMarker(self.canvas, pointXY, Qt.red, 5, QgsVertexMarker.ICON_BOX, 3)

            self.canvas.refresh()
            self.dragging = False
            self.feature = None
            self.vertex = None


    def moveVertexTo(self, positionBild):
        geometry = self.feature.geometry()
        positionMap = self.canvas.getCoordinateTransform().toMapCoordinates(positionBild.x(), positionBild.y())
        geometry.moveVertex(positionMap.x(), positionMap.y(), self.vertex)
        self.digiPolygonLayer.changeGeometry(self.feature.id(), geometry)

        return positionMap

    def moveVertexToSnap(self, positionMap):
        geometry = self.feature.geometry()
        geometry.moveVertex(positionMap.x(), positionMap.y(), self.vertex)
        self.digiPolygonLayer.changeGeometry(self.feature.id(), geometry)

        return positionMap

    def deleteVertex(self, feature, vertex):
        geometry = feature.geometry()
        if geometry.wkbType() == QgsWkbTypes.LineString:
            lineString = geometry.asPolyline()
            if len(lineString) <= 2:
                return

        elif geometry.wkbType() == QgsWkbTypes.Polygon:
            polygon = geometry.asPolygon()
            exterior = polygon[0]
            if len(exterior) <= 4:
                return

        if geometry.deleteVertex(vertex):
            self.digiPolygonLayer.changeGeometry(feature.id(), geometry)

    def canvasDoubleClickEvent(self, event):

        feature = self.findFeatureAt(event.pos())
        if feature == None:
            return
        #mapPt,layerPt = self.transformCoordinates(event.pos())
        layerPt = self.canvas.getCoordinateTransform().toMapCoordinates(event.x(), event.y())

        geometry = feature.geometry()
        distSquared,closestPt,beforeVertex,leftOrRightOfSegment = geometry.closestSegmentWithContext(layerPt)
        distance = math.sqrt(distSquared)
        tolerance = self.calcTolerance(self.canvas, event.pos())
        if distance > tolerance:
            return

        geometry.insertVertex(closestPt.x(), closestPt.y(), beforeVertex)
        self.digiPolygonLayer.changeGeometry(feature.id(), geometry)
        self.canvas.refresh()

    def setDigiPolygonLayer(self, digiPolygonLayer):
        self.digiPolygonLayer = digiPolygonLayer

    def setSnapping(self, enableSnapping):
        if enableSnapping is True:
            self.snapping = True
        else:
            self.snapping = False