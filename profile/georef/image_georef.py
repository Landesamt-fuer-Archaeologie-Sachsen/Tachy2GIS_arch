# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from PyQt5.QtCore import QFileInfo
import shutil
from osgeo import gdal, osr
from PIL import Image
import numpy as np

from qgis.core import QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsFeature, QgsPointXY, QgsGeometry
from PyQt5.QtCore import QVariant

from ..ahojnnes.transformation import Transformation

from ..digitize.rotation_coords import RotationCoords

class ImageGeoref():

    def __init__(self, dialogInstance, dataStoreGeoref):

        print('init ImageGeoref')

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')

        self.dialogInstance = dialogInstance

        self.imageFileIn = ''

        self.imageFileOut = ''

        self.gcpPoints = ''

        self.dataStoreGeoref = dataStoreGeoref


    def runGeoref(self, georefData):
        print('run ImageGeoref')

        self.gcpPoints = georefData
        self.startTranslate()
        self.createGcpShape()

        print('Finish ImageGeoref')

        #self.startTranslatePIL()
        #self.startTranslateAh()
        #self.startWarp()

    def find_coeffs(self, source_coords, target_coords):
        print('source_coords', source_coords)
        print('target_coords', target_coords)
        matrix = []
        for s, t in zip(source_coords, target_coords):
            matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
            matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])
        A = np.matrix(matrix, dtype=np.float)
        B = np.array(source_coords).reshape(8)
        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return np.array(res).reshape(8)

    '''
    def find_coeffs(self, pa, pb):
        print('pa', pa)
        print('pb', pb)
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

        A = np.matrix(matrix, dtype=np.float)
        B = np.array(pb).reshape(8)

        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return np.array(res).reshape(8)
    '''
    def startTranslatePIL(self):
        print('self.imageFileIn', self.imageFileIn)
        print('self.imageFileOut', self.imageFileOut)

        img = Image.open(self.imageFileIn)
        width, height = img.size


        gcps_source = []
        gcps_target = []

        for point in self.gcpPoints:

            gcps_source.append((point['input_x'], point['input_z']))

            gcps_target.append((point['aar_x'], point['aar_z']))

        coeffs = self.find_coeffs(gcps_source, gcps_source)

        print('coeffs', coeffs)

        #coeffs_startTranslateAh = self.startTranslateAh()

        #print('coeffs_startTranslateAh', coeffs_startTranslateAh)

        img.transform((width, height), Image.PERSPECTIVE, coeffs, Image.BICUBIC).save(self.imageFileOut)

        """
        m = -0.5
        xshift = abs(m) * width
        new_width = width + int(round(xshift))
        img = img.transform((new_width, height), Image.AFFINE,
                (1, m, -xshift if m > 0 else 0, 0, 1, 0), Image.BICUBIC)
        img.save(self.imageFileOut)
        """

    def startTranslateAh(self):
        print('self.imageFileIn', self.imageFileIn)
        print('self.imageFileOut', self.imageFileOut)

        ahTrans = Transformation()

        gcps_source = []
        gcps_target = []

        for point in self.gcpPoints:

            gcps_source.append([point['input_x'], point['input_z']])

            gcps_target.append([point['aar_x'], point['aar_z']])

        print('gcps_source', gcps_source)
        print('gcps_target', gcps_target)

        ahTrans.make_tform(np.array(gcps_source),np.array(gcps_target))

        print('ahTrans', ahTrans)
        print('ahTrans.params', ahTrans.params)

        return ahTrans.params

        #fwdResult = ahTrans.fwd(np.array([[0, 0], [4750,0], [4750,3167], [0,3167]]))
        #print('fwdResult', fwdResult)



    def startTranslate(self):

        print('self.imageFileIn', self.imageFileIn)
        tempOut = self.imageFileOut[:-4]
        tempOut = tempOut + '_translate.tif'
        print('tempOut', tempOut)
        print('self.imageFileOut', self.imageFileOut)
        # Create a copy of the original file and save it as the output filename:

        gdal.Translate(tempOut, self.imageFileIn)

        # Open the output file for writing for writing:
        ds = gdal.Open(tempOut, gdal.GA_Update)
        print ('ds', ds)
        # Set spatial reference:
        sr = osr.SpatialReference()
        sr.ImportFromEPSG(31468)

        # Enter the GCPs
        #   Format: [map x-coordinate(longitude)], [map y-coordinate (latitude)], [elevation],
        #   [image column index(x)], [image row index (y)]

        gcps_aar = []
        print('self.gcpPoints', self.gcpPoints)
        for point in self.gcpPoints:

            gcps_aar.append(gdal.GCP(float(point['aar_x']), float(point['aar_z']), 0, float(point['input_x']), float(point['input_z'])))
            #gcps_aar_test.append([point['aar_x'], point['aar_z'], 0,point['input_x'], point['input_z']])

        # Apply the GCPs to the open output file:
        ds.SetGCPs(gcps_aar, sr.ExportToWkt())

        print('start warp')
        #ds = gdal.Open(self.imageFileOut)
        #gdal.Warp(self.imageFileOut, ds, dstSRS=ds.GetProjection(), options="-overwrite -r bilinear -co compress=none")

        gdal.Warp(self.imageFileOut, ds, dstSRS=ds.GetProjection(), options="-overwrite -r bilinear -order 1 -co compress=none")

        #gdal.Warp(self.imageFileOut, ds, dstSRS=ds.GetProjection(), options="-overwrite -r bilinear -tps -co compress=none")

        # Close the output file in order to be able to work with it in other programs:
        ds = None

        os.remove(tempOut)

        print('finish warp')

    def createGcpShape(self):

        self.rotationCoords = RotationCoords()

        self.rotationCoords.setAarTransformationParams(self.dataStoreGeoref.getAarTransformationParams())

        vl = QgsVectorLayer("Point", "temporary_points", "memory")

        pr = vl.dataProvider()
        vl.startEditing()
        pr.addAttributes([QgsField('UUID', QVariant.String), QgsField('type', QVariant.String)])
        #vl.updateFields()

        shpOut = self.imageFileOut[:-4]
        shpOut = shpOut + 'gcp_aar.shp'

        for point in self.gcpPoints:

            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(point['aar_x']), float(point['aar_z']))))
            feat.setAttributes([point['uuid'], 'aar'])
            pr.addFeature(feat)

            feat = QgsFeature()

            retObj = self.rotationCoords.rotationReverse(float(point['aar_x']), float(point['aar_z']), True)

            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(retObj['x_trans'], retObj['y_trans'])))
            feat.setAttributes([point['uuid'], 'reverse_aar'])
            pr.addFeature(feat)

        vl.updateExtents()

        vl.commitChanges()

        QgsVectorFileWriter.writeAsVectorFormat(vl, shpOut, "UTF-8", QgsCoordinateReferenceSystem('EPSG:31468'), "ESRI Shapefile")







    def updateMetadata(self, refData):

        self.imageFileIn = refData['imagePath']
        self.imageFileOut = refData['savePath']
