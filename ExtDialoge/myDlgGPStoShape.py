# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import *
from ..functions import *
from ..t2g_arch_dockwidget import T2G_ArchDockWidget
import os, csv

class dlgGPStoShape(QtWidgets.QDialog):
    def __init__(self, iface, parent=None):
        super(dlgGPStoShape, self).__init__(parent)
        pfad = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), "./..")))
        iconpfad = os.path.join(os.path.join(pfad,'Icons'))
        self.ui = uic.loadUi(os.path.join(pfad, 'ExtDialoge/myDlgGPStoShape.ui'), self)
        #self.ui.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'Icons/Schriftfeld.jpg')))
        self.iface = iface
        #self.ui.txtLayGemarkung.textChanged.connect(self.stempel)
        #self.ui.txtLayGemarkung.setToolTip('Gemarkung')

        self.ui.cboDelimiter.currentIndexChanged.connect(self.pointImpVor)
        #self.ui.cboLayHoehenbezug.editTextChanged.connect(self.stempel)
        self.ui.cboDelimiter.setToolTip('Trennzeichen')

        self.ui.butPfadGPS.clicked.connect(self.pointImpVor)
        self.ui.butOK.clicked.connect(self.OK)
        self.ui.butAbbruch.clicked.connect(self.Abbruch)
        self.ui.setup()

    def setup(self):
        pass

    def OK(self):
        self.ui.close()
    def Abbruch(self):
        self.ui.close()
    def setActiveLayer(self):
        activeLayer = self.ui.mapLayerComboBox.currentLayer()
        if activeLayer is None:
            return
        self.iface.setActiveLayer(activeLayer)

    def pointImpVor(self):
        if self.ui.txtPfadGPS.text() == '':
            input_file = QFileDialog.getOpenFileName(None, 'Quellpfad',
                                                     QgsProject.instance().readPath('./../Jobs'),
                                                     'Excel (*.csv);;Alle Dateien (*.*)')
            self.ui.txtPfadGPS.setText(input_file[0])
        deli = self.ui.cboDelimiter.currentText()
        self.ui.tableWidget.clear()
        if deli == 'Leerzeichen':
            deli = ' '
        if deli == 'Tab':
            deli = '\t'

        if self.ui.txtPfadGPS.text() != '':

            readerCSV = csv.reader(open(self.ui.txtPfadGPS.text(),newline=''), delimiter=deli, quotechar='|')

            cc = list(csv.reader(open(self.ui.txtPfadGPS.text(),"r"))).count()
            #cc=len(readerCSV)
            #readerCSV.seek(0)
            rc = len(list(csv.reader(open(self.ui.txtPfadGPS.text(),"r"))))
            self.ui.labCount.setText('Spalten ' + str(cc) + ' / Zeilen ' + str(rc))
            self.ui.tableWidget.setColumnCount(cc)
            self.ui.tableWidget.setRowCount(rc)
            r = 0
            for row in readerCSV:
                 c = 0
                 for column in row:
                     self.ui.tableWidget.setItem(r, c, QTableWidgetItem(str(column)))
                     c = c + 1
                 r = r + 1


