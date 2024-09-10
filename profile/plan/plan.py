import json
import os

import processing
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsPointXY,
    QgsFeature,
    QgsField,
    QgsVectorFileWriter,
    QgsProject,
    QgsVectorLayer,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsPoint,
    QgsGeometry,
    QgsFeatureRequest, )

from .data_store_plan import DataStorePlan
from ..rotation_coords import RotationCoords


## @brief The class is used to implement functionalities for work with profile-plans within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2022-03-15
class Plan:

    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):
        print("init plan")
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace

        self.aar_direction = None
        self.prof_nr = None

        self.dataStorePlan = DataStorePlan()
        self.rotationCoords = RotationCoords()

        self.createConnects()

    ## @brief Initializes the functionality for profile modul
    #
    def setup(self):
        print("Setup plan")

        # set datatype filter to profileFotosComboGeoref
        self.__dockwidget.profilePlanSelect.setFilter("Images (*.jpg)")

        self.__dockwidget.startPlanBtn.clicked.connect(self.__startPlanCreation)

    def createConnects(self):

        self.dataStorePlan.pup.register("pushTransformationParams", self.rotationCoords.setAarTransformationParams)

    def __startPlanCreation(self):

        planData = self.__getSelectedValues()

        baseFilePath = planData["profilePath"][:-4]

        metaChecker = True
        try:
            self.__importMetaData(planData["profilePath"])

        except ValueError as err:
            metaChecker = False
            self.__iface.messageBar().pushMessage("Error", str(err.args[0]), level=1, duration=3)

        if metaChecker == True:
            self.dataStorePlan.triggerAarTransformationParams(self.aar_direction)

            refData = self.__getInputlayers(True)

            self.__exportPlanLayers(refData, baseFilePath)

            self.__iface.messageBar().pushMessage(
                "Hinweis", "Die Daten zum Plan wurden im Geopackage des Projektes in den (unregistrierten) Tabellen profildata_* abgelegt", level=3, duration=5
            )

            # self.layout.startLayout(planData)

    def __getSelectedValues(self):

        # Profilbild
        profilePath = self.__dockwidget.profilePlanSelect.filePath()

        planData = {"profilePath": profilePath}

        print("planData", planData)

        return planData

    def __importMetaData(self, profilePath):

        metaFileName = profilePath[:-3]
        metaFileName = metaFileName + "meta"

        if os.path.isfile(metaFileName):

            with open(metaFileName) as json_file:
                data = json.load(json_file)

                if (
                    data["aar_direction"] == "horizontal"
                    or data["aar_direction"] == "absolute height"
                    or data["aar_direction"] == "original"
                ):

                    self.dataStorePlan.addProfileNumber(data["profilnummer"])
                    self.dataStorePlan.addProfile(data["profil"])
                    self.dataStorePlan.addProfileFoto(data["profilfoto"])
                    self.dataStorePlan.addView(data["blickrichtung"])
                    self.dataStorePlan.addEntzerrungsebene(data["entzerrungsebene"])
                    self.dataStorePlan.addGcps(data["gcps"])
                    self.dataStorePlan.addTransformParams(data["transform_params"])

                    self.aar_direction = data["aar_direction"]
                    self.prof_nr = data["profilnummer"]

                else:
                    raise ValueError("AAR direction muss horizontal, absolute height oder original sein!")

        else:
            raise ValueError("Keine .meta Datei zum Profil vorhanden!")

    ## \brief Get all inputlayers from the folder "Eingabelayer" of the layertree
    #
    # Inputlayers must be of type vector
    #
    # \param isClone - should the return a copy of the layers or just a pointer to the layers
    # @returns Array of inputlayers
    def __getInputlayers(self, isClone):

        inputLayers = []
        root = QgsProject.instance().layerTreeRoot()

        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup) and group.name() == "Eingabelayer":
                for child in group.children():
                    if isinstance(child, QgsLayerTreeLayer):
                        if isClone == True:

                            if isinstance(child.layer(), QgsVectorLayer):
                                inputLayers.append(child.layer().clone())
                        else:
                            if isinstance(child.layer(), QgsVectorLayer):
                                inputLayers.append(child.layer())

        refData = {}

        for layer in inputLayers:

            if layer.name() == "E_Point":
                refData["pointLayer"] = layer.clone()

            if layer.name() == "E_Line":
                refData["lineLayer"] = layer.clone()

            if layer.name() == "E_Polygon":
                refData["polygonLayer"] = layer.clone()

        return refData

    def __exportPlanLayers(self, refData, baseFilePath):

        # Flexible buffersize from gui
        bufferGeometry = self.rotationCoords.profileBuffer(
            self.__dockwidget.profileBufferSpinBox.value(), self.aar_direction
        )
        # epsg from pointLayer - Todo search better solution (from meta file)
        epsgCode = refData["pointLayer"].crs().authid()

        if self.__dockwidget.radioProfilePlanNumber.isChecked():
            profile_number = self.dataStorePlan.getProfileNumber()
        else:
            profile_number = None

        # Punktlayer schreiben
        selFeaturesPoint = self.__getPointFeaturesFromEingabelayer(
            refData["pointLayer"], bufferGeometry, "profile", profile_number
        )
        self.__writeLayer(refData["pointLayer"], selFeaturesPoint, baseFilePath, "point")

        # Linelayer schreiben
        selFeaturesLine = self.__getLineFeaturesFromEingabelayer(
            refData["lineLayer"], bufferGeometry, "profile", profile_number
        )
        self.__writeLayer(refData["lineLayer"], selFeaturesLine, baseFilePath, "line")

        # Polygonlayer schreiben
        selFeaturesPolygon = self.__getPolygonFeaturesFromEingabelayer(
            refData["polygonLayer"], bufferGeometry, "profile", profile_number
        )
        self.__writeLayer(refData["polygonLayer"], selFeaturesPolygon, baseFilePath, "polygon")

        # GCP Layer schreiben
        gcpLayer, selFeatures = self.__getGcpLayer(epsgCode)
        self.__writeLayer(gcpLayer, selFeatures, baseFilePath, "gcp")

    def __getPointFeaturesFromEingabelayer(self, pointLayer, bufferGeometry, geoType, profile_number=None):
        if geoType != "profile":
            return []

        if profile_number:
            featsSel = pointLayer.getFeatures()
        else:
            bbox = bufferGeometry.boundingBox()
            req = QgsFeatureRequest()
            filterRect = req.setFilterRect(bbox)
            featsSel = pointLayer.getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:
            if feature["geo_quelle"] != "profile_object":
                continue

            if (
                    (profile_number and feature["prof_nr"] == profile_number) or
                    (not profile_number and feature.geometry().within(bufferGeometry))
            ):
                rotFeature = QgsFeature(pointLayer.fields())

                rotateGeom = self.rotationCoords.rotatePointFeatureFromOrg(feature, self.aar_direction)
                zPoint = QgsPoint(rotateGeom["x_trans"], rotateGeom["z_trans"], rotateGeom["z_trans"])
                gZPoint = QgsGeometry(zPoint)
                rotFeature.setGeometry(gZPoint)
                rotFeature.setAttributes(feature.attributes())

                selFeatures.append(rotFeature)

        return selFeatures

    def __getLineFeaturesFromEingabelayer(self, lineLayer, bufferGeometry, geoType, profile_number=None):
        if geoType != "profile":
            return []

        if profile_number:
            featsSel = lineLayer.getFeatures()
        else:
            bbox = bufferGeometry.boundingBox()
            req = QgsFeatureRequest()
            filterRect = req.setFilterRect(bbox)
            featsSel = lineLayer.getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:
            if feature["geo_quelle"] != "profile_object":
                continue

            if (
                    (profile_number and feature["prof_nr"] == profile_number) or
                    (not profile_number and feature.geometry().within(bufferGeometry))
            ):
                rotFeature = QgsFeature(lineLayer.fields())

                rotateGeom = self.rotationCoords.rotateLineFeatureFromOrg(feature, self.aar_direction)
                rotFeature.setGeometry(rotateGeom)
                rotFeature.setAttributes(feature.attributes())

                selFeatures.append(rotFeature)

        return selFeatures

    def __getPolygonFeaturesFromEingabelayer(self, polygonLayer, bufferGeometry, geoType, profile_number=None):
        if geoType != "profile":
            return []

        if profile_number:
            featsSel = polygonLayer.getFeatures()
        else:
            bbox = bufferGeometry.boundingBox()
            req = QgsFeatureRequest()
            filterRect = req.setFilterRect(bbox)
            featsSel = polygonLayer.getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:
            if feature["geo_quelle"] != "profile_object":
                continue

            if (
                    (profile_number and feature["prof_nr"] == profile_number) or
                    (not profile_number and feature.geometry().within(bufferGeometry))
            ):

                rotFeature = QgsFeature(polygonLayer.fields())

                rotateGeom = self.rotationCoords.rotatePolygonFeatureFromOrg(feature, self.aar_direction)
                rotFeature.setGeometry(rotateGeom)
                rotFeature.setAttributes(feature.attributes())

                selFeatures.append(rotFeature)

        return selFeatures

    def __getGcpLayer(self, epsgCode):

        gcpObj = self.dataStorePlan.getGcps()

        # create layer

        gcpLayer = QgsVectorLayer("point?crs=" + epsgCode, "gcp_points", "memory")
        gcpLayer.startEditing()
        pr = gcpLayer.dataProvider()

        # add attributes

        attributes = []

        for key, value in gcpObj[0].items():

            if key != "aar_y":

                if isinstance(value, str):
                    attributes.append(QgsField(key, QVariant.String))

                if isinstance(value, float):
                    attributes.append(QgsField(key, QVariant.Double))

        pr.addAttributes(attributes)
        gcpLayer.updateFields()

        # add features
        features = []
        for item in gcpObj:

            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(item["aar_x"], item["aar_z"])))

            attributesFeat = []

            for key, value in item.items():
                if key != "aar_y":
                    attributesFeat.append(value)

            feat.setAttributes(attributesFeat)
            features.append(feat)

        pr.addFeatures(features)

        # Rename fields
        for field in gcpLayer.fields():
            if field.name() == "aar_x":
                gcpLayer.startEditing()
                idx = gcpLayer.fields().indexFromName(field.name())
                gcpLayer.renameAttribute(idx, "x_orig")
                gcpLayer.commitChanges()

            if field.name() == "aar_z":
                gcpLayer.startEditing()
                idx = gcpLayer.fields().indexFromName(field.name())
                gcpLayer.renameAttribute(idx, "y_orig")
                gcpLayer.commitChanges()

            if field.name() == "aar_z_org":
                gcpLayer.startEditing()
                idx = gcpLayer.fields().indexFromName(field.name())
                gcpLayer.renameAttribute(idx, "z_orig")
                gcpLayer.commitChanges()

        gcpLayer.updateFields()
        gcpLayer.updateExtents()
        gcpLayer.endEditCommand()

        return gcpLayer, features

    def __writeLayer(self, inputLayer, selFeatures, baseFilePath, layerType):
        layer_name = f"profildata_{inputLayer.name()}"

        inputLayer.selectAll()
        temporary_layer = processing.run(
            "native:saveselectedfeatures",
            {"INPUT": inputLayer, "OUTPUT": "memory:"}
        )["OUTPUT"]

        temporary_layer.removeSelection()
        temporary_layer.startEditing()

        # Layer leeren
        pr = temporary_layer.dataProvider()
        pr.truncate()
        pr.addFeatures(selFeatures)

        # add field to layer:
        pr.addAttributes([QgsField('aar_direction', QVariant.String, len=20)])
        if inputLayer.name() == "gcp_points":
            pr.addAttributes([QgsField('profil_nr', QVariant.String, len=20)])
        temporary_layer.updateFields()

        # write values for new field in every feature:
        for f in temporary_layer.getFeatures():
            f['aar_direction'] = self.aar_direction
            if inputLayer.name() == "gcp_points":
                f['profil_nr'] = self.prof_nr
            temporary_layer.updateFeature(f)

        temporary_layer.commitChanges()
        temporary_layer.updateExtents()
        temporary_layer.endEditCommand()

        # get geopackage used in project:
        data_provider_set = set()
        for layer in QgsProject.instance().mapLayers(validOnly=True).values():
            data_provider = layer.dataProvider().dataSourceUri().split("|")[0]
            if data_provider.lower().endswith(".gpkg"):
                data_provider_set.add(data_provider)
        geopackage_path = list(data_provider_set)[0]

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.onlySelectedFeatures = False
        options.onlyAttributes = False
        options.layerName = layer_name

        # check if layer (maybe unregistered in project) already exists in gpkg:
        geopackage_layers = []
        layer = QgsVectorLayer(geopackage_path, '', 'ogr')
        if layer.isValid():
            for subLayerName in layer.dataProvider().subLayers():
                subLayerName = subLayerName.split('!!::!!')[1]  # Extract layer name
                geopackage_layers.append(subLayerName)
        else:
            print("Failed to open GeoPackage")
            return
        if layer_name in geopackage_layers:
            print(f"layer {layer_name} already exists: AppendToLayerNoNewFields")
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
            self.__delete_profile_number(str(geopackage_path), layer_name, self.prof_nr)
        else:
            print(f"create layer {layer_name}: CreateOrOverwriteLayer")
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            temporary_layer,
            str(geopackage_path),
            QgsProject.instance().transformContext(),
            options
        )

        print(error, "temporary_layer is written to:", geopackage_path)
        if error[0] == 7:
            print(
                "MÖGLICHE LÖSUNG für unique table name nach manuellem Löschen der Tabellen: "
                "lösche auch Referenzen in gpkg_*-Tabellen!"
            )

    def __delete_profile_number(self, gpkg_path, layer_name, profile_number):
        layer = QgsVectorLayer(f"{gpkg_path}|layername={layer_name}", layer_name, "ogr")
        if not layer.isValid():
            print(f"__delete_profile_number({gpkg_path}, {layer_name}, {profile_number}) Layer failed to load!")
            return

        layer.startEditing()

        # gcp table has profil_nr and E_* tables have prof_nr
        filter_expression = f"profil_nr = '{profile_number}' OR prof_nr = '{profile_number}'"
        request = QgsFeatureRequest().setFilterExpression(filter_expression)
        features = layer.getFeatures(request)

        feature_ids = [feature.id() for feature in features]
        if not feature_ids:
            print(f"__delete_profile_number({gpkg_path}, {layer_name}, {profile_number}) No features matched the filter.")
            return

        if layer.deleteFeatures(feature_ids):
            print(f"__delete_profile_number({gpkg_path}, {layer_name}, {profile_number}) Features deleted successfully.")
        else:
            print(f"__delete_profile_number({gpkg_path}, {layer_name}, {profile_number}) Failed to delete features.")

        layer.commitChanges()
