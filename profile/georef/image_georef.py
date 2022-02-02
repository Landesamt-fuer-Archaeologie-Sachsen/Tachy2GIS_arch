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

    def __init__(self, dialogInstance, dataStoreGeoref, iFace):

        print('init ImageGeoref')

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')

        self.dialogInstance = dialogInstance

        self.imageFileIn = ''

        self.imageFileOut = ''

        self.gcpPoints = ''

        self.dataStoreGeoref = dataStoreGeoref

        self.__iface = iFace

        self.crs = ''


    def runGeoref(self, georefData, crs):
        print('run ImageGeoref')

        self.crs = crs
        retVal = 'ok'
        self.gcpPoints = georefData
        if len(self.gcpPoints) > 2:
            self.startTranslate()
            self.createGcpShape()
        else:
            retVal = 'error'
            self.__iface.messageBar().pushMessage("Hinweis", "Konnte Profil nicht georeferenzieren. Es müssen min. 3 GCP gesetzt sein!", level=1, duration=5)

        return retVal


    def startTranslate(self):

        tempOut = self.imageFileOut[:-4]
        tempOut = tempOut + '_translate.tif'
        # Create a copy of the original file and save it as the output filename:

        gdal.Translate(tempOut, self.imageFileIn)

        # Open the output file for writing:
        ds = gdal.Open(tempOut, gdal.GA_Update)
        # Set spatial reference:
        sr = osr.SpatialReference()
        sr.ImportFromEPSG(self.crs.postgisSrid()) #z.B 31468

        # Enter the GCPs
        #   Format: [map x-coordinate(longitude)], [map y-coordinate (latitude)], [elevation],
        #   [image column index(x)], [image row index (y)]

        gcps_aar = []
        for point in self.gcpPoints:

            gcps_aar.append(gdal.GCP(float(point['aar_x']), float(point['aar_z']), 0, float(point['input_x']), float(point['input_z'])))

        # Apply the GCPs to the open output file:

        ds.SetGCPs(gcps_aar, sr.ExportToWkt())

        print('start warp', self.crs.authid())
        gdal.Warp(self.imageFileOut, ds, srcSRS=self.crs.authid(), dstSRS=self.crs.authid(), options="-overwrite -r bilinear -order 1 -co compress=none -co worldfile=yes")

        # Close the output file in order to be able to work with it in other programs:
        ds = None

        jpgOut = self.imageFileOut[:-4]
        jpgOut = jpgOut + '.jpg'

        translateoptions = gdal.TranslateOptions(creationOptions=['WORLDFILE=YES'], format='JPEG')

        gdal.Translate(jpgOut, self.imageFileOut, options=translateoptions)

        os.remove(tempOut)

        print('finish warp')

    def createGcpShape(self):

        self.rotationCoords = RotationCoords(self)

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
