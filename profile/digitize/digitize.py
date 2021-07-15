## @package QGIS geoEdit extension..
import shutil
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsApplication, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsRectangle, QgsVectorFileWriter
from processing.gui import AlgorithmExecutor
from qgis import processing

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

    ## @brief Initializes the functionality for profile modul
    #

    def setup(self):

        #set datatype filter to profileFotosComboGeoref
        self.__dockwidget.profileDigitize.setFilter('Images (*.tif)')
        #Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        self.__preselectionPointLayer()
        self.__preselectionLineLayer()
        self.__preselectionPolygonLayer()

        self.__dockwidget.startDigitizeBtn.clicked.connect(self.__startDigitizeDialog)

        self.digitizeDialog = DigitizeDialog(self)



    ## \brief Start digitize dialog
    #
    #
    def __startDigitizeDialog(self):

        refData = self.__getSelectedValues()

        print('refData', refData)
        self.digitizeDialog.showDigitizeDialog(refData)


    ## \brief get selected values
    #
    #
    def __getSelectedValues(self):

        #DigitizeLayers
        pointLayer = self.__dockwidget.pointLayerDigitize.currentLayer().clone()
        lineLayer = self.__dockwidget.lineLayerDigitize.currentLayer().clone()
        polygonLayer = self.__dockwidget.polygonLayerDigitize.currentLayer().clone()

        #Foto
        profilePath = self.__dockwidget.profileDigitize.filePath()

        refData = {'pointLayer': pointLayer, 'lineLayer': lineLayer, 'polygonLayer': polygonLayer, 'profilePath': profilePath}

        return refData

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
