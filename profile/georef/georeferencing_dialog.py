# -*- coding: utf-8 -*-
import os
import json
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QAction, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from qgis.gui import QgsMessageBar

from .profile_image_canvas import ProfileImageCanvas
from .profile_gcp_canvas import ProfileGcpCanvas
from .profile_georef_table import GeorefTable
from .image_parambar import ImageParambar
from .gcp_parambar import GcpParambar
from .image_georef import ImageGeoref

from ..profileAAR.profileAAR import profileAAR

## @brief With the GeoreferencingDialog class a dialog window for the georeferencing of profiles is realized
#
# The class inherits form QMainWindow
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-25-05

class GeoreferencingDialog(QMainWindow):

    def __init__(self, t2GArchInstance, dataStoreGeoref, rotationCoords, iFace):

        super(GeoreferencingDialog, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')

        self.t2GArchInstance = t2GArchInstance

        self.setAttribute(Qt.WA_DeleteOnClose)

        self.refData = None

        self.__iface = iFace

        #DataStore
        self.dataStoreGeoref = dataStoreGeoref

        self.rotationCoords = rotationCoords

        self.createMenu()
        self.createComponents()
        self.createLayout()
        self.createConnects()

    def closeEvent(self, event):
        print('close')
        self.dataStoreGeoref.clearStore()
        #self.georefTable.cleanGeorefTable()

        #self.canvasImage

    ## \brief Create different menus
    #
    #
    # creates the menuBar at upper part of the window and statusBar in the lower part
    #
    def createMenu(self):

        self.statusBar()

        self.statusBar().reformat()
        self.statusBar().setStyleSheet('background-color: #FFF8DC;')
        self.statusBar().setStyleSheet("QStatusBar::item {border: none;}")

        exitAct = QAction(QIcon(os.path.join(self.iconpath , 'Ok_grau.png')), 'Exit', self)

        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Anwendung schließen')
        exitAct.triggered.connect(self.close)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Datei')
        fileMenu.addAction(exitAct)

    ## \brief ECreates the components of the window
    #
    # - MessageBar to give hints
    # - Parameterbar to show the results of the transformation, instantiate class GeoreferencingDialogParambar() as self.transformationParamsBar
    # - Canvas component for layer display, instantiate class GeoreferencingDialogCanvas as self.canvasTransform
    # - Table with the GCPs, instantiate class GeoreferencingDialogTable() as self.georefTable
    # - Coordinates in statusBar
    # - instantiate class GeoreferencingCalculations as self.paramCalc

    # @returns
    def createComponents(self):

        #messageBar
        self.messageBar = QgsMessageBar()

        #Canvas Elemente
        self.canvasImage = ProfileImageCanvas(self)
        self.canvasGcp = ProfileGcpCanvas(self, self.rotationCoords)

        #paramsBar
        self.imageParambar = ImageParambar(self, self.canvasImage)
        self.gcpParambar = GcpParambar(self, self.canvasGcp)

        #Actions
        self.createActions()

        #Toolbars
        self.createToolbars()

        #GcpTable
        self.georefTable = GeorefTable(self, self.dataStoreGeoref)

        #profileAAR
        self.profileAAR = profileAAR()

        #Bildgeoreferenzierung
        self.imageGeoref = ImageGeoref(self, self.dataStoreGeoref, self.__iface)



    ## \brief Event connections
    #

    def createConnects(self):

        self.georefTable.pup.register('activatePoint', self.canvasGcp.setActivePoint)
        self.georefTable.pup.register('activatePoint', self.canvasImage.setActivePoint)
        self.georefTable.pup.register('activatePoint', self.imageParambar.activateMapToolMove)
        self.canvasImage.pup.register('imagePointCoordinates', self.georefTable.updateImageCoordinates)
        self.canvasImage.pup.register('imagePointCoordinates', self.dataStoreGeoref.addImagePoint)
        self.canvasImage.pup.register('imagePointCoordinates', self.georefTable.updateErrorValues)

        self.georefTable.pup.register('dataChanged', self.profileAAR.run)

        self.profileAAR.pup.register('aarPointsChanged', self.dataStoreGeoref.addAarPoints)

        self.dataStoreGeoref.pup.register('pushTransformationParams', self.rotationCoords.setAarTransformationParams)

        self.canvasGcp.pup.register('moveCoordinate',self.gcpParambar.updateCoordinate)
        self.canvasImage.pup.register('moveCoordinate',self.imageParambar.updateCoordinate)

        self.startGeorefBtn.clicked.connect(self.startGeoreferencing)

    ## \brief create actions
    #
    def createActions(self):

        #Export
        iconExport = QIcon(os.path.join(self.iconpath, 'mActionSaveGCPpointsAs.png'))
        self.actionExport = QAction(iconExport, "Export data", self)

        #Import
        iconImport = QIcon(os.path.join(self.iconpath, 'mActionLoadGCPpoints.png'))
        self.actionImport = QAction(iconImport, "Import data", self)

    ## \brief create toolbars
    #
    # - toolbarMap
    def createToolbars(self):

        #Toolbar Kartennavigation
        self.toolbarMap = self.addToolBar("Kartennavigation")

        self.startGeorefBtn = QPushButton("Profil entzerren", self)

        self.startGeorefBtn.setStyleSheet("background-color: green; width: 200px")

        self.toolbarMap.addWidget(self.startGeorefBtn)

        #self.toolbarMap.setContentsMargins(4,4,4,4);


        #self.toolbarMap.setStyleSheet("padding-top: 8px; padding-bottom: 8px;")

        #self.toolbarMap.addAction(self.canvasTransform.actionPan)
        #self.toolbarMap.addAction(self.canvasTransform.actionZoomIn)
        #self.toolbarMap.addAction(self.canvasTransform.actionZoomOut)
        #self.toolbarMap.addAction(self.canvasTransform.actionExtent)

    ## \brief Creates the layout for the window and assigns the created components
    #

    def createLayout(self):

        widgetCentral = QWidget()

        verticalLayout = QVBoxLayout()
        verticalLayout.setContentsMargins(0,0,0,0)
        verticalLayout.setSpacing(0)
        widgetCentral.setLayout(verticalLayout)
        self.setCentralWidget(widgetCentral)

        verticalLayout.addWidget(self.messageBar)

        verticalImageLayout = QVBoxLayout()
        verticalImageLayout.addWidget(self.imageParambar)
        verticalImageLayout.addWidget(self.canvasImage)

        verticalGcpLayout = QVBoxLayout()
        verticalGcpLayout.addWidget(self.gcpParambar)
        verticalGcpLayout.addWidget(self.canvasGcp)

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addLayout(verticalImageLayout)
        horizontalLayout.addLayout(verticalGcpLayout)

        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addWidget(self.georefTable)

    def restore(self, refData):

        self.refData = refData

        self.georefTable.cleanGeorefTable()
        self.georefTable.updateGeorefTable(refData)
        self.georefTable.pointUsageChanged()

        validImageLayer = self.canvasImage.updateCanvas(refData['imagePath'])

        if validImageLayer == True:
            self.canvasGcp.updateCanvas(refData)

            self.dataStoreGeoref.addTargetPoints(refData)

            self.imageGeoref.updateMetadata(refData)

            self.adjustSize()
            self.show()
            self.resize(1000, 700)
        else:
            self.__iface.messageBar().pushMessage("Error", "Rasterlayer konnte nicht gelesen werden", level=1, duration=3)

    ## \brief Export GCP-Data in a textfile
    #
    def writeMetafile(self):

        saveFileName = self.refData['savePath'][:-3]
        saveFileName = saveFileName + 'meta'
        print('saveFileName', saveFileName)

        if self.refData['horizontal'] == True:
            ebene = 'vertikal'
        else:
            ebene = 'geneigt'

        data = {
        	"profilnummer": self.refData['profileNumber'],
        	"profil": self.refData['savePath'],
        	"profilfoto": self.refData['imagePath'],
        	"blickrichtung": self.refData['viewDirection'],
        	"entzerrungsebene": ebene,
        	"gcps": self.dataStoreGeoref.getGeorefData(),
        	"transform_params": self.dataStoreGeoref.getAarTransformationParams()
        }

        with open(saveFileName, 'w') as outfile:
            json.dump(data, outfile)

        return saveFileName
    ## \brief Open up the transformation dialog
    #
    # calls the funcion restore()
    #
    # \param refData

    def showGeoreferencingDialog(self, refData):

        self.restore(refData)


    def startGeoreferencing(self):
        georefData = self.dataStoreGeoref.getGeorefData()
        georefChecker = self.imageGeoref.runGeoref(georefData, self.refData['crs'])
        if georefChecker == 'ok':
            fileName = self.writeMetafile()
            print('fertig')
            self.__iface.messageBar().pushMessage("Hinweis", "Das Profil wurde unter "+fileName+" referenziert", level=3, duration=5)

        self.close()
        self.destroy()
