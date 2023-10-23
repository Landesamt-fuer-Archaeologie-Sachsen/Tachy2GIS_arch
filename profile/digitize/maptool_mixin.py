import math
import uuid
from qgis.PyQt.QtCore import QPoint

from qgis.gui import QgsVertexMarker
from qgis.core import QgsProject, QgsExpression, QgsExpressionContextUtils, QgsRectangle, QgsFeatureRequest, QgsVectorLayer, QgsPointXY

class MapToolMixin:
    
    def transformCoordinates(self, canvas, screenPt):
        return canvas.getCoordinateTransform().toMapCoordinates(screenPt.x(), screenPt.y())

        
    def calcTolerance(self, canvas, pos):
        pt1 = QPoint(pos.x(), pos.y())
        pt2 = QPoint(pos.x() + 15, pos.y())

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

        vertexCoord,vertex,prevVertex,nextVertex,distSquared = feature.geometry().closestVertex(pointXY)
        
        distance = math.sqrt(distSquared)
        if distance > tolerance:
            return None
        else:
            return vertex

    #will return the coordinate of the clicked-on vertex
    def snapToNearestVertex(self, canvas, pos, excludeFeature=None):

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


    def getCustomProjectVariable(self, variableName):
        project = QgsProject.instance()
        if str(QgsExpressionContextUtils.projectScope(project).variable(variableName)) == 'NULL':
            return str('')
        else:
            return QgsExpressionContextUtils.projectScope(project).variable(variableName)


    def setPlaceholders(self, feature, prof_nr):

        #uuid to identify feature
        feature_uuid = uuid.uuid4()
        feature['obj_uuid'] = str(feature_uuid)

        #Type of digitize
        feature['geo_quelle'] = 'profile_object'
        ## set current date
        e = QgsExpression( " $now " )
        feature['messdatum'] = e.evaluate()

        #aktCode
        try:
            aktcode = self.getCustomProjectVariable('aktcode')
            feature['aktcode'] = aktcode
        except:
            pass

        #obj_type
        feature['obj_typ'] = 'Befund'

        #prf_nr
        feature['prof_nr'] = prof_nr
        