## @package QGIS geoEdit extension..
import os
import json

import processing
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsPointXY, QgsFeature, QgsField, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsProject, QgsVectorLayer, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsPoint, QgsGeometry, QgsFeatureRequest

from .layout import Layout

from .data_store_plan import DataStorePlan
from ..rotation_coords import RotationCoords

## @brief The class is used to implement functionalities for work with profile-plans within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2022-03-15
class Plan():

    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):
        print('init plan')
        self.__iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace

        self.dataStorePlan = DataStorePlan()
        self.rotationCoords = RotationCoords()

        self.createConnects()

    ## @brief Initializes the functionality for profile modul
    #

    def setup(self):
        print('Setup plan')

        #set datatype filter to profileFotosComboGeoref
        self.__dockwidget.profilePlanSelect.setFilter('Images (*.jpg)')

        self.layout = Layout(self.__iface)

        self.__dockwidget.startPlanBtn.clicked.connect(self.__startPlanCreation)


    ## \brief Event connections
    #

    def createConnects(self):

        self.dataStorePlan.pup.register('pushTransformationParams', self.rotationCoords.setAarTransformationParams)


    ## \brief Start digitize dialog
    #
    #
    def __startPlanCreation(self):

        planData = self.__getSelectedValues()

        baseFilePath = planData['profilePath'][:-4]

        metaChecker = True
        try:
            self.__importMetaData(planData['profilePath'])

        except ValueError as err:
            metaChecker = False
            self.__iface.messageBar().pushMessage("Error", str(err.args[0]), level=1, duration=3)

        if metaChecker == True:

            self.dataStorePlan.triggerAarTransformationParams()

            refData = self.__getInputlayers(True)

            self.__exportPlanLayers(refData, baseFilePath)

            self.__iface.messageBar().pushMessage("Hinweis", "Die Daten zum Plan wurden unter "+str(baseFilePath)+" abgelegt", level=3, duration=5)

            #self.layout.startLayout(planData)

    ## \brief get selected values
    #
    #
    def __getSelectedValues(self):

        #Profilbild
        profilePath = self.__dockwidget.profilePlanSelect.filePath()

        planData = {'profilePath': profilePath}

        print('planData', planData)

        return planData

    ## \brief get meta data to profile
    #
    #
    def __importMetaData(self, profilePath):

        metaFileName = profilePath[:-3]
        metaFileName = metaFileName + 'meta'

        if os.path.isfile(metaFileName):

            with open(metaFileName) as json_file:
                data = json.load(json_file)

                if data['aar_direction'] == 'horizontal' or data['aar_direction'] == 'absolute height':

                    self.dataStorePlan.addProfileNumber(data['profilnummer'])
                    self.dataStorePlan.addProfile(data['profil'])
                    self.dataStorePlan.addProfileFoto(data['profilfoto'])
                    self.dataStorePlan.addView(data['blickrichtung'])
                    self.dataStorePlan.addEntzerrungsebene(data['entzerrungsebene'])
                    self.dataStorePlan.addGcps(data['gcps'])
                    self.dataStorePlan.addTransformParams(data['transform_params'])

                else:
                    raise ValueError('AAR direction muss horizontal oder absolute height sein!')

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
            if isinstance(group, QgsLayerTreeGroup) and group.name() == 'Eingabelayer':
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

            if layer.name() == 'E_Point':
                refData['pointLayer'] = layer.clone()

            if layer.name() == 'E_Line':
                 refData['lineLayer'] = layer.clone()

            if layer.name() == 'E_Polygon':
                 refData['polygonLayer'] = layer.clone()

        return refData

    ## \brief export layers
    #
    #

    def __exportPlanLayers(self, refData, baseFilePath):
        
        #Flexible buffersize from gui
        bufferGeometry = self.rotationCoords.profileBuffer(self.__dockwidget.profileBufferSpinBox.value())
        #epsg from pointLayer - Todo search better solution (from meta file)
        epsgCode = refData['pointLayer'].crs().authid()

        #Punktlayer schreiben
        selFeaturesPoint = self.__getPointFeaturesFromEingabelayer(refData['pointLayer'], bufferGeometry, 'profile')
        self.__writeLayer(refData['pointLayer'], selFeaturesPoint, baseFilePath, 'point')

        #Linelayer schreiben
        selFeaturesLine = self.__getLineFeaturesFromEingabelayer(refData['lineLayer'], bufferGeometry, 'profile')
        self.__writeLayer(refData['lineLayer'], selFeaturesLine, baseFilePath, 'line')        

        #Polygonlayer schreiben
        selFeaturesPolygon =  self.__getPolygonFeaturesFromEingabelayer(refData['polygonLayer'], bufferGeometry, 'profile')
        self.__writeLayer(refData['polygonLayer'], selFeaturesPolygon, baseFilePath, 'polygon')   

        #GCP Layer schreiben
        gcpLayer, selFeatures = self.__getGcpLayer(epsgCode)
        self.__writeLayer(gcpLayer, selFeatures, baseFilePath, 'gcp')   


    ## \brief get points from eingabelayer
    #
    #
    def __getPointFeaturesFromEingabelayer(self, pointLayer, bufferGeometry, geoType):
        #aus Eingabelayer holen

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = pointLayer.getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:

            if feature.geometry().within(bufferGeometry):

                if geoType == 'profile':
                    if feature['geo_quelle'] == 'profile_object':

                        rotFeature = QgsFeature(pointLayer.fields())

                        rotateGeom = self.rotationCoords.rotatePointFeatureFromOrg(feature)

                        zPoint = QgsPoint(rotateGeom['x_trans'], rotateGeom['z_trans'], rotateGeom['z_trans'])

                        gZPoint = QgsGeometry(zPoint)
                        rotFeature.setGeometry(gZPoint)
                        rotFeature.setAttributes(feature.attributes())

                        selFeatures.append(rotFeature)

        return selFeatures

    ## \brief get lines from eingabelayer
    #
    #

    def __getLineFeaturesFromEingabelayer(self, lineLayer, bufferGeometry, geoType):

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = lineLayer.getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:

            if feature.geometry().within(bufferGeometry):

                if geoType == 'profile':
                    if feature['geo_quelle'] == 'profile_object':

                        rotFeature = QgsFeature(lineLayer.fields())

                        rotateGeom = self.rotationCoords.rotateLineFeatureFromOrg(feature)

                        rotFeature.setGeometry(rotateGeom)

                        rotFeature.setAttributes(feature.attributes())

                        selFeatures.append(rotFeature)

        return selFeatures

    ## \brief get polygons from eingabelayer
    #
    #

    def __getPolygonFeaturesFromEingabelayer(self, polygonLayer, bufferGeometry, geoType):

        bbox = bufferGeometry.boundingBox()
        req = QgsFeatureRequest()
        filterRect = req.setFilterRect(bbox)
        featsSel = polygonLayer.getFeatures(filterRect)

        selFeatures = []
        for feature in featsSel:

            if feature.geometry().within(bufferGeometry):

                if geoType == 'profile':
                    if feature['geo_quelle'] == 'profile_object':

                        rotFeature = QgsFeature(polygonLayer.fields())

                        rotateGeom = self.rotationCoords.rotatePolygonFeatureFromOrg(feature)

                        rotFeature.setGeometry(rotateGeom)

                        rotFeature.setAttributes(feature.attributes())

                        selFeatures.append(rotFeature)

        return selFeatures

    ## \brief get gcps
    #
    #

    def __getGcpLayer(self, epsgCode):

        gcpObj = self.dataStorePlan.getGcps()

        # create layer

        gcpLayer = QgsVectorLayer("point?crs="+epsgCode, "gcp_points", "memory")
        gcpLayer.startEditing()
        pr = gcpLayer.dataProvider()

        #add attributes
        
        attributes = []
        
        for key, value in gcpObj[0].items():

            if key != 'aar_y':

                if isinstance(value, str):
                    attributes.append(QgsField(key, QVariant.String))

                if isinstance(value, float):
                    attributes.append(QgsField(key, QVariant.Double))

        pr.addAttributes(attributes)
        gcpLayer.updateFields()
        
    
        #add features
        features = []
        for item in gcpObj:
            
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(item['aar_x'],item['aar_z'])))

            attributesFeat = []

            for key, value in item.items():
                if key != 'aar_y':
                    attributesFeat.append(value)

            feat.setAttributes(attributesFeat)
            features.append(feat)

        pr.addFeatures(features)

        # Rename fields
        for field in gcpLayer.fields():
            print('fieldname', field.name())
            if field.name() == 'aar_x':
                gcpLayer.startEditing()
                idx = gcpLayer.fields().indexFromName(field.name())
                gcpLayer.renameAttribute(idx, 'x_orig')
                gcpLayer.commitChanges()

            if field.name() == 'aar_z':
                gcpLayer.startEditing()
                idx = gcpLayer.fields().indexFromName(field.name())
                gcpLayer.renameAttribute(idx, 'y_orig')
                gcpLayer.commitChanges()

            if field.name() == 'aar_z_org':
                gcpLayer.startEditing()
                idx = gcpLayer.fields().indexFromName(field.name())
                gcpLayer.renameAttribute(idx, 'z_orig')
                gcpLayer.commitChanges()

        gcpLayer.updateFields()
        gcpLayer.updateExtents()
        gcpLayer.endEditCommand()

        return gcpLayer, features

    ## \brief __writeLayer
    #
    #
    def __writeLayer(self, inputLayer, selFeatures, baseFilePath, layerType):

        inputLayer.selectAll()
        outputLayer = processing.run("native:saveselectedfeatures", {'INPUT': inputLayer, 'OUTPUT': 'memory:'})['OUTPUT']
        outputLayer.removeSelection()

        outputLayer.startEditing()

        #Layer leeren
        pr = outputLayer.dataProvider()
        pr.truncate()

        #add features
        pr.addFeatures(selFeatures)

        outputLayer.commitChanges()

        outputLayer.updateExtents()

        outputLayer.endEditCommand()

        # Save mem layer as a shapefile
        fileOutPath = f'{baseFilePath}_{layerType}.shp'

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"

        QgsVectorFileWriter.writeAsVectorFormatV2(outputLayer, fileOutPath, QgsCoordinateTransformContext(), options)

        print('outputLayer Layer is written to: ', fileOutPath)

