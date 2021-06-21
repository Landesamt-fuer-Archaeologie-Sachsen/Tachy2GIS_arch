# -*- coding: utf-8 -*-
import os
import csv
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QAction, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from qgis.gui import QgsMessageBar

from .profile_image_canvas import ProfileImageCanvas
from .profile_gcp_canvas import ProfileGcpCanvas
from .profile_georef_table import GeorefTable
from .image_parambar import ImageParambar
from .gcp_parambar import GcpParambar
from .image_georef import ImageGeoref
from .data_store import DataStore

from .profileAAR.profileAAR import profileAAR

## @brief With the GeoreferencingDialog class a dialog window for the georeferencing of profiles is realized
#
# The class inherits form QMainWindow
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-25-05

class GeoreferencingDialog(QMainWindow):

    def __init__(self, t2GArchInstance):

        super(GeoreferencingDialog, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), 'Icons')

        self.t2GArchInstance = t2GArchInstance

        self.createMenu()
        self.createComponents()
        self.createLayout()
        self.createConnects()

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
        self.canvasGcp = ProfileGcpCanvas(self)

        #paramsBar
        self.imageParambar = ImageParambar(self, self.canvasImage)
        self.gcpParambar = GcpParambar(self, self.canvasGcp)

        #Actions
        self.createActions()

        #Toolbars
        self.createToolbars()

        #Coordinates in statusBar
        #self.createStatusBar()

        #TransformationParamsBar
        #self.transformationParamsBar = TransformationDialogParambar(self)

        #GcpTable
        self.georefTable = GeorefTable(self)

        #profileAAR
        self.profileAAR = profileAAR()

        #Bildgeoreferenzierung
        self.imageGeoref = ImageGeoref(self)

        #DataStore
        self.dataStore = DataStore()

    ## \brief Event connections
    #

    def createConnects(self):

        self.georefTable.pup.register('activatePoint', self.canvasGcp.setActivePoint)
        self.georefTable.pup.register('activatePoint', self.canvasImage.setActivePoint)
        self.georefTable.pup.register('activatePoint', self.imageParambar.activateMapToolMove)
        self.canvasImage.pup.register('imagePointCoordinates', self.georefTable.updateImageCoordinates)
        self.canvasImage.pup.register('imagePointCoordinates', self.dataStore.addImagePoint)

        self.georefTable.pup.register('dataChanged', self.profileAAR.run)

        self.profileAAR.pup.register('aarPointsChanged', self.dataStore.addAarPoints)

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

        self.toolbarMap.addWidget(self.startGeorefBtn)
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

        self.georefTable.cleanGeorefTable()
        self.georefTable.updateGeorefTable(refData)
        self.georefTable.pointUsageChanged()

        self.canvasImage.updateCanvas(refData['imagePath'])
        self.canvasGcp.updateCanvas(refData)

        self.dataStore.addTargetPoints(refData)

        self.imageGeoref.updateMetadata(refData)

        self.adjustSize()
        self.show()
        self.resize(1000, 700)


    ## \brief Open up the transformation dialog
    #
    # calls the funcion restore()
    #
    # \param refData

    def showGeoreferencingDialog(self, refData):
        self.restore(refData)


    def startGeoreferencing(self):
        georefData = self.dataStore.getGeorefData()
        self.imageGeoref.runGeoref(georefData)
