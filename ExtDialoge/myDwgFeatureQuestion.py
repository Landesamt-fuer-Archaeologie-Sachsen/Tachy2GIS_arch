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
    os.path.dirname(__file__), 'myDwgFeatureQuestion.ui'))


class FeatureQuestionDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, layer, feature, parent=None):
        """Constructor."""
        super(FeatureQuestionDockWidget, self).__init__(parent)
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
        self.layer = layer
        self.feature = feature
        self.koordList = []
        self.maker = makerAndRubberbands()
        self.maker.setColor(QColor(0, 255, 0))
        self.makerTemp = makerAndRubberbands()
        self.makerTemp.setColor(QColor(0, 0, 255))
        self.makerTemp.setMakerType(QgsVertexMarker.ICON_X)
        self.vertexMaker = makerAndRubberbands()
        self.vertexMaker.setMakerType(QgsVertexMarker.ICON_X)
        self.rubberBand = makerAndRubberbands()

        self.cb = QtWidgets.QApplication.clipboard()
        self.i = ''
        self.x = None
        self.y = None
        self.z = None
        self.ui.butOK.clicked.connect(self.OK)
        self.ui.butAbbruch.clicked.connect(self.Abbruch)
        self.ui.butFeatureMove.clicked.connect(self.featureMove)
        self.ui.butFeatureMove.setIcon(QIcon(os.path.join(iconpfad, 'FeatureMove.gif')))
        self.ui.butFeatureMove.setToolTip('Objekt verschieben')
        self.ui.butFeatureVertexMove.clicked.connect(self.featureVertexMove)
        self.ui.butFeatureVertexMove.setIcon(QIcon(os.path.join(iconpfad, 'FeatureVertexMove.gif')))
        self.ui.butFeatureVertexMove.setToolTip('Stützpunkte verschieben')
        self.ui.txtPoint.setToolTip(
            'Vormat:@ x.x , y.y , z.z \n @ relative Koordinaten')# \n absolute Koordinaten')
        self.ui.txtPoint.textEdited.connect(self.setTempKoord)
        self.ui.butFangPunkt.clicked.connect(self.koordholen)
        self.ui.butFangPunkt.setIcon(QIcon(os.path.join(iconpfad, 'Fang_von Punkt.gif')))
        self.ui.butFangPunkt.setToolTip('Fangen von Punkt')


        self.ui.tableWidget.itemChanged.connect(self.vertexEdit)
        self.ui.tableWidget.itemSelectionChanged.connect(self.test)
        self.ui.tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tableWidget.customContextMenuRequested.connect(self.on_customContextMenu)
        self.ui.txtPoint_2.textChanged.connect(self.setMarker2)

        self.ui.canvas_clicked = PrintClickedPoint(self.iface.mapCanvas(), self.ui)
        #self.ui.lineEdit.textChanged.connect(self.nearest)

        self.ui.setup()

    def setup(self):
        self.koordList = []
        # multipart
        if self.feature.geometry().isMultipart():
            parts = self.feature.geometry().asGeometryCollection()
            for part in parts:
                for vertex in part.vertices():
                    koord = {0: vertex.x(), 1: vertex.y(), 2: vertex.z()}
                    self.koordList.append(koord)
                    QgsMessageLog.logMessage(str(koord), 'T2G Archäologie', Qgis.Info)
                    pass
                QgsMessageLog.logMessage(str(len(self.feature.geometry().get())), 'T2G Archäologie', Qgis.Info)
            pass
        # singlepart
        else:
            if self.layer.geometryType() == QgsWkbTypes.PointGeometry:
                self.ui.labFeatType.setText('Typ:  Punkt')
                koord = {0: self.feature.geometry().get().x(), 1: self.feature.geometry().get().y(),
                         2: self.feature.geometry().get().z()}
                self.koordList.append(koord)
                # self.ui.txtGrabung.setText(str(self.koordList[0]['x']))
                self.setMarker(None)
            elif self.layer.geometryType() == QgsWkbTypes.LineGeometry:
                self.ui.labFeatType.setText('Typ:  Linie')
                for i in range(len(self.feature.geometry().asPolyline()[0])):
                    koord = {0: self.feature.geometry().vertexAt(i).x(), 1: self.feature.geometry().vertexAt(i).y(),
                             2: self.feature.geometry().vertexAt(i).z()}
                    self.koordList.append(koord)

            elif self.layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                self.ui.labFeatType.setText('Typ:  Polygon')
                for i in range(len(self.feature.geometry().asPolygon()[0])):
                    koord = {0: self.feature.geometry().vertexAt(i).x(), 1: self.feature.geometry().vertexAt(i).y(),
                             2: self.feature.geometry().vertexAt(i).z()}
                    self.koordList.append(koord)

        for i in range(len(self.koordList)):
            self.tableWidget.insertRow(i)
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(self.koordList[i][0])))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.koordList[i][1])))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(self.koordList[i][2])))
        self.ui.labPunktcount.setText(str(len(self.koordList)) + ' Punkte')
        self.rubberBand.setRubberBandPoly(self.koordList,3)
        self.setVertexMarker()
        self.maker.makerClean()
        self.koordholen()

    def setVertexMarker(self):
         for row in range(self.ui.tableWidget.rowCount()):
            # QgsMessageLog.logMessage(str(item.text()), 'T2G Archäologie', Qgis.Info)
            self.vertexMaker.setMarker(self.koordList[row][0], self.koordList[row][1], 10,2)


    def test(self):
        self.maker.makerClean()
        for item in self.ui.tableWidget.selectedItems():
            # QgsMessageLog.logMessage(str(item.text()), 'T2G Archäologie', Qgis.Info)
            self.setMarker(item)

    def clipboardSetText(self):
        self.cb.setText(self.ui.tableWidget.selectedItems()[0].text())

    def clipboardText(self):
        # item = self.ui.tableWidget.selectedItems()[0]
        cbText = self.cb.text()
        self.maker.makerClean()
        if isNumber(cbText):
            pass
        for item in self.ui.tableWidget.selectedItems():
            item.setText(cbText)
            # QgsMessageLog.logMessage(str(item.column()), 'T2G Archäologie', Qgis.Info)

    def on_customContextMenu(self, pos):
        contextMenu = QtWidgets.QMenu()
        clipbordCopy = contextMenu.addAction(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "Icons", "kopieren.jpg")), "kopieren")
        clipbordCopy.triggered.connect(self.clipboardSetText)
        clipbordInsert = contextMenu.addAction(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "Icons", "einfügen.gif")), "einfügen")
        clipbordInsert.triggered.connect(self.clipboardText)
        contextMenu.exec_(QtGui.QCursor.pos())

    def rubberBandClean(self):
        self.rubberBand.rubberBandClean()

    def OK(self):
        self.featureUpdate()
        self.ui.close()

    def Abbruch(self):
        self.ui.close()

    def setMarker(self, item):
        if item is None:
            row = 0
        else:
            row = item.row()
            #col = item.column()
        self.maker.setMarker(self.koordList[row][0], self.koordList[row][1],10,2)

    def setMarker2(self):
        self.makerTemp.makerClean()
        text = self.ui.txtPoint_2.text().split(',')
        self.x = text[0]
        self.y = text[1]

        self.makerTemp.setMarker(self.x, self.y,10,2)

    def vertexEdit(self, item):
        # self.ui.lineEdit.setText(str(item.row()))
        # self.layer.changeGeometry(self.feature.id(), newgeom)
        # QgsMessageLog.logMessage(str(item.text()), 'T2G Archäologie', Qgis.Info)
        if isNumber(item.text()):
            if item.column() == 0:
                self.koordList[item.row()][0] = item.text()
            if item.column() == 1:
                self.koordList[item.row()][1] = item.text()
            if item.column() == 2:
                self.koordList[item.row()][2] = item.text()
            self.rubberBand.rubberBandClean()
            self.rubberBand.setRubberBandPoly(self.koordList,3)
            #self.setMarker(item)


    def featureUpdate(self):
        ptList = []
        for a in self.koordList:
            item = QgsPoint(float(a[0]), float(a[1]), float(a[2]))
            ptList.append(item)
        self.layer.startEditing()
        if self.layer.geometryType() == QgsWkbTypes.PointGeometry:
            self.layer.dataProvider().changeGeometryValues({self.feature.id(): QgsGeometry(ptList[0])})
        else:
            self.layer.dataProvider().changeGeometryValues({self.feature.id(): QgsGeometry.fromPolyline(ptList)})
        QgsMessageLog.logMessage('Geometrie geändert', 'T2G Archäologie', Qgis.Info)
        self.layer.commitChanges()

    def setTempKoord(self):

        if self.ui.txtPoint.text() == '':
            self.i = None
            self.x = None
            self.y = None
            self.z = None
        else:
            try:
                text = self.ui.txtPoint.text().split(',')
                self.i = text[0][0]
                self.x = text[0][1:]
                self.y = text[1]
                self.z = text[2]
                QgsMessageLog.logMessage(self.i + ',' + self.x + ',' + self.y + ',' + self.z, 'T2G Archäologie',
                                         Qgis.Info)
            except:
                pass

        if self.i == '#':
            QgsMessageLog.logMessage('rechne2', 'T2G Archäologie', Qgis.Info)
            #try:
            text = self.ui.txtPointTemp.text().split(',')
            self.i = '@'
            self.x = float(self.x)-float(text[0])
            self.y = float(self.y)-float(text[1])
            #self.z = float(self.z) - 0
            QgsMessageLog.logMessage(str(self.i) + ',' + str(self.x) + ',' + str(self.y) + ',' + str(self.z), 'T2G Archäologie',
                                     Qgis.Info)
            #except:
            #    pass

    def featureMove(self):
        if self.ui.txtPoint.text() == '':
            QMessageBox.information(None, "Meldung", u"Keine Verschiebungskoordinate eingegeben!")
        else:
            tw = self.ui.tableWidget
            tw.selectAll()
            self.featureVertexMove()

    def featureVertexMove(self):
        self.maker.makerClean()
        tw = self.ui.tableWidget
        if len(self.ui.tableWidget.selectedItems()) == 0:
            # QgsMessageLog.logMessage('Keine Punkte gewählt', 'T2G Archäologie', Qgis.Info)
            QMessageBox.information(None, "Meldung", u"Keine Punkte zum verschieben gewählt!")
            return

        if self.i == '@':
            # QMessageBox.information(None, "Meldung", u"@")

            rowtemp = -1
            for item in tw.selectedItems():
                if item.row() > rowtemp:
                    QgsMessageLog.logMessage(str(tw.item(item.row(), item.column()).text()), 'T2G Archäologie',
                                             Qgis.Info)
                    wert = str(float(tw.item(item.row(), 0).text()) + float(self.x))
                    tw.item(item.row(), 0).setText(wert)
                    wert = str(float(tw.item(item.row(), 1).text()) + float(self.y))
                    tw.item(item.row(), 1).setText(wert)
                    if self.z is not None:
                        wert = str(float(tw.item(item.row(), 2).text()) + float(self.z))
                        tw.item(item.row(), 2).setText(wert)
                    rowtemp = item.row()
            else:
                return

        elif self.i == '#':
            QMessageBox.information(None, "Meldung", u"#")


    def closeEvent(self, event):
        self.dwgClose()
        event.accept()

    def dwgClose(self):
        self.closingPlugin.emit()
        self.maker.makerClean()

        self.ui.canvas_clicked = None
        self.vertexMaker.makerClean()
        self.makerTemp.makerClean()
        self.rubberBandClean()
        iface.mapCanvas().refreshAllLayers()


    def koordholen(self):
        self.iface.mapCanvas().setMapTool(self.ui.canvas_clicked)
