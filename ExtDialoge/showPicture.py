# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import *
from ..functions import *
from ..t2g_arch_dockwidget import T2G_ArchDockWidget

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'showPicture.ui'))

class ShowPicture(QtWidgets.QDialog,FORM_CLASS):
    def __init__(self, iface, picpfad, parent=None):
        super(ShowPicture, self).__init__(parent)
        pfad = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), "./..")))
        iconpfad = os.path.join(os.path.join(pfad,'Icons'))
        #self.ui = uic.loadUi(os.path.join(pfad, 'showPicture.ui'), self)
        #self.ui.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'Icons/Ptneu.jpg')))
        self.setupUi(self)
        self.iface = iface
        self.picpfad = picpfad
        self.ui = self
        self.setup()
        self.loadPicture()

    def setup(self):
        self.QgisDateiPfad = QgsProject.instance().readPath('./')
        self.ProjPfad = os.path.abspath(os.path.join(self.QgisDateiPfad, "./.."))

    def loadPicture(self):

        pixmap = QPixmap.fromImage(QImage('C:/111.jpg')).scaled(64,64,Qt.KeepAspectRatio)
        self.ui.labPict.setPixmap(pixmap)
