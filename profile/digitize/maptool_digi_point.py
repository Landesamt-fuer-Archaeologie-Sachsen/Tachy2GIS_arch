from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsAttributeDialog, QgsAttributeEditorContext
from qgis.core import QgsPoint, QgsFeature, QgsGeometry, QgsFeatureRequest

from ..publisher import Publisher
from .maptool_mixin import MapToolMixin

class MapToolDigiPoint(QgsMapTool, MapToolMixin):
    def __init__(self, canvas, iFace, rotationCoords, dataStoreDigitize):
        
        self.__iface = iFace
        self.pup = Publisher()
        self.rotationCoords = rotationCoords
        self.dataStoreDigitize = dataStoreDigitize
        self.canvas = canvas
        self.digiPointLayer = None
        self.featGeometry = None
        self.feat = None
        self.dialogAttributes = None
        QgsMapTool.__init__(self, self.canvas)
        self.vertexMarker = None
        self.point = None
        self.refData = None
        self.snapping = False

    def canvasPressEvent(self, event):

        if event.button() == Qt.RightButton:
            if self.vertexMarker:

                self.featGeometry = QgsGeometry.fromPointXY(self.vertexMarker.center())
                self.showdialog()

        else:
            self.active = True

            if self.snapping is True:
                pointXY, position = self.snapToNearestVertex(self.canvas, event.pos())
                self.point = pointXY
            else:
                self.point = self.toMapCoordinates(event.pos())

            self.clearVertexMarker()

            self.vertexMarker = self.createVertexMarker(self.canvas, self.point, Qt.red, 5, QgsVertexMarker.ICON_BOX, 3)

            self.isEmittingPoint = True

    def showdialog(self):

        self.createFeature()

        self.feat.setFields(self.digiPointLayer.fields())

        self.digiPointLayer.startEditing()
        self.refData['pointLayer'].startEditing()

        prof_nr = self.dataStoreDigitize.getProfileNumber()
        self.setPlaceholders(self.feat, prof_nr)

        self.dialogAttributes = QgsAttributeDialog(self.refData['pointLayer'], self.feat, False, None)
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)

        self.dialogAttributes.show()

        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)

        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)

    def closeAttributeDialog(self):
        self.clearVertexMarker()
        self.refData['pointLayer'].commitChanges()

    def writeToTable(self, fields, feature):

        dataObj = {}

        for item in fields:

            if item.name() == 'uuid' or item.name() == 'id' or item.name() == 'obj_typ' or item.name() == 'obj_art' or item.name() == 'zeit' or item.name() == 'material' or item.name() == 'bemerkung' or item.name() == 'bef_nr' or item.name() == 'fund_nr' or item.name() == 'prob_nr':
                dataObj[item.name()] = feature[item.name()]

        dataObj['layer'] = self.refData['pointLayer'].sourceName()

        self.pup.publish('pointFeatureAttr', dataObj)

    def acceptedAttributeDialog(self):

        self.refData['pointLayer'].commitChanges()

        atrObj = self.dialogAttributes.feature().attributes()

        self.feat.setAttributes(atrObj)

        self.feat['geo_quelle'] = 'profile_object'

        self.addFeature2Layer()
        self.clearVertexMarker()

        dialogFeature = self.dialogAttributes.feature()

        #write to table
        self.writeToTable(self.feat.fields(), dialogFeature)

        self.digiPointLayer.updateExtents()
        self.canvas.refresh()



    def clearVertexMarker(self):
        self.canvas.scene().removeItem(self.vertexMarker)
        self.vertexMarker = None

    def createFeature(self):

        self.feat = QgsFeature()
        self.feat.setGeometry(self.featGeometry) #2 correction

    def addFeature2Layer(self):

        pr = self.digiPointLayer.dataProvider()
        pr.addFeatures([self.feat])
        self.digiPointLayer.updateExtents()

        self.digiPointLayer.endEditCommand()

    def reverseRotation2Eingabelayer(self, layer_id, aar_direction):
        #in Ergebnislayer schreiben

        self.refData['pointLayer'].startEditing()
        
        pr = self.refData['pointLayer'].dataProvider()

        features = self.digiPointLayer.getFeatures()

        #iterrieren über zu schreibende features
        for feature in features:
            
            #Zielfeature erzeugen
            rotFeature = QgsFeature(self.refData['pointLayer'].fields())

            #Geometrie in Kartenebene umrechnen
            rotateGeom = self.rotationCoords.rotatePointFeature(feature, aar_direction)

            #Zielpunktgeometrie erzeugen und zum Zielfeature hinzufügen
            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])
            gZPoint = QgsGeometry(zPoint)
            rotFeature.setGeometry(gZPoint)

            #Attribute setzen
            rotFeature.setAttributes(feature.attributes())

            sourceLayerFeatures = self.refData['pointLayer'].getFeatures()

            #Prüfen ob im Ziellayer das Feature bereits vorhanden ist
            #wenn ja dann löschen und durch Zielfeature ersetzen
            checker = True
            for sourceFeature in sourceLayerFeatures:
                if feature["uuid"] == sourceFeature["uuid"]:
                    pr.deleteFeatures([sourceFeature.id()])
                    pr.addFeatures([rotFeature])
                    checker = False

            if checker == True:

                pr.addFeatures([rotFeature])

        self.refData['pointLayer'].removeSelection()
        self.refData['pointLayer'].commitChanges()
        self.refData['pointLayer'].updateExtents()
        self.refData['pointLayer'].endEditCommand()


    def getFeaturesFromEingabelayer(self, bufferGeometry, geoType, aar_direction):
        #aus Eingabelayer holen
        self.digiPointLayer.startEditing()
        pr = self.digiPointLayer.dataProvider()

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = self.refData['pointLayer'].getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:

            if feature.geometry().within(bufferGeometry):

                if geoType == 'tachy':
                    if feature['geo_quelle'] != 'profile_object':

                        rotFeature = QgsFeature(self.digiPointLayer.fields())

                        rotateGeom = self.rotationCoords.rotatePointFeatureFromOrg(feature, aar_direction)

                        zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                        gZPoint = QgsGeometry(zPoint)
                        rotFeature.setGeometry(gZPoint)
                        rotFeature.setAttributes(feature.attributes())

                        checker = True
                        for digiPointFeature in self.digiPointLayer.getFeatures():
                            if feature["uuid"] == digiPointFeature["uuid"]:
                                checker = False

                        if checker == True:
                            selFeatures.append(rotFeature)

                if geoType == 'profile':
                    if feature['geo_quelle'] == 'profile_object':

                        rotFeature = QgsFeature(self.digiPointLayer.fields())

                        rotateGeom = self.rotationCoords.rotatePointFeatureFromOrg(feature, aar_direction)

                        zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                        gZPoint = QgsGeometry(zPoint)
                        rotFeature.setGeometry(gZPoint)
                        rotFeature.setAttributes(feature.attributes())

                        checker = True
                        for digiPointFeature in self.digiPointLayer.getFeatures():
                            if feature["uuid"] == digiPointFeature["uuid"]:
                                checker = False

                        if checker == True:
                            selFeatures.append(rotFeature)

                        #write to table
                        self.writeToTable(feature.fields(), feature)
                       
        pr.addFeatures(selFeatures)

        self.digiPointLayer.commitChanges()
        self.digiPointLayer.updateExtents()
        self.digiPointLayer.endEditCommand()

    def removeNoneProfileFeatures(self):

        self.digiPointLayer.startEditing()
        pr = self.digiPointLayer.dataProvider()
        features = self.digiPointLayer.getFeatures()

        removeFeatures = []
        for feature in features:

            if feature['geo_quelle'] != 'profile_object':
                removeFeatures.append(feature.id())

        pr.deleteFeatures(removeFeatures)

        self.digiPointLayer.commitChanges()
        self.digiPointLayer.updateExtents()
        self.digiPointLayer.endEditCommand()

    def removeFeatureInEingabelayerByUuid(self, uuid):
        features = self.refData['pointLayer'].getFeatures()

        for feature in features:
            if feature['uuid'] == uuid:
                if feature['geo_quelle'] == 'profile_object':
                    self.refData['pointLayer'].startEditing()
                    self.refData['pointLayer'].deleteFeature(feature.id())
                    self.refData['pointLayer'].commitChanges()

    def setDigiPointLayer(self, digiPointLayer):
        self.digiPointLayer = digiPointLayer

    def update(self, refData):
        self.refData = refData

    def setSnapping(self, enableSnapping):
        if enableSnapping is True:
            self.snapping = True
        else:
            self.snapping = False
