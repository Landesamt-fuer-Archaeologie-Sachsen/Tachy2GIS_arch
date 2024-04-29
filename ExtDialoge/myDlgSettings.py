# -*- coding: utf-8 -*-
from qgis.PyQt import uic
from qgis.core import *
from qgis.gui import *
from utils.functions import *
import os

from configparser import ConfigParser
import os.path


class DlgSettings(QtWidgets.QDialog):
    def __init__(self,t2gArchInstance, config):
        super(DlgSettings, self).__init__()
        pfad = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), "./..")))
        self.QgisDateiPfad = QgsProject.instance().readPath('./')
        self.ProjPfad = os.path.abspath(os.path.join(self.QgisDateiPfad, "./.."))
        self.iconpfad = os.path.join(os.path.join(pfad,'Icons'))
        self.ui = uic.loadUi(os.path.join(os.path.dirname(__file__), 'myDlgSettings.ui'), self)
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__inipfad = os.path.join(self.ProjPfad,'_System_/config.ini')
        self.__config = config
        self.ui.treeWidget.itemClicked.connect(self.on_itemClicked)
        self.ui.butOK.clicked.connect(self.ok)
        self.ui.butAbruch.clicked.connect(self.abbruch)
        # self.ui.setup()  # extra call; constructor is not allowed to fail

    def setup(self):
        # Alle Tabs Sichtbarkeit aus
        for index in range(self.ui.tabWidget.count()):
            self.ui.tabWidget.setTabVisible(index, False)
        QgsMessageLog.logMessage('setup', 'T2G Archäologie', Qgis.Info)
        # Config lesen
        val = self.__config.getValue("AutoSave","time",'10')
        self.ui.txtautoSaveTime.setText(val)
        val = self.__config.getValue("AutoSave","enabled",'True')
        self.ui.chbautoSave.setChecked(str2bool(val))
        val = self.__config.getValue("Textgröße","value",'0.70')
        self.ui.spbTextGr.setValue(float(val))
        # Punktexportpfad
        val = self.__config.getValue("Punkte Export","pfad Exportordner",'./../Jobs')
        self.ui.txtPointPfadExp.setText(val)
        # Punktimportpfad
        val = self.__config.getValue("Punkte Import","pfad Importordner",'./../Jobs')
        self.ui.txtPointPfadImp.setText(val)
        # Profilentzerrpunkteexport
        val = self.__config.getValue("Profilentzerrung","pfad Exportordner",'./../Jobs')
        self.ui.txtProfilFEPPfadExp.setText(val)
        val = self.__config.getValue("Profilentzerrung","feldNProfNr",'prof_nr')
        self.ui.txtfeldNProfNr.setText(val)
        val = self.__config.getValue("Profilentzerrung","feldNFEP",'obj_typ')
        self.ui.txtFeldNFEP.setText(val)
        val = self.__config.getValue("Profilentzerrung","attFEP",'Fotoentzerrpunkt')
        self.ui.txtAttFEP.setText(val)
        # MouseInfo
        val = self.__config.getValue("MouseInfo","anzeigen",'True')
        self.ui.chbMInfo_1.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","beiBeginn",'True')
        self.ui.chbMInfo_2.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","immer",'True')
        self.ui.chbMInfo_3.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","geometrieart",'True')
        self.ui.chbMInfo_4.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","objekttyp",'True')
        self.ui.chbMInfo_5.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","objektart",'True')
        self.ui.chbMInfo_6.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","schnitt",'True')
        self.ui.chbMInfo_7.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","planum",'True')
        self.ui.chbMInfo_8.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","befund",'True')
        self.ui.chbMInfo_9.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","fund",'True')
        self.ui.chbMInfo_10.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","profil",'True')
        self.ui.chbMInfo_11.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","probe",'True')
        self.ui.chbMInfo_12.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","punktNr",'True')
        self.ui.chbMInfo_13.setChecked(str2bool(val))
        val = self.__config.getValue("MouseInfo","koordinaten",'True')
        self.ui.chbMInfo_14.setChecked(str2bool(val))

    def ok(self):
        """Werte in Configparser eintragen"""
        self.__config.updateValue("AutoSave","time",self.ui.txtautoSaveTime.text())
        self.__config.updateValue("AutoSave","enabled",str(self.ui.chbautoSave.checkState()))
        self.__config.updateValue("Textgröße","value",str(self.ui.spbTextGr.value()))
        self.__config.updateValue("Punkte Export","pfad Exportordner",self.ui.txtPointPfadExp.text())
        self.__config.updateValue("Punkte Import","Pfad Importordner",self.ui.txtPointPfadImp.text())
        self.__config.updateValue("Profilentzerrung","pfad Exportordner",self.ui.txtProfilFEPPfadExp.text())
        self.__config.updateValue("Profilentzerrung","feldNProfNr",self.ui.txtfeldNProfNr.text())
        self.__config.updateValue("Profilentzerrung","feldNFEP",self.ui.txtFeldNFEP.text())
        self.__config.updateValue("Profilentzerrung","attFEP",self.ui.txtAttFEP.text())
        # mouseInfo
        self.__config.updateValue("MouseInfo","anzeigen",str(self.ui.chbMInfo_1.checkState()))
        self.__config.updateValue("MouseInfo","beiBeginn",str(self.ui.chbMInfo_2.checkState()))
        self.__config.updateValue("MouseInfo","immer",str(self.ui.chbMInfo_3.checkState()))
        self.__config.updateValue("MouseInfo","geometrieart",str(self.ui.chbMInfo_4.checkState()))
        self.__config.updateValue("MouseInfo","objekttyp",str(self.ui.chbMInfo_5.checkState()))
        self.__config.updateValue("MouseInfo","objektart",str(self.ui.chbMInfo_6.checkState()))
        self.__config.updateValue("MouseInfo","schnitt",str(self.ui.chbMInfo_7.checkState()))
        self.__config.updateValue("MouseInfo","planum",str(self.ui.chbMInfo_8.checkState()))
        self.__config.updateValue("MouseInfo","befund",str(self.ui.chbMInfo_9.checkState()))
        self.__config.updateValue("MouseInfo","fund",str(self.ui.chbMInfo_10.checkState()))
        self.__config.updateValue("MouseInfo","profil",str(self.ui.chbMInfo_11.checkState()))
        self.__config.updateValue("MouseInfo","probe",str(self.ui.chbMInfo_12.checkState()))
        self.__config.updateValue("MouseInfo","punktNr",str(self.ui.chbMInfo_13.checkState()))
        self.__config.updateValue("MouseInfo","koordinaten",str(self.ui.chbMInfo_14.checkState()))


        self.__config.saveFile()
        self.__t2gArchInstance.eventReadProject()

        self.ui.close()

    def abbruch(self):
        self.ui.close()
        pass

    def on_itemClicked(self,item,column):
        """TreeViewClick zeigt Tab"""
        #title = str(item.text(column))
        self.ui.tabWidget.setCurrentIndex(self.ui.treeWidget.indexOfTopLevelItem(item))
        for index in range(self.ui.tabWidget.count()):
            if index != self.ui.treeWidget.indexOfTopLevelItem(item):
                self.ui.tabWidget.setTabVisible(index, False)
            else:
                self.ui.tabWidget.setTabVisible(index, True)


class Configfile():

    def __init__(self,pfad):
        self.__config_object = ConfigParser()
        self.__inipfad = pfad
        self.run()

    def run(self):
        # Existenz der Config-Datei prüfen gegebenfalls mit Standartwerte anlegen
        if not os.path.exists(self.__inipfad):
            QgsMessageLog.logMessage('Config-Datei nicht vorhanden! Eine neue Config-Datei mit Standartwerten wird gespeichert.', 'T2G Archäologie', Qgis.Info)
            self.saveStandarValue()
        else:
            self.__config_object.read(self.__inipfad)

    def saveStandarValue(self):
        # Configfile mit Standartdaten speichern
        self.setStandartValues()
        self.saveFile()

    def setStandartValues(self):
        # Configparser mit Standartdaten füllen
        self.__config_object["AutoSave"] = {"time": "5",
                                        "enabled": "off",}

        self.__config_object["Punkte Import"] = {"pfad Importordner": "./../Jobs"}

        self.__config_object["Punkte Export"] = {"pfad Exportordner": "./../Jobs"}

        self.__config_object["Profilentzerrung"] = {"feldNProfNr": "prof_nr",
                                                    "feldNFEP": "obj_typ",
                                                    "attFEP": "Fotoentzerrpunkt",
                                                    "pfad Exportordner": "./../Jobs"}

        self.__config_object["Grabungsfotos"] = {"orgPfad": "../Fotos Eingebunden/Thumbs/",
                                            "thumbPfad": "../Fotos Eingebunden/"}

        self.__config_object["Projekt"] = {"aktivität": "aaa",
                                        "gemarkung": "bbb",
                                        "gemeinde": "ccc",
                                        "projektname": "ddd",}

        self.__config_object["Messen"] = {"schriftGroesse": "1,00",
                                            "cursorInfo": "on"}


        self.__config_object["ListenausgabeBefund"] = {"-": "-"}

        self.__config_object["ListenausgabeFund"] = {"-": "-"}

        self.__config_object["ListenausgabeProfil"] = {"-": "-"}

        self.__config_object["ListenausgabeProbe"] = {"-": "-"}

    def saveFile(self):
        # Configdaten in Datei speichern
        try:
            with open(self.__inipfad, 'w') as conf:
                self.__config_object.write(conf)
        except PermissionError:
            QgsMessageLog.logMessage('Config-Datei nicht vorhanden!', 'T2G Archäologie', Qgis.Critical)

    def getValue(self, section, option, default=None):
        if not self.__config_object.has_section(section):
            self.__config_object.add_section(section)
        if not self.__config_object.has_option(section, option):
            self.__config_object.set(section, option, default)
            value = default
        else:
            value = self.__config_object[section][option]
        return value

    def updateValue(self,section,option,value):
        try:
             self.__config_object[section][option] = value
             #self.saveFile()
        except Exception as e:
            #QgsMessageLog.logMessage('Schlüssel ['+ section + '] ['+ option +'] ist nicht in config.ini vorhanden!', 'T2G Archäologie', Qgis.Critical)
            QgsMessageLog.logMessage(str(e), 'config', Qgis.Info)
