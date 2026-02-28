import subprocess
from os import path as os_path, stat as os_stat, startfile, system

from qgis.PyQt.QtCore import pyqtSignal, Qt, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QCursor
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QHeaderView,
    QTableWidgetItem,
    QMenu,
    QApplication,
    QMessageBox,
    QFileDialog,
    QInputDialog,
    QDialog,
)
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsMapLayer, QgsMessageLog, Qgis
from qgis.utils import iface

from .operations import gtiff2jpg, rasterCut, setCutMask, delCutMask
from ...settings import PLUGIN_NAME
from ...common.utils import FileFunctions, ProgressBar
from ...icons import ICON_PATHS


class RasterGui:
    def __init__(self, dockWidget):
        self.dockwidget = dockWidget
        self._raster_layer_view = None
        self.dockwidget.pushButton_4.setIcon(QIcon(ICON_PATHS["V_Jpg-Tif"]))
        self.dockwidget.pushButton_4.clicked.connect(gtiff2jpg)
        self.dockwidget.pushButton_5.setIcon(QIcon(ICON_PATHS["cut"]))
        self.dockwidget.pushButton_5.clicked.connect(rasterCut)
        self.dockwidget.pushButton_6.setIcon(QIcon(ICON_PATHS["cutmask"]))
        self.dockwidget.pushButton_6.clicked.connect(setCutMask)
        self.dockwidget.pushButton_7.setIcon(QIcon(ICON_PATHS["cutmaskdel"]))
        self.dockwidget.pushButton_7.clicked.connect(delCutMask)
        self.dockwidget.pushButton_11.setIcon(QIcon(ICON_PATHS["Thumbs"]))
        self.dockwidget.pushButton_11.clicked.connect(self._show_raster_layer_view)
        self.dockwidget.pushButton_11.setToolTip("Übersicht der Rasterlayer")

    def _show_raster_layer_view(self):
        if self._raster_layer_view is None:
            self._raster_layer_view = RasterLayerViewDockWidget()
            iface.addDockWidget(Qt.TopDockWidgetArea, self._raster_layer_view)
        self._raster_layer_view.show()
        self._raster_layer_view.raise_()

    def setup(self):
        pass


FORM_CLASS, _ = uic.loadUiType(os_path.join(os_path.dirname(__file__), "forms", "dlgRasterLayerView.ui"))


class RasterLayerViewDockWidget(QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.canvas = iface.mapCanvas()
        self.layer = None
        self.singleView = False
        self.viewlist = []
        self.currentItem = None
        self.statusString = ""
        self.suchstrlist = []
        self.row = None
        self.column = None
        self.tableWidget.setMouseTracking(True)
        self.tableWidget.itemClicked.connect(self.on_itemClicked)
        self.tableWidget.currentItemChanged.connect(self.on_currentItemChanged)
        self.tableWidget.itemSelectionChanged.connect(self.status)
        self.tableWidget.cellClicked.connect(self.on_cellClicked)
        self.tableWidget.cellChanged.connect(self.on_cellChanged)
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.on_customContextMenu)
        self.butSave.clicked.connect(self.saveBitmap)
        self.butSave.setIcon(QIcon(ICON_PATHS["media-floppy"]))
        self.butSave.setToolTip("Ausgewählte Bilder in anderem Order kopieren")

        self.butSave_2.clicked.connect(self.savePictureList)
        self.butSave_2.setIcon(QIcon(ICON_PATHS["floppyList"]))
        self.butSave_2.setToolTip("Ausgewählte Bilder als Liste exportieren")

        self.butFilter.clicked.connect(self.setFilter)
        self.butFilter.setIcon(QIcon(ICON_PATHS["Filter"]))
        self.butFilter.setToolTip("Auswahl mit Filter")

        self.butFilterDel.clicked.connect(self.delFilter)
        self.butFilterDel.setIcon(QIcon(ICON_PATHS["FilterAllLayerEnt"]))
        self.butFilterDel.setToolTip("Filter löschen")

        self.butchecked.clicked.connect(self.on_checked)
        self.butchecked.setIcon(QIcon(ICON_PATHS["checked"]))
        self.butchecked.setToolTip("Alle an")
        self.butunchecked.clicked.connect(self.on_unchecked)
        self.butunchecked.setIcon(QIcon(ICON_PATHS["unchecked"]))
        self.butunchecked.setToolTip("Alle aus")

        self.butsingleView.clicked.connect(self.setSingleView)
        self.butsingleView.setIcon(QIcon(ICON_PATHS["Ok_grau"]))
        self.butsingleView.setToolTip("Nur ein Layer sichtbar")

        QgsProject.instance().legendLayersAdded.connect(self.setup)
        QgsProject.instance().layersRemoved.connect(self.setup)

        # self.sp.valueChanged.connect(self.on_setOpacity)
        self.setup()

    def setup(self):
        self.tableWidget.setRowCount(0)
        header = self.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(0, QHeaderView.Stretch)
        i = 0
        self.tableWidget.setSortingEnabled(True)
        try:
            for layer in QgsProject.instance().mapLayers().values():
                if layer.type() == QgsMapLayer.RasterLayer:
                    if "http://" in layer.source() or "https://" in layer.source():
                        continue
                    self.tableWidget.insertRow(i)
                    # pic = QIcon(layer.source())
                    # image = QTableWidgetItem()
                    # image.setData(Qt.DecorationRole,pic)
                    chkItem = QTableWidgetItem()
                    chkItem.setText(str(layer.name()))
                    if QgsProject.instance().layerTreeRoot().findLayer(layer.id()).itemVisibilityChecked():
                        chkItem.setCheckState(Qt.Checked)
                    else:
                        chkItem.setCheckState(Qt.Unchecked)
                    self.tableWidget.setItem(i, 0, chkItem)
                    erw = os_path.splitext(str(layer.source()))[1]
                    self.tableWidget.setItem(i, 1, QTableWidgetItem(str(erw)))
                    self.tableWidget.setItem(i, 2, QTableWidgetItem(str(layer.source())))
                    dateigroesse = str(round(float(os_stat(layer.source()).st_size) / 1000000, 2))
                    self.tableWidget.setItem(i, 3, QTableWidgetItem(str(dateigroesse) + " MB"))
                    self.tableWidget.setItem(i, 4, QTableWidgetItem(str(layer.id())))
                    # self.sp.setValue(1)#(layer.renderer().opacity())
                    # self.tableWidget.setItem(i, 5, self.sp)
                    opacity = str(round(layer.renderer().opacity() * 100, 1)) + " %"
                    self.tableWidget.setItem(i, 5, QTableWidgetItem(opacity))

                    i = i + 1
        except Exception as e:
            QgsMessageLog.logMessage(
                message="RasterLayerViewDockWidget->setup: failed: " + str(e),
                tag=PLUGIN_NAME,
                level=Qgis.MessageLevel.Warning,
            )
        self.tableWidget.setColumnHidden(4, True)
        self.status()

    def status(self):
        try:
            view = 0
            picturelist = []
            for row in range(self.tableWidget.rowCount()):
                item = self.tableWidget.item(row, 0)
                picturelist.append(self.tableWidget.item(row, 2).text())
                if item.checkState() == Qt.Checked:
                    view = view + 1
            picturelist = sorted(set(picturelist), key=picturelist.index)
            selectCount = len(self.tableWidget.selectedIndexes())
            layerCount = self.tableWidget.rowCount()

            self.label_2.setText(" " + str(view))
            self.label_4.setText(" " + str(selectCount))
            self.label_6.setText(" " + str(layerCount))
            self.label_8.setText(" " + str(len(picturelist)))
            # self.label.setText('  Ansicht: ' + str(view) + ' - Auswahl: ' + str(selectCount) + ' - Layer: ' + str(layerCount))
        except Exception as e:
            QgsMessageLog.logMessage(str(e), PLUGIN_NAME, level=Qgis.MessageLevel.Warning)

    def on_customContextMenu(self, pos):
        contextMenu = QMenu()
        layOn = contextMenu.addAction(QIcon(ICON_PATHS["Sichtbar_an"]), " an")
        layOn.triggered.connect(self.layerVisibilityOn)
        layOff = contextMenu.addAction(QIcon(ICON_PATHS["Sichtbar_aus"]), " aus")
        layOff.triggered.connect(self.layerVisibilityOff)
        trans = contextMenu.addAction(QIcon(ICON_PATHS["transp"]), " Transparenz")
        trans.triggered.connect(self.setOpacity)
        expl = contextMenu.addAction(QIcon(ICON_PATHS["ordner-open"]), " Explorer")
        expl.triggered.connect(self.openExplorer)
        open = contextMenu.addAction(QIcon(ICON_PATHS["Edit"]), " Bearbeiten")
        open.triggered.connect(self.openApp)
        # rasterMerge = contextMenu.addAction(
        #    QtGui.QIcon(ICON_PATHS["Edit"]), " Bearbeiten")
        # rasterMerge.triggered.connect(self.rasterMerge)
        contextMenu.exec_(QCursor.pos())

    def on_cellClicked(self, row, column):
        self.row = row
        self.column = column

    def setOpacity(self):
        layerList = []
        for item in self.tableWidget.selectedIndexes():
            id = self.tableWidget.item(item.row(), 4).text()
            for layer in QgsProject.instance().mapLayers().values():
                if str(layer.id()) == id:
                    layerList.append(layer)

        opa = Opacity(layerList)
        while opa.close == False:
            QApplication.processEvents()
        QgsMessageLog.logMessage("weiter", "opa", Qgis.Info)
        if opa.opacity is None:
            opacity = "100,0 %"
        else:
            opacity = str(round(opa.opacity * 100, 1)) + " %"
        for item in self.tableWidget.selectedIndexes():
            self.tableWidget.item(item.row(), 5).setText(opacity)

    def layerVisibilityOn(self):
        for item in self.tableWidget.selectedIndexes():
            item1 = self.tableWidget.item(item.row(), 0)
            item2 = self.tableWidget.item(item.row(), 4)
            id = item2.text()
            QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(True)
            item1.setCheckState(Qt.Checked)
            self.tableWidget.clearSelection()

    def layerVisibilityOff(self):
        for item in self.tableWidget.selectedIndexes():
            item1 = self.tableWidget.item(item.row(), 0)
            item2 = self.tableWidget.item(item.row(), 4)
            id = item2.text()
            QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)
            item1.setCheckState(Qt.Unchecked)
            self.tableWidget.clearSelection()

    def on_checked(self):
        self.tableWidget.selectAll()
        self.layerVisibilityOn()
        self.status()

    def on_unchecked(self):
        self.tableWidget.selectAll()
        # self.tableWidget.clearSelection()
        self.layerVisibilityOff()
        self.status()

    def openExplorer(self):
        pfad = ""
        for item in self.tableWidget.selectedIndexes():
            pfad = pfad + '"' + self.tableWidget.item(item.row(), 2).text() + '"' + ","
            # pfad = pfad + self.tableWidget.item(item.row(), 2).text() + ','
            # break
        pfad = pfad.replace("/", "\\")[:-1]  # + '"'
        QgsMessageLog.logMessage(str(pfad), PLUGIN_NAME, Qgis.Info)
        subprocess.Popen("explorer.exe /e, /select, " + pfad)
        subprocess.Popen(
            r"C:\Windows\System32\rundll32.exe C:\Programme (x86)\Windows Photo Viewer\PhotoViewer.dll " + pfad
        )

    def openApp(self):
        for item in self.tableWidget.selectedIndexes():
            pfad = self.tableWidget.item(item.row(), 2).text()
            pfad = os_path.realpath(pfad)
            startfile(pfad)

    def rasterMerge(self):
        pfad = ""
        for item in self.tableWidget.selectedIndexes():
            value = self.tableWidget.item(item.row(), 2).text()
            pfad = pfad + value + " "
        pfad = pfad.replace("/", "\\")[:-1]
        for item in self.tableWidget.selectedIndexes():
            value = self.tableWidget.item(item.row(), 2).text()
            QgsMessageLog.logMessage(str(value), PLUGIN_NAME, Qgis.Info)
            string = r"gdal_merge -ot Float32 -of GTiff -o C:/444.tif C:/111.tif"  # + value  + '"'
            system(string)

    def on_cellChanged(self, row, column):
        QgsMessageLog.logMessage(str(row), PLUGIN_NAME, Qgis.Info)
        try:
            if column == 0:
                id = self.tableWidget.item(row, 4).text()
                name = self.tableWidget.item(row, 0).text()
                QgsProject.instance().layerTreeRoot().findLayer(id).setName(name)
        except Exception as e:
            QgsMessageLog.logMessage(str(e), PLUGIN_NAME, Qgis.Info)

    def on_itemClicked(self, item):
        try:
            if item.column() == 0 or self.singleView == True:
                id = self.tableWidget.item(item.row(), 4).text()
                if item.checkState() == Qt.Checked:
                    QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(True)
                else:
                    QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)

            id = self.tableWidget.item(item.row(), 4).text()
            for layer in QgsProject.instance().mapLayers().values():
                if layer.type() == QgsMapLayer.RasterLayer:
                    if str(layer.id()) == id:
                        self.layer = layer
                        iface.setActiveLayer(self.layer)
                        self.canvas.setExtent(self.layer.extent())
                        self.canvas.refresh()

            if self.singleView == True:
                item1 = self.tableWidget.item(item.row(), 0)
                item1.setCheckState(Qt.Checked)

        except Exception as e:
            QgsMessageLog.logMessage(str(e), PLUGIN_NAME, Qgis.Info)

        self.status()

    def on_currentItemChanged(self, current, previous):
        try:
            if self.singleView == True:
                id = self.tableWidget.item(previous.row(), 4).text()
                QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)
                item = self.tableWidget.item(previous.row(), 0)
                item.setCheckState(Qt.Unchecked)

                id = self.tableWidget.item(current.row(), 4).text()
                QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(True)
                item = self.tableWidget.item(current.row(), 0)
                item.setCheckState(Qt.Checked)
        except Exception as e:
            QgsMessageLog.logMessage(str(e), PLUGIN_NAME, Qgis.Info)

    def saveBitmap(self):
        selectCount = len(self.tableWidget.selectedIndexes())
        if selectCount == 0:
            QMessageBox.information(None, "Meldung", "Keine Einträge ausgewählt!")
            return
        else:
            dst_root = QFileDialog.getExistingDirectory(
                None, "Speicherpfad", QgsProject.instance().readPath("./../Jobs")
            )
        if dst_root == "":
            return
        progress = ProgressBar("Fortschritt")
        QCoreApplication.processEvents()

        progress.setMaximum(selectCount)
        dateiGroesse = 0
        for item in self.tableWidget.selectedIndexes():
            v = float(self.tableWidget.item(item.row(), 3).text().split(" ")[0])
            dateiGroesse = dateiGroesse + v

        picturelist = []
        for item in self.tableWidget.selectedIndexes():
            picturelist.append(self.tableWidget.item(item.row(), 2).text())
        picturelist = sorted(set(picturelist), key=picturelist.index)
        count = 1

        for src_dir in picturelist:
            if progress.close:
                break
            progress.setValue(count)
            progress.setText(f"{count} von {len(picturelist)} Bilder kopiert ({round(dateiGroesse, 2)} MB)")

            head, tail = os_path.split(src_dir)
            FileFunctions().file_copy(src_dir, os_path.join(dst_root, tail))
            # wld Datei kopieren
            tailsplit = tail.split(".")

            FileFunctions().file_copy(src_dir, os_path.join(dst_root, tailsplit[0] + ".wld"))
            FileFunctions().file_copy(src_dir, os_path.join(dst_root, tail + ".aux.xml"))
            count = count + 1
            QCoreApplication.processEvents()
            QgsMessageLog.logMessage(str(os_path.join(dst_root, tail)), PLUGIN_NAME, Qgis.Info)

    def savePictureList(self):
        selectCount = len(self.tableWidget.selectedIndexes())
        if selectCount == 0:
            QMessageBox.information(None, "Meldung", "Keine Einträge ausgewählt!")
            return

        output_file = QFileDialog.getSaveFileName(
            None,
            "Speicherpfad",
            QgsProject.instance().readPath("./../Jobs"),
            "Excel (*.csv);;Text mit Tab (*.txt);;Alle Dateien (*.*)",
        )
        if output_file[0] != "":
            erw = str(output_file[1])
            output_file = open(output_file[0], "w")
            output_file.write("Layername\tTyp\tPfad\tGröße\n")
            for item in self.tableWidget.selectedIndexes():
                name = self.tableWidget.item(item.row(), 0).text()
                typ = self.tableWidget.item(item.row(), 1).text()
                pfad = self.tableWidget.item(item.row(), 2).text()
                groesse = self.tableWidget.item(item.row(), 3).text()
                if erw == "Excel (*.csv)":
                    line = "%s, %s, %s, %s\n" % (
                        '"' + name + '"',
                        '"' + typ + '"',
                        '"' + pfad + '"',
                        '"' + groesse + '"',
                    )
                    line = line.replace(" ", "")
                elif erw == "Text mit Tab (*.txt)":
                    line = "%s, %s, %s, %s\n" % (name + "\t", typ + "\t", pfad + "\t", groesse)
                    line = line.replace("\t,", "\t")
                QgsMessageLog.logMessage(str(line), PLUGIN_NAME, Qgis.Info)

                output_file.write(str(line))
            output_file.close()

    def setFilter(self):
        find = False
        # suchstr, ok = QInputDialog.getText(self, 'Suche', 'Suchstring')

        # self.suchstrlist = ("keine", "100", "75", "50", "25")
        suchstr, ok = QInputDialog.getItem(None, "Suche", "Zeichenfolge eingeben", self.suchstrlist, 0, True)
        if ok != True:
            return

        self.layerVisibilityOff()
        for row in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(row, 0)
            item2 = self.tableWidget.item(row, 4)
            text = item.text()
            id = item2.text()

            if suchstr in text:
                item.setCheckState(Qt.Checked)
                QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(True)
                self.tableWidget.showRow(row)
                find = True
            else:
                item.setCheckState(Qt.Unchecked)
                QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)
                self.tableWidget.hideRow(row)

        if find == False:
            QMessageBox.information(None, "Meldung", "Keine Einträge gefunden!")
        else:
            self.suchstrlist.append(suchstr)
        self.status()

    def delFilter(self):
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.showRow(row)
        self.status()

    def setSingleView(self):
        try:
            if self.singleView == False:
                self.butsingleView.setIcon(QIcon(ICON_PATHS["Ok"]))
                self.singleView = True
                for layer in QgsProject.instance().mapLayers().values():
                    if layer.type() == QgsMapLayer.RasterLayer:
                        if QgsProject.instance().layerTreeRoot().findLayer(layer.id()).itemVisibilityChecked():
                            self.viewlist.append(layer.id())

                self.on_unchecked()
                self.status()
            else:
                self.butsingleView.setIcon(QIcon(ICON_PATHS["Ok_grau"]))
                self.singleView = False
                for i in range(len(self.viewlist)):
                    QgsProject.instance().layerTreeRoot().findLayer(self.viewlist[i]).setItemVisibilityChecked(True)
                    QgsMessageLog.logMessage(str(self.viewlist[i]), PLUGIN_NAME, Qgis.Info)
                    id = self.tableWidget.item(self.currentItem["row"], 4).text()
                    if id not in self.viewlist:
                        QgsProject.instance().layerTreeRoot().findLayer(id).setItemVisibilityChecked(False)
                self.viewlist = []
                self.setup()

        except Exception as e:
            QgsMessageLog.logMessage(str(e), PLUGIN_NAME, Qgis.Info)


FORM_CLASS, _ = uic.loadUiType(os_path.join(os_path.dirname(__file__), "forms", "opacity.ui"))


class Opacity(QDialog, FORM_CLASS):
    def __init__(self, layerlist, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.show()
        self.opacity = layerlist[0].renderer().opacity()
        self.layerlist = layerlist
        self.mOpacityWidget.opacityChanged.connect(self.setOpacity)
        self.close = False
        self.mOpacityWidget.setOpacity(self.opacity)

        QgsMessageLog.logMessage("klick" + str(self.opacity), PLUGIN_NAME, Qgis.Info)

    def setOpacity(self, value):
        for layer in self.layerlist:
            layer.renderer().setOpacity(float(value))
            layer.triggerRepaint()
        self.opacity = float(value)

    def closeEvent(self, event):
        self.close = True
        event.accept()
