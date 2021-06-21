# -*- coding: utf-8 -*-
import os
import subprocess
from PyQt5.QtCore import QFileInfo

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
        self.startWarp()

    def startTranslate(self):

        fileInfo = QFileInfo(self.imageFileIn)
        baseName = fileInfo.baseName()

        command = 'gdal_translate -of GTiff'

        for point in self.gcpPoints:
            command += ' -gcp '+str(float(point['input_x']))+' '+str(float(point['input_z']))+' '+str(float(point['aar_x']))+' '+str(float(point['aar_y']))

        command += ' '+self.imageFileIn+' '+self.imageFileOut

        print('command', command)
        proc = subprocess.Popen(command)

    def startWarp(self):
        pass

        #gdal_translate -of GTiff -gcp 310.316 1329.26 4.57733e+06 5.7099e+06 -gcp 2320.42 1278.32 4.57733e+06 5.7099e+06 -gcp 4409.26 1306.11 4.57733e+06 5.7099e+06 -gcp 4154.53 2876.21 4.57733e+06 5.7099e+06 -gcp 2292.63 2853.05 4.57733e+06 5.7099e+06 "Y:/Projekte/2021/lfa_profil/beispieldaten/AZB-16/AZB-16/Entzerrungen/AZB-16_Pr50.JPG" "C:/Users/Mario/AppData/Local/Temp/AZB-16_Pr50.JPG"
        #gdalwarp -r near -order 1 -co COMPRESS=NONE  "C:/Users/Mario/AppData/Local/Temp/AZB-16_Pr50.JPG" "Y:/Projekte/2021/lfa_profil/tests/AZB-16_Pr50_modifiziert.tif"


    def updateMetadata(self, refData):

        self.imageFileIn = refData['imagePath']
        self.imageFileOut = refData['savePath']
