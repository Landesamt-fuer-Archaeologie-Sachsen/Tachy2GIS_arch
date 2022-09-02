from PyQt5.QtCore import Qt
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker, QgsAttributeDialog, QgsAttributeEditorContext
from qgis.core import QgsWkbTypes, QgsFeature, QgsGeometry, QgsFeatureRequest

from ..publisher import Publisher
from .maptool_mixin import MapToolMixin
class MapToolDigiLine(QgsMapTool, MapToolMixin):
    def __init__(self, canvas, iFace, rotationCoords, dataStoreDigitize):
        self.__iface = iFace

        self.pup = Publisher()
        self.rotationCoords = rotationCoords
        self.dataStoreDigitize = dataStoreDigitize
        self.canvas = canvas
        self.digiLineLayer = None
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
        self.rubberband = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
        self.rubberband.setStrokeColor(Qt.red)
        self.rubberband.setWidth(3)
        self.rubberband.show()

    def canvasPressEvent(self, event):

        if event.button() == Qt.RightButton:

            self.featGeometry = self.rubberband.asGeometry()
            self.showdialog()

        else:
            print('canvasPressEvent')
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
            self.showLine()

    def showLine(self):

        self.rubberband.setToGeometry(QgsGeometry.fromPolylineXY(self.points), None)

    def showdialog(self):

        self.createFeature()

        self.feat.setFields(self.digiLineLayer.fields())

        self.digiLineLayer.startEditing()
        self.refData['lineLayer'].startEditing()

        prof_nr = self.dataStoreDigitize.getProfileNumber()
        self.setPlaceholders(self.feat, prof_nr)

        self.dialogAttributes = QgsAttributeDialog(self.refData['lineLayer'], self.feat, False, None)
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)
        self.dialogAttributes.show()

        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)

        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)

    def closeAttributeDialog(self):
        print('closeAttributeDialog')
        self.clearRubberband()
        self.refData['lineLayer'].commitChanges()

    def writeToTable(self, fields, feature):

        dataObj = {}

        for item in fields:
            if item.name() == 'uuid' or item.name() == 'id' or item.name() == 'obj_type' or item.name() == 'obj_art' or item.name() == 'zeit' or item.name() == 'material' or item.name() == 'bemerkung' or item.name() == 'benerkung' or item.name() == 'bef_nr' or item.name() == 'fund_nr' or item.name() == 'prob_nr':

                #Workaround - In Line Shapedatei hat das Feld "Bemerkung" den Namen benerkung
                if item.name() == 'benerkung':
                    dataObj['bemerkung'] = feature[item.name()]
                else:
                    dataObj[item.name()] = feature[item.name()]

        dataObj['layer'] = self.refData['lineLayer'].sourceName()

        self.pup.publish('lineFeatureAttr', dataObj)


    def acceptedAttributeDialog(self):

        print('acceptedAttributeDialog')
        self.refData['lineLayer'].commitChanges()

        atrObj = self.dialogAttributes.feature().attributes()
        self.feat.setAttributes(atrObj)

        self.feat['geo_quelle'] = 'profile_object'

        self.addFeature2Layer()
        self.clearRubberband()

        dialogFeature = self.dialogAttributes.feature()

        #write to table
        self.writeToTable(self.feat.fields(), dialogFeature)

        self.digiLineLayer.updateExtents()
        self.canvas.refresh()


    def clearRubberband(self):
        self.rubberband.reset(QgsWkbTypes.LineGeometry)
        self.points = []
        self.canvas.scene().removeItem(self.vertexMarker)

    def createFeature(self):

        self.feat = QgsFeature()
        self.feat.setGeometry(self.featGeometry) #2 correction

    def addFeature2Layer(self):

        pr = self.digiLineLayer.dataProvider()
        pr.addFeatures([self.feat])
        self.digiLineLayer.updateExtents()
        self.digiLineLayer.endEditCommand()

    def getFeaturesFromEingabelayer(self, bufferGeometry, geoType):

        self.digiLineLayer.startEditing()
        pr = self.digiLineLayer.dataProvider()

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = self.refData['lineLayer'].getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:

            if feature.geometry().within(bufferGeometry):

                if geoType == 'tachy':
                    if feature['geo_quelle'] != 'profile_object':

                        rotFeature = QgsFeature(self.digiLineLayer.fields())

                        rotateGeom = self.rotationCoords.rotateLineFeatureFromOrg(feature)

                        rotFeature.setGeometry(rotateGeom)

                        rotFeature.setAttributes(feature.attributes())

                        selFeatures.append(rotFeature)

                if geoType == 'profile':
                    if feature['geo_quelle'] == 'profile_object':
                        print('getFeaturesFromEingabelayer')
                        rotFeature = QgsFeature(self.digiLineLayer.fields())

                        rotateGeom = self.rotationCoords.rotateLineFeatureFromOrg(feature)

                        rotFeature.setGeometry(rotateGeom)

                        rotFeature.setAttributes(feature.attributes())

                        selFeatures.append(rotFeature)

                        #write to table
                        self.writeToTable(feature.fields(), feature)
                        

        pr.addFeatures(selFeatures)

        self.digiLineLayer.commitChanges()
        self.digiLineLayer.updateExtents()
        self.digiLineLayer.endEditCommand()

    def removeNoneProfileFeatures(self):

        self.digiLineLayer.startEditing()
        pr = self.digiLineLayer.dataProvider()
        features = self.digiLineLayer.getFeatures()

        removeFeatures = []
        for feature in features:

            if feature['geo_quelle'] != 'profile_object':

                removeFeatures.append(feature.id())

        pr.deleteFeatures(removeFeatures)

        self.digiLineLayer.commitChanges()
        self.digiLineLayer.updateExtents()
        self.digiLineLayer.endEditCommand()

    def reverseRotation2Eingabelayer(self, layer_id):
        print('reverseRotation', layer_id)

        self.refData['lineLayer'].startEditing()

        pr = self.refData['lineLayer'].dataProvider()

        features = self.digiLineLayer.getFeatures()

        #iterrieren über zu schreibende features
        for feature in features:
            #Zielgeometrie erzeugen

            emptyTargetGeometry = self.rubberband.asGeometry()

            #Zielfeature erzeugen
            rotFeature = QgsFeature(self.refData['lineLayer'].fields())

            #Geometrie in Kartenebene umrechnen
            rotateGeom = self.rotationCoords.rotateLineFeature(feature, emptyTargetGeometry)
            rotFeature.setGeometry(rotateGeom)

            rotFeature.setAttributes(feature.attributes())

            checker = True
            #Features aus Eingabelayer
            #schauen ob es schon existiert (anhand uuid), wenn ja dann löschen und durch Zielfeature ersetzen
            sourceLayerFeatures = self.refData['lineLayer'].getFeatures()
            for sourceFeature in sourceLayerFeatures:
                if feature["uuid"] == sourceFeature["uuid"]:
                    pr.deleteFeatures([sourceFeature.id()])
                    pr.addFeatures([rotFeature])

                    checker = False

            #wenn feature nicht vorhanden, neues feature im Layer anlegen
            if checker == True:
                retObj = pr.addFeatures([rotFeature])

        self.refData['lineLayer'].removeSelection()
        self.refData['lineLayer'].commitChanges()
        self.refData['lineLayer'].updateExtents()
        self.refData['lineLayer'].endEditCommand()

    def removeFeatureInEingabelayerByUuid(self, uuid):
        features = self.refData['lineLayer'].getFeatures()

        for feature in features:
            if feature['uuid'] == uuid:
                if feature['geo_quelle'] == 'profile_object':
                    self.refData['lineLayer'].startEditing()
                    self.refData['lineLayer'].deleteFeature(feature.id())
                    self.refData['lineLayer'].commitChanges()

    def setDigiLineLayer(self, digiLineLayer):
        self.digiLineLayer = digiLineLayer

    def update(self, refData):
        self.refData = refData

    def setSnapping(self, enableSnapping):
        if enableSnapping is True:
            self.snapping = True
        else:
            self.snapping = False