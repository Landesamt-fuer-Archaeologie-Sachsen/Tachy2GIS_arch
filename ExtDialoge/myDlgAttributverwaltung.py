# -*- coding: utf-8 -*-
from os import path as os_path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QInputDialog, QLineEdit, QDialog, QMessageBox
from qgis.PyQt import uic
from qgis.core import QgsProject

from ..utils.functions import csvToList, csvWriter, Listfilter, getListfilterIndex


class DlgAttributverwaltung(QDialog):
    def __init__(self, iface, parent=None):
        super(DlgAttributverwaltung, self).__init__(parent)
        iconpfad = os_path.join(os_path.dirname(__file__), "..", "Icons")
        self.ui = uic.loadUi(os_path.join(os_path.dirname(__file__), "myDlgAttributverwaltung.ui"), self)
        self.iface = iface
        # self.ui.txtLayGemarkung.textChanged.connect(self.stempel)
        # self.ui.txtLayGemarkung.setToolTip('Gemarkung')

        self.ui.listObjektTyp.currentItemChanged.connect(self.item_click_Typ)
        self.ui.listObjektArt.currentItemChanged.connect(self.item_click_Art)
        self.ui.butaddFilter.clicked.connect(self.addFilter)
        self.ui.butdelFilter.clicked.connect(self.delFilter)
        self.ui.butaddFilter.setIcon(QIcon(os_path.join(iconpfad, "go-next.jpg")))
        self.ui.butObjektTypNeu.clicked.connect(self.objektTypNeu)
        self.ui.butObjektTypNeu.setIcon(QIcon(os_path.join(iconpfad, "NeuDS.jpg")))
        self.ui.butObjektArtNeu.clicked.connect(self.objektArtNeu)
        self.ui.butObjektArtNeu.setIcon(QIcon(os_path.join(iconpfad, "NeuDS.jpg")))
        self.ui.butObjektTypLayerArtEdit.clicked.connect(self.objektTypLayerArtEdit)
        self.ui.butObjektTypLayerArtEdit.setIcon(QIcon(os_path.join(iconpfad, "Edit.bmp")))

        self.ui.setup()

    def setup(self):
        self.QgisDateiPfad = QgsProject.instance().readPath("./")
        self.ProjPfad = os_path.abspath(os_path.join(self.QgisDateiPfad, "./.."))
        self.objektTypList = csvToList(os_path.join(self.ProjPfad, "Listen\Objekttypen.csv"))
        self.objektArtList = csvToList(os_path.join(self.ProjPfad, "Listen\Objektarten.csv"))

        self.listSort()
        self.aaa()

    def listSort(self):
        self.objektTypList = sorted(self.objektTypList, key=lambda x: "".join(x).lower())
        self.objektArtList = sorted(self.objektArtList, key=lambda x: "".join(x).lower())

    def csvWrite(self):
        csvWriter(os_path.join(self.ProjPfad, "Listen\Objekttypen.csv"), self.objektTypList)
        csvWriter(os_path.join(self.ProjPfad, "Listen\Objektarten.csv"), self.objektArtList)

    def aaa(self):
        self.ui.listObjektTyp.clear()
        self.ui.listObjektArt.clear()

        for item in self.objektTypList:
            self.ui.listObjektTyp.addItem(item[0])
        for item in self.objektArtList:
            self.ui.listObjektArt.addItem(item[0])

        self.ui.labObjektTypCount.setText(str(len(self.ui.listObjektTyp)) + " Einträge")
        self.ui.labObjektArtCount.setText(str(len(self.ui.listObjektArt)) + " Einträge")

    def item_click_Typ(self, item):
        if item == None:
            return
        self.ui.txtObjektTypLayerArt.clear()
        swert = str(item.text())
        wert = Listfilter(self.objektTypList, 4, 0, swert, "genau")
        self.ui.txtObjektTypLayerArt.setText(wert[0])

        self.ui.listObjektArt_2.clear()
        swert = "|" + str(item.text()) + "|"
        wert = Listfilter(self.objektArtList, 0, 1, swert, "")
        wert.sort()
        self.ui.listObjektArt_2.addItems(wert)
        self.ui.labObjektArtCount_2.setText(str(len(self.ui.listObjektArt_2)) + " Einträge")

    def item_click_Art(self, item):
        if item == None:
            return
        self.ObjTypItem = item
        self.ui.listObjektArtFilter.clear()
        swert = str(item.text())
        string = str(Listfilter(self.objektArtList, 1, 0, swert, "genau")[0])[1:-1]
        wert = string.split("|")

        for i in range(len(wert)):
            self.ui.listObjektArtFilter.addItem(wert[i])
        pass

    def addFilter(self):
        items = []
        for row in self.objektArtList:
            items.append(row[0])
        item, okPressed = QInputDialog.getItem(self, "Objektart", "Objektart:", items, 0, False)
        if okPressed and item:
            i = getListfilterIndex(self.objektArtList, 0, item, "genau")
            a = self.listObjektTyp.currentRow()
            wert = self.objektTypList[a][0]
            self.objektArtList[i][1] = (self.objektArtList[i][1])[:-1] + "|" + wert + "|"

            self.csvWrite()
            self.setup()
            self.listObjektTyp.setCurrentRow(a)

    def delFilter(self):
        if (self.listObjektArt_2.currentItem()) is None:
            return
        a = self.ui.listObjektTyp.currentRow()
        item = self.listObjektArt_2.currentItem().text()
        i = getListfilterIndex(self.objektArtList, 0, item, "genau")
        string = self.objektArtList[i][1]
        delstring = self.listObjektTyp.currentItem().text() + "|"
        string = string.replace(delstring, "")
        # QgsMessageLog.logMessage(str(string), 'T2G Archäologie', Qgis.Info)
        # QgsMessageLog.logMessage(str(delstring), 'T2G Archäologie', Qgis.Info)
        self.objektArtList[i][1] = string
        self.csvWrite()
        self.setup()
        self.listObjektTyp.setCurrentRow(a)

    def objektTypNeu(self):
        text, okPressed = QInputDialog.getText(self, "Neuer Objekttyp", "Objekttyp:", QLineEdit.Normal, "")
        if okPressed and text != "":
            if getListfilterIndex(self.objektTypList, 0, text, "genau") is None:
                row = [text, "", "", "1"]
                items = ["Punkt", "Linie", "Punkt/Linie"]
                item, okPressed = QInputDialog.getItem(self, "Geometrie", "Layertyp:", items, 0, False)
                if okPressed and item:
                    row.append(item)
                    self.objektTypList.append(row)
                    self.listSort()
                    self.csvWrite()
                    self.setup()
            else:
                QMessageBox.critical(None, "Meldung", "In Liste vorhanden! Abbruch!", QMessageBox.Abort)

    def objektTypLayerArtEdit(self, index):
        if (self.listObjektTyp.currentItem()) is None:
            return
        items = ["Punkt", "Linie", "Punkt/Linie"]
        item, okPressed = QInputDialog.getItem(self, "Objektart", "Objektart:", items, 0, False)
        if okPressed and item:
            i = self.listObjektTyp.currentRow()
            self.objektTypList[i][4] = item
            # QgsMessageLog.logMessage(str(item), 'T2G Archäologie', Qgis.Info)
            self.csvWrite()
            self.setup()
            self.listObjektTyp.setCurrentRow(i)
        pass

    def objektArtNeu(self):
        a = self.listObjektTyp.currentRow()
        text, okPressed = QInputDialog.getText(self, "Neue Objektart", "Objektart:", QLineEdit.Normal, "")
        if okPressed and text != "":
            if getListfilterIndex(self.objektArtList, 0, text, "genau") is None:

                row = [text, "", "", "1"]
                self.objektArtList.append(row)

                self.listSort()
                self.csvWrite()
                self.setup()

                i = getListfilterIndex(self.objektArtList, 0, text, "genau")
                wert = self.objektTypList[a][0]
                self.objektArtList[i][1] = (self.objektArtList[i][1])[:-1] + "|" + wert + "|"
                self.csvWrite()
                self.setup()
                self.listObjektTyp.setCurrentRow(a)

            else:
                QMessageBox.critical(None, "Meldung", "In Liste vorhanden! Abbruch!", QMessageBox.Abort)
