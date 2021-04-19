# -*- coding: utf-8 -*-
import os
import numpy as np
import math
from scipy import stats

from qgis.core import QgsGeometry, QgsApplication, QgsRectangle
from processing.gui import AlgorithmExecutor

from .simil import simil

## @brief Core calculations for the transformation
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-11-09

class TransformationCalculations():

    ## The constructor.
    #
    #  @param dialogInstance pointer to the dialogInstance
    def __init__(self, dialogInstance):

        self.dialogInstance = dialogInstance

    ## \brief Start of the calculation of the transformation parameters
    #
    # - calls calcTransformation2D() to calculate the 2D-parameters
    # - calls calcTransformationZ() to calculate Z translation value
    #
    # \param GcpData Dictionary
    # @returns zAngle, translationX, translationY, globalError2D, translationZ, GcpData, globalErrorZ
    def calcTransformationParams(self, GcpData):

        zAngle, translationX, translationY, globalError2D, pointError2D = self.calcTransformation2D(GcpData)

        translationZ, residualsZ, globalErrorZ = self.calcTransformationZ(GcpData)

        # Rueckgabe
        for i in range(0,len(GcpData)):
            if GcpData[i]['usage'] == '3D' or GcpData[i]['usage'] == 'Z':
                for z in range(0,len(residualsZ)):
                    if GcpData[i]['uuid'] == residualsZ[z][3]:
                        GcpData[i]['errorZ'] = residualsZ[z][2]
            else:
                GcpData[i]['errorZ'] = -99999

        for i in range(0,len(GcpData)):
            if GcpData[i]['usage'] == '3D' or GcpData[i]['usage'] == '2D':
                for z in range(0,len(pointError2D)):
                    if GcpData[i]['uuid'] == pointError2D[z][7]:
                        GcpData[i]['errorXY'] = pointError2D[z][6]
            else:
                GcpData[i]['errorXY'] = -99999

        return zAngle, translationX, translationY, globalError2D, translationZ, GcpData, globalErrorZ

    ## \brief Calculates the 2D-parameters for the transformation
    #
    # - Prepares data for the calculation
    # - calls simil.process()
    # - calls rotMat2Euler() to get the euler angle from rotation matrix
    # - calls estimateError2d() to calculate the errors
    #
    # \param GcpData Dictionary
    # @returns zAngle, translationX, translationY, globalError2D, pointError2D

    def calcTransformation2D(self, GcpData):
        sourcePointsWithId = []
        targetPointsWithId = []

        for pointObj in GcpData:
            if pointObj['usage'] == '3D' or pointObj['usage'] == '2D':
                selectedSourcePoints = pointObj['sourcePoints'].copy()
                selectedSourcePoints.append(pointObj['uuid'])

                selectedTargetPoints = pointObj['targetPoints'].copy()
                selectedTargetPoints.append(pointObj['uuid'])

                sourcePointsWithId.append(selectedSourcePoints)
                targetPointsWithId.append(selectedTargetPoints)

        # set z value to 0 to force a 2d transformation, ohne id
        sourcePoints2D = np.array(sourcePointsWithId)[:,0:2]
        sourcePoints2D = np.insert(sourcePoints2D, 2, values = 0, axis=1)
        targetPoints2D = np.array(targetPointsWithId)[:,0:2]
        targetPoints2D = np.insert(targetPoints2D, 2, values = 0, axis=1)

        sourcePoints2D = np.array(sourcePoints2D)[:,0:2]
        sourcePoints2D = np.insert(sourcePoints2D, 2, values = 0, axis=1)
        sourcePoints2D = sourcePoints2D.astype(float)
        targetPoints2D = np.array(targetPoints2D)[:,0:2]
        targetPoints2D = np.insert(targetPoints2D, 2, values = 0, axis=1)
        targetPoints2D = targetPoints2D.astype(float)

        #start estimation of the 2D parameters
        m, r, t = simil.process(sourcePoints2D, targetPoints2D, scale=False)
        #euler from rotation matrix
        E = self.rotMat2Euler(r)
        #zAngle
        zAngle = (E[2]*180/math.pi)*-1
        #translation x and y
        translationX = t[0][0].item()
        translationY = t[1][0].item()

        #check if translationX and Y Value are type complex, then just use real part (when all points have the same coordinates)
        if isinstance(translationX, complex):
            translationX = translationX.real

        if isinstance(translationY, complex):
            translationY = translationY.real

        #estimate 2d error
        globalError2D, pointError2D = self.estimateError2d([m,r,t], sourcePointsWithId, targetPointsWithId)

        #print('translationX', translationX)
        return zAngle, translationX, translationY, globalError2D, pointError2D

    ## \brief Calculates the Z-translation for the transformation
    #
    # - Prepares data for the calculation
    # - calls calculate1dTranslationParams()
    # - calls estimateError1d() to calculate the error
    #
    # \param GcpData Dictionary
    # @returns translationZ, residualsZ, globalErrorZ

    def calcTransformationZ(self, GcpData):

        # Inputdaten 1d Z-translation aufbereiten
        sourcePointsZWithId = []
        targetPointsZWithId = []

        for pointObj in GcpData:
            if pointObj['usage'] == '3D' or pointObj['usage'] == 'Z':

                selectedSourcePointsZ = pointObj['sourcePoints'].copy()
                selectedSourcePointsZ.append(pointObj['uuid'])

                selectedTargetPointsZ = pointObj['targetPoints'].copy()
                selectedTargetPointsZ.append(pointObj['uuid'])

                sourcePointsZWithId.append(selectedSourcePointsZ)
                targetPointsZWithId.append(selectedTargetPointsZ)

        sourcePointsZ = np.array(sourcePointsZWithId)[:,2]
        sourcePointsZ = sourcePointsZ.astype(float)
        targetPointsZ = np.array(targetPointsZWithId)[:,2]
        targetPointsZ = targetPointsZ.astype(float)

        #calculation of z translation
        translationZ = self.calculate1dTranslationParams(sourcePointsZ, targetPointsZ)
        #error calculation
        residualsZ, globalErrorZ = self.estimateError1d(translationZ, sourcePointsZWithId, targetPointsZWithId)

        return translationZ, residualsZ, globalErrorZ

    ## \brief layer translation Z direction
    #
    # \param layer
    # \param tranlationDirection - forward or reverse
    # \param translationZ - Translation value
    # @returns

    def layerTranslationZ(self, layer, tranlationDirection, translationZ):

        layerName = layer.name()
        print('Transformation - Translation Z: ', layerName)

        #layer.startEditing()
        layer.beginEditCommand( 'Beginn edit Translation Z' )
        for zFeat in layer.getFeatures():

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
                provGeom = layer.dataProvider().convertToProviderType(adjustGeom)
                fid = zFeat.id()

                if provGeom == None:
                    layer.dataProvider().changeGeometryValues({ fid : adjustGeom })
                else:
                    layer.dataProvider().changeGeometryValues({ fid : provGeom })

            #point - 0
            if geomType == 0:
                if tranlationDirection == 'forward':
                    g.get().setZ(g.get().z() + translationZ)
                if tranlationDirection == 'reverse':
                    g.get().setZ(g.get().z() - translationZ)

                fid = zFeat.id()
                layer.dataProvider().changeGeometryValues({ fid : g })

        layer.dataProvider().createSpatialIndex()
        layer.endEditCommand()


    ## \brief layer rotation
    #
    # \param layer
    # \param rotationDirection - forward or reverse
    # \param zAngle - rotation angle
    # @returns

    def layerRotation(self, layer, rotationDirection, zAngle):

        print('Transformation - Rotation: ', layer.name())
        #Rotation
        if rotationDirection == 'forward':
            angleValue = zAngle * -1
        if rotationDirection == 'reverse':
            angleValue = zAngle

        layer.startEditing()
        rotateAlg = QgsApplication.processingRegistry().createAlgorithmById('native:rotatefeatures')
        paramRotate = { 'ANCHOR' : '0,0', 'ANGLE' : angleValue, 'INPUT': layer}
        AlgorithmExecutor.execute_in_place(rotateAlg, paramRotate)
        layer.commitChanges()


    ## \brief layer translation X and Y
    #
    # \param layer
    # \param tranlationDirection - forward or reverse
    # \param translationX
    # \param translationY
    # @returns

    def layerTranslationXY(self, layer, tranlationDirection, translationX, translationY):

        layerName = layer.name()

        if tranlationDirection == 'forward':
            tranlationXValue = translationX
            tranlationYValue = translationY
        if tranlationDirection == 'reverse':
            tranlationXValue = translationX * -1
            tranlationYValue = translationY * -1

        print('Transformation - Translation X and Y: ', layerName)

        layer.startEditing()
        translateAlg = QgsApplication.processingRegistry().createAlgorithmById('native:translategeometry')
        paramTranslate = { 'DELTA_Y' : tranlationYValue, 'DELTA_X' : tranlationXValue, 'INPUT': layer}
        AlgorithmExecutor.execute_in_place(translateAlg, paramTranslate)
        layer.commitChanges()


    ## \brief layer translation X, Y and Z direction
    #
    # \param layer
    # \param tranlationDirection - forward or reverse
    # \param translationX
    # \param translationY
    # \param translationZ

    def layerTranslationXYZ(self, layer, tranlationDirection, translationX, translationY, translationZ):

        layerName = layer.name()

        if tranlationDirection == 'forward':
            tranlationXValue = translationX
            tranlationYValue = translationY
            tranlationZValue = translationZ
        if tranlationDirection == 'reverse':
            tranlationXValue = translationX * -1
            tranlationYValue = translationY * -1
            tranlationZValue = translationZ * -1

        print('Transformation - Translation X, Y and Z: ', layerName)

        layer.startEditing()
        translateAlg = QgsApplication.processingRegistry().createAlgorithmById('native:translategeometry')

        layerType = layer.wkbType()
        print("layerType", layerType)
        #Abfrage nach Z und ZM Multi Layertypen
        #1004 MultiPointZ , 1005 MultiLineZ, 1006 MultiPolygonZ
        if layerType == 1004 or layerType == 1005 or layerType == 1006:

            paramTranslate = { 'DELTA_Y' : tranlationYValue, 'DELTA_X' : tranlationXValue, 'DELTA_Z' : tranlationZValue, 'INPUT': layer}

        else:
            paramTranslate = { 'DELTA_Y' : tranlationYValue, 'DELTA_X' : tranlationXValue, 'DELTA_Z' : tranlationZValue, 'DELTA_M' : 0, 'INPUT': layer}

        print("paramTranslate ", paramTranslate)
        AlgorithmExecutor.execute_in_place(translateAlg, paramTranslate)
        layer.commitChanges()

    ## \brief Calculates the current extent of a layer
    #
    # \param layer
    # @returns
    def recalculateLayerExtent(self, layer):

        targetExtent = QgsRectangle()
        targetExtent.setMinimal()
        for feat in layer.getFeatures():

            bbox = feat.geometry().boundingBox()
            targetExtent.combineExtentWith(bbox)

        layer.setExtent(targetExtent)

    ## \brief This function creates a new spatial index for a layer
    #
    # \param layer
    # @returns
    def createLayerSpatialIndex(self, layer):
        layer.dataProvider().createSpatialIndex()

    ## @brief Get the Euler angles from a rotation matrix
    #
    # @param R The rotation matrix
    # @returns Eul The Euler angles [E1, E2, E3]
    def rotMat2Euler(self, R):
        if R[0,2] == 1 or R[0,2] == -1:
          #special case
          E3 = 0 #set arbitrarily
          dlta = math.atan2(R[0,1],R[0,2])
          if R[0,2] == -1:
            E2 = pi/2
            E1 = E3 + dlta
          else:
            E2 = -pi/2
            E1 = -E3 + dlta
        else:
          E2 = - math.asin(R[0,2])
          E1 = math.atan2(R[1,2]/math.cos(E2), R[2,2]/math.cos(E2))
          E3 = math.atan2(R[0,1]/math.cos(E2), R[0,0]/math.cos(E2))

        Eul = [E1, E2, E3]
        return Eul

    ## @brief Error estimation for 2d transformation (translation and rotation)
    # With the transformation matrix, the source points are transformed and then compared with the target coordinates
    # @param transform The transformation parameters [m, r, t], where m is the multiplier factor, r is the rotation matrix, t is the translation matrix
    # @param origin The original local coordinates as 2d list [[x0,y0],[x1,y1],...,[xn,yn]]
    # @param target The measured GPS coordinates as 2d list [[x0,y0],[x1,y1],...,[xn,yn]]
    # @returns e The estimated error for the whole dataset, error_container error information for each point
    def estimateError2d(self, transform, origin, target):

        # total error as std
        e = 0
        # get the transformation parameters
        #m = scale =  1
        m = transform[0]
        #r Rotationmatrx
        r = transform[1]
        #t Translationmatrix
        t = transform[2]

        originNoId = np.array(origin)[:,0:2]
        originNoId = originNoId.astype(float)
        originNoId = np.insert(originNoId, 2, values = 0, axis=1)
        targetNoId = np.array(target)[:,0:2]
        targetNoId = targetNoId.astype(float)
        targetNoId = np.insert(targetNoId, 2, values = 0, axis=1)

        #print(m, r,t)
        origin2 = []
        for i in originNoId:
            origin2.append(m * r @ i[0:3] + t)

        # get length of array
        N = len(origin2)

        # loop through each coordinate pair
        se = 0.0
        error_container = []

        for i in range(N):
            pointId = origin[i][3]
            ox = origin2[i][0][0]
            oy = origin2[i][1][1]
            tx = target[i][0]
            ty = target[i][1]

            dx = ox - tx
            dy = oy - ty

            se += dx * dx + dy * dy
            # Fehler für den Punkt
            e_point = math.sqrt((dx * dx + dy * dy))

            error_container.append([ox,oy,dx,tx,ty,dy,e_point,pointId])

        if N == 0:
            e = 0
        else:
            # standard deviation
            e = math.sqrt(se / N)

        return e, error_container

    ## @brief Error estimation for 1d translation of z axis
    ## @param t The parameters of the linear least square regression
    ## @param origin The source z matrix
    ## @param target The target z matrix
    ## @returns residuals The residuals for each z pair [source, target] and std_z (standard deviation)
    def estimateError1d(self, translation_z, origin, target):
        # total error as std

        sourcePointsZ = np.array(origin)[:,2]
        sourcePointsZ = sourcePointsZ.astype(float)
        targetPointsZ = np.array(target)[:,2]
        targetPointsZ = targetPointsZ.astype(float)

        residuals = []

        N = len(origin)
        for i in range(N):
            z_residuals = targetPointsZ[i]  - (sourcePointsZ[i] + translation_z)
            residuals.append([targetPointsZ[i], sourcePointsZ[i], z_residuals, origin[i][3]])

        linEq = stats.linregress(sourcePointsZ, targetPointsZ)
        std_z = linEq.stderr

        return residuals, std_z

    ## @brief Calculate 1d translation parameters by the average difference between source and target z values
    ## @param src_z The source z matrix
    ## @param tgt_z The target z matrix
    ## @returns z The z translation value
    def calculate1dTranslationParams(self, src_z, tgt_z):
        z = None

        z = (tgt_z - src_z).mean()

        return z
