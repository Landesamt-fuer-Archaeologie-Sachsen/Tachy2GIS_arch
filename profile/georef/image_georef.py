# -*- coding: utf-8 -*-
import os
from osgeo import gdal, osr
from PIL import Image
import numpy as np
import math

from qgis.core import QgsVectorLayer, QgsField, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsFeature, QgsPointXY, QgsGeometry
from qgis.analysis import QgsGcpTransformerInterface
from PyQt5.QtCore import QVariant

from ..rotation_coords import RotationCoords

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


    def runGeoref(self, georefData, crs, imageFileIn, imageFileOut):

        self.imageFileIn = imageFileIn
        self.imageFileOut = imageFileOut

        print('run ImageGeoref')

        self.crs = crs
        retVal = 'ok'
        self.gcpPoints = georefData
        #print('self.gcpPoints', self.gcpPoints)
        if len(self.gcpPoints) > 3:
            self.__startProjective()
            #self.createGcpShape()
        else:
            retVal = 'error'
            self.__iface.messageBar().pushMessage("Hinweis", "Konnte Profil nicht georeferenzieren. Es müssen min. 4 GCP gesetzt sein!", level=1, duration=5)

        return retVal

   ## \brief Start georeferencing dialog
    #
    #
    def __startProjective(self):
        print('projective - QgsGcpTransformerInterface')

        #source image
        imagePath = self.imageFileIn
        print('imagePath', imagePath)
        imgOrg = Image.open(imagePath)
        src_w, src_h = imgOrg.size

        # vertices of source image (Ecken - Bildraum)
        src_ll = (0, -src_h)
        src_lr = (src_w, -src_h)
        src_ur = (src_w, 0)
        src_ul = (0, 0)

        ############ QgsGcpTransformerInterface ##########

        src_cp = []
        geo_cp = []
        for point in self.gcpPoints:
            src_cp.append(QgsPointXY(float(point['input_x']), float(point['input_z']) * -1 ))
            geo_cp.append(QgsPointXY(float(point['aar_x']), float(point['aar_z'])))

        print('src_cp', src_cp)
        print('geo_cp', geo_cp)

        #(1) get matrix for transformation T1 (src → geo) from 4...n control points
        transformMethod = QgsGcpTransformerInterface.TransformMethod(6) # 6 - projective
        qgisTransformer = QgsGcpTransformerInterface.createFromParameters(transformMethod, src_cp, geo_cp)

        # get extent of destination image in georeferenced area
        # transformation of source image vertices with transformation T1
        # Ecken in Geokoordinaten
        geo_vp_ul = qgisTransformer.transform(src_ul[0], src_ul[1], False)[1:3]
        geo_vp_ll = qgisTransformer.transform(src_ll[0], src_ll[1], False)[1:3]
        geo_vp_ur = qgisTransformer.transform(src_ur[0], src_ur[1], False)[1:3] 
        geo_vp_lr = qgisTransformer.transform(src_lr[0], src_lr[1], False)[1:3] 

        print('geo_vp_ul', geo_vp_ul)
        print('geo_vp_ll', geo_vp_ll)
        print('geo_vp_ur', geo_vp_ur)
        print('geo_vp_lr', geo_vp_lr)

        # calculation of destination image extent in georeferenced area
        #Ausdehnung Geo
        geo_left = min(geo_vp_ul[0], geo_vp_ll[0], geo_vp_ur[0], geo_vp_lr[0])
        geo_lower = min(geo_vp_ul[1], geo_vp_ll[1], geo_vp_ur[1], geo_vp_lr[1])
        geo_right = max(geo_vp_ul[0], geo_vp_ll[0], geo_vp_ur[0], geo_vp_lr[0])
        geo_upper = max(geo_vp_ul[1], geo_vp_ll[1], geo_vp_ur[1], geo_vp_lr[1])

        print('geo_left', geo_left)
        print('geo_lower', geo_lower)
        print('geo_right', geo_right)
        print('geo_upper', geo_upper)

        geo_ll = np.array([geo_left, geo_lower])
        geo_lr = np.array([geo_right, geo_lower])
        geo_ur = np.array([geo_right, geo_upper])
        geo_ul = np.array([geo_left, geo_upper])

        print('geo_ll', geo_ll)
        print('geo_lr', geo_lr)
        print('geo_ur', geo_ur)
        print('geo_ul', geo_ul)

        geo_w = geo_right - geo_left
        geo_h = geo_upper - geo_lower

        print('geo_w', geo_w)
        print('geo_h', geo_h)

        # (3) get transformation T2 from extent of destination image in local
        # (3a) shift upper left vertex to (0,0)
        t2_shift = np.array([-geo_left, -geo_upper])
        print('t2_shift', t2_shift)

        # (3b) resolution of destination image in pixel/m
        # calculated from image extent

        #Strecke oben-links zu unten-rechts

        dist_geo = math.dist(geo_vp_ul,geo_vp_lr)
        dist_img = math.dist(src_ul,src_lr)

        res_geo = dist_img / dist_geo
        res_img = dist_geo / dist_img

        print('dist_img', dist_img)
        print('dist_geo', dist_geo)

        print('res_geo', res_geo)
        print('res_img', res_img)

        dst_resolution = res_geo    

        # (3c) scaling with resolution of destination image
        # korrigiert
        dst_w = dst_resolution * geo_w #Anzahl Pixel im Bildraum
        dst_h = dst_resolution * geo_h

        print('dst_w', dst_w)
        print('dst_h', dst_h)

        # (as 2-dimensional vectors:)

        dst_ll = dst_resolution * (geo_ll + t2_shift)
        dst_lr = dst_resolution * (geo_lr + t2_shift)
        dst_ur = dst_resolution * (geo_ur + t2_shift)
        dst_ul = dst_resolution * (geo_ul + t2_shift)

        print('dst_ll', dst_ll)
        print('dst_lr', dst_lr)
        print('dst_ur', dst_ur)
        print('dst_ul', dst_ul)

        # (4) T2-transformation of the 4 T1-transformed vertices of source image
        # (taken from (2))
        dst_vp_ul = dst_resolution * (geo_vp_ul + t2_shift)
        dst_vp_ll = dst_resolution * (geo_vp_ll + t2_shift)
        dst_vp_ur = dst_resolution * (geo_vp_ur + t2_shift)
        dst_vp_lr = dst_resolution * (geo_vp_lr + t2_shift)

        #dst_vp_ul = res_img * np.array(geo_vp_ul)
        #dst_vp_ll = res_img * np.array(geo_vp_ll)
        #dst_vp_ur = res_img * np.array(geo_vp_ur)
        #dst_vp_lr = res_img * np.array(geo_vp_lr)

        print('geo_vp_ul', geo_vp_ul)
        print('t2_shift', t2_shift)
        print('sum', geo_vp_ul + t2_shift)
        print('dst_vp_ul', dst_vp_ul)
        print('dst_vp_ll', dst_vp_ll)
        print('dst_vp_ur', dst_vp_ur)
        print('dst_vp_lr', dst_vp_lr)

        ########### PIL ##########

        ###goe: hier spiegeln wir die Koordinaten von src und dst vom 4. in den 1. Quadranten, weil Pillow nur mit positiven Passpunkten arbeitet
        ###goe: anstatt 'abs' (das wäre nur bei positiven x-Werten richtig, die wir aber im Prinzip auch haben)
        ###goe: schlage ich aber die Multiplikation mit (1, -1) vor, d.h. alle y-Werte werden mit -1 multipliziert
		#imgCoordEdges = [src_ul, src_ur, src_lr, src_ll]
        ###goe: und 'edges' sind Kanten, reduzieren wir lieber auf imgCoords
        imgCoords = np.multiply([src_ul, src_ur, src_lr, src_ll], (1,-1))
        #projectiveCoordEdges = [tuple(dst_vp_ul), tuple(dst_vp_ur), tuple(dst_vp_lr), tuple(dst_vp_ll)]
        projectiveCoords = np.multiply([tuple(dst_vp_ul), tuple(dst_vp_ur), tuple(dst_vp_lr), tuple(dst_vp_ll)], (1,-1))
        coeffs = self.__find_pill_coeffs(projectiveCoords,imgCoords)

        print('coeffs', coeffs)
        self.__imgTransform(self.imageFileIn, self.imageFileOut, coeffs, dst_h, dst_w)
        print('finish pil')
        worldfilePath = self.imageFileOut[:-3]+"wld"
        #imageGeoWidth = ur_geo[1] - ul_geo[1]
        #print('imageGeoWidth', imageGeoWidth)
        self.__writeWorldFile(worldfilePath, geo_ul, res_img)
        print('finish worldfile')


    #where pb is the four vertices in the current plane, and pa contains four vertices in the resulting plane.
    def __find_pill_coeffs(self, pa, pb):
        matrix = []
        for p1, p2 in zip(pa, pb):
            matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
            matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])

        A = np.matrix(matrix, dtype=np.float)
        B = np.array(pb).reshape(8)

        res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
        return np.array(res).reshape(8)


    def __imgTransform(self, image_in, image_out, coeffs, heightDst, widthDst):

        img = Image.open(image_in)

        img.transform((int(widthDst), int(heightDst)), Image.PERSPECTIVE, coeffs, Image.BICUBIC).save(image_out)

    def __writeWorldFile(self, worldfilePath, geo_ul, res_img):

        pixelwidth = res_img
        pixelheight = res_img * -1

        lines = [str(pixelwidth), str(0.0), str(0.0), str(pixelheight), str(geo_ul[0]), str(geo_ul[1])]
        with open(worldfilePath, 'w') as f:
            for line in lines:
                f.write(line)
                f.write('\n')


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

    #def updateMetadata(self, refData):
    #    self.imageFileIn = refData['imagePath']
    #    self.imageFileOut = refData['savePath']
