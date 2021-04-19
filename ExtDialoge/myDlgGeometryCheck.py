# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LfADockWidget
                                 A QGIS plugin
 Tool für das Landesamt für Archäologie Dresden
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2018-11-29
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Daniel Timmel
        email                : aaa@web.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

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
    os.path.dirname(__file__), 'myDlgGeometryCheck.ui'))


class GeometryCheckDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(GeometryCheckDockWidget, self).__init__(parent)
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
        self.layer = None
        #self.feature = feature
        self.koordList = []
        self.ui.butOK.clicked.connect(self.OK)
        self.ui.butAbbruch.clicked.connect(self.Abbruch)
        self.ui.tableWidget.itemChanged.connect(self.vertexEdit)
        self.ui.cboLayerName.currentIndexChanged.connect(self.setCheckLayer)
        #self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.ui)
        self.setup()

    def setCheckLayer(self):
        self.layer = QgsProject.instance().mapLayersByName(self.ui.cboLayerName.currentText())[0]
        self.check()

    def setup(self):
        list = ['E_Polygon','E_Line','E_Point']
        self.ui.cboLayerName.addItems(list)
        #self.setCheckLayer()

    def OK(self):
        self.ui.close()

    def Abbruch(self):
        self.ui.close()

    def check(self):
        delLayer("Geometrie z-Koord Check")
        templayer = QgsVectorLayer("Point?crs=31469", "Geometrie z-Koord Check", "memory")
        templayer.setCrs(self.layer.crs())
        QgsProject.instance().addMapLayer(templayer, False)
        root = QgsProject.instance().layerTreeRoot()
        g = root.findGroup('Vermessung')
        g.insertChildNode(0, QgsLayerTreeLayer(templayer))

        symbol = templayer.renderer().symbol()
        symbol.setColor(QColor.fromRgb(0, 225, 0))
        # symbol.setWidth(0.75)
        sym = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'red', 'size': '3', 'outline_width': '1'})
        templayer.renderer().setSymbol(sym)
        templayer.triggerRepaint()
        iface.layerTreeView().refreshLayerSymbology(templayer.id())
        sel = []
        self.koordList = []

        templayer.startEditing()

        if self.layer.geometryType() == QgsWkbTypes.PointGeometry:
            for f in self.layer.getFeatures():
                try:
                    koord = {'x': f.geometry().get().x(), 'y': f.geometry().get().y(),
                     'z': f.geometry().get().z()}
                    if f.geometry().get().z() == 0:
                        self.koordList.append(koord)
                    # self.ui.txtGrabung.setText(str(self.koordList[0]['x']))
                except Exception as e:
                    QgsMessageLog.logMessage(str(e), 'T2G Archäologie', Qgis.Info)
                    sel.append(f.id())
                    continue

        elif self.layer.geometryType() == QgsWkbTypes.LineGeometry:
            for f in self.layer.getFeatures():
                try:
                    for i in range(len(f.geometry().asPolyline()[0])):
                        koord = {'x': f.geometry().vertexAt(i).x(), 'y': f.geometry().vertexAt(i).y(),
                                 'z': f.geometry().vertexAt(i).z()}
                        if f.geometry().vertexAt(i).z() == 0:
                            self.koordList.append(koord)
                except:
                    sel.append(f.id())
                    continue

        elif self.layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            for f in self.layer.getFeatures():
                try:
                    for i in range(len(f.geometry().asPolygon()[0])):
                        koord = {'x': f.geometry().vertexAt(i).x(), 'y': f.geometry().vertexAt(i).y(),
                                 'z': f.geometry().vertexAt(i).z()}
                        if f.geometry().vertexAt(i).z() == 0:
                            self.koordList.append(koord)
                except:
                    sel.append(f.id())
                    continue

        self.layer.selectByIds(sel)
        #templayer.startEditing()
        #listOfIds = [feat.id() for feat in templayer.getFeatures()]
        #templayer.deleteFeatures(listOfIds)
        #templayer.commitChanges()
        tableWidgetRemoveRows(self.tableWidget)
        for i in range(len(self.koordList)):
            self.tableWidget.insertRow(i)
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(self.koordList[i]['x'])))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.koordList[i]['y'])))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(self.koordList[i]['z'])))
            feature = QgsFeature()
            pt = QgsPoint(float(self.koordList[i]['x']), float(self.koordList[i]['y']),
                          float(self.koordList[i]['z']))
            feature.setGeometry(QgsGeometry(pt))
            templayer.dataProvider().addFeatures([feature])

        self.ui.labvertexcount.setText(str(len(self.koordList)) + ' Punkte')
        templayer.updateExtents()
        templayer.commitChanges()

    def vertexEdit(self, item):
        # self.ui.lineEdit.setText(str(item.row()))
        # self.layer.changeGeometry(self.feature.id(), newgeom)
        # QgsMessageLog.logMessage(str(item.text()), 'T2G Archäologie', Qgis.Info)
        if isNumber(item.text()):
            if item.column() == 0:
                self.koordList[item.row()]['x'] = item.text()
            if item.column() == 1:
                self.koordList[item.row()]['y'] = item.text()
            if item.column() == 2:
                self.koordList[item.row()]['z'] = item.text()


    def closeEvent(self, event):
        self.dwgClose()
        event.accept()

    def dwgClose(self):
        self.closingPlugin.emit()
        delLayer("Geometrie z-Koord Check")
        iface.mapCanvas().refreshAllLayers()
