# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QAction, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from qgis.gui import QgsMessageBar

from .parambar import Parambar
from .digitize_canvas import DigitizeCanvas

## @brief With the GeoreferencingDialog class a dialog window for the georeferencing of profiles is realized
#
# The class inherits form QMainWindow
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-25-05

class DigitizeDialog(QMainWindow):

    def __init__(self, t2GArchInstance):

        super(DigitizeDialog, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')

        self.t2GArchInstance = t2GArchInstance

        self.createMenu()
        self.createComponents()
        self.createLayout()
        #self.createConnects()

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
        self.canvasDigitize = DigitizeCanvas(self)

        #paramsBar
        self.parambar = Parambar(self, self.canvasDigitize)


    ## \brief Creates the layout for the window and assigns the created components
    #

    def createLayout(self):

        widgetCentral = QWidget()

        verticalLayout = QVBoxLayout()
        verticalLayout.setContentsMargins(0,0,0,0)
        widgetCentral.setLayout(verticalLayout)
        self.setCentralWidget(widgetCentral)

        verticalLayout.addWidget(self.messageBar)
        verticalLayout.addWidget(self.parambar)
        verticalLayout.addWidget(self.canvasDigitize)

    def restore(self, refData):

        self.canvasDigitize.update(refData['profilePath'])
        self.parambar.update(refData)

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
