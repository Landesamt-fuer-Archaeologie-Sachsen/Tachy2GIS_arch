import os.path
from configparser import ConfigParser

from qgis.core import QgsMessageLog, QgsProject, Qgis

from ..settings import PLUGIN_NAME


def get_config_ini_path() -> str:
    """Return the absolute path to the project's config.ini file.
    The _System_ folder lives in the parent directory of the .qgz project file.
    """
    project_file = QgsProject.instance().fileName()
    project_dir = os.path.dirname(project_file)
    parent_dir = os.path.dirname(project_dir)
    return os.path.normpath(os.path.join(parent_dir, "_System_", "config.ini"))


class Configfile:

    def __init__(self, pfad):
        self.__config_object = ConfigParser()
        self.__inipfad = pfad
        self.run()

    def run(self):
        # Existenz der Config-Datei prüfen gegebenfalls mit Standartwerte anlegen
        if not os.path.exists(self.__inipfad):
            QgsMessageLog.logMessage(
                "Config-Datei nicht vorhanden! Eine neue Config-Datei mit Standartwerten wird gespeichert.",
                PLUGIN_NAME,
                Qgis.Info,
            )
            self.saveStandarValue()
        else:
            self.__config_object.read(self.__inipfad)

    def saveStandarValue(self):
        # Configfile mit Standartdaten speichern
        self.setStandartValues()
        self.saveFile()

    def setStandartValues(self):
        # Configparser mit Standartdaten füllen
        self.__config_object["AutoSave"] = {
            "enabled": "off",
            "interval_in_min": "15",
            "keep_last_n_backups": "10",
        }

        self.__config_object["Punkte Import"] = {"pfad Importordner": "./../Jobs"}

        self.__config_object["Punkte Export"] = {"pfad Exportordner": "./../Jobs"}

        self.__config_object["Profilentzerrung"] = {
            "feldNProfNr": "prof_nr",
            "feldNFEP": "obj_typ",
            "attFEP": "Fotoentzerrpunkt",
            "pfad Exportordner": "./../Jobs",
        }

        self.__config_object["Grabungsfotos"] = {
            "orgPfad": "../Fotos Eingebunden/Thumbs/",
            "thumbPfad": "../Fotos Eingebunden/",
        }

        self.__config_object["Projekt"] = {
            "aktivität": "aaa",
            "gemarkung": "bbb",
            "gemeinde": "ccc",
            "projektname": "ddd",
        }

        self.__config_object["Messen"] = {"schriftGroesse": "1,00", "cursorInfo": "on"}

        self.__config_object["ListenausgabeBefund"] = {"-": "-"}

        self.__config_object["ListenausgabeFund"] = {"-": "-"}

        self.__config_object["ListenausgabeProfil"] = {"-": "-"}

        self.__config_object["ListenausgabeProbe"] = {"-": "-"}

    def saveFile(self):
        # Configdaten in Datei speichern
        try:
            with open(self.__inipfad, "w") as conf:
                self.__config_object.write(conf)
        except PermissionError:
            QgsMessageLog.logMessage("Config-Datei nicht vorhanden!", "T2G Archäologie", Qgis.Critical)

    def getValue(self, section, option, default=None):
        if not self.__config_object.has_section(section):
            self.__config_object.add_section(section)
        if not self.__config_object.has_option(section, option):
            self.__config_object.set(section, option, default)
            value = default
        else:
            value = self.__config_object[section][option]
        return value

    def updateValue(self, section, option, value):
        try:
            self.__config_object[section][option] = value
            # self.saveFile()
        except Exception as e:
            # QgsMessageLog.logMessage('Schlüssel ['+ section + '] ['+ option +'] ist nicht in config.ini vorhanden!', 'T2G Archäologie', Qgis.Critical)
            QgsMessageLog.logMessage(str(e), "config", Qgis.Info)
