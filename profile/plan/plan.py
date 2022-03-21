## @package QGIS geoEdit extension..
import os

from .layout import Layout

## @brief The class is used to implement functionalities for work with profile-plans within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2022-03-15
class Plan():

    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):
        print('init plan')
        self.__iconpath = os.path.join(os.path.dirname(__file__), '...', 'Icons')
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace

    ## @brief Initializes the functionality for profile modul
    #

    def setup(self):
        print('Setup plan')

                #set datatype filter to profileFotosComboGeoref
        self.__dockwidget.profilePlanSelect.setFilter('Images (*.jpg)')

        self.layout = Layout(self.__iface)

        self.__dockwidget.startPlanBtn.clicked.connect(self.__startPlanCreation)


    ## \brief Start digitize dialog
    #
    #
    def __startPlanCreation(self):

        planData = self.__getSelectedValues()

        self.layout.startLayout(planData)

    ## \brief get selected values
    #
    #
    def __getSelectedValues(self):

        #Profilbild
        profilePath = self.__dockwidget.profilePlanSelect.filePath()

        planData = {'profilePath': profilePath}

        print('planData', planData)

        return planData
