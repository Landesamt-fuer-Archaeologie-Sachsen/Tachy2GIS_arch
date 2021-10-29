import uuid
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QPushButton, QDialogButtonBox, QVBoxLayout
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker, QgsAttributeDialog, QgsAttributeEditorContext
from qgis.core import QgsExpression, QgsWkbTypes, QgsPointXY, QgsFeature, QgsGeometry, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsVectorLayerUtils, QgsFeatureRequest

from ..publisher import Publisher

class MapToolDigiLine(QgsMapTool):
    def __init__(self, canvas, iFace, rotationCoords):
        self.__iface = iFace

        self.pup = Publisher()

        self.rotationCoords = rotationCoords

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
            self.showLine()

    def showLine(self):

        self.rubberband.setToGeometry(QgsGeometry.fromPolylineXY(self.points), None)

    def showdialog(self):

        self.createFeature()

        self.feat.setFields(self.digiLineLayer.fields())

        self.digiLineLayer.startEditing()
        self.refData['lineLayer'].startEditing()

        #uuid to identify feature
        feature_uuid = uuid.uuid4()
        self.feat['uuid'] = str(feature_uuid)

        ## set current date
        e = QgsExpression( " $now " )
        self.feat['messdatum'] = e.evaluate()

        self.dialogAttributes = QgsAttributeDialog(self.refData['lineLayer'], self.feat, False, None)
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)
        self.dialogAttributes.show()

        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)

        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)

    def closeAttributeDialog(self):
        print('closeAttributeDialog')
        self.clearRubberband()
        self.refData['lineLayer'].commitChanges()

    def acceptedAttributeDialog(self):

        print('acceptedAttributeDialog')
        self.refData['lineLayer'].commitChanges()

        self.addFeature2Layer()
        self.clearRubberband()

        dialogFeature = self.dialogAttributes.feature()
        dataObj = {}

        for item in self.feat.fields():
            if item.name() == 'uuid' or item.name() == 'id' or item.name() == 'obj_type' or item.name() == 'obj_art' or item.name() == 'zeit' or item.name() == 'material' or item.name() == 'bemerkung' or item.name() == 'benerkung':

                #Workaround - In Line Shapedatei hat das Feld "Bemerkung" den Namen benerkung
                if item.name() == 'benerkung':
                    dataObj['bemerkung'] = dialogFeature[item.name()]
                else:
                    dataObj[item.name()] = dialogFeature[item.name()]

        dataObj['layer'] = self.refData['lineLayer'].sourceName()

        self.digiLineLayer.updateExtents()
        self.canvas.refresh()
        self.pup.publish('lineFeatureAttr', dataObj)

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

    def rotationFromEingabelayer(self, bufferGeometry):

        self.digiLineLayer.startEditing()
        pr = self.digiLineLayer.dataProvider()

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = self.refData['lineLayer'].getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:

            if feature.geometry().within(bufferGeometry):

                rotFeature = QgsFeature(self.digiLineLayer.fields())

                rotateGeom = self.rotationCoords.rotateLineFeatureFromOrg(feature)

                rotFeature.setGeometry(rotateGeom)

                rotFeature.setAttributes(feature.attributes())

                selFeatures.append(rotFeature)

        #print('selFeatures', selFeatures)
        pr.addFeatures(selFeatures)

        self.digiLineLayer.commitChanges()
        self.digiLineLayer.endEditCommand()

    def reverseRotation2Eingabelayer(self, layer_id):
        print('reverseRotation', layer_id)

        pr = self.refData['lineLayer'].dataProvider()

        features = self.digiLineLayer.getFeatures()

        for feature in features:
            self.refData['lineLayer'].startEditing()

            rotFeature = QgsFeature(self.refData['lineLayer'].fields())

            rotateGeom = self.rotationCoords.rotateLineFeature(feature)
            rotFeature.setGeometry(rotateGeom)

            rotFeature.setAttributes(feature.attributes())

            sourceLayerFeatures = self.refData['lineLayer'].getFeatures()

            checker = True
            for sourceFeature in sourceLayerFeatures:
                if feature["uuid"] == sourceFeature["uuid"]:
                    checker = False

            if checker == True:
                retObj = pr.addFeatures([rotFeature])

            self.refData['lineLayer'].removeSelection()

            self.refData['lineLayer'].commitChanges()

            self.refData['lineLayer'].updateExtents()

            self.refData['lineLayer'].endEditCommand()

    def setDigiLineLayer(self, digiLineLayer):
        self.digiLineLayer = digiLineLayer

    def update(self, refData):
        self.refData = refData
