from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot
from qgis.core import QgsFeature, QgsGeometry, QgsFeatureRequest, QgsMessageLog, Qgis, QgsProject
from qgis.gui import QgsAttributeDialog, QgsAttributeEditorContext

from .map_tools import PolygonMapTool
from .maptool_mixin import MapToolMixin
from ..publisher import Publisher


class MapToolDigiPolygon(PolygonMapTool, MapToolMixin):
    # darf nicht in den Konstruktor:
    digi_layer_changed = pyqtSignal()

    def __init__(self, canvas, iFace, rotationCoords, dataStoreDigitize):
        self.canvas = canvas
        self.iface = iFace
        self.rotationCoords = rotationCoords
        self.dataStoreDigitize = dataStoreDigitize
        self.pup = Publisher()
        self.digiPolygonLayer = None
        self.featGeometry = None
        self.feat = None
        self.dialogAttributes = None
        self.refData = None
        PolygonMapTool.__init__(self, self.canvas)
        self.finished_geometry.connect(self.got_geometry)

    def setDigiPolygonLayer(self, digiPolygonLayer):
        self.digiPolygonLayer = digiPolygonLayer

    def update(self, refData):
        self.refData = refData

    def got_geometry(self, geometry):
        self.featGeometry = geometry
        if self.featGeometry.isNull():
            return

        if self.feat and self.feat.hasGeometry():
            self.feat.setGeometry(self.featGeometry)
            self.digiPolygonLayer.startEditing()
            self.digiPolygonLayer.addFeature(self.feat)
            self.digiPolygonLayer.commitChanges()
            self.digiPolygonLayer.endEditCommand()
            self.clear_map_tool()
        else:
            self.showdialog()

        self.digi_layer_changed.emit()

    @pyqtSlot(QgsFeature)
    def set_feature_for_editing(self, feature):
        self.feat = feature
        self.set_geometry_for_editing(feature.geometry())
        self.digiPolygonLayer.startEditing()
        self.digiPolygonLayer.deleteFeature(feature.id())
        self.digiPolygonLayer.commitChanges()
        self.digiPolygonLayer.endEditCommand()
        self.canvas.setMapTool(self)

    def clear_map_tool(self):
        self.reset_geometry()
        self.feat = None

    def createFeature(self):
        self.feat = QgsFeature()
        self.feat.setGeometry(self.featGeometry)

    def showdialog(self):
        self.createFeature()
        proj_layer = QgsProject.instance().mapLayersByName("E_Polygon")[0]

        self.feat.setFields(self.digiPolygonLayer.fields())

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

        self.digiPolygonLayer.startEditing()
        self.refData["polygonLayer"].startEditing()

        prof_nr = self.dataStoreDigitize.getProfileNumber()
        self.setPlaceholders(self.feat, prof_nr)

        self.dialogAttributes = QgsAttributeDialog(self.refData["polygonLayer"], self.feat, False, None)
        self.dialogAttributes.setMode(QgsAttributeEditorContext.FixAttributeMode)
        self.dialogAttributes.rejected.connect(self.closeAttributeDialog)
        self.dialogAttributes.accepted.connect(self.acceptedAttributeDialog)
        self.dialogAttributes.show()

    def closeAttributeDialog(self):
        self.clear_map_tool()
        self.refData["polygonLayer"].commitChanges()

    def acceptedAttributeDialog(self):
        self.refData["polygonLayer"].commitChanges()

        atrObj = self.dialogAttributes.feature().attributes()
        self.feat.setAttributes(atrObj)

        self.feat["geo_quelle"] = "profile_object"

        self.addFeature2Layer()

        dialogFeature = self.dialogAttributes.feature()

        # write to table
        self.writeToTable(self.feat.fields(), dialogFeature)

        self.digiPolygonLayer.updateExtents()
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

        dataObj["layer"] = self.refData["polygonLayer"].sourceName()

        self.pup.publish("polygonFeatureAttr", dataObj)

    def addFeature2Layer(self):
        pr = self.digiPolygonLayer.dataProvider()
        pr.addFeatures([self.feat])
        self.digiPolygonLayer.updateExtents()
        self.digiPolygonLayer.endEditCommand()

    def getFeaturesFromEingabelayer(self, bufferGeometry, geoType, aar_direction, no_buffer_profile_nr=None):
        self.digiPolygonLayer.startEditing()
        pr = self.digiPolygonLayer.dataProvider()

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = self.refData["polygonLayer"].getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:
            if no_buffer_profile_nr:
                if feature["prof_nr"] != no_buffer_profile_nr:
                    continue
            elif not feature.geometry().within(bufferGeometry):
                continue

            if geoType == "tachy" and feature["geo_quelle"] != "profile_object":
                rotFeature = QgsFeature(self.digiPolygonLayer.fields())
                rotateGeom = self.rotationCoords.rotatePolygonFeatureFromOrg(feature, aar_direction)
                rotFeature.setGeometry(rotateGeom)
                rotFeature.setAttributes(feature.attributes())
                selFeatures.append(rotFeature)

            elif geoType == "profile" and feature["geo_quelle"] == "profile_object":
                rotFeature = QgsFeature(self.digiPolygonLayer.fields())
                rotateGeom = self.rotationCoords.rotatePolygonFeatureFromOrg(feature, aar_direction)
                rotFeature.setGeometry(rotateGeom)
                rotFeature.setAttributes(feature.attributes())

                selFeatures.append(rotFeature)

                # write to table
                self.writeToTable(feature.fields(), feature)

        try:
            pr.addFeatures(selFeatures)
        except Exception as e:
            QgsMessageLog.logMessage(str(e), "T2G Archäologie", Qgis.Info)

        self.digiPolygonLayer.commitChanges()
        self.digiPolygonLayer.updateExtents()
        self.digiPolygonLayer.endEditCommand()

        self.digi_layer_changed.emit()

    def removeNoneProfileFeatures(self):
        self.digiPolygonLayer.startEditing()
        pr = self.digiPolygonLayer.dataProvider()
        features = self.digiPolygonLayer.getFeatures()

        removeFeatures = []
        for feature in features:
            if feature["geo_quelle"] != "profile_object":
                removeFeatures.append(feature.id())

        pr.deleteFeatures(removeFeatures)

        self.digiPolygonLayer.commitChanges()
        self.digiPolygonLayer.updateExtents()
        self.digiPolygonLayer.endEditCommand()

    # in den Eingabelayer schreiben
    def reverseRotation2Eingabelayer(self, layer_id, aar_direction):

        pr = self.refData["polygonLayer"].dataProvider()
        proj_layer = QgsProject.instance().mapLayersByName("E_Polygon")[0]

        features_to_write = self.digiPolygonLayer.getFeatures()

        for feature in features_to_write:

            if feature["geo_quelle"] != "profile_object":
                continue

            self.refData["polygonLayer"].startEditing()

            # Zielgeometrie erzeugen
            emptyTargetGeometry = QgsGeometry.fromMultiPolygonXY([])

            # Zielfeature erzeugen
            rotFeature = QgsFeature(self.refData["polygonLayer"].fields())

            # Geometrie in Kartenebene umrechnen
            rotateGeom = self.rotationCoords.rotatePolygonFeature(feature, emptyTargetGeometry, aar_direction)
            rotFeature.setGeometry(rotateGeom)
            rotFeature.setAttributes(feature.attributes())

            missing = True
            # Features aus Eingabelayer
            # schauen ob es schon existiert (anhand uuid), wenn ja dann löschen und durch Zielfeature ersetzen
            sourceLayerFeatures = self.refData["polygonLayer"].getFeatures()
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
            self.refData["polygonLayer"].removeSelection()
            self.refData["polygonLayer"].commitChanges()
            self.refData["polygonLayer"].updateExtents()
            self.refData["polygonLayer"].endEditCommand()

            # update feature attribute in digiLineLayer
            self.digiPolygonLayer.startEditing()
            self.digiPolygonLayer.changeAttributeValue(
                feature.id(),
                self.digiPolygonLayer.fields().indexFromName("fid"),
                field_default_value
            )
            print("commitChanges", self.digiPolygonLayer.commitChanges())
            self.digiPolygonLayer.endEditCommand()

            # update table fid
            dataObj = {}
            for item in proj_layer.fields():
                if item.name() == "obj_uuid" or item.name() == "fid":
                    dataObj[item.name()] = rotFeature[item.name()]
            self.pup.publish("updateFeatureAttr", dataObj)

    def removeFeatureInEingabelayerByUuid(self, uuid):
        features = self.refData["polygonLayer"].getFeatures()

        for feature in features:
            if feature["obj_uuid"] == uuid:
                if feature["geo_quelle"] == "profile_object":
                    self.refData["polygonLayer"].startEditing()
                    self.refData["polygonLayer"].deleteFeature(feature.id())
                    print("commitChanges", self.refData["polygonLayer"].commitChanges())

        self.digi_layer_changed.emit()
