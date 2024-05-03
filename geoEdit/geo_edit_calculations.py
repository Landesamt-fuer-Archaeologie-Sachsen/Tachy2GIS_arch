## @package QGIS geoEdit extension..
import shutil

from qgis.core import QgsGeometry, QgsApplication
from processing.gui import AlgorithmExecutor
from qgis import processing

## @brief The class is used to implement functionalities for translate geometies within the geoEdit Module
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-01-22
class GeoEditCalculations():

    ## The constructor.
    #  Defines attributes for the GeoEditCalculations
    #
    #  @param geoEditInstance pointer to the geoEditInstance
    def __init__(self, geoEditInstance):
        self.geoEditInstance = geoEditInstance

    ## \brief Absolute translation of sourcelayer in z direction
    #
    # \param tranlationDirection - forward or reverse
    # \param sourceLayer - used layer for translation
    # \param translationZ - Value for translation in z direction
    # \param selectedFeatures - Array with selected features in the sourcelayer
    #
    # - Forward translation: The function uses the algorithm qgis:setvalue. The height of the feature geometry is set to the translationZ value, even if individual points of the geometry have different height values.
    # - Reverse translation: The current geometries are exchanged with the geometries saved before the transformation.
    def layerTranslationZAbsolute(self, tranlationDirection, sourceLayer, translationZ, selectedFeatures):

        layerName = sourceLayer.name()

        #Translation forward
        if tranlationDirection == 'forward':
            tranlationZValue = translationZ

            print('Translation z - forward and absolute: ', layerName)

            sourceLayer.startEditing()
            translateAlg = QgsApplication.processingRegistry().createAlgorithmById('qgis:setzvalue')
            paramTranslate = {'Z_VALUE' : tranlationZValue, 'INPUT' : sourceLayer}
            print(paramTranslate)
            AlgorithmExecutor.execute_in_place(translateAlg, paramTranslate)

            sourceLayer.commitChanges()

        #Translation reverse
        if tranlationDirection == 'reverse':

            print('Translation z - reverse and absolute: ', layerName)
            sourceLayer.startEditing()

            for feat in sourceLayer.getFeatures():
                for selFeat in selectedFeatures:
                    if feat.id() == selFeat.id():

                        sourceLayer.dataProvider().changeGeometryValues({ feat.id() : selFeat.geometry()})

            sourceLayer.commitChanges()


    ## \brief relative translation of sourcelayer in z direction
    #
    # \param tranlationDirection - forward or reverse
    # \param translationZ - Value for translation in z direction
    #
    # - Forward translation: The height of the individual points of the geometry is calculated by adding the translationZ to the current value.
    # - Reverse translation: The translationZ is subtracted from the individual points.
    def layerTranslationZ(self, tranlationDirection, sourceLayer, translationZ):

        layerName = sourceLayer.name()
        print('Transformation - Translation Z: ', layerName)

        #layer.startEditing()
        sourceLayer.beginEditCommand( 'Beginn edit Translation Z' )
        for zFeat in sourceLayer.selectedFeatures():

            g = zFeat.geometry() #QgsGeometry
            geomType = g.type()

            #line - 1, polygon - 2
            if geomType == 1 or geomType == 2:

                mls = g.get() #QgsMultiPolygon

                adjustGeom = QgsGeometry(mls.createEmptyWithSameType())
                geomArray = []
                for v in mls.vertices():

                    if tranlationDirection == 'forward':
                        newZVal = v.z() + translationZ
                    if tranlationDirection == 'reverse':
                        newZVal = v.z() - translationZ

                    v.setZ(newZVal)
                    geomArray.append(v)

                adjustGeom.addPoints(geomArray)
                provGeom = sourceLayer.dataProvider().convertToProviderType(adjustGeom)
                fid = zFeat.id()

                if provGeom == None:
                    sourceLayer.dataProvider().changeGeometryValues({ fid : adjustGeom })
                else:
                    sourceLayer.dataProvider().changeGeometryValues({ fid : provGeom })

            #point - 0
            if geomType == 0:
                if tranlationDirection == 'forward':
                    g.get().setZ(g.get().z() + translationZ)
                if tranlationDirection == 'reverse':
                    g.get().setZ(g.get().z() - translationZ)

                fid = zFeat.id()
                sourceLayer.dataProvider().changeGeometryValues({ fid : g })

        sourceLayer.dataProvider().createSpatialIndex()
        sourceLayer.endEditCommand()

    ## \brief Translation of the sourcelayer in x and y direction
    #
    # \param tranlationDirection - forward or reverse
    # \param sourceLayer - used layer for translation
    # \param translationX - Value for translation in x direction
    # \param translationY - Value for translation in y direction
    def layerTranslationXY(self, tranlationDirection, sourceLayer, translationX, translationY):

        layerName = sourceLayer.name()

        if tranlationDirection == 'forward':
            tranlationXValue = translationX
            tranlationYValue = translationY
        if tranlationDirection == 'reverse':
            tranlationXValue = translationX * -1
            tranlationYValue = translationY * -1

        print('Transformation - Translation X and Y: ', layerName)

        sourceLayer.startEditing()
        translateAlg = QgsApplication.processingRegistry().createAlgorithmById('native:translategeometry')
        paramTranslate = { 'DELTA_Y' : tranlationYValue, 'DELTA_X' : tranlationXValue, 'INPUT' : sourceLayer}
        print(paramTranslate)
        AlgorithmExecutor.execute_in_place(translateAlg, paramTranslate)

        sourceLayer.commitChanges()

    ## \brief Translation of the sourcelayer in x, y and z direction
    #
    # \param tranlationDirection - forward or reverse
    # \param sourceLayer - used layer for translation
    # \param translationX - Value for translation in x direction
    # \param translationY - Value for translation in y direction
    # \param translationZ - Value for translation in z direction
    def layerTranslationXYZ(self, tranlationDirection, sourceLayer, translationX, translationY, translationZ):

        layerName = sourceLayer.name()

        if tranlationDirection == 'forward':
            tranlationXValue = translationX
            tranlationYValue = translationY
            tranlationZValue = translationZ
        if tranlationDirection == 'reverse':
            tranlationXValue = translationX * -1
            tranlationYValue = translationY * -1
            tranlationZValue = translationZ * -1

        print('Transformation - Translation X, Y and Z: ', layerName)

        sourceLayer.startEditing()
        translateAlg = QgsApplication.processingRegistry().createAlgorithmById('native:translategeometry')

        layerType = sourceLayer.wkbType()
        print("layerType", layerType)

        #Abfrage nach Z und ZM Multi Layertypen
        #1004 MultiPointZ , 1005 MultiLineZ, 1006 MultiPolygonZ
        if layerType == 1004 or layerType == 1005 or layerType == 1006:

            paramTranslate = { 'DELTA_Y' : tranlationYValue, 'DELTA_X' : tranlationXValue, 'DELTA_Z' : tranlationZValue, 'INPUT': sourceLayer}

        else:
            paramTranslate = { 'DELTA_Y' : tranlationYValue, 'DELTA_X' : tranlationXValue, 'DELTA_Z' : tranlationZValue, 'DELTA_M' : 0, 'INPUT': sourceLayer}

        print("paramTranslate ", paramTranslate)
        AlgorithmExecutor.execute_in_place(translateAlg, paramTranslate)
        sourceLayer.commitChanges()
