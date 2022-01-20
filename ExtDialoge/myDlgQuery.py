# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import *
from ..functions import *
from ..t2g_arch_dockwidget import T2G_ArchDockWidget
import os, csv




FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'myDlgQuery.ui'))


class AllLayerQuestionDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent='iface.mainWindow()'):
        """Constructor."""
        super(AllLayerQuestionDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        pfad = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), "./..")))
        iconpfad = os.path.join(os.path.join(pfad, 'Icons'))
        self.ui = self
        # self.ui.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'Icons/Schriftfeld.jpg')))
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.ui.butPaste.clicked.connect(self.paste)
        self.ui.butOK.clicked.connect(self.OK)
        self.ui.butAbbruch.clicked.connect(self.Abbruch)
        self.setup()

    def setup(self):
        self.ui.cboBeispiele.addItem('"bef_nr" = \'20\'')
        self.ui.cboBeispiele.addItem('"prob_nr" = \'50\'')
        self.ui.cboBeispiele.addItem('"messdatum" = \'2019-08-26\'')
        self.ui.cboBeispiele.addItem('"bef_nr" LIKE \'%,71\' or "bef_nr" LIKE \'71\' or "bef_nr" LIKE \'%71,\'')
        pass

    def paste(self):
        self.ui.txtQuery.setText(self.ui.cboBeispiele.currentText())

    def setAllLayerFilter(self):
        value, ok = QInputDialog().getText(None, 'Such Befund Nr eingeben', '')
        if ok:
            for layer in QgsProject.instance().mapLayers().values():
                if 'Line.shp' in layer.source() or 'Polygon.shp' in layer.source() or 'Point.shp' in layer.source():
                    QgsMessageLog.logMessage(layer.source(), 'T2G Archäologie', Qgis.Info)

                    i=str(value)
                    query = '"bef_nr" LIKE \'%,' + i + '\'' + ' or "bef_nr" LIKE ' + '\'' + i +'\'' + ' or "bef_nr" LIKE \'%'+i+',\''     #self.ui.txtQuery.text()
                    self.ui.txtQuery.setText(query)
                    QgsMessageLog.logMessage(query, 'T2G Archäologie', Qgis.Info)
                    layer.setSubsetString(query)

    def OK(self):
        self.setAllLayerFilter()
        #self.ui.close()

    def Abbruch(self):
        self.ui.close()

    def closeEvent(self, event):
        event.accept()


