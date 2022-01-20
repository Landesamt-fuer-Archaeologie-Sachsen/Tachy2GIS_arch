## @package QGIS geoEdit extension..
import shutil
import os
import json

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsApplication, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsRectangle, QgsVectorFileWriter
from processing.gui import AlgorithmExecutor
from qgis import processing

from .data_store_digitize import DataStoreDigitize
from .digitize_dialog import DigitizeDialog


## @brief The class is used to implement functionalities for work with profiles within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-05-07
class Digitize():

    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):

        self.__iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace

        self.dataStoreDigitize = DataStoreDigitize()

    ## @brief Initializes the functionality for profile modul
    #

    def setup(self):

        #set datatype filter to profileFotosComboGeoref
        self.__dockwidget.profileDigitize.setFilter('Images (*.jpg)')
        #Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        self.__preselectionPointLayer()
        self.__preselectionLineLayer()
        self.__preselectionPolygonLayer()

        self.__dockwidget.startDigitizeBtn.clicked.connect(self.__startDigitizeDialog)

    ## \brief Start digitize dialog
    #
    #
    def __startDigitizeDialog(self):

        refData = self.__getSelectedValues()

        if refData != 'error':

            metaChecker = True
            try:
                self.__importMetaData(refData['profilePath'])

            except:
                metaChecker = False
                self.__iface.messageBar().pushMessage("Error", "Keine .meta Datei zum Profil vorhanden!", level=1, duration=3)

            if metaChecker == True:

                self.digitizeDialog = DigitizeDialog(self.dataStoreDigitize, self.__iface)

                self.dataStoreDigitize.triggerAarTransformationParams()

                self.digitizeDialog.showDigitizeDialog(refData)

    ## \brief get meta data to profile
    #
    #
    def __importMetaData(self, profilePath):

        metaFileName = profilePath[:-3]
        metaFileName = metaFileName + 'meta'
        print('metaFileName', metaFileName)

        with open(metaFileName) as json_file:
            data = json.load(json_file)

            self.dataStoreDigitize.addProfileNumber(data['profilnummer'])
            self.dataStoreDigitize.addProfile(data['profil'])
            self.dataStoreDigitize.addProfileFoto(data['profilfoto'])
            self.dataStoreDigitize.addView(data['blickrichtung'])
            self.dataStoreDigitize.addEntzerrungsebene(data['entzerrungsebene'])
            self.dataStoreDigitize.addGcps(data['gcps'])
            self.dataStoreDigitize.addTransformParams(data['transform_params'])



    def __validateInputLayers(self, layerArray):

        errorArray = []

        for layer in layerArray:
            checkerGeoQuelle = False

            fieldNames = layer.fields().names()

            for name in fieldNames:
                if name == 'geo_quelle':
                    checkerGeoQuelle = True

            if checkerGeoQuelle == False:
                errorArray.append({'error': True, 'layer': layer.name()})
                self.__iface.messageBar().pushMessage("Error", "Im Layer "+layer.name() + " fehlt die Spalte 'geo_quelle'", level=1, duration=5)

        return errorArray


    ## \brief get selected values
    #
    #
    def __getSelectedValues(self):

        #DigitizeLayers
        pointLayer = self.__dockwidget.pointLayerDigitize.currentLayer().clone()
        lineLayer = self.__dockwidget.lineLayerDigitize.currentLayer().clone()
        polygonLayer = self.__dockwidget.polygonLayerDigitize.currentLayer().clone()

        layerArray = [pointLayer, lineLayer, polygonLayer]
        errorArray = self.__validateInputLayers(layerArray)

        if len(errorArray) == 0:
            #Foto
            profilePath = self.__dockwidget.profileDigitize.filePath()

            refData = {'pointLayer': pointLayer, 'lineLayer': lineLayer, 'polygonLayer': polygonLayer, 'profilePath': profilePath}

            return refData
        else:
        	return 'error'



    ## \brief Preselection of Point-Inputlayers
    #
    # If layer E_Point exists then preselect this
    def __preselectionPointLayer(self):

        notInputLayers = self.__getNotInputlayers(0)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.pointLayerDigitize.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == 'E_Point':
                self.__dockwidget.pointLayerDigitize.setLayer(layer)


    ## \brief Preselection of Line-Inputlayers
    #
    # If layer E_Line exists then preselect this
    def __preselectionLineLayer(self):

        notInputLayers = self.__getNotInputlayers(1)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.lineLayerDigitize.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == 'E_Line':
                self.__dockwidget.lineLayerDigitize.setLayer(layer)


    ## \brief Preselection of Point-Inputlayers
    #
    # If layer E_Point exists then preselect this
    def __preselectionPolygonLayer(self):

        notInputLayers = self.__getNotInputlayers(2)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.polygonLayerDigitize.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == 'E_Polygon':
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
            if isinstance(group, QgsLayerTreeGroup) and group.name() == 'Eingabelayer':
                for child in group.children():
                    if isinstance(child, QgsLayerTreeLayer):
                        if isinstance(child.layer(), QgsVectorLayer):
                            if (geomType == 0 or geomType == 1 or geomType == 2):
                                if child.layer().geometryType() == geomType:
                                    inputLayer.append(child.layer())
                            if geomType == 'all':
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
            if isinstance(group, QgsLayerTreeGroup) and group.name() == 'Eingabelayer':
                 for child in group.children():
                     if isinstance(child, QgsLayerTreeLayer):
                         if isClone == True:

                             if isinstance(child.layer(), QgsVectorLayer):
                                 inputLayers.append(child.layer().clone())
                         else:
                             if isinstance(child.layer(), QgsVectorLayer):
                                 inputLayers.append(child.layer())

        return inputLayers
