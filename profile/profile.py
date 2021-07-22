## @package QGIS geoEdit extension..
import shutil
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsApplication, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsRectangle, QgsVectorFileWriter
from processing.gui import AlgorithmExecutor
from qgis import processing

from .data_store import DataStore
from .georef.georef import Georef
from .digitize.digitize import Digitize

## @brief The class is used to implement functionalities for work with profiles within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-05-07
class Profile():

    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):

        self.__iconpath = os.path.join(os.path.dirname(__file__), 'Icons')
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace

        self.dataStore = DataStore()


        self.georef = Georef(self.__t2gArchInstance, iFace, self.dataStore)
        self.digitize = Digitize(self.__t2gArchInstance, iFace, self.dataStore)

    ## @brief Initializes the functionality for profile modul
    #

    def setup(self):
        self.georef.setup()
        self.digitize.setup()
