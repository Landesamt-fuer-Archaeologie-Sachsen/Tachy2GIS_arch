# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, uic
from qgis.core import QgsProject
import os, time, sys, shutil, os.path
from datetime import date
from qgis.utils import iface
from qgis.core import QgsExpressionContextUtils
from qgis.gui import QgsMapCanvas


project_pfad = QgsProject.instance().readPath('./..')

class dlg_intro(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        #self.ui = uic.loadUi(os.path.join(project_pfad,"_System_\Intro.ui"),self)
        self.ui.OKButton.clicked.connect(self.onOK)
        self.iface = iface
        #QtWidgets.QMessageBox.warning(None, "Meldung", project_pfad)

    def onOK(self):
        #QgsExpressionContextUtils.setProjectVariable(project,'ZFaktor',str(self.ui.spinBox.value()))
        self.close()

def project_save(quelle):
    try:
        datum = unicode(time.strftime("%Y.%m.%d"))
        zeit = unicode(time.strftime("%H-%M-%S"))
        ziel = os.path.join(quelle, r'_Sicherungen_', datum, zeit)
        #QMessageBox.warning(None, "Warnung", os.path.join(quelle,'Shape'))
        #QMessageBox.warning(None, "Warnung", os.path.join(quelle, ziel, 'Shape'))
        ordner_kopie(os.path.join(quelle,'Shape'),os.path.join(ziel, 'Shape'))
        ordner_kopie(os.path.join(quelle,'Projekt'),os.path.join(ziel, 'Projekt'))


        os.remove(os.path.join(ziel, 'Projekt', 'intro.py'))
        ordner_loeschen(os.path.join(ziel, 'Projekt','__pycache__'))
        return 'True'
    except:
        #QMessageBox.information(None, "Hinweis", 'Fehler beim löschen.')
        ordner_loeschen(ziel)
        return 'False'

def ordner_loeschen(path):
    # check if folder exists
    if os.path.exists(path):
        # remove if exists
        shutil.rmtree(path)

def ordner_kopie(quelle, ziel):
    root_src_dir = unicode(quelle)
    root_dst_dir = unicode(ziel)
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir.replace('\\','/',1))
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.copy(src_file, dst_dir)

class dlg_Variablen(QtWidgets.QDialog):

    def __init__(self,parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi(os.path.join(project_pfad,"_System_\Variablen.ui"),self)
        self.ui.buttonBox.accepted.connect(self.onOK)
        #self.ui.buttonbox.rejected.connect(self.onReject)
        self.iface = iface
        #QtWidgets.QMessageBox.warning(None, "Meldung", project_pfad)
        self.project = QgsProject.instance()
        self.lineEdit.setText(QgsExpressionContextUtils.projectScope(self.project).variable('aktcode'))

    def onOK(self):
        QgsExpressionContextUtils.setProjectVariable(self.project,'aktcode',str(self.lineEdit.text()))
        self.close()