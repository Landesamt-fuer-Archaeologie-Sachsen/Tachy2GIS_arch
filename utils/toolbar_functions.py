import os
import subprocess
import sys

from qgis.core import QgsProject

from .functions import project_backup


def openProjectFolder():
    # from "Projekt" folder go one up
    projectPath = QgsProject.instance().readPath("..")
    if sys.platform == "win32":
        os.startfile(projectPath.replace('/', '\\'))
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, projectPath])


def saveProject(iface):
    project_backup(iface, "manuell")
