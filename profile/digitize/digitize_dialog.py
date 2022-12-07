# -*- coding: utf-8 -*-
import os
from PyQt5.QtWidgets import QWidget, QMainWindow, QAction, QVBoxLayout
from PyQt5.QtGui import QIcon
from qgis.gui import QgsMessageBar

from .parambar import Parambar
from .digitize_canvas import DigitizeCanvas
from .digitize_table import DigitizeTable
from .maptool_identify import MapToolIdentify
from .maptool_digi_point import MapToolDigiPoint
from .maptool_digi_line import MapToolDigiLine
from .maptool_digi_polygon import MapToolDigiPolygon

from .maptool_edit_point import MapToolEditPoint
from .maptool_edit_line import MapToolEditLine
from .maptool_edit_polygon import MapToolEditPolygon
## @brief With the GeoreferencingDialog class a dialog window for the georeferencing of profiles is realized
#
# The class inherits form QMainWindow
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-25-05

class DigitizeDialog(QMainWindow):

    def __init__(self, dataStoreDigitize, rotationCoords, iFace, aar_direction):

        super(DigitizeDialog, self).__init__()

        self.__iface = iFace

        self.iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')

        self.aar_direction = aar_direction

        self.dataStoreDigitize = dataStoreDigitize
        self.rotationCoords = rotationCoords

        prof_nr = self.dataStoreDigitize.getProfileNumber()
        self.setWindowTitle(f"Digitalisieren im Profil: {prof_nr}")

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
        self.canvasDigitize = DigitizeCanvas(self, self.__iface)

        #MapTools
        self.toolIdentify = MapToolIdentify(self.canvasDigitize, self.__iface)
        self.toolDigiPoint = MapToolDigiPoint(self.canvasDigitize, self.__iface, self.rotationCoords, self.dataStoreDigitize)
        self.toolDigiLine = MapToolDigiLine(self.canvasDigitize, self.__iface, self.rotationCoords, self.dataStoreDigitize)
        self.toolDigiPolygon = MapToolDigiPolygon(self.canvasDigitize, self.__iface, self.rotationCoords, self.dataStoreDigitize)

        self.toolEditPoint = MapToolEditPoint(self.canvasDigitize, self.__iface, self.rotationCoords)
        self.toolEditLine = MapToolEditLine(self.canvasDigitize, self.__iface, self.rotationCoords)
        self.toolEditPolygon = MapToolEditPolygon(self.canvasDigitize, self.__iface, self.rotationCoords)

        #paramsBar
        self.parambar = Parambar(self, self.canvasDigitize, self.toolIdentify, self.toolDigiPoint, self.toolDigiLine, self.toolDigiPolygon, self.toolEditPoint, self.toolEditLine, self.toolEditPolygon, self.rotationCoords, self.aar_direction)

        #Table
        self.tableDigitize = DigitizeTable(self)

    ## \brief Event connections
    #

    def createConnects(self):

        self.canvasDigitize.pup.register('moveCoordinate', self.parambar.updateCoordinate)
        self.canvasDigitize.pup.register('setDigiPointLayer', self.toolDigiPoint.setDigiPointLayer)
        self.canvasDigitize.pup.register('setDigiLineLayer', self.toolDigiLine.setDigiLineLayer)
        self.canvasDigitize.pup.register('setDigiPolygonLayer', self.toolDigiPolygon.setDigiPolygonLayer)

        self.canvasDigitize.pup.register('setDigiPointLayer', self.toolIdentify.setDigiPointLayer)
        self.canvasDigitize.pup.register('setDigiLineLayer', self.toolIdentify.setDigiLineLayer)
        self.canvasDigitize.pup.register('setDigiPolygonLayer', self.toolIdentify.setDigiPolygonLayer)

        self.canvasDigitize.pup.register('setDigiPointLayer', self.toolEditPoint.setDigiPointLayer)
        self.canvasDigitize.pup.register('setDigiLineLayer', self.toolEditLine.setDigiLineLayer)
        self.canvasDigitize.pup.register('setDigiPolygonLayer', self.toolEditPolygon.setDigiPolygonLayer)

        self.canvasDigitize.pup.register('updateFeatureAttr', self.tableDigitize.updateFeature)

        #self.parambar.pup.register('triggerAarTransformationParams', self.dataStoreDigitize.triggerAarTransformationParams)
        self.dataStoreDigitize.pup.register('pushTransformationParams', self.rotationCoords.setAarTransformationParams)

        self.toolDigiPoint.pup.register('pointFeatureAttr', self.tableDigitize.insertFeature)
        self.toolDigiLine.pup.register('lineFeatureAttr', self.tableDigitize.insertFeature)
        self.toolDigiPolygon.pup.register('polygonFeatureAttr', self.tableDigitize.insertFeature)

        self.tableDigitize.pup.register('removeFeatureByUuid', self.canvasDigitize.removeFeatureByUuid)
        self.tableDigitize.pup.register('editFeatureAttributes', self.canvasDigitize.editFeatureAttributes)

        self.tableDigitize.pup.register('removeFeatureByUuid', self.toolDigiPoint.removeFeatureInEingabelayerByUuid)
        self.tableDigitize.pup.register('removeFeatureByUuid', self.toolDigiLine.removeFeatureInEingabelayerByUuid)
        self.tableDigitize.pup.register('removeFeatureByUuid', self.toolDigiPolygon.removeFeatureInEingabelayerByUuid)

        self.toolIdentify.pup.register('removeHoverFeatures', self.canvasDigitize.removeHoverFeatures)
        self.toolIdentify.pup.register('addHoverFeatures', self.canvasDigitize.addHoverFeatures)

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
        verticalLayout.addWidget(self.parambar)
        verticalLayout.addWidget(self.canvasDigitize)
        verticalLayout.addWidget(self.tableDigitize)

    def restore(self, refData):

        self.canvasDigitize.update(refData)
        self.parambar.update(refData)
        self.toolDigiPoint.update(refData)
        self.toolDigiLine.update(refData)
        self.toolDigiPolygon.update(refData)

        self.adjustSize()
        self.show()
        self.resize(1000, 700)


    ## \brief Open up the digitize dialog
    #
    # calls the funcion restore()
    #
    # \param refData

    def showDigitizeDialog(self, refData):
        self.restore(refData)

        bufferGeometry = self.rotationCoords.profileBuffer(1, self.aar_direction)

        self.toolDigiPoint.getFeaturesFromEingabelayer(bufferGeometry, 'profile', self.aar_direction)
        self.toolDigiLine.getFeaturesFromEingabelayer(bufferGeometry, 'profile', self.aar_direction)
        self.toolDigiPolygon.getFeaturesFromEingabelayer(bufferGeometry, 'profile', self.aar_direction)
