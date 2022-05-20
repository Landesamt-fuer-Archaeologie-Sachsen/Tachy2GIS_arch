import math
from PyQt5.QtCore import QPoint

from qgis.gui import QgsVertexMarker
from qgis.core import QgsRectangle, QgsFeatureRequest, QgsVectorLayer, QgsPointXY

class MapToolMixin:
    
    def transformCoordinates(self, canvas, screenPt):
        return canvas.getCoordinateTransform().toMapCoordinates(screenPt.x(), screenPt.y())

        
    def calcTolerance(self, canvas, pos):
        print('pos', pos)
        pt1 = QPoint(pos.x(), pos.y())
        pt2 = QPoint(pos.x() + 20, pos.y())

        pointXY1 = self.transformCoordinates(canvas, pt1)
        pointXY2 = self.transformCoordinates(canvas, pt2)
        tolerance = pointXY2.x() - pointXY1.x()
        
        return tolerance

    def createVertexMarker(self, canvas, point, color, iconSize, iconType, penWidth):
        vertexMarker = QgsVertexMarker(canvas)
        vertexMarker.setCenter(point)
        vertexMarker.setColor(color)
        vertexMarker.setIconSize(iconSize)
        vertexMarker.setIconType(iconType)
        vertexMarker.setPenWidth(penWidth)

        return vertexMarker


    #finds a feature close to the click location

    def getFeatureAtPosition(self, canvas, pos, excludeFeature=None):
        pointXY = self.transformCoordinates(canvas, pos)
        tolerance = self.calcTolerance(canvas, pos)
        searchRect = QgsRectangle(pointXY.x() - tolerance, pointXY.y() - tolerance,pointXY.x() + tolerance,pointXY.y() + tolerance)
        
        request = QgsFeatureRequest()
        request.setFilterRect(searchRect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)

        for layer in canvas.layers():

            if isinstance(layer, QgsVectorLayer):
                for feature in layer.getFeatures(request):
                    if excludeFeature != None:
                        if feature.id() == excludeFeature.id():
                            continue
                    
                    return feature
                
        return None

    #identifies the vertex close to the given click location (if any)

    def findVertexAt(self, canvas, feature, pos):
        pointXY = self.transformCoordinates(canvas, pos)
        tolerance = self.calcTolerance(canvas, pos)

        print('tolerance', tolerance)

        vertexCoord,vertex,prevVertex,nextVertex,distSquared = feature.geometry().closestVertex(pointXY)
        
        distance = math.sqrt(distSquared)
        if distance > tolerance:
            return None
        else:
            return vertex

    #will return the coordinate of the clicked-on vertex
    def snapToNearestVertex(self, canvas, pos, excludeFeature=None):
        print('snapToNearestVertex')
        
        pointXY = self.transformCoordinates(canvas, pos)

        feature = self.getFeatureAtPosition(canvas, pos, excludeFeature)
        
        if feature == None: 
            return pointXY, QPoint(pointXY.x(),pointXY.y())
        
        vertex = self.findVertexAt(canvas, feature, pos)
        
        if vertex == None: 
            return pointXY, QPoint(pointXY.x(),pointXY.y())
            
        snapPoint = feature.geometry().vertexAt(vertex)
        snapPointXY = QgsPointXY(snapPoint.x(), snapPoint.y())
        
        return snapPointXY, snapPoint
        