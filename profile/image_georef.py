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

        import shutil
        from osgeo import gdal, osr

        orig_fn = self.imageFileIn
        output_fn = self.imageFileOut

        print('orig_fn', orig_fn)
        print('output_fn', output_fn)
        # Create a copy of the original file and save it as the output filename:
        shutil.copy(orig_fn, output_fn)
        print('copy_fin')
        # Open the output file for writing for writing:
        ds = gdal.Open(output_fn, gdal.GA_Update)
        # Set spatial reference:
        sr = osr.SpatialReference()
        sr.ImportFromEPSG(31468) #2193 refers to the NZTM2000, but can use any desired projection

        # Enter the GCPs
        #   Format: [map x-coordinate(longitude)], [map y-coordinate (latitude)], [elevation],
        #   [image column index(x)], [image row index (y)]
        '''
        gcps = []
        for point in self.gcpPoints:

            gcps.append(gdal.GCP(float(point['aar_x']), float(point['aar_y']), 0, float(point['input_x']), float(point['input_z'])))

        '''
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

        print('gcps', gcps)
        # Apply the GCPs to the open output file:
        ds.SetGCPs(gcps, sr.ExportToWkt())

        # Close the output file in order to be able to work with it in other programs:
        ds = None
















    def startTranslate_old(self):

        fileInfo = QFileInfo(self.imageFileIn)
        baseName = fileInfo.baseName()

        command = 'gdal_translate -of GTiff'

        for point in self.gcpPoints:
            command += ' -gcp '+str(float(point['input_x']))+' '+str(float(point['input_z']))+' '+str(float(point['aar_x']))+' '+str(float(point['aar_y']))

        command += ' '+self.imageFileIn+' '+self.imageFileOut

        print('command', command)
        proc = subprocess.Popen(command)

    def startWarp(self):

        command = 'gdalwarp -r near -order 1 -co COMPRESS=NONE '+self.imageFileOut+' '+self.imageFileOut

        print('command', command)
        proc = subprocess.Popen(command)


        #gdal_translate -of GTiff -gcp 310.316 1329.26 4.57733e+06 5.7099e+06 -gcp 2320.42 1278.32 4.57733e+06 5.7099e+06 -gcp 4409.26 1306.11 4.57733e+06 5.7099e+06 -gcp 4154.53 2876.21 4.57733e+06 5.7099e+06 -gcp 2292.63 2853.05 4.57733e+06 5.7099e+06 "Y:/Projekte/2021/lfa_profil/beispieldaten/AZB-16/AZB-16/Entzerrungen/AZB-16_Pr50.JPG" "C:/Users/Mario/AppData/Local/Temp/AZB-16_Pr50.JPG"
        #gdalwarp -r near -order 1 -co COMPRESS=NONE  "C:/Users/Mario/AppData/Local/Temp/AZB-16_Pr50.JPG" "Y:/Projekte/2021/lfa_profil/tests/AZB-16_Pr50_modifiziert.tif"


    def updateMetadata(self, refData):

        self.imageFileIn = refData['imagePath']
        self.imageFileOut = refData['savePath']
