import json
import os
import tempfile
from glob import glob
from shutil import rmtree

import processing
from PyQt5.QtCore import Qt
from osgeo import ogr
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsPointXY,
    QgsFeature,
    QgsField,
    QgsProject,
    QgsVectorLayer,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsPoint,
    QgsGeometry,
    QgsFeatureRequest,
    QgsVectorFileWriter,
)

from .data_store_plan import DataStorePlan
from ..rotation_coords import RotationCoords
from ...utils.functions import layers_not_in_edit_mode, set_vsi_cached, is_vsi_cached


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

        self.__dockwidget.check_profile_buffer.stateChanged.connect(self.handle_check_profile_buffer)
        self.handle_check_profile_buffer(Qt.Unchecked)

    def createConnects(self):

        self.dataStorePlan.pup.register("pushTransformationParams", self.rotationCoords.setAarTransformationParams)

    def handle_check_profile_buffer(self, state):
        visible_bool = state == Qt.Checked
        self.__dockwidget.profileBufferSpinBox.setVisible(visible_bool)
        self.__dockwidget.label_profileBuffer.setVisible(visible_bool)

    def __startPlanCreation(self):

        if not layers_not_in_edit_mode(["E_Point", "E_Line", "E_Polygon", "Messpunkte"]):
            self.__iface.messageBar().pushMessage(
                "Error", "Bitte den Editiermodus der Eingabelayer beenden.", level=1, duration=3
            )
            return

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
                "Hinweis",
                "Die Daten zum Plan wurden im Geopackage des Projektes in den (unregistrierten) Tabellen profildata_* abgelegt",
                level=3, duration=5
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

        if self.__dockwidget.check_profile_buffer.isChecked():
            profile_number = None
        else:
            profile_number = self.dataStorePlan.getProfileNumber()

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

        # needs to be this order for plan export
        spalten_reihenfolge = [
            "obj_uuid", "ptnr", "input_x", "input_z", "aar_x", "aar_z", "aar_z_org", "aar_distance", "aar_direction"
        ]
        for key in spalten_reihenfolge:
            value = gcpObj[0][key]

            if isinstance(value, str):
                attributes.append(QgsField(key, QVariant.String))

            if isinstance(value, float):
                attributes.append(QgsField(key, QVariant.Double))

        pr.addAttributes(attributes)
        gcpLayer.updateFields()

        # add features
        features = []
        for obj in gcpObj:
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(obj["aar_x"], obj["aar_z"])))
            feat.setAttributes([obj[key] for key in spalten_reihenfolge])
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
        was_vsi_cached = False
        if is_vsi_cached():
            was_vsi_cached = True
            set_vsi_cached(False)

        layer_name = f"profildata_{inputLayer.name()}"
        tmp_data_path = "no_tmp_data"

        # get geopackage used in project:
        data_provider_set = set()
        for project_layer in QgsProject.instance().mapLayers(validOnly=True).values():
            data_provider = project_layer.dataProvider().dataSourceUri().split("|")[0]
            if data_provider.lower().endswith(".gpkg"):
                data_provider_set.add(data_provider)
        geopackage_path = list(data_provider_set)[0]

        # get all layers of gpkg:
        geopackage_layers = []
        all_project_layer = QgsVectorLayer(geopackage_path, "", "ogr")
        if not all_project_layer.isValid():
            print("Failed to open GeoPackage")
            return
        for subLayerName in all_project_layer.dataProvider().subLayers():
            subLayerName = subLayerName.split("!!::!!")[1]  # Extract layer name
            geopackage_layers.append(subLayerName)

        # check if layer (maybe unregistered in project) already exists in gpkg:
        if layer_name in geopackage_layers:
            # save existing data:
            tmp_data_path = self.layer_from_gpkg_to_gpkg(layer_name, geopackage_path)
            if not tmp_data_path:
                print(f"ERROR saving tmp data")
                return

            # delete layer:
            ds = ogr.Open(geopackage_path, update=1)
            if ds is None:
                print(f"Could not open {geopackage_path}")
                return
            ds.DeleteLayer(layer_name)
            ds = None  # Close the datasource

        inputLayer.selectAll()
        temporary_layer = processing.run(
            "native:saveselectedfeatures",
            {"INPUT": inputLayer, "OUTPUT": "memory:"}
        )["OUTPUT"]

        temporary_layer.removeSelection()
        temporary_layer.startEditing()

        pr = temporary_layer.dataProvider()
        pr.truncate()  # Layer leeren

        # if inputLayer.name() == "gcp_points":
        #     print("### DEBUG: selFeatures")
        #     self.print_feature_list(selFeatures)
        pr.addFeatures(selFeatures)

        if inputLayer.name() == "gcp_points":
            pr.addAttributes([QgsField("prof_nr", QVariant.String, len=20)])
        else:
            pr.addAttributes([QgsField("aar_direction", QVariant.String, len=20)])

        temporary_layer.updateFields()

        # write values for new field in every feature:
        for feature in temporary_layer.getFeatures():
            feature["aar_direction"] = self.aar_direction
            if inputLayer.name() == "gcp_points":
                feature["prof_nr"] = self.prof_nr
            # else:
            #     print("### DEBUG: inputLayer.name()", inputLayer.name(), "is not gcp_points")
            temporary_layer.updateFeature(feature)

        if tmp_data_path and tmp_data_path != "no_tmp_data":
            self.__delete_profile_number(str(tmp_data_path), layer_name, self.prof_nr)

            # restoring existing data into temporary_layer:
            tmp_data_feature_list = self.layer_from_gpkg_to_feature_list(layer_name, tmp_data_path)
            if not isinstance(tmp_data_feature_list, list):
                print("ERROR restoring tmp data")
                return
            # if inputLayer.name() == "gcp_points":
            #     print("### DEBUG: tmp_data_feature_list")
            #     self.print_feature_list(tmp_data_feature_list)
            pr.addFeatures(tmp_data_feature_list)

        if inputLayer.name() != "gcp_points":
            features_list = [feature for feature in temporary_layer.getFeatures()]
            sorted_features = sorted(features_list, key=lambda f: f.attribute(0))
            pr.truncate()  # Layer leeren
            pr.addFeatures(sorted_features)

        temporary_layer.commitChanges()
        temporary_layer.updateExtents()
        temporary_layer.endEditCommand()

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.onlySelectedFeatures = False
        options.onlyAttributes = False
        options.layerName = layer_name
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

        QgsProject.instance().removeMapLayer(temporary_layer.id())

        if was_vsi_cached:
            set_vsi_cached(True)

    def __delete_profile_number(self, gpkg_path, layer_name, profile_number):
        layer = QgsVectorLayer(f"{gpkg_path}|layername={layer_name}", layer_name, "ogr")
        if not layer.isValid():
            print(
                f"__delete_profile_number({gpkg_path}, {layer_name}, {profile_number}) Layer failed to load! "
                f"Fehlerdetails: {layer.dataProvider().lastError()}"
            )
            return

        layer.startEditing()

        # (OLD gcp table has profil_nr) E_* tables have prof_nr
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
        layer = None

    def layer_from_gpkg_to_gpkg(self, layer_name, from_gpkg, to_gpkg=None):
        tmp_dir_prefix = "plan_data_temp_gpkg_"
        # cleanup last sessions
        pattern = os.path.join(tempfile.gettempdir(), f"{tmp_dir_prefix}*")
        for item in glob(pattern):
            if os.path.isdir(item):
                rmtree(item, ignore_errors=True)

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.onlySelectedFeatures = False
        options.onlyAttributes = False
        options.layerName = layer_name

        if to_gpkg:
            to_gpkg_path = to_gpkg
            options.actionOnExistingFile = QgsVectorFileWriter.AppendToLayerNoNewFields
        else:
            tmp_dir = tempfile.mkdtemp(prefix=tmp_dir_prefix)
            to_gpkg_path = os.path.join(tmp_dir, "temp_layer.gpkg")
            # options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile

        # Load the existing layer
        uri = f"{from_gpkg}|layername={layer_name}"
        from_layer = QgsVectorLayer(uri, layer_name, "ogr")

        if not from_layer.isValid():
            print(f"Layer {layer_name} not loaded.")
            return None

        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            from_layer,
            to_gpkg_path,
            QgsProject.instance().transformContext(),
            options
        )

        if error[0] != QgsVectorFileWriter.NoError:
            print(f"Error when writing vector layer to {to_gpkg_path}")
            print(error)
            return None

        print(f"Layer {layer_name} has been copied to {to_gpkg_path}")

        from_layer = None
        return to_gpkg_path

    def layer_from_gpkg_to_feature_list(self, layer_name, from_gpkg):
        layer = QgsVectorLayer(f"{from_gpkg}|layername={layer_name}", layer_name, "ogr")

        if not layer.isValid():
            print(f"layer_from_gpkg_to_feature_list() Layer failed to load! Fehlerdetails: {layer.dataProvider().lastError()}")
            return None

        if layer_name.endswith("gcp_points"):
            layer.startEditing()
            # Remove the first field
            layer.deleteAttribute(0)
            layer.updateFields()
            layer.commitChanges()
        # else:
        #     print("### DEBUG: layer_name", layer_name, "does not end with gcp_points")

        features_list = []
        for feature in layer.getFeatures():
            features_list.append(feature)

        layer = None
        return features_list

    def print_feature_list(self, features_list):
        # Assuming 'features' is your list of QgsFeature objects
        for feature in features_list:
            # Print feature ID
            print(f"Feature ID: {feature.id()}")

            # Print feature geometry
            geom = feature.geometry()
            print(f"Geometry: {geom.asWkt()}")

            # Print feature attributes
            attributes = feature.attributes()
            print("Attributes:")
            for i, attr in enumerate(attributes):
                print(f"  {i}: {attr}")

            # Print a separator for better readability
            print("---")
