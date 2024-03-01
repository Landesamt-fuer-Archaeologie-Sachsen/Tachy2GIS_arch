from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot
from qgis.gui import QgsAttributeDialog, QgsAttributeEditorContext
from qgis.core import QgsFeature, QgsGeometry, QgsFeatureRequest

from .map_tools import MultilineMapTool
from ..publisher import Publisher
from .maptool_mixin import MapToolMixin


class MapToolDigiLine(MultilineMapTool, MapToolMixin):
    # darf nicht in den Konstruktor:
    digi_layer_changed = pyqtSignal()

    def __init__(self, canvas, iFace, rotationCoords, dataStoreDigitize):
        self.canvas = canvas
        self.__iface = iFace
        self.rotationCoords = rotationCoords
        self.dataStoreDigitize = dataStoreDigitize
        self.pup = Publisher()
        self.digiLineLayer = None
        self.featGeometry = None
        self.feat = None
        self.dialogAttributes = None
        self.refData = None
        MultilineMapTool.__init__(self, self.canvas)
        self.finished_geometry.connect(self.got_geometry)

    def setDigiLineLayer(self, digiLineLayer):
        self.digiLineLayer = digiLineLayer

    def update(self, refData):
        self.refData = refData

    def got_geometry(self, geometry):
        self.featGeometry = geometry
        if self.featGeometry.isNull():
            return

        if self.feat and self.feat.hasGeometry():
            self.feat.setGeometry(self.featGeometry)
            self.digiLineLayer.startEditing()
            self.digiLineLayer.addFeature(self.feat)
            self.digiLineLayer.commitChanges()
            self.digiLineLayer.endEditCommand()
            self.clear_map_tool()
        else:
            self.showdialog()

        self.digi_layer_changed.emit()

    @pyqtSlot(QgsFeature)
    def set_feature_for_editing(self, feature):
        self.feat = feature
        self.set_geometry_for_editing(feature.geometry())
        self.digiLineLayer.startEditing()
        self.digiLineLayer.deleteFeature(feature.id())
        self.digiLineLayer.commitChanges()
        self.digiLineLayer.endEditCommand()
        self.canvas.setMapTool(self)

    def clear_map_tool(self):
        self.reset_geometry()
        self.feat = None

    def createFeature(self):
        self.feat = QgsFeature()
        self.feat.setGeometry(self.featGeometry)

    def showdialog(self):
        self.createFeature()

        self.feat.setFields(self.digiLineLayer.fields())

        self.digiLineLayer.startEditing()
        self.refData["lineLayer"].startEditing()

        prof_nr = self.dataStoreDigitize.getProfileNumber()
        self.setPlaceholders(self.feat, prof_nr)

        self.dialogAttributes = QgsAttributeDialog(
            self.refData["lineLayer"], self.feat, False, None
        )
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)
        self.dialogAttributes.show()

        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)

        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)

    def closeAttributeDialog(self):
        self.clear_map_tool()
        self.refData["lineLayer"].commitChanges()

    def acceptedAttributeDialog(self):
        self.refData["lineLayer"].commitChanges()

        atrObj = self.dialogAttributes.feature().attributes()
        self.feat.setAttributes(atrObj)

        self.feat["geo_quelle"] = "profile_object"

        self.addFeature2Layer()

        dialogFeature = self.dialogAttributes.feature()

        # write to table
        self.writeToTable(self.feat.fields(), dialogFeature)

        self.digiLineLayer.updateExtents()
        self.canvas.refresh()

        self.clear_map_tool()
        self.digi_layer_changed.emit()

    def writeToTable(self, fields, feature):
        dataObj = {}

        for item in fields:
            if (
                item.name() == "obj_uuid"
                or item.name() == "fid"
                or item.name() == "obj_type"
                or item.name() == "obj_art"
                or item.name() == "zeit"
                or item.name() == "material"
                or item.name() == "bemerkung"
                or item.name() == "benerkung"  # Workaround
                or item.name() == "bef_nr"
                or item.name() == "fund_nr"
                or item.name() == "prob_nr"
            ):
                # Workaround - In Line Shapedatei hat das Feld "Bemerkung" den Namen benerkung
                if item.name() == "benerkung":
                    dataObj["bemerkung"] = feature[item.name()]
                else:
                    dataObj[item.name()] = feature[item.name()]

        dataObj["layer"] = self.refData["lineLayer"].sourceName()

        self.pup.publish("lineFeatureAttr", dataObj)

    def addFeature2Layer(self):
        pr = self.digiLineLayer.dataProvider()
        pr.addFeatures([self.feat])
        self.digiLineLayer.updateExtents()
        self.digiLineLayer.endEditCommand()

    def getFeaturesFromEingabelayer(self, bufferGeometry, geoType, aar_direction):
        self.digiLineLayer.startEditing()
        pr = self.digiLineLayer.dataProvider()

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = self.refData["lineLayer"].getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:
            if not feature.geometry().within(bufferGeometry):
                continue

            if geoType == "tachy" and feature["geo_quelle"] != "profile_object":
                rotFeature = QgsFeature(self.digiLineLayer.fields())
                rotateGeom = self.rotationCoords.rotateLineFeatureFromOrg(
                    feature, aar_direction
                )
                rotFeature.setGeometry(rotateGeom)
                rotFeature.setAttributes(feature.attributes())
                selFeatures.append(rotFeature)

            elif geoType == "profile" and feature["geo_quelle"] == "profile_object":
                rotFeature = QgsFeature(self.digiLineLayer.fields())
                rotateGeom = self.rotationCoords.rotateLineFeatureFromOrg(
                    feature, aar_direction
                )
                rotFeature.setGeometry(rotateGeom)
                rotFeature.setAttributes(feature.attributes())

                selFeatures.append(rotFeature)

                # write to table
                self.writeToTable(feature.fields(), feature)

        pr.addFeatures(selFeatures)

        self.digiLineLayer.commitChanges()
        self.digiLineLayer.updateExtents()
        self.digiLineLayer.endEditCommand()

        self.digi_layer_changed.emit()

    def removeNoneProfileFeatures(self):
        self.digiLineLayer.startEditing()
        pr = self.digiLineLayer.dataProvider()
        features = self.digiLineLayer.getFeatures()

        removeFeatures = []
        for feature in features:
            if feature["geo_quelle"] != "profile_object":
                removeFeatures.append(feature.id())

        pr.deleteFeatures(removeFeatures)

        self.digiLineLayer.commitChanges()
        self.digiLineLayer.updateExtents()
        self.digiLineLayer.endEditCommand()

    # in den Eingabelayer schreiben
    def reverseRotation2Eingabelayer(self, layer_id, aar_direction):
        self.refData["lineLayer"].startEditing()

        pr = self.refData["lineLayer"].dataProvider()

        features = self.digiLineLayer.getFeatures()

        # iterrieren über zu schreibende features
        for feature in features:
            # Zielgeometrie erzeugen
            emptyTargetGeometry = QgsGeometry.fromPolyline([])

            # Zielfeature erzeugen
            rotFeature = QgsFeature(self.refData["lineLayer"].fields())

            # Geometrie in Kartenebene umrechnen
            rotateGeom = self.rotationCoords.rotateLineFeature(
                feature, emptyTargetGeometry, aar_direction
            )
            rotFeature.setGeometry(rotateGeom)
            rotFeature.setAttributes(feature.attributes())

            checker = True
            # Features aus Eingabelayer
            # schauen ob es schon existiert (anhand obj_uuid), wenn ja dann löschen und durch Zielfeature ersetzen
            sourceLayerFeatures = self.refData["lineLayer"].getFeatures()
            for sourceFeature in sourceLayerFeatures:
                if feature["obj_uuid"] == sourceFeature["obj_uuid"]:
                    pr.deleteFeatures([sourceFeature.id()])
                    pr.addFeatures([rotFeature])

                    checker = False

            # wenn feature nicht vorhanden, neues feature im Layer anlegen
            if checker == True:
                retObj = pr.addFeatures([rotFeature])

        self.refData["lineLayer"].removeSelection()
        self.refData["lineLayer"].commitChanges()
        self.refData["lineLayer"].updateExtents()
        self.refData["lineLayer"].endEditCommand()

    def removeFeatureInEingabelayerByUuid(self, obj_uuid):
        features = self.refData["lineLayer"].getFeatures()

        for feature in features:
            if feature["obj_uuid"] == obj_uuid:
                if feature["geo_quelle"] == "profile_object":
                    self.refData["lineLayer"].startEditing()
                    self.refData["lineLayer"].deleteFeature(feature.id())
                    self.refData["lineLayer"].commitChanges()

        self.digi_layer_changed.emit()
