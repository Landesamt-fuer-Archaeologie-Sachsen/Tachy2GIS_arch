# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QAction, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from qgis.gui import QgsMessageBar

from .parambar import Parambar
from .digitize_canvas import DigitizeCanvas
from .digitize_table import DigitizeTable
from .maptool_digi_point import MapToolDigiPoint
from .maptool_digi_line import MapToolDigiLine
from .maptool_digi_polygon import MapToolDigiPolygon

from .maptool_edit_line import MapToolEditLine
from .rotation_coords import RotationCoords
## @brief With the GeoreferencingDialog class a dialog window for the georeferencing of profiles is realized
#
# The class inherits form QMainWindow
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-25-05

class DigitizeDialog(QMainWindow):

    def __init__(self, dataStoreDigitize, iFace):

        super(DigitizeDialog, self).__init__()

        self.__iface = iFace

        self.iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')

        self.dataStoreDigitize = dataStoreDigitize

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

        #RotationCoords
        self.rotationCoords = RotationCoords()

        #MapTools
        self.toolDigiPoint = MapToolDigiPoint(self.canvasDigitize, self.__iface, self.rotationCoords)
        self.toolDigiLine = MapToolDigiLine(self.canvasDigitize, self.__iface, self.rotationCoords)
        self.toolDigiPolygon = MapToolDigiPolygon(self.canvasDigitize, self.__iface, self.rotationCoords)

        self.toolEditLine = MapToolEditLine(self.canvasDigitize, self.__iface, self.rotationCoords)

        #paramsBar
        self.parambar = Parambar(self, self.canvasDigitize, self.toolDigiPoint, self.toolDigiLine, self.toolDigiPolygon, self.toolEditLine, self.rotationCoords)

        #Table
        self.tableDigitize = DigitizeTable(self)



    ## \brief Event connections
    #

    def createConnects(self):

        self.canvasDigitize.pup.register('moveCoordinate', self.parambar.updateCoordinate)
        self.canvasDigitize.pup.register('setDigiPointLayer', self.toolDigiPoint.setDigiPointLayer)
        self.canvasDigitize.pup.register('setDigiLineLayer', self.toolDigiLine.setDigiLineLayer)
        self.canvasDigitize.pup.register('setDigiPolygonLayer', self.toolDigiPolygon.setDigiPolygonLayer)

        self.canvasDigitize.pup.register('setDigiLineLayer', self.toolEditLine.setDigiLineLayer)

        #self.parambar.pup.register('triggerAarTransformationParams', self.dataStoreDigitize.triggerAarTransformationParams)
        self.dataStoreDigitize.pup.register('pushTransformationParams', self.rotationCoords.setAarTransformationParams)

        self.toolDigiPoint.pup.register('pointFeatureAttr', self.tableDigitize.insertFeature)
        self.toolDigiLine.pup.register('lineFeatureAttr', self.tableDigitize.insertFeature)
        self.toolDigiPolygon.pup.register('polygonFeatureAttr', self.tableDigitize.insertFeature)

        self.tableDigitize.pup.register('removeFeatureByUuid', self.canvasDigitize.removeFeatureByUuid)

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
