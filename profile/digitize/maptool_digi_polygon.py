import uuid
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QPushButton, QDialogButtonBox, QVBoxLayout
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker, QgsAttributeDialog, QgsAttributeEditorContext
from qgis.core import QgsExpression, QgsWkbTypes, QgsPointXY, QgsPoint, QgsFeature, QgsGeometry, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsVectorLayerUtils, QgsFeatureRequest

from ..publisher import Publisher

class MapToolDigiPolygon(QgsMapTool):
    def __init__(self, canvas, iFace, rotationCoords):
        self.__iface = iFace

        self.pup = Publisher()

        self.rotationCoords = rotationCoords

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

    def createRubberband(self):
        self.rubberband = QgsRubberBand(self.canvas, True)
        self.rubberband.setStrokeColor(Qt.red)
        self.rubberband.setWidth(3)
        self.rubberband.show()

    def canvasPressEvent(self, event):

        if event.button() == Qt.RightButton:

            self.featGeometry = self.rubberband.asGeometry()
            self.showdialog()

        else:

            self.active = True

            self.point = self.toMapCoordinates(event.pos())
            self.canvas.scene().removeItem(self.vertexMarker)
            self.vertexMarker = QgsVertexMarker(self.canvas)
            self.vertexMarker.setCenter(self.point)
            self.vertexMarker.setColor(Qt.red)
            self.vertexMarker.setIconSize(5)
            self.vertexMarker.setIconType(QgsVertexMarker.ICON_BOX)
            self.vertexMarker.setPenWidth(3)

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

        #uuid to identify feature
        feature_uuid = uuid.uuid4()
        self.feat['uuid'] = str(feature_uuid)

        ## set current date
        e = QgsExpression( " $now " )
        self.feat['messdatum'] = e.evaluate()

        self.dialogAttributes = QgsAttributeDialog(self.refData['polygonLayer'], self.feat, False, None)
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)
        self.dialogAttributes.show()

        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)

        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)

    def closeAttributeDialog(self):
        print('closeAttributeDialog')
        self.clearRubberband()
        self.refData['polygonLayer'].commitChanges()

    def acceptedAttributeDialog(self):

        print('acceptedAttributeDialog')
        self.refData['polygonLayer'].commitChanges()

        atrObj = self.dialogAttributes.feature().attributes()
        self.feat.setAttributes(atrObj)

        self.addFeature2Layer()
        self.clearRubberband()

        dialogFeature = self.dialogAttributes.feature()
        dataObj = {}

        for item in self.feat.fields():
            #print(item.name())
            if item.name() == 'uuid' or item.name() == 'id' or item.name() == 'obj_type' or item.name() == 'obj_art' or item.name() == 'zeit' or item.name() == 'material' or item.name() == 'bemerkung':
                dataObj[item.name()] = dialogFeature[item.name()]

        dataObj['layer'] = self.refData['polygonLayer'].sourceName()

        self.digiPolygonLayer.updateExtents()
        self.canvas.refresh()
        self.pup.publish('polygonFeatureAttr', dataObj)

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

        print('qqqqqqqqqqq')
        #self.__iface.actionVertexToolActiveLayer()
        print('wwwwwwwwwww')

    def rotationFromEingabelayer(self, bufferGeometry):

        self.digiPolygonLayer.startEditing()
        pr = self.digiPolygonLayer.dataProvider()

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = self.refData['polygonLayer'].getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:

            if feature.geometry().within(bufferGeometry):

                rotFeature = QgsFeature(self.digiPolygonLayer.fields())

                rotateGeom = self.rotationCoords.rotatePolygonFeatureFromOrg(feature)
                print('rotateGeom', rotateGeom)
                print('rotateGeom', type(rotateGeom))
                rotFeature.setGeometry(rotateGeom)

                rotFeature.setAttributes(feature.attributes())

                selFeatures.append(rotFeature)

        #print('selFeatures', selFeatures)
        pr.addFeatures(selFeatures)

        self.digiPolygonLayer.commitChanges()
        self.digiPolygonLayer.endEditCommand()

    def reverseRotation2Eingabelayer(self, layer_id):
        print('reverseRotation', layer_id)

        pr = self.refData['polygonLayer'].dataProvider()

        features = self.digiPolygonLayer.getFeatures()

        for feature in features:
            self.refData['polygonLayer'].startEditing()

            rotFeature = QgsFeature(self.refData['polygonLayer'].fields())

            rotateGeom = self.rotationCoords.rotatePolygonFeature(feature)
            rotFeature.setGeometry(rotateGeom)
            print('feature.attributes()', feature.attributes())
            rotFeature.setAttributes(feature.attributes())

            sourceLayerFeatures = self.refData['polygonLayer'].getFeatures()

            checker = True
            for sourceFeature in sourceLayerFeatures:
                if feature["uuid"] == sourceFeature["uuid"]:
                    checker = False

            if checker == True:
                retObj = pr.addFeatures([rotFeature])

            self.refData['polygonLayer'].removeSelection()

            self.refData['polygonLayer'].commitChanges()

            self.refData['polygonLayer'].updateExtents()

            self.refData['polygonLayer'].endEditCommand()

    def setDigiPolygonLayer(self, digiPolygonLayer):
        self.digiPolygonLayer = digiPolygonLayer

    def update(self, refData):
        self.refData = refData
