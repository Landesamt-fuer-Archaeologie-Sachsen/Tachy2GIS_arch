import uuid
from PyQt5.QtCore import Qt
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsAttributeDialog, QgsAttributeEditorContext
from qgis.core import QgsExpression, QgsPoint, QgsFeature, QgsGeometry, QgsFeatureRequest

from ..publisher import Publisher

class MapToolDigiPoint(QgsMapTool):
    def __init__(self, canvas, iFace, rotationCoords):
        self.__iface = iFace

        self.pup = Publisher()

        self.rotationCoords = rotationCoords

        self.canvas = canvas

        self.digiPointLayer = None

        self.featGeometry = None

        self.feat = None

        self.dialogAttributes = None

        QgsMapTool.__init__(self, self.canvas)

        self.vertexMarker = None

        self.point = None

        self.refData = None


    def canvasPressEvent(self, event):

        if event.button() == Qt.RightButton:
            self.featGeometry = QgsGeometry.fromPointXY(self.vertexMarker.center())

            self.showdialog()


        else:
            self.active = True

            self.point = self.toMapCoordinates(event.pos())
            self.clearVertexMarker()
            self.vertexMarker = QgsVertexMarker(self.canvas)
            self.vertexMarker.setCenter(self.point)
            self.vertexMarker.setColor(Qt.red)
            self.vertexMarker.setIconSize(5)
            self.vertexMarker.setIconType(QgsVertexMarker.ICON_BOX)
            self.vertexMarker.setPenWidth(3)

            self.isEmittingPoint = True

    def showdialog(self):

        self.createFeature()

        self.feat.setFields(self.digiPointLayer.fields())

        self.digiPointLayer.startEditing()
        self.refData['pointLayer'].startEditing()

        #uuid to identify feature
        feature_uuid = uuid.uuid4()
        self.feat['uuid'] = str(feature_uuid)

        #Type of digitize
        self.feat['geo_quelle'] = 'profile_object'
        ## set current date
        e = QgsExpression( " $now " )
        self.feat['messdatum'] = e.evaluate()

        self.dialogAttributes = QgsAttributeDialog(self.refData['pointLayer'], self.feat, False, None)
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)

        self.dialogAttributes.show()

        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)

        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)

    def closeAttributeDialog(self):
        self.clearVertexMarker()
        self.refData['pointLayer'].commitChanges()

    def acceptedAttributeDialog(self):

        print('acceptedAttributeDialog')
        self.refData['pointLayer'].commitChanges()

        atrObj = self.dialogAttributes.feature().attributes()

        self.feat.setAttributes(atrObj)

        self.feat['geo_quelle'] = 'profile_object'

        self.addFeature2Layer()
        self.clearVertexMarker()

        dialogFeature = self.dialogAttributes.feature()
        dataObj = {}

        for item in self.feat.fields():
            if item.name() == 'uuid' or item.name() == 'id' or item.name() == 'obj_type' or item.name() == 'obj_art' or item.name() == 'zeit' or item.name() == 'material' or item.name() == 'bemerkung':
                dataObj[item.name()] = dialogFeature[item.name()]

        dataObj['layer'] = self.refData['pointLayer'].sourceName()

        self.digiPointLayer.updateExtents()

        self.canvas.refresh()

        self.pup.publish('pointFeatureAttr', dataObj)


    def clearVertexMarker(self):
        self.canvas.scene().removeItem(self.vertexMarker)

    def createFeature(self):

        self.feat = QgsFeature()
        self.feat.setGeometry(self.featGeometry) #2 correction

    def addFeature2Layer(self):

        pr = self.digiPointLayer.dataProvider()
        pr.addFeatures([self.feat])
        self.digiPointLayer.updateExtents()

        self.digiPointLayer.endEditCommand()

    def reverseRotation2Eingabelayer(self, layer_id):
        #in Ergebnislayer schreiben
        print('reverseRotation', layer_id)

        pr = self.refData['pointLayer'].dataProvider()

        features = self.digiPointLayer.getFeatures()

        for feature in features:
            self.refData['pointLayer'].startEditing()

            rotFeature = QgsFeature(self.refData['pointLayer'].fields())

            rotateGeom = self.rotationCoords.rotatePointFeature(feature)

            zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['y_trans'], rotateGeom['z_trans'])

            gZPoint = QgsGeometry(zPoint)
            rotFeature.setGeometry(gZPoint)
            rotFeature.setAttributes(feature.attributes())

            sourceLayerFeatures = self.refData['pointLayer'].getFeatures()

            checker = True
            for sourceFeature in sourceLayerFeatures:
                if feature["uuid"] == sourceFeature["uuid"]:
                    checker = False

            if checker == True:

                retObj = pr.addFeatures([rotFeature])

            self.refData['pointLayer'].removeSelection()

            self.refData['pointLayer'].commitChanges()

            self.refData['pointLayer'].updateExtents()

            self.refData['pointLayer'].endEditCommand()


    def getFeaturesFromEingabelayer(self, bufferGeometry, geoType):
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

                        rotateGeom = self.rotationCoords.rotatePointFeatureFromOrg(feature)

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

                        rotateGeom = self.rotationCoords.rotatePointFeatureFromOrg(feature)

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
                        dataObj = {}
                        for item in feature.fields():
                            if item.name() == 'uuid' or item.name() == 'id' or item.name() == 'obj_type' or item.name() == 'obj_art' or item.name() == 'zeit' or item.name() == 'material' or item.name() == 'bemerkung':
                                dataObj[item.name()] = feature[item.name()]

                        dataObj['layer'] = self.refData['pointLayer'].sourceName()

                        self.pup.publish('pointFeatureAttr', dataObj)

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
