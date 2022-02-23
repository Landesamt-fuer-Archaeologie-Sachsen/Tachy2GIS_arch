## @package QGIS geoEdit extension..
import os
import math

from qgis.core import QgsProject, QgsVectorLayer, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsWkbTypes

from .data_store_georef import DataStoreGeoref
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

        self.dataStoreGeoref = DataStoreGeoref()

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
        self.__dockwidget.profileFotosComboGeoref.fileChanged.connect(self.__changedProfileImage)
        #Preselection View direction
        self.__preselectViewDirection()
        #set datatype filter and save mode to profileSaveComboGeoref
        self.__dockwidget.profileSaveComboGeoref.setFilter('Images (*.jpg)')
        self.__dockwidget.profileSaveComboGeoref.setStorageMode(3)

        self.__dockwidget.startGeoreferencingBtn.clicked.connect(self.__startGeoreferencingDialog)

        self.__dockwidget.layerGcpGeoref.currentIndexChanged.connect(self.__calculateViewDirection)

        self.__dockwidget.profileIdsComboGeoref.currentIndexChanged.connect(self.__calculateViewDirection)

        self.__dockwidget.layerProfileGeoref.currentIndexChanged.connect(self.__calculateViewDirection)

        #self.__dockwidget.profileInfoBtn.clicked.connect(self.__testProjective)


    ## \brief Start georeferencing dialog
    #
    #
    def __startGeoreferencingDialog(self):

        refData = self.__getSelectedValues()

        self.georeferencingDialog = GeoreferencingDialog(self, self.dataStoreGeoref, self.__iface)
        self.georeferencingDialog.showGeoreferencingDialog(refData)


    ## \brief SaveComboBox is clicked
    #
    # suggest saveFilePath

    def __changedProfileImage(self):

        imageFilePath = self.__dockwidget.profileFotosComboGeoref.filePath()
        shortFilePath = imageFilePath.rsplit('.', 1)[0]
        suggestTargetFilePath = shortFilePath + '_entz.jpg'
        self.__dockwidget.profileSaveComboGeoref.setFilePath(suggestTargetFilePath)

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

        refData = {'lineLayer': lineLayer, 'pointLayer': pointLayer, 'crs': pointLayer.crs(), 'profileNumber': profileNumber, 'imagePath': imagePath, 'viewDirection': viewDirection, 'horizontal': horizontalCheck, 'savePath': savePath, 'saveMetadata': metadataCheck, 'targetGCP': targetGCP}

        return refData

    ## \brief Blickrichtung bestimmen
    #
    #
    def __calculateViewDirection(self):

        #lineLayer
        lineLayer = self.__dockwidget.layerProfileGeoref.currentLayer().clone()

        #Profilnummer
        profileNumber = self.__dockwidget.profileIdsComboGeoref.currentText()

        lineLayer.setSubsetString("prof_nr = '"+profileNumber+"'")

        view = None


        if lineLayer.geometryType() ==  QgsWkbTypes.LineGeometry:
            for feat in lineLayer.getFeatures():

                geom = feat.geometry()
                #Singlepart
                if QgsWkbTypes.isSingleType(geom.wkbType()):
                    line = geom.asPolyline()
                else:
                    # Multipart
                    line = geom.asMultiPolyline()[0]

                pointA = line[0]
                pointB = line[-1]

                pointAx = pointA.x()
                pointAy = pointA.y()
                pointBx = pointB.x()
                pointBy = pointB.y()

                dx = pointBx - pointAx
                dy = pointBy - pointAy
                vp = [dx, dy]
                v0 = [-1, 1]
                # Lösung von hier: https://stackoverflow.com/questions/14066933/direct-way-of-computing-clockwise-angle-between-2-vectors/16544330#16544330, angepasst auf Berechnung ohne numpy
                dot = v0[0] * vp[0] + v0[1] * vp[1]  # dot product: x1*x2 + y1*y2
                det = v0[0] * vp[1] - vp[0] * v0[1]  # determinant: x1*y2 - y1*x2

                radians = math.atan2(det, dot)
                angle = math.degrees(radians)
                # negative Winkelwerte (3. und 4. Quadrant, Laufrichtung entgegen Uhrzeigersinn) in fortlaufenden Wert (181 bis 360) umrechnen
                if angle < 0:
                    angle *= -1
                    angle = 180 - angle + 180

                if angle <= 90:
                    view = "Nord"
                elif angle <= 180:
                    view = "West"
                elif angle <= 270:
                    view = "Süd"
                elif angle > 270:
                    view = "Ost"

                self.__dockwidget.profileViewDirectionComboGeoref.setCurrentText(view)


    ### Ende Blickrichtung bestimmen

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