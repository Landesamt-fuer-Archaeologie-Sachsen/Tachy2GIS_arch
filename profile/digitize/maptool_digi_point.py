from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot
from qgis.core import QgsFeature, QgsGeometry, QgsFeatureRequest, QgsPoint, QgsProject, QgsMessageLog, Qgis
from qgis.gui import QgsAttributeDialog, QgsAttributeEditorContext

from .map_tools import PointMapTool
from .maptool_mixin import MapToolMixin
from ..publisher import Publisher


class MapToolDigiPoint(PointMapTool, MapToolMixin):
    # darf nicht in den Konstruktor:
    digi_layer_changed = pyqtSignal()

    def __init__(self, canvas, iFace, rotationCoords, dataStoreDigitize):
        self.canvas = canvas
        self.iface = iFace
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
        proj_layer = QgsProject.instance().mapLayersByName("E_Point")[0]

        self.feat.setFields(self.digiPointLayer.fields())

        # use default values from actual project layer
        # as self.digiLineLayer has no defaultValueDefinitions aka expressions
        for field in proj_layer.fields():
            field_name = field.name()
            field_index = proj_layer.fields().indexFromName(field_name)
            if field_name == "fid":
                field_default_value = "-999"
            else:
                # formula for fid: if (count("fid") = 0, 0, maximum("fid") + 1)
                field_default_value = proj_layer.defaultValue(field_index)
            self.feat.setAttribute(field_name, field_default_value)

        self.digiPointLayer.startEditing()
        self.refData["pointLayer"].startEditing()

        prof_nr = self.dataStoreDigitize.getProfileNumber()
        self.setPlaceholders(self.feat, prof_nr)

        self.dialogAttributes = QgsAttributeDialog(self.refData["pointLayer"], self.feat, False, None)
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)
        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)
        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)
        self.dialogAttributes.show()

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
                or item.name() == "probe_nr"
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
                print("No Pointfeatures within buffer geometry!")
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

        try:
            pr.addFeatures(selFeatures)
        except Exception as e:
            QgsMessageLog.logMessage(str(e), "T2G Archäologie", Qgis.Info)

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
        pr = self.refData["pointLayer"].dataProvider()
        proj_layer = QgsProject.instance().mapLayersByName("E_Point")[0]

        features_to_write = self.digiPointLayer.getFeatures()

        for feature in features_to_write:
            if feature["geo_quelle"] != "profile_object":
                continue

            self.refData["pointLayer"].startEditing()

            # Zielfeature erzeugen
            rotFeature = QgsFeature(self.refData["pointLayer"].fields())

            # Geometrie in Kartenebene umrechnen
            rotateGeom = self.rotationCoords.rotatePointFeature(feature, aar_direction)

            # Zielpunktgeometrie erzeugen und zum Zielfeature hinzufügen
            zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["y_trans"], rotateGeom["z_trans"])
            gZPoint = QgsGeometry(zPoint)
            rotFeature.setGeometry(gZPoint)

            rotFeature.setAttributes(feature.attributes())

            missing = True
            # Features aus Eingabelayer
            # schauen ob es schon existiert (anhand obj_uuid), wenn ja dann löschen und durch Zielfeature ersetzen
            sourceLayerFeatures = self.refData["pointLayer"].getFeatures()
            for sourceFeature in sourceLayerFeatures:
                if feature["obj_uuid"] == sourceFeature["obj_uuid"]:
                    pr.deleteFeatures([sourceFeature.id()])
                    pr.addFeatures([rotFeature])
                    missing = False
            if not missing:
                continue

            # wenn feature nicht vorhanden, neues feature im Layer anlegen

            # use default values for fid from actual project layer
            # as self.digiLineLayer has no defaultValueDefinitions aka expressions
            # formula for fid: if (count("fid") = 0, 0, maximum("fid") + 1)
            field_default_value = proj_layer.defaultValue(proj_layer.fields().indexFromName("fid"))
            rotFeature.setAttribute("fid", field_default_value)

            retObj = pr.addFeatures([rotFeature])
            self.refData["pointLayer"].removeSelection()
            self.refData["pointLayer"].commitChanges()
            self.refData["pointLayer"].updateExtents()
            self.refData["pointLayer"].endEditCommand()

            # update feature attribute in digiLineLayer
            self.digiPointLayer.startEditing()
            self.digiPointLayer.changeAttributeValue(
                feature.id(),
                self.digiPointLayer.fields().indexFromName("fid"),
                field_default_value
            )
            print("commitChanges", self.digiPointLayer.commitChanges())
            self.digiPointLayer.endEditCommand()

            # update table fid
            dataObj = {}
            for item in proj_layer.fields():
                if item.name() == "obj_uuid" or item.name() == "fid":
                    dataObj[item.name()] = rotFeature[item.name()]
            self.pup.publish("updateFeatureAttr", dataObj)

    def removeFeatureInEingabelayerByUuid(self, obj_uuid):
        features = self.refData["pointLayer"].getFeatures()

        for feature in features:
            if feature["obj_uuid"] == obj_uuid:
                if feature["geo_quelle"] == "profile_object":
                    self.refData["pointLayer"].startEditing()
                    self.refData["pointLayer"].deleteFeature(feature.id())
                    print("commitChanges", self.refData["pointLayer"].commitChanges())

        self.digi_layer_changed.emit()
