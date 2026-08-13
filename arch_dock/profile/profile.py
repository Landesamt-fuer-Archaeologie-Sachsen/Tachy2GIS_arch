from .digitize.digitize import Digitize
from .georef.georef import Georef
from .plan.plan import Plan
from .rotation_coords import RotationCoords


## @brief The class is used to implement functionalities for work with profiles within the dock widget of the Tachy2GIS_arch plugin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2021-05-07
class Profile:

    ## The constructor.
    #  Defines attributes for the Profile
    #
    #  @param dockWidget pointer to the dockwidget
    def __init__(self, arch_dock):
        self.dockwidget = arch_dock

        # RotationCoords
        self.rotationCoords = RotationCoords()

        self.georef = Georef(self.dockwidget, self.rotationCoords)
        self.digitize = Digitize(self.dockwidget, self.rotationCoords)
        self.plan = Plan(self.dockwidget)

    ## @brief Initializes the functionality for profile modul
    #

    def setup(self):
        self.georef.setup()
        self.digitize.setup()
        self.plan.setup()

    def teardown(self):
        self.digitize.closeDigitizeDialog()
