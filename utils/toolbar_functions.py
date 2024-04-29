from qgis.core import (Qgis,
                       QgsMessageLog,
                       QgsProject)
from qgis.utils import iface
import os, subprocess
from .functions import ProjectSaveFunc

projectPath = QgsProject.instance().readPath('../')  # location of prj files (qgz files)
projectFolderPath = os.path.abspath(os.path.join(projectPath, "./..")) # location of folder contains all data

def openProjectFolder():
    subprocess.call(r'explorer "' + projectFolderPath + '"')

def saveProject():
    ProjectSaveFunc().shapesSave()

    # save the project qgz (e.g. leer.qgz)
    QgsProject.instance().write()

    if not ProjectSaveFunc().dayprojectSave(projectFolderPath):
        iface.messageBar().pushMessage("T2G Archäologie: ", "Speicherung Tagesdatei: Fehler!",
                                        level=Qgis.Critical)
        QgsMessageLog.logMessage("Speicherung Tagesdatei: Fehler!", 'T2G Archäologie', Qgis.Critical)
    else:
        iface.messageBar().pushMessage("T2G Archäologie: ", "Speicherung Tagesdatei: Erfolgreich.",
                                        level=Qgis.Info)
        QgsMessageLog.logMessage("Speicherung Tagesdatei: Erfolgreich.", 'T2G Archäologie', Qgis.Info)
