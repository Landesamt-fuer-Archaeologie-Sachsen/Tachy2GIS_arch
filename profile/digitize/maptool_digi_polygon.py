from PyQt5.QtCore import Qt
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker, QgsAttributeDialog, QgsAttributeEditorContext
from qgis.core import QgsWkbTypes, QgsFeature, QgsGeometry, QgsFeatureRequest

from ..publisher import Publisher
from .maptool_mixin import MapToolMixin

class MapToolDigiPolygon(QgsMapTool, MapToolMixin):
    def __init__(self, canvas, iFace, rotationCoords, dataStoreDigitize):
        
        self.__iface = iFace
        self.pup = Publisher()
        self.rotationCoords = rotationCoords
        self.dataStoreDigitize = dataStoreDigitize
        self.canvas = canvas
        self.digiPolygonLayer = None
        self.featGeometry = None
        self.feat = None
        self.dialogAttributes = None
        QgsMapTool.__init__(self, self.canvas)
        self.rubberband = None
        self.vertexMarker = None
        self.createRubberband()
        self.point = None
        self.points = []
        self.refData = None
        self.snapping = False

    def createRubberband(self):
        self.rubberband = QgsRubberBand(self.canvas, True)
        self.rubberband.setStrokeColor(Qt.red)
        self.rubberband.setWidth(3)
        self.rubberband.show()

    def canvasPressEvent(self, event):

        if event.button() == Qt.RightButton:

            self.featGeometry = self.rubberband.asGeometry()

            if self.featGeometry:
                if len(self.points) > 2:
                    self.showdialog()

        else:

            self.active = True

            if self.snapping is True:
                pointXY, position = self.snapToNearestVertex(self.canvas, event.pos())
                self.point = pointXY
            else:
                self.point = self.toMapCoordinates(event.pos())

            self.canvas.scene().removeItem(self.vertexMarker)
            self.vertexMarker = self.createVertexMarker(self.canvas, self.point, Qt.red, 5, QgsVertexMarker.ICON_BOX, 3)

            self.points.append(self.point)
            self.isEmittingPoint = True
            self.showPoly()

    def showPoly(self):

        self.rubberband.setToGeometry(QgsGeometry.fromPolygonXY([self.points]), None)

    def showdialog(self):

        self.createFeature()

        self.feat.setFields(self.digiPolygonLayer.fields())

        self.digiPolygonLayer.startEditing()
        self.refData['polygonLayer'].startEditing()

        prof_nr = self.dataStoreDigitize.getProfileNumber()
        self.setPlaceholders(self.feat, prof_nr)

        self.dialogAttributes = QgsAttributeDialog(self.refData['polygonLayer'], self.feat, False, None)
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)
        self.dialogAttributes.show()

        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)

        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)

    def closeAttributeDialog(self):
        print('closeAttributeDialog')
        self.clearRubberband()
        self.refData['polygonLayer'].commitChanges()


    def writeToTable(self, fields, feature):

        dataObj = {}

        for item in fields:

            if item.name() == 'uuid' or item.name() == 'id' or item.name() == 'obj_type' or item.name() == 'obj_art' or item.name() == 'zeit' or item.name() == 'material' or item.name() == 'bemerkung' or item.name() == 'bef_nr' or item.name() == 'fund_nr' or item.name() == 'prob_nr':
                dataObj[item.name()] = feature[item.name()]

        dataObj['layer'] = self.refData['polygonLayer'].sourceName()

        self.pup.publish('polygonFeatureAttr', dataObj)

    def acceptedAttributeDialog(self):

        print('acceptedAttributeDialog')
        self.refData['polygonLayer'].commitChanges()

        atrObj = self.dialogAttributes.feature().attributes()
        self.feat.setAttributes(atrObj)

        self.feat['geo_quelle'] = 'profile_object'

        self.addFeature2Layer()
        self.clearRubberband()

        dialogFeature = self.dialogAttributes.feature()

        #write to table
        self.writeToTable(self.feat.fields(), dialogFeature)
        
        self.digiPolygonLayer.updateExtents()
        self.canvas.refresh()
        

    def clearRubberband(self):
        self.rubberband.reset(QgsWkbTypes.PolygonGeometry)
        self.points = []
        self.canvas.scene().removeItem(self.vertexMarker)

    def createFeature(self):

        self.feat = QgsFeature()
        self.feat.setGeometry(self.featGeometry)

    def addFeature2Layer(self):

        pr = self.digiPolygonLayer.dataProvider()
        pr.addFeatures([self.feat])
        self.digiPolygonLayer.updateExtents()

        self.digiPolygonLayer.endEditCommand()

    def getFeaturesFromEingabelayer(self, bufferGeometry, geoType):

        self.digiPolygonLayer.startEditing()
        pr = self.digiPolygonLayer.dataProvider()

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = self.refData['polygonLayer'].getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:

            if feature.geometry().within(bufferGeometry):

                if geoType == 'tachy':
                    if feature['geo_quelle'] != 'profile_object':

                        rotFeature = QgsFeature(self.digiPolygonLayer.fields())

                        rotateGeom = self.rotationCoords.rotatePolygonFeatureFromOrg(feature)

                        rotFeature.setGeometry(rotateGeom)

                        rotFeature.setAttributes(feature.attributes())

                        selFeatures.append(rotFeature)

                if geoType == 'profile':
                    if feature['geo_quelle'] == 'profile_object':
                        print('getFeaturesFromEingabelayer')
                        rotFeature = QgsFeature(self.digiPolygonLayer.fields())

                        rotateGeom = self.rotationCoords.rotatePolygonFeatureFromOrg(feature)
                        rotFeature.setGeometry(rotateGeom)

                        rotFeature.setAttributes(feature.attributes())

                        selFeatures.append(rotFeature)

                        #write to table
                        self.writeToTable(feature.fields(), feature)


        pr.addFeatures(selFeatures)

        self.digiPolygonLayer.commitChanges()
        self.digiPolygonLayer.updateExtents()
        self.digiPolygonLayer.endEditCommand()

    def removeNoneProfileFeatures(self):

        self.digiPolygonLayer.startEditing()
        pr = self.digiPolygonLayer.dataProvider()
        features = self.digiPolygonLayer.getFeatures()

        removeFeatures = []
        for feature in features:

            if feature['geo_quelle'] != 'profile_object':

                removeFeatures.append(feature.id())

        pr.deleteFeatures(removeFeatures)

        self.digiPolygonLayer.commitChanges()
        self.digiPolygonLayer.updateExtents()
        self.digiPolygonLayer.endEditCommand()

    #in den Eingabelayer schreiben
    def reverseRotation2Eingabelayer(self, layer_id):
 
        self.refData['polygonLayer'].startEditing()

        pr = self.refData['polygonLayer'].dataProvider()

        features = self.digiPolygonLayer.getFeatures()

        #iterrieren über zu schreibende features
        for feature in features:
            #Zielgeometrie erzeugen
            emptyTargetGeometry = self.rubberband.asGeometry()

            #Zielfeature erzeugen
            rotFeature = QgsFeature(self.refData['polygonLayer'].fields())

            #Geometrie in Kartenebene umrechnen
            rotateGeom = self.rotationCoords.rotatePolygonFeature(feature, emptyTargetGeometry)
            rotFeature.setGeometry(rotateGeom)
            rotFeature.setAttributes(feature.attributes())

            checker = True
            #Features aus Eingabelayer
            #schauen ob es schon existiert (anhand uuid), wenn ja dann löschen und durch Zielfeature ersetzen
            sourceLayerFeatures = self.refData['polygonLayer'].getFeatures()
            for sourceFeature in sourceLayerFeatures:
                if feature["uuid"] == sourceFeature["uuid"]:
                    pr.deleteFeatures([sourceFeature.id()])
                    pr.addFeatures([rotFeature])

                    checker = False

            #wenn feature nicht vorhanden, neues feature im Layer anlegen
            if checker == True:
                retObj = pr.addFeatures([rotFeature])

        self.refData['polygonLayer'].removeSelection()
        self.refData['polygonLayer'].commitChanges()
        self.refData['polygonLayer'].updateExtents()
        self.refData['polygonLayer'].endEditCommand()

    def removeFeatureInEingabelayerByUuid(self, uuid):
        features = self.refData['polygonLayer'].getFeatures()

        for feature in features:
            if feature['uuid'] == uuid:
                if feature['geo_quelle'] == 'profile_object':
                    self.refData['polygonLayer'].startEditing()
                    self.refData['polygonLayer'].deleteFeature(feature.id())
                    self.refData['polygonLayer'].commitChanges()

    def setDigiPolygonLayer(self, digiPolygonLayer):
        self.digiPolygonLayer = digiPolygonLayer

    def update(self, refData):
        self.refData = refData

    def setSnapping(self, enableSnapping):
        if enableSnapping is True:
            self.snapping = True
        else:
            self.snapping = False