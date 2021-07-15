## @package QGIS geoEdit extension..
import shutil
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsApplication, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsRectangle, QgsVectorFileWriter
from processing.gui import AlgorithmExecutor
from qgis import processing

from .georeferencing_dialog import GeoreferencingDialog

## @brief The class is used to implement functionalities for work with profiles within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-05-07
class Georef():

    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):

        self.__iconpath = os.path.join(os.path.dirname(__file__), 'Icons')
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace

        self.georeferencingDialog = GeoreferencingDialog(self)

    ## @brief Initializes the functionality for profile modul
    #

    def setup(self):

        #Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        preselectedLineLayer = self.__preselectionProfileLayer()
        #Preselection profilenumber
        self.__preselectProfileNumbers(preselectedLineLayer)
        #Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        self.__preselectionGcpLayer()
        #set datatype filter to profileFotosComboGeoref
        self.__dockwidget.profileFotosComboGeoref.setFilter('Images (*.png *.JPG *.jpg *.jpeg *.tif)')
        #Preselection View direction
        self.__preselectViewDirection()
        #set datatype filter and save mode to profileSaveComboGeoref
        self.__dockwidget.profileSaveComboGeoref.setFilter('Images (*.tif)')
        self.__dockwidget.profileSaveComboGeoref.setStorageMode(3)

        self.__dockwidget.startGeoreferencingBtn.clicked.connect(self.__startGeoreferencingDialog)


    ## \brief Start georeferencing dialog
    #
    #
    def __startGeoreferencingDialog(self):

        refData = self.__getSelectedValues()

        print('refData', refData)
        self.georeferencingDialog.showGeoreferencingDialog(refData)


    ## \brief get selected values
    #
    #
    def __getSelectedValues(self):

        #lineLayer
        lineLayer = self.__dockwidget.layerProfileGeoref.currentLayer().clone()

        #Profilnummer
        profileNumber = self.__dockwidget.profileIdsComboGeoref.currentText()

        #pointLayer
        pointLayer = self.__dockwidget.layerGcpGeoref.currentLayer().clone()
        pointLayer.setSubsetString("obj_type = 'Fotoentzerrpunkt' and obj_art = 'Profil' and prof_nr = '"+profileNumber+"'")

        #Zielkoordinaten
        targetGCP = {}
        targetGCP['points'] = []

        for feature in pointLayer.getFeatures():

            g = feature.geometry()

            pointObj = {'uuid': feature.attribute("uuid"), 'ptnr': feature.attribute("ptnr"), 'id': feature.attribute("id"), 'x': float(g.get().x()), 'y': float(g.get().y()), 'z': float(g.get().z())}

            targetGCP['points'].append(pointObj)

        #Foto
        imagePath = self.__dockwidget.profileFotosComboGeoref.filePath()
        #Blickrichtung
        viewDirLong = self.__dockwidget.profileViewDirectionComboGeoref.currentText()

        if viewDirLong == 'Nord':
            viewDirection = 'N'
        if viewDirLong == 'Ost':
            viewDirection = 'E'
        if viewDirLong == 'Süd':
            viewDirection = 'S'
        if viewDirLong == 'West':
            viewDirection = 'W'
        #horizontal true/false
        horizontalCheck = self.__dockwidget.radioDirectionHorizontal.isChecked()
        #Speichern unter
        savePath = self.__dockwidget.profileSaveComboGeoref.filePath()
        #Metadaten
        metadataCheck = self.__dockwidget.metaProfileCheckbox.isChecked()

        refData = {'lineLayer': lineLayer, 'pointLayer': pointLayer, 'profileNumber': profileNumber, 'imagePath': imagePath, 'viewDirection': viewDirection, 'horizontal': horizontalCheck, 'savePath': savePath, 'saveMetadata': metadataCheck, 'targetGCP': targetGCP}

        return refData

    ## \brief Preselection of __preselectViewDirection
    #
    #
    def __preselectViewDirection(self):

        self.__dockwidget.profileViewDirectionComboGeoref.addItems(['Nord', 'Ost', 'Süd', 'West'])

    ## \brief Preselection of __preselectProfileNumbers
    #
    #  @param lineLayer
    def __preselectProfileNumbers(self, lineLayer):
        profileList = self.__getProfileNumbers(lineLayer)

        self.__dockwidget.profileIdsComboGeoref.addItems(profileList)

    ## \brief Preselection of __getProfileNumbers
    #
    #  @param lineLayer
    # @returns list of profile id's
    def __getProfileNumbers(self, lineLayer):

        profileList = []
        for feat in lineLayer.getFeatures():
            if feat.attribute('Objekttyp') == 'Profil':
                if feat.attribute('prof_nr'):
                    profileList.append(feat.attribute('prof_nr'))

        return sorted(profileList, key=str.lower)

    ## \brief Preselection of Inputlayers
    #
    # If layer E_Point exists then preselect this
    def __preselectionGcpLayer(self):

        notInputLayers = self.__getNotInputlayers(0)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.layerGcpGeoref.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == 'E_Point':
                self.__dockwidget.layerGcpGeoref.setLayer(layer)


    ## \brief Preselection of Inputlayers
    #
    # If layer E_Line exists then preselect this
    def __preselectionProfileLayer(self):

        notInputLayers = self.__getNotInputlayers(1)
        inputLayers = self.__getInputlayers(False)

        self.__dockwidget.layerProfileGeoref.setExceptedLayerList(notInputLayers)

        for layer in inputLayers:
            if layer.name() == 'E_Line':
                self.__dockwidget.layerProfileGeoref.setLayer(layer)

        lineLayer = self.__dockwidget.layerProfileGeoref.currentLayer()

        return lineLayer

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
