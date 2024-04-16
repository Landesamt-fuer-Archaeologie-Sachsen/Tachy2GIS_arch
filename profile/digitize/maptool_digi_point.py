from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot
from qgis.gui import QgsAttributeDialog, QgsAttributeEditorContext
from qgis.core import QgsFeature, QgsGeometry, QgsFeatureRequest, QgsPoint

from .map_tools import PointMapTool
from ..publisher import Publisher
from .maptool_mixin import MapToolMixin


class MapToolDigiPoint(PointMapTool, MapToolMixin):
    # darf nicht in den Konstruktor:
    digi_layer_changed = pyqtSignal()

    def __init__(self, canvas, iFace, rotationCoords, dataStoreDigitize):
        self.canvas = canvas
        self.__iface = iFace
        self.rotationCoords = rotationCoords
        self.dataStoreDigitize = dataStoreDigitize
        self.pup = Publisher()
        self.digiPointLayer = None
        self.featGeometry = None
        self.feat = None
        self.dialogAttributes = None
        self.refData = None
        PointMapTool.__init__(self, self.canvas)
        self.finished_geometry.connect(self.got_geometry)

    def setDigiPointLayer(self, digiPointLayer):
        self.digiPointLayer = digiPointLayer

    def update(self, refData):
        self.refData = refData

    def got_geometry(self, geometry):
        self.featGeometry = geometry
        if self.featGeometry.isNull():
            return

        if self.feat and self.feat.hasGeometry():
            self.feat.setGeometry(self.featGeometry)
            self.digiPointLayer.startEditing()
            self.digiPointLayer.addFeature(self.feat)
            self.digiPointLayer.commitChanges()
            self.digiPointLayer.endEditCommand()
            self.clear_map_tool()
        else:
            self.showdialog()

        self.digi_layer_changed.emit()

    @pyqtSlot(QgsFeature)
    def set_feature_for_editing(self, feature):
        self.feat = feature
        self.set_geometry_for_editing(feature.geometry())
        self.digiPointLayer.startEditing()
        self.digiPointLayer.deleteFeature(feature.id())
        self.digiPointLayer.commitChanges()
        self.digiPointLayer.endEditCommand()
        self.canvas.setMapTool(self)

    def clear_map_tool(self):
        self.reset_geometry()
        self.feat = None

    def createFeature(self):
        self.feat = QgsFeature()
        self.feat.setGeometry(self.featGeometry)

    def showdialog(self):
        self.createFeature()

        self.feat.setFields(self.digiPointLayer.fields())

        self.digiPointLayer.startEditing()
        self.refData["pointLayer"].startEditing()

        prof_nr = self.dataStoreDigitize.getProfileNumber()
        self.setPlaceholders(self.feat, prof_nr)

        self.dialogAttributes = QgsAttributeDialog(self.refData["pointLayer"], self.feat, False, None)
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)
        self.dialogAttributes.show()

        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)

        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)

    def closeAttributeDialog(self):
        self.clear_map_tool()
        self.refData["pointLayer"].commitChanges()

    def acceptedAttributeDialog(self):
        self.refData["pointLayer"].commitChanges()

        atrObj = self.dialogAttributes.feature().attributes()
        self.feat.setAttributes(atrObj)

        self.feat["geo_quelle"] = "profile_object"

        self.addFeature2Layer()

        dialogFeature = self.dialogAttributes.feature()

        # write to table
        self.writeToTable(self.feat.fields(), dialogFeature)

        self.digiPointLayer.updateExtents()
        self.canvas.refresh()

        self.clear_map_tool()
        self.digi_layer_changed.emit()

    def writeToTable(self, fields, feature):
        dataObj = {}

        for item in fields:
            if (
                item.name() == "obj_uuid"
                or item.name() == "fid"
                or item.name() == "obj_typ"
                or item.name() == "obj_art"
                or item.name() == "zeit"
                or item.name() == "material"
                or item.name() == "bemerkung"
                or item.name() == "bef_nr"
                or item.name() == "fund_nr"
                or item.name() == "prob_nr"
            ):
                dataObj[item.name()] = feature[item.name()]

        dataObj["layer"] = self.refData["pointLayer"].sourceName()

        self.pup.publish("pointFeatureAttr", dataObj)

    def addFeature2Layer(self):
        pr = self.digiPointLayer.dataProvider()
        pr.addFeatures([self.feat])
        self.digiPointLayer.updateExtents()
        self.digiPointLayer.endEditCommand()

    def getFeaturesFromEingabelayer(self, bufferGeometry, geoType, aar_direction):
        self.digiPointLayer.startEditing()
        pr = self.digiPointLayer.dataProvider()

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = self.refData["pointLayer"].getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:
            if not feature.geometry().within(bufferGeometry):
                continue

            if geoType == "tachy" and feature["geo_quelle"] != "profile_object":
                rotFeature = QgsFeature(self.digiPointLayer.fields())
                rotateGeom = self.rotationCoords.rotatePointFeatureFromOrg(feature, aar_direction)
                zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["z_trans"], rotateGeom["z_trans"])
                gZPoint = QgsGeometry(zPoint)
                rotFeature.setGeometry(gZPoint)
                rotFeature.setAttributes(feature.attributes())

                checker = True
                for digiPointFeature in self.digiPointLayer.getFeatures():
                    if feature["obj_uuid"] == digiPointFeature["obj_uuid"]:
                        checker = False

                if checker == True:
                    selFeatures.append(rotFeature)

            elif geoType == "profile" and feature["geo_quelle"] == "profile_object":
                rotFeature = QgsFeature(self.digiPointLayer.fields())
                rotateGeom = self.rotationCoords.rotatePointFeatureFromOrg(feature, aar_direction)
                zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["z_trans"], rotateGeom["z_trans"])
                gZPoint = QgsGeometry(zPoint)
                rotFeature.setGeometry(gZPoint)
                rotFeature.setAttributes(feature.attributes())

                checker = True
                for digiPointFeature in self.digiPointLayer.getFeatures():
                    if feature["obj_uuid"] == digiPointFeature["obj_uuid"]:
                        checker = False

                if checker == True:
                    selFeatures.append(rotFeature)

                # write to table
                self.writeToTable(feature.fields(), feature)

        pr.addFeatures(selFeatures)

        self.digiPointLayer.commitChanges()
        self.digiPointLayer.updateExtents()
        self.digiPointLayer.endEditCommand()

        self.digi_layer_changed.emit()

    def removeNoneProfileFeatures(self):
        self.digiPointLayer.startEditing()
        pr = self.digiPointLayer.dataProvider()
        features = self.digiPointLayer.getFeatures()

        removeFeatures = []
        for feature in features:
            if feature["geo_quelle"] != "profile_object":
                removeFeatures.append(feature.id())

        pr.deleteFeatures(removeFeatures)

        self.digiPointLayer.commitChanges()
        self.digiPointLayer.updateExtents()
        self.digiPointLayer.endEditCommand()

    # in den Eingabelayer schreiben
    def reverseRotation2Eingabelayer(self, layer_id, aar_direction):

        self.refData["pointLayer"].startEditing()

        pr = self.refData["pointLayer"].dataProvider()

        features = self.digiPointLayer.getFeatures()

        # iterrieren über zu schreibende features
        for feature in features:

            if feature['geo_quelle'] == 'profile_object':
                # Zielfeature erzeugen
                rotFeature = QgsFeature(self.refData["pointLayer"].fields())

                # Geometrie in Kartenebene umrechnen
                rotateGeom = self.rotationCoords.rotatePointFeature(feature, aar_direction)

                # Zielpunktgeometrie erzeugen und zum Zielfeature hinzufügen
                zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["y_trans"], rotateGeom["z_trans"])
                gZPoint = QgsGeometry(zPoint)
                rotFeature.setGeometry(gZPoint)

                # Attribute setzen
                rotFeature.setAttributes(feature.attributes())

                sourceLayerFeatures = self.refData["pointLayer"].getFeatures()

                # Prüfen ob im Ziellayer das Feature bereits vorhanden ist
                # wenn ja dann löschen und durch Zielfeature ersetzen
                checker = True
                for sourceFeature in sourceLayerFeatures:
                    if feature["obj_uuid"] == sourceFeature["obj_uuid"]:
                        pr.deleteFeatures([sourceFeature.id()])
                        pr.addFeatures([rotFeature])
                        checker = False

                if checker == True:
                    pr.addFeatures([rotFeature])

        self.refData["pointLayer"].removeSelection()
        self.refData["pointLayer"].commitChanges()
        self.refData["pointLayer"].updateExtents()
        self.refData["pointLayer"].endEditCommand()

    def removeFeatureInEingabelayerByUuid(self, obj_uuid):
        features = self.refData["pointLayer"].getFeatures()

        for feature in features:
            if feature["obj_uuid"] == obj_uuid:
                if feature["geo_quelle"] == "profile_object":
                    self.refData["pointLayer"].startEditing()
                    self.refData["pointLayer"].deleteFeature(feature.id())
                    self.refData["pointLayer"].commitChanges()

        self.digi_layer_changed.emit()
