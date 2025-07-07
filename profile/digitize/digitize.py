## @package QGIS geoEdit extension..
import json
import os

from qgis.core import QgsProject, QgsVectorLayer, QgsLayerTreeGroup, QgsLayerTreeLayer
from qgis.utils import iface

from .data_store_digitize import DataStoreDigitize
from .digitize_dialog import DigitizeDialog
from ...utils.functions import layers_not_in_edit_mode


## @brief The class is used to implement functionalities for work with profiles within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-05-07
class Digitize:

    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace, rotationCoords):

        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace

        self.digitizeDialog = None

        self.dataStoreDigitize = DataStoreDigitize()
        self.rotationCoords = rotationCoords

        self.aar_direction = None

    def setup(self):

        # set datatype filter to profileFotosComboGeoref
        self.__dockwidget.profileDigitize.setFilter("Images (*.jpg)")
        # Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        self.__preselectionPointLayer()
        self.__preselectionLineLayer()
        self.__preselectionPolygonLayer()

        self.__dockwidget.startDigitizeBtn.clicked.connect(self.__startDigitizeDialog)

    def __startDigitizeDialog(self):

        if not layers_not_in_edit_mode(["E_Point", "E_Line", "E_Polygon", "Messpunkte"]):
            iface.messageBar().pushMessage(
                "Error", "Bitte den Editiermodus der Eingabelayer beenden.", level=1, duration=3
            )
            return

        refData = self.__getSelectedValues()

        if refData != "error":

            metaChecker = True
            try:
                self.__importMetaData(refData["profilePath"])

            except ValueError as err:
                metaChecker = False
                self.__iface.messageBar().pushMessage("Error", str(err.args[0]), level=1, duration=3)

            if metaChecker == True:

                if self.digitizeDialog and self.digitizeDialog.isVisible():
                    self.digitizeDialog.close()

                self.digitizeDialog = DigitizeDialog(
                    self.dataStoreDigitize, self.rotationCoords, self.__iface, self.aar_direction
                )
                self.dataStoreDigitize.triggerAarTransformationParams(self.aar_direction)
                self.digitizeDialog.showDigitizeDialog(refData, self.dataStoreDigitize.getProfileNumber())

    ## \brief get meta data to profile
    #
    #
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

                    self.dataStoreDigitize.addProfileNumber(data["profilnummer"])
                    self.dataStoreDigitize.addProfile(data["profil"])
                    self.dataStoreDigitize.addProfileFoto(data["profilfoto"])
                    self.dataStoreDigitize.addView(data["blickrichtung"])
                    self.dataStoreDigitize.addEntzerrungsebene(data["entzerrungsebene"])
                    self.dataStoreDigitize.addGcps(data["gcps"])
                    self.dataStoreDigitize.addTransformParams(data["transform_params"])

                    self.aar_direction = data["aar_direction"]

                else:
                    raise ValueError("AAR direction muss horizontal, absolute height oder original sein!")

        else:
            raise ValueError("Keine .meta Datei zum Profil vorhanden!")

    def __validateInputLayers(self, layerArray):

        errorArray = []

        for layer in layerArray:
            checkerGeoQuelle = False

            fieldNames = layer.fields().names()

            for name in fieldNames:
                if name == "geo_quelle":
                    checkerGeoQuelle = True

            if checkerGeoQuelle == False:
                errorArray.append({"error": True, "layer": layer.name()})
                self.__iface.messageBar().pushMessage(
                    "Error", "Im Layer " + layer.name() + " fehlt die Spalte 'geo_quelle'", level=1, duration=5
                )

        return errorArray

    ## \brief get selected values
    #
    #
    def __getSelectedValues(self):

        # DigitizeLayers
        pointLayer = self.__dockwidget.pointLayerDigitize.currentLayer().clone()
        lineLayer = self.__dockwidget.lineLayerDigitize.currentLayer().clone()
        polygonLayer = self.__dockwidget.polygonLayerDigitize.currentLayer().clone()

        layerArray = [pointLayer, lineLayer, polygonLayer]
        errorArray = self.__validateInputLayers(layerArray)

        if len(errorArray) == 0:
            # Foto
            profilePath = self.__dockwidget.profileDigitize.filePath()

            refData = {
                "pointLayer": pointLayer,
                "lineLayer": lineLayer,
                "polygonLayer": polygonLayer,
                "profilePath": profilePath,
            }

            return refData
        else:
            return "error"

    ## \brief Preselection of Point-Inputlayers
    #
    # If layer E_Point exists then preselect this
    def __preselectionPointLayer(self):

        notInputLayers = self.__getNotInputlayers(0)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.pointLayerDigitize.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == "E_Point":
                self.__dockwidget.pointLayerDigitize.setLayer(layer)

    ## \brief Preselection of Line-Inputlayers
    #
    # If layer E_Line exists then preselect this
    def __preselectionLineLayer(self):

        notInputLayers = self.__getNotInputlayers(1)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.lineLayerDigitize.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == "E_Line":
                self.__dockwidget.lineLayerDigitize.setLayer(layer)

    ## \brief Preselection of Point-Inputlayers
    #
    # If layer E_Point exists then preselect this
    def __preselectionPolygonLayer(self):

        notInputLayers = self.__getNotInputlayers(2)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.polygonLayerDigitize.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == "E_Polygon":
                self.__dockwidget.polygonLayerDigitize.setLayer(layer)

    ## \brief Get all layers from the layertree exept those from the folder "Eingabelayer"
    #
    # layers must be of type vectorlayer
    # geomType could be 0 - 'point', 1 - 'line', 2 - 'polygon', 'all'
    def __getNotInputlayers(self, geomType):

        allLayers = QgsProject.instance().mapLayers().values()

        inputLayer = []
        notInputLayer = []
        root = QgsProject.instance().layerTreeRoot()

        for group in root.children():
            if isinstance(group, QgsLayerTreeGroup) and group.name() == "Eingabelayer":
                for child in group.children():
                    if isinstance(child, QgsLayerTreeLayer):
                        if isinstance(child.layer(), QgsVectorLayer):
                            if geomType == 0 or geomType == 1 or geomType == 2:
                                if child.layer().geometryType() == geomType:
                                    inputLayer.append(child.layer())
                            if geomType == "all":
                                inputLayer.append(child.layer())

        for layerA in allLayers:
            check = False
            for layerIn in inputLayer:
                if layerA == layerIn:
                    check = True

            if check == False:
                notInputLayer.append(layerA)

        return notInputLayer

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

        return inputLayers
