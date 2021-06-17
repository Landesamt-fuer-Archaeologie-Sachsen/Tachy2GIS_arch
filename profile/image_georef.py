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

        self.gcpPoints = [
            [100, 200, 5674562, 5463215],
            [200, 200, 5674562, 5463215],
            [300, 200, 5674562, 5463215],
            [400, 200, 5674562, 5463215]
        ]


    def runGeoref(self):
        print('run ImageGeoref')
        self.startTranslate()
        self.startWarp()

    def startTranslate(self):

        fileInfo = QFileInfo(self.imageFileIn)
        baseName = fileInfo.baseName()

        command = ['gdal_translate', '-of', 'GTiff']

        for point in self.gcpPoints:
            command.append("-gcp")
            command.append(str(round(float(point[0]))))
            command.append(str(round(float(point[1]))))
            command.append(str(round(float(point[2]))))
            command.append(str(round(float(point[3]))))

        command.append(self.imageFileIn)
        command.append(self.imageFileOut)

        print('command', command)
        proc = subprocess.Popen(command)

    def startWarp(self):
        pass

    def updateMetadata(self, refData):

        self.imageFileIn = refData['imagePath']
        self.imageFileOut = refData['savePath']
