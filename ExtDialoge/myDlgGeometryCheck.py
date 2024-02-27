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

from qgis.PyQt.QtCore import Qt, pyqtSignal, QVariant
from qgis.PyQt import QtWidgets, QtCore, QtGui, uic
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
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

        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.layer = None
        self.templayer = None
        self.koordList = []

        self.ui.butOK.clicked.connect(self.OK)
        self.ui.butAbbruch.clicked.connect(self.Abbruch)
        self.ui.tableWidget.itemChanged.connect(self.vertexEdit)
        self.ui.tableWidget.cellClicked.connect(self.on_cellClicked)
        self.ui.cboLayerName.currentIndexChanged.connect(self.setCheckLayer)

        self.setup()

    def setCheckLayer(self):
        self.layer = QgsProject.instance().mapLayersByName(self.ui.cboLayerName.currentText())[0]
        self.Check()

    def setup(self):
        list = ['E_Polygon','E_Line','E_Point']
        self.ui.cboLayerName.addItems(list)
        #self.setCheckLayer()

    def OK(self):
        self.ui.close()

    def Abbruch(self):
        self.ui.close()

    def Check(self):
        delLayer("Geometrie z-Koord Check")
        self.templayer = QgsVectorLayer("Point", "Geometrie z-Koord Check", "memory")
        self.templayer.setCrs(self.layer.crs())

        pr = self.templayer.dataProvider()
        pr.addAttributes([QgsField("id", QVariant.Int, 'integer')])
        self.templayer.updateFields()

        QgsProject.instance().addMapLayer(self.templayer, False)
        root = QgsProject.instance().layerTreeRoot()
        g = root.findGroup('Vermessung')
        g.insertChildNode(0, QgsLayerTreeLayer(self.templayer))

        symbol = self.templayer.renderer().symbol()
        symbol.setColor(QColor.fromRgb(0, 225, 0))
        # symbol.setWidth(0.75)
        sym = QgsMarkerSymbol.createSimple({'name': 'circle', 'color': 'red', 'size': '3', 'outline_width': '1'})
        self.templayer.renderer().setSymbol(sym)
        self.templayer.triggerRepaint()
        iface.layerTreeView().refreshLayerSymbology(self.templayer.id())
        sel = []
        self.koordList = []
        tableWidgetRemoveRows(self.tableWidget)
        self.tableWidget.setSortingEnabled(False)
        self.templayer.startEditing()

        if self.layer.geometryType() == QgsWkbTypes.PointGeometry:
            for f in self.layer.getFeatures():
                try:
                    koord = {'x': f.geometry().get().x(), 'y': f.geometry().get().y(),
                     'z': f.geometry().get().z()}
                    self.koordList.append(koord)
                except Exception as e:
                    QgsMessageLog.logMessage(str(e), 'T2G Archäologie', Qgis.Info)
                    sel.append(f.id())
                    #continue

        elif self.layer.geometryType() == QgsWkbTypes.LineGeometry:
            for f in self.layer.getFeatures():
                if f.geometry().isMultipart():
                    parts = f.geometry().asGeometryCollection()
                    for part in parts:
                        for vertex in part.vertices():
                            koord = {'x': vertex.x(), 'y': vertex.y(), 'z': vertex.z()}
                            self.koordList.append(koord)
                else:
                    try:
                        for i in range(len(f.geometry().asPolyline()[0])):
                            koord = {'x': f.geometry().vertexAt(i).x(), 'y': f.geometry().vertexAt(i).y(),
                                     'z': f.geometry().vertexAt(i).z()}
                            self.koordList.append(koord)
                    except:
                        sel.append(f.id())
                        #continue

        elif self.layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                for f in self.layer.getFeatures():
                    if f.geometry().isMultipart():
                        parts = f.geometry().asGeometryCollection()
                        for part in parts:
                            for vertex in part.vertices():
                                koord = {'x': vertex.x(), 'y': vertex.y(), 'z': vertex.z()}
                                self.koordList.append(koord)
                    else:
                        try:
                            for i in range(len(f.geometry().asPolygon()[0])):
                                koord = {'x': f.geometry().vertexAt(i).x(), 'y': f.geometry().vertexAt(i).y(),
                                         'z': f.geometry().vertexAt(i).z()}
                                self.koordList.append(koord)
                        except:
                            sel.append(f.id())
                            #continue

        #self.layer.selectByIds(sel)
        #tableWidgetRemoveRows(self.tableWidget)
        for i in range(len(self.koordList)):
            self.tableWidget.insertRow(i)
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(self.koordList[i]['x'])))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.koordList[i]['y'])))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(self.koordList[i]['z'])))
            self.tableWidget.setItem(i, 3, QTableWidgetItem(str(i)))
            feature = QgsFeature()
            pt = QgsPoint(float(self.koordList[i]['x']), float(self.koordList[i]['y']),
                          float(self.koordList[i]['z']))
            feature.setGeometry(QgsGeometry(pt))
            feature.setAttributes([int(i)])
            self.templayer.dataProvider().addFeatures([feature])

        self.tableWidget.setSortingEnabled(True)
        self.ui.labvertexcount.setText(str(len(self.koordList)) + ' Punkte')
        self.templayer.updateExtents()
        self.templayer.commitChanges()

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

    def on_cellClicked(self,row,column):
        x = self.ui.tableWidget.item(row, 0).text()
        y = self.ui.tableWidget.item(row, 1).text()
        id = self.ui.tableWidget.item(row, 3).text()

        expr = QgsExpression('id=' + '\'' + id + '\'')
        #QgsMessageLog.logMessage(str(suchstr), 'T2G Archäologie', Qgis.Info)
        it = self.templayer.getFeatures(QgsFeatureRequest(expr))
        ids = [i.id() for i in it]
        self.templayer.selectByIds(ids)
        if self.templayer.selectedFeatureCount() > 0:
            self.iface.mapCanvas().zoomToSelected(self.templayer)
            self.iface.mapCanvas().zoomByFactor(5)
        '''
        canvas = iface.mapCanvas()
        scale=50
        rect = QgsRectangle(float(x)-scale,float(y)-scale,float(x)+scale,float(y)+scale)
        QgsMessageLog.logMessage(str(rect), 'T2G Archäologie', Qgis.Info)
        canvas.setExtent(rect)
        canvas.refresh()
        '''
        pass

    def closeEvent(self, event):
        self.dwgClose()
        event.accept()

    def dwgClose(self):
        self.closingPlugin.emit()
        delLayer("Geometrie z-Koord Check")
        iface.mapCanvas().refreshAllLayers()
