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
from .showPicture import *
import os, csv, subprocess, re


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'myDlgRasterLayerView.ui'))


class RasterLayerViewDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(RasterLayerViewDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        pfad = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), "./..")))
        self.iconpfad = os.path.join(os.path.join(pfad, 'Icons'))
        self.ui = self
        #self.ui.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), 'Icons/Thumbs.gif')))
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.layer = None
        self.singleView = False
        self.viewlist = []
        self.currentItem = None
        self.statusString = ''
        self.suchstrlist = []
        self.row = None
        self.column = None
        self.iface.addDockWidget(Qt.TopDockWidgetArea, self.ui)
        self.ui.tableWidget.setMouseTracking(True)
        self.ui.tableWidget.itemClicked.connect(self.on_itemClicked)
        self.ui.tableWidget.currentItemChanged.connect(self.on_currentItemChanged)
        self.ui.tableWidget.itemSelectionChanged.connect(self.status)
        self.ui.tableWidget.cellClicked.connect(self.on_cellClicked)
        self.ui.tableWidget.cellChanged.connect(self.on_cellChanged)
        self.ui.tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.tableWidget.customContextMenuRequested.connect(self.on_customContextMenu)
        self.ui.butSave.clicked.connect(self.saveBitmap)
        self.ui.butSave.setIcon(QIcon(os.path.join(self.iconpfad, 'media-floppy.png')))
        self.ui.butSave.setToolTip('Ausgewählte Bilder in anderem Order kopieren')

        self.ui.butSave_2.clicked.connect(self.savePictureList)
        self.ui.butSave_2.setIcon(QIcon(os.path.join(self.iconpfad, 'floppyList.gif')))
        self.ui.butSave_2.setToolTip('Ausgewählte Bilder als Liste exportieren')

        self.ui.butFilter.clicked.connect(self.setFilter)
        self.ui.butFilter.setIcon(QIcon(os.path.join(self.iconpfad, 'Filter.gif')))
        self.ui.butFilter.setToolTip('Auswahl mit Filter')

        self.ui.butFilterDel.clicked.connect(self.delFilter)
        self.ui.butFilterDel.setIcon(QIcon(os.path.join(self.iconpfad, 'FilterAllLayerEnt.gif')))
        self.ui.butFilterDel.setToolTip('Filter löschen')

        self.ui.butchecked.clicked.connect(self.on_checked)
        self.ui.butchecked.setIcon(QIcon(os.path.join(self.iconpfad, 'checked.gif')))
        self.ui.butchecked.setToolTip('Alle an')
        self.ui.butunchecked.clicked.connect(self.on_unchecked)
        self.ui.butunchecked.setIcon(QIcon(os.path.join(self.iconpfad, 'unchecked.gif')))
        self.ui.butunchecked.setToolTip('Alle aus')

        self.ui.butsingleView.clicked.connect(self.setSingleView)
        self.ui.butsingleView.setIcon(QIcon(os.path.join(self.iconpfad, 'Ok_grau.png')))
        self.ui.butsingleView.setToolTip('Nur ein Layer sichtbar')

        QgsProject.instance().legendLayersAdded.connect(self.setup)
        QgsProject.instance().layersRemoved.connect(self.setup)

        #self.sp.valueChanged.connect(self.on_setOpacity)
        self.setup()

    def setup(self):
        self.tableWidget.setRowCount(0)
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        #header.setSectionResizeMode(0,QtWidgets.QHeaderView.Stretch)
        i=0
        self.tableWidget.setSortingEnabled(True)
        try:
            for layer in QgsProject.instance().mapLayers().values():
                #QgsMessageLog.logMessage(str(layer.type()), 'T2G Archäologie', Qgis.Info)
                if layer.type() == QgsMapLayer.RasterLayer:
                    if 'http://' in layer.source() or 'https://' in layer.source():
                        continue
                    self.tableWidget.insertRow(i)
                    #pic = QtGui.QIcon(layer.source())
                    #image = QTableWidgetItem()
                    #image.setData(Qt.DecorationRole,pic)
                    chkItem = QTableWidgetItem()
                    chkItem.setText(str(layer.name()))
                    if QgsProject.instance().layerTreeRoot().findLayer(layer.id()).itemVisibilityChecked():
                        chkItem.setCheckState(QtCore.Qt.Checked)
                    else:
                        chkItem.setCheckState(QtCore.Qt.Unchecked)
                    self.tableWidget.setItem(i, 0, chkItem)
                    erw = os.path.splitext(str(layer.source()))[1]
                    self.tableWidget.setItem(i, 1, QTableWidgetItem(str(erw)))
                    self.tableWidget.setItem(i, 2, QTableWidgetItem(str(layer.source())))
                    dateigroesse = str(round(float(os.stat(layer.source()).st_size)/1000000,2))
                    self.tableWidget.setItem(i, 3, QTableWidgetItem(str(dateigroesse) + ' MB'))
                    self.tableWidget.setItem(i, 4, QTableWidgetItem(str(layer.id())))
                    #self.sp.setValue(1)#(layer.renderer().opacity())
                    #self.tableWidget.setItem(i, 5, self.sp)
                    opacity = str(round(layer.renderer().opacity() * 100, 1)) + ' %'
                    self.tableWidget.setItem(i, 5, QTableWidgetItem(opacity))

                    i=i+1
        except:
            pass
        self.tableWidget.setColumnHidden(4,True)
        self.status()

    def status(self):
        try:
            view = 0
            picturelist = []
            for row in range(self.ui.tableWidget.rowCount()):
                item = self.ui.tableWidget.item(row,0)
                picturelist.append(self.tableWidget.item(row, 2).text())
                if item.checkState() == QtCore.Qt.Checked:
                     view = view + 1
            picturelist = sorted(set(picturelist), key=picturelist.index)
            selectCount = len(self.tableWidget.selectedIndexes())
            layerCount = self.ui.tableWidget.rowCount()

            self.ui.label_2.setText(' ' + str(view))
            self.ui.label_4.setText(' ' + str(selectCount))
            self.ui.label_6.setText(' ' + str(layerCount))
            self.ui.label_8.setText(' ' + str(len(picturelist)))
            #self.ui.label.setText('  Ansicht: ' + str(view) + ' - Auswahl: ' + str(selectCount) + ' - Layer: ' + str(layerCount))
        except Exception as e:
            QgsMessageLog.logMessage(str(e), 'T2G Archäologie', Qgis.Info)

    def on_customContextMenu(self, pos):
        contextMenu = QtWidgets.QMenu()
        layOn = contextMenu.addAction(
            QtGui.QIcon(os.path.join(self.iconpfad, "Sichtbar_an.gif")), " an")
        layOn.triggered.connect(self.layerVisibilityOn)
        layOff = contextMenu.addAction(
            QtGui.QIcon(os.path.join(self.iconpfad, "Sichtbar_aus.gif")), " aus")
        layOff.triggered.connect(self.layerVisibilityOff)
        trans = contextMenu.addAction(
            QtGui.QIcon(os.path.join(self.iconpfad, "transp.png")), " Transparenz")
        trans.triggered.connect(self.setOpacity)
        expl = contextMenu.addAction(
            QtGui.QIcon(os.path.join(self.iconpfad, "ordner-open.png")), " Explorer")
        expl.triggered.connect(self.openExplorer)
        open = contextMenu.addAction(
            QtGui.QIcon(os.path.join(self.iconpfad, "Edit.bmp")), " Bearbeiten")
        open.triggered.connect(self.openApp)
        #rasterMerge = contextMenu.addAction(
        #    QtGui.QIcon(os.path.join(self.iconpfad, "Edit.bmp")), " Bearbeiten")
        #rasterMerge.triggered.connect(self.rasterMerge)
        contextMenu.exec_(QtGui.QCursor.pos())

    def on_cellClicked(self,row,column):
        self.row = row
        self.column = column

    def setOpacity(self):
        layerList = []
        for item in self.tableWidget.selectedIndexes():
            id = self.tableWidget.item(item.row(), 4).text()
            for layer in QgsProject.instance().mapLayers().values():
                    if str(layer.id()) == id:
                        layerList.append(layer)

        opa = Opacity(self.iface,layerList)
        while opa.close == False:
            QApplication.processEvents()
        QgsMessageLog.logMessage('weiter', 'opa', Qgis.Info)
        if opa.opacity is None:
            opacity = '100,0 %'
        else:
            opacity = str(round(opa.opacity * 100,1)) + ' %'
        for item in self.tableWidget.selectedIndexes():
            self.tableWidget.item(item.row(), 5).setText(opacity)

    def layerVisibilityOn(self):
        for item in self.tableWidget.selectedIndexes():
            item1 = self.ui.tableWidget.item(item.row(), 0)
            item2 = self.ui.tableWidget.item(item.row(), 4)
            id = item2.text()
            QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(True)
            item1.setCheckState(QtCore.Qt.Checked)
            self.ui.tableWidget.clearSelection()

    def layerVisibilityOff(self):
        for item in self.tableWidget.selectedIndexes():
            item1 = self.ui.tableWidget.item(item.row(), 0)
            item2 = self.ui.tableWidget.item(item.row(), 4)
            id = item2.text()
            QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)
            item1.setCheckState(QtCore.Qt.Unchecked)
            self.ui.tableWidget.clearSelection()

    def on_checked(self):
        self.ui.tableWidget.selectAll()
        self.layerVisibilityOn()
        self.status()

    def on_unchecked(self):
        self.ui.tableWidget.selectAll()
        #self.ui.tableWidget.clearSelection()
        self.layerVisibilityOff()
        self.status()

    def openExplorer(self):
        pfad = ''
        for item in self.tableWidget.selectedIndexes():
            pfad = pfad + '"' + self.tableWidget.item(item.row(), 2).text() + '"' + ','
            #pfad = pfad + self.tableWidget.item(item.row(), 2).text() + ','
            #break
        pfad = pfad.replace('/','\\')[:-1] #+ '"'
        QgsMessageLog.logMessage(str(pfad), 'T2G Archäologie', Qgis.Info)
        subprocess.Popen("explorer.exe /e, /select, " + pfad)
        #subprocess.Popen(r"C:\Windows\System32\rundl32.exe C:\Program Files (x86)\Windows Photo Viewer\PhotoViewer.dll " + pfad)

    def openApp(self):
        for item in self.tableWidget.selectedIndexes():
            pfad = self.tableWidget.item(item.row(), 2).text()
            pfad = os.path.realpath(pfad)
            os.startfile(pfad)

    def rasterMerge(self):
        pfad = ''
        for item in self.tableWidget.selectedIndexes():
            value = self.tableWidget.item(item.row(), 2).text()
            pfad = pfad + value + ' '
        pfad = pfad.replace('/', '\\')[:-1]
        for item in self.tableWidget.selectedIndexes():
            value = self.tableWidget.item(item.row(), 2).text()
            QgsMessageLog.logMessage(str(value) , 'T2G Archäologie', Qgis.Info)
            string = r'gdal_merge -ot Float32 -of GTiff -o C:/444.tif C:/111.tif'# + value  + '"'
            os.system(string)

    def on_cellChanged(self, row, column):
        QgsMessageLog.logMessage(str(row), 'T2G Archäologie', Qgis.Info)
        try:
            if column == 0:
                id = self.tableWidget.item(row, 4).text()
                name = self.tableWidget.item(row, 0).text()
                QgsProject.instance().layerTreeRoot().findLayer(id).setName(name)
        except Exception as e:
            pass
            #QgsMessageLog.logMessage(str(e), 'T2G Archäologie', Qgis.Info)

    def on_itemClicked(self,item):
        self.currentItem = {'row': item.row(), 'column': item.column()}
        try:
            if item.column() == 0 or self.singleView == True:
                id = self.tableWidget.item(item.row(), 4).text()
                if item.checkState() == QtCore.Qt.Checked:
                    QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(True)
                else:
                    QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)

            id = self.tableWidget.item(item.row(), 4).text()
            for layer in QgsProject.instance().mapLayers().values():
                if layer.type() == QgsMapLayer.RasterLayer:
                    if str(layer.id()) == id:
                        self.layer = layer
                        self.iface.setActiveLayer(self.layer)
                        self.canvas.setExtent(self.layer.extent())
                        self.canvas.refresh()

            if self.singleView == True:
                item1 = self.ui.tableWidget.item(item.row(), 0)
                item1.setCheckState(QtCore.Qt.Checked)

        except Exception as e:
            QgsMessageLog.logMessage(str(e), 'T2G Archäologie', Qgis.Info)

        self.status()

    def on_currentItemChanged(self,current,previous):
        try:
            if self.singleView == True:
                id = self.tableWidget.item(previous.row(), 4).text()
                QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)
                item = self.tableWidget.item(previous.row(), 0)
                item.setCheckState(QtCore.Qt.Unchecked)

                id = self.tableWidget.item(current.row(), 4).text()
                QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(True)
                item = self.tableWidget.item(current.row(), 0)
                item.setCheckState(QtCore.Qt.Checked)
        except Exception as e:
            QgsMessageLog.logMessage(str(e), 'T2G Archäologie', Qgis.Info)

    def saveBitmap(self):
        selectCount = len(self.tableWidget.selectedIndexes())
        if selectCount == 0:
            QMessageBox.information(None, "Meldung", u"Keine Einträge ausgewählt!")
            return
        else:
            dst_root = QFileDialog.getExistingDirectory(None, 'Speicherpfad',
                                                        QgsProject.instance().readPath('./../Jobs'))
        if dst_root == '':
            return
        progress = progressBar('Fortschritt')
        QCoreApplication.processEvents()

        progress.setMaximum(selectCount)
        dateiGroesse = 0
        for item in self.tableWidget.selectedIndexes():
            v = float(self.tableWidget.item(item.row(), 3).text().split(' ')[0])
            dateiGroesse = dateiGroesse + v

        picturelist = []
        for item in self.tableWidget.selectedIndexes():
            picturelist.append(self.tableWidget.item(item.row(), 2).text())
        picturelist = sorted(set(picturelist),key=picturelist.index)
        count = 1

        for i in range(len(picturelist)):
            if progress.close == False:
                progress.setValue(count)
                progress.setText(str(count) + ' von ' + str(len(picturelist)) + ' Bilder kopiert'+ ' (' + str(round(dateiGroesse,2)) +' MB)')
                src_dir = picturelist[i]
                head, tail = os.path.split(src_dir)
                fileFunc().file_copy(src_dir,os.path.join(dst_root,tail))
                #wld Datei kopieren
                tailsplit = tail.split('.')

                fileFunc().file_copy(src_dir, os.path.join(dst_root, tailsplit[0] + '.wld'))
                fileFunc().file_copy(src_dir, os.path.join(dst_root, tail + '.aux.xml'))
                count = count + 1
                QCoreApplication.processEvents()
                QgsMessageLog.logMessage(str(os.path.join(dst_root,tail)), 'T2G Archäologie', Qgis.Info)
            else:
                break
        pass

    def savePictureList(self):
        selectCount = len(self.tableWidget.selectedIndexes())
        if selectCount == 0:
            QMessageBox.information(None, "Meldung", u"Keine Einträge ausgewählt!")
            return
        else:
            output_file = QFileDialog.getSaveFileName(None, 'Speicherpfad',
                                                      QgsProject.instance().readPath('./../Jobs'),
                                                      'Excel (*.csv);;Text mit Tab (*.txt);;Alle Dateien (*.*)')
            if output_file[0] != '':
                erw = str(output_file[1])
                output_file = open(output_file[0], 'w')
                output_file.write('Layername\tTyp\tPfad\tGröße\n')
                for item in self.tableWidget.selectedIndexes():
                    name = self.tableWidget.item(item.row(), 0).text()
                    typ = self.tableWidget.item(item.row(), 1).text()
                    pfad = self.tableWidget.item(item.row(), 2).text()
                    groesse = self.tableWidget.item(item.row(), 3).text()
                    if erw == 'Excel (*.csv)':
                        line = '%s, %s, %s, %s\n' % ('"'+name+'"','"'+ typ+'"','"'+ pfad+'"','"'+groesse+'"')
                        line = line.replace(' ', '')
                    elif erw == 'Text mit Tab (*.txt)':
                        line = '%s, %s, %s, %s\n' % (name + '\t',typ + '\t',pfad + '\t',groesse)
                        line = line.replace('\t,', '\t')
                    QgsMessageLog.logMessage(str(line), 'T2G Archäologie', Qgis.Info)

                    output_file.write(str(line))
                output_file.close()

    def setFilter(self):
        find = False
        #suchstr, ok = QInputDialog.getText(self, 'Suche', 'Suchstring')

        #self.suchstrlist = ("keine", "100", "75", "50", "25")
        suchstr, ok = QInputDialog.getItem(None, 'Suche', 'Zeichenfolge eingeben', self.suchstrlist, 0, True)
        if ok != True:
            return

        self.layerVisibilityOff()
        for row in range(self.ui.tableWidget.rowCount()):
            item = self.ui.tableWidget.item(row,0)
            item2 = self.ui.tableWidget.item(row,4)
            text = item.text()
            id = item2.text()

            if suchstr in text:
                item.setCheckState(QtCore.Qt.Checked)
                QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(True)
                self.ui.tableWidget.showRow(row)
                find = True
            else:
                item.setCheckState(QtCore.Qt.Unchecked)
                QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)
                self.ui.tableWidget.hideRow(row)

        if find == False:
             QMessageBox.information(None, "Meldung", u"Keine Einträge gefunden!")
        else:
            self.suchstrlist.append(suchstr)
        self.status()

    def delFilter(self):
        for row in range(self.ui.tableWidget.rowCount()):
            self.ui.tableWidget.showRow(row)
        self.status()

    def setSingleView(self):
        QgsMessageLog.logMessage('klick', 'T2G Archäologie', Qgis.Info)
        try:
            if self.singleView == False:
                self.ui.butsingleView.setIcon(QIcon(os.path.join(self.iconpfad, 'Ok.png')))
                self.singleView = True
                #self.checkRowList = []
                for layer in QgsProject.instance().mapLayers().values():
                    if layer.type() == QgsMapLayer.RasterLayer:
                        if QgsProject.instance().layerTreeRoot().findLayer(layer.id()).itemVisibilityChecked():
                            self.viewlist.append(layer.id())

                self.on_unchecked()
                self.status()
            else:
                self.ui.butsingleView.setIcon(QIcon(os.path.join(self.iconpfad, 'Ok_grau.png')))
                self.singleView = False
                for i in range(len(self.viewlist)):
                    QgsProject.instance().layerTreeRoot().findLayer(self.viewlist [i]).setItemVisibilityChecked(True)
                    QgsMessageLog.logMessage(str(self.viewlist [i]), 'T2G Archäologie', Qgis.Info)
                    id = self.ui.tableWidget.item(self.currentItem['row'], 4).text()
                    if id  not in self.viewlist:
                        QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)
                self.viewlist = []
                self.setup()

        except Exception as e:
            QgsMessageLog.logMessage(str(e), 'T2G Archäologie', Qgis.Info)

    def OK(self):
        self.ui.close()

    def Abbruch(self):
        self.ui.close()

    def closeEvent(self, event):
        event.accept()


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'opacity.ui'))

class Opacity(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface,layerlist, parent=None):
        super(Opacity, self).__init__(parent)
        self.setupUi(self)
        self.ui = self
        self.ui.show()
        self.opacity = layerlist[0].renderer().opacity()
        self.iface = iface
        self.layerlist = layerlist
        self.ui.mOpacityWidget.opacityChanged.connect(self.setOpasity)
        self.close = False
        self.ui.mOpacityWidget.setOpacity(self.opacity)

        QgsMessageLog.logMessage('klick'+str(self.opacity), 'T2G Archäologie', Qgis.Info)
    def setOpasity(self,value):
        for layer in self.layerlist:
            layer.renderer().setOpacity(float(value))
            layer.triggerRepaint()
        self.opacity = float(value)

    def closeEvent(self, event):
        #self.opacity = self.ui.mOpacityWidget.opacity
        self.close = True
        event.accept()