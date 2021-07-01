# -*- coding: utf-8 -*-
import os
import subprocess
from PyQt5.QtCore import QFileInfo
import shutil
from osgeo import gdal, osr

class ImageGeoref():

    def __init__(self, dialogInstance):

        print('init ImageGeoref')

        self.iconpath = os.path.join(os.path.dirname(__file__), 'Icons')

        self.dialogInstance = dialogInstance

        self.imageFileIn = ''

        self.imageFileOut = ''

        self.gcpPoints = ''


    def runGeoref(self, georefData):
        print('run ImageGeoref')

        self.gcpPoints = georefData
        self.startTranslate()
        #self.startWarp()


    def startTranslate(self):

        print('self.imageFileIn', self.imageFileIn)
        print('self.imageFileOut', self.imageFileOut)
        # Create a copy of the original file and save it as the output filename:

        gdal.Translate(self.imageFileOut, self.imageFileIn)

        # Open the output file for writing for writing:
        ds = gdal.Open(self.imageFileOut, gdal.GA_Update)
        print ('ds', ds)
        # Set spatial reference:
        sr = osr.SpatialReference()
        sr.ImportFromEPSG(31468) #2193 refers to the NZTM2000, but can use any desired projection

        # Enter the GCPs
        #   Format: [map x-coordinate(longitude)], [map y-coordinate (latitude)], [elevation],
        #   [image column index(x)], [image row index (y)]

        gcps_aar = []
        gcps_aar_test = []
        for point in self.gcpPoints:

            gcps_aar.append(gdal.GCP(float(point['aar_x']), float(point['aar_z']), 0, float(point['input_x']), float(point['input_z'])))
            gcps_aar_test.append([point['aar_x'], point['aar_z'], 0,point['input_x'], point['input_z']])



        gcps = [
             gdal.GCP(4577329.306, 5709902.965, 0, 324.211, 1338.53),
             gdal.GCP(4577329.25, 5709903.024, 0, 518.737, 2778.95),
             gdal.GCP(4577327.626, 5709902.911, 0, 4409.26, 1301.47),
             gdal.GCP(4577327.635, 5709902.953, 0, 4159.16, 2862.32)

        ]

        #gdal.GCP  (316.80P,-1344.00L) -> (4577329.3363898E,5709903.5600224N,0.00)
        #gdal.GCP  (4396.80P,-1305.60L) -> (4577328.5085405E,5709902.3338992N,0.00)
        #gdal.GCP  (4128.00P,-2880.00L) -> (4577327.7580637E,5709902.3699617N,0.00)
        #gdal.GCP  (518.40P,-2774.40L) -> (4577328.5335992E,5709903.5621437N,0.00)
        print('gcps_aar_test', gcps_aar_test)
        print('gcps', gcps)
        # Apply the GCPs to the open output file:
        ds.SetGCPs(gcps_aar, sr.ExportToWkt())

        # Close the output file in order to be able to work with it in other programs:
        ds = None

    def startWarp(self):

        command = 'gdalwarp -r near -order 1 -co COMPRESS=NONE '+self.imageFileOut+' '+self.imageFileOut

        print('command', command)
        proc = subprocess.Popen(command)


        #gdal_translate -of GTiff -gcp 310.316 1329.26 4.57733e+06 5.7099e+06 -gcp 2320.42 1278.32 4.57733e+06 5.7099e+06 -gcp 4409.26 1306.11 4.57733e+06 5.7099e+06 -gcp 4154.53 2876.21 4.57733e+06 5.7099e+06 -gcp 2292.63 2853.05 4.57733e+06 5.7099e+06 "Y:/Projekte/2021/lfa_profil/beispieldaten/AZB-16/AZB-16/Entzerrungen/AZB-16_Pr50.JPG" "C:/Users/Mario/AppData/Local/Temp/AZB-16_Pr50.JPG"
        #gdalwarp -r near -order 1 -co COMPRESS=NONE  "C:/Users/Mario/AppData/Local/Temp/AZB-16_Pr50.JPG" "Y:/Projekte/2021/lfa_profil/tests/AZB-16_Pr50_modifiziert.tif"


    def updateMetadata(self, refData):

        self.imageFileIn = refData['imagePath']
        self.imageFileOut = refData['savePath']
