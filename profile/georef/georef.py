## @package QGIS geoEdit extension..
import os
import math
import pathlib

from PyQt5.QtWidgets import QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsWkbTypes

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
    def __init__(self, t2gArchInstance, iFace, rotationCoords):

        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace

        self.rotationCoords = rotationCoords

    ## @brief Initializes the functionality for profile modul
    #

    def setup(self):

        #Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
        preselectedLineLayer = self.__preselectionProfileLayer()
        #Tooltip
        self.__dockwidget.profileTargetName.setToolTip("Die Ergebnisdateien werden in Unterverzeichnissen vom Profilfoto abgelegt, die Dateinamen beginnen so wie hier angegeben.")
        #Preselection profilenumber
        if isinstance(preselectedLineLayer, QgsVectorLayer):

            self.__preselectProfileNumbers(preselectedLineLayer)
            #Preselection of Inputlayers (only Layer below "Eingabelayer" are available)
            self.__preselectionGcpLayer()
            #set datatype filter to profileFotosComboGeoref
            self.__dockwidget.profileFotosComboGeoref.setFilter('Images (*.png *.JPG *.jpg *.jpeg *.tif)')
            self.__dockwidget.profileFotosComboGeoref.fileChanged.connect(self.__changedProfileImage)
            #Preselection View direction
            self.__preselectViewDirection()

            self.__dockwidget.startGeoreferencingBtn.clicked.connect(self.__startGeoreferencingDialog)

            self.__dockwidget.layerGcpGeoref.currentIndexChanged.connect(self.__calculateViewDirection)

            self.__dockwidget.profileIdsComboGeoref.currentIndexChanged.connect(self.__calculateViewDirection)

            self.__dockwidget.layerProfileGeoref.currentIndexChanged.connect(self.__calculateViewDirection)

            profil_start_idx = self.__dockwidget.profileIdsComboGeoref.currentIndex()

            #Connection to info messagebox
            self.__dockwidget.profileInfoBtn.clicked.connect(self.__openInfoMessageBox)

            # Calculate initial profile view
            self.__calculateViewDirection(profil_start_idx)

        else:
            print('preselectedLineLayer is kein QgsVectorLayer')


    ## \brief Start georeferencing dialog
    #
    #
    def __startGeoreferencingDialog(self):
        refData = self.__getSelectedValues()
        self.__createFolders(refData)
        
        self.georeferencingDialog = GeoreferencingDialog(self, self.rotationCoords, self.__iface)
        self.georeferencingDialog.showGeoreferencingDialog(refData)

    ## \brief SaveComboBox is clicked
    #
    # suggest profileTargetName
    
    def __changedProfileImage(self):

        imageFilePath = self.__dockwidget.profileFotosComboGeoref.filePath()
        shortFileName = pathlib.Path(imageFilePath).stem
        suggestTargetName = shortFileName + '_entz'
        self.__dockwidget.profileTargetName.setText(suggestTargetName)


    ## \brief get selected values
    #
    #refData
    #{
    #    'lineLayer': < QgsVectorLayer: 'E_Line'(ogr) > ,
    #    'pointLayer': < QgsVectorLayer: 'E_Point'(ogr) > ,
    #    'crs': < QgsCoordinateReferenceSystem: EPSG: 31468 > ,
    #    'profileNumber': '131',
    #    'imagePath': 'path\\to\\AZB-16_Pr_132.jpg',
    #    'viewDirection': 'E',
    #    'horizontal': True,
    #    'profileTargetName': 'AZB-16_Pr_132_entz',
    #    'savePath': 'path\\to\\Profil_132',
    #    'profileDirs': {
    #        'dirPa': 'path\\to\\pa',
    #        'dirPo': 'path\\to\\po',
    #        'dirPh': 'path\\to\\ph',
    #        'dir3d': 'path\\to\\3d'
    #    },
    #    'saveMetadata': True,
    #    'targetGCP': {
    #        'points': [{
    #            'uuid': '{f9a241b4-1a9b-4695-a493-5262efa1857c}',
    #            'ptnr': '1',
    #            'id': 745,
    #            'x': 4577275.697,
    #            'y': 5710099.149,
    #            'z': 84.729
    #        }, {...}]
    #    }
    #}
    #
    # @return refData
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

        validGeomCheck = True
        orgGeomType = ''

        for feature in pointLayer.getFeatures():

            org_geom = feature.geometry()
            orgGeomType = org_geom.wkbType()
            
            g = self.rotationCoords.castMultipointGeometry(org_geom)

            geoType = g.wkbType()

            if geoType == 1001 or geoType == 3001:

                pointObj = {'uuid': feature.attribute("uuid"), 'ptnr': feature.attribute("ptnr"), 'id': feature.attribute("id"), 'x': float(g.get().x()), 'y': float(g.get().y()), 'z': float(g.get().z())}
                targetGCP['points'].append(pointObj)

            else:
                validGeomCheck = False

        if validGeomCheck is False:

            errorMsg = f'Kann Geometrietyp nicht verarbeiten {orgGeomType}'
            self.__iface.messageBar().pushMessage("Error", errorMsg, level=1, duration=3)

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
        #horizontalCheck = self.__dockwidget.radioDirectionHorizontal.isChecked()

        #profileTargetName
        profileTargetName = self.__dockwidget.profileTargetName.text()
        #Speicherpfad
        fullPath = self.__dockwidget.profileFotosComboGeoref.filePath()
        p_path = pathlib.Path(fullPath)
        savePath = p_path.parent

        profileDirs = {
            "dirPa": str(savePath / 'pa'), "dirPo": str(savePath / 'po'),  "dirPh": str(savePath / 'ph'),  "dir3d": str(savePath / '3d')
        }     

        #Metadaten
        metadataCheck = True #self.__dockwidget.metaProfileCheckbox.isChecked()

        refData = {'lineLayer': lineLayer, 'pointLayer': pointLayer, 'crs': pointLayer.crs(), 'profileNumber': profileNumber, 'imagePath': imagePath, 'viewDirection': viewDirection, 'horizontal': horizontalCheck, 'profileTargetName': profileTargetName, 'savePath': str(savePath), 'profileDirs': profileDirs, 'saveMetadata': metadataCheck, 'targetGCP': targetGCP}

        return refData

    ## \brief Blickrichtung bestimmen
    #
    #
    def __calculateViewDirection(self, idx):	

        if isinstance(idx, int) and idx >= 0:

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


    def __createFolders(self, refData):

        print('Create missing folders ...')

        profileDirs = refData['profileDirs']

        for key, value in profileDirs.items():        
            if not os.path.exists(value):
                os.makedirs(value)



    ## \brief Opens a message box with background informations
    #

    def __openInfoMessageBox(self):

        infoText = "Ein archäologisches Profil ist ein (nahezu) vertikaler Schnitt durch einen oder mehrere archäologische Befunde und bietet daher gute Voraussetzungen zur dreidimensionalen Dokumentation von Grabungsszenen. \n\nDas Profiltool bietet die Möglichkeit Profilfotos anhand von Messpunkten zu georeferenzieren. Weiterhin können im erstellten Profil geometische Strukturen digitalisiert werden und die Daten für Profilpläne erzeugt werden."
        self.infoTranssformMsgBox = QMessageBox()
        self.infoTranssformMsgBox.setText(infoText)

        self.infoTranssformMsgBox.setWindowTitle("Hintergrundinformationen")
        self.infoTranssformMsgBox.setStandardButtons((QMessageBox.Ok))
        self.infoTranssformMsgBox.exec_()
