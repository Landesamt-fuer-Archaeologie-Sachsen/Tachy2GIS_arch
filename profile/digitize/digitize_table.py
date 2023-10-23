# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox
from qgis.PyQt.QtGui import QIcon, QPalette, QColor
from qgis.PyQt.QtCore import Qt

from ..publisher import Publisher
## @brief With the DigitizeTable class a table based on QTableWidget is realized
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2022-10-11

class DigitizeTable(QTableWidget):

    def __init__(self, dialogInstance):

        super(DigitizeTable, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')

        self.pup = Publisher()

        self.dialogInstance = dialogInstance

        self.colHeaders = ['UUID', 'ID', 'Objekttyp', 'Objektart', 'Befundnr.', 'Probennr.', 'Fundnr.', 'Bemerkung', 'Layer', 'Bearbeiten', 'Löschen']

        self.setObjectName("georefTable")
        self.setRowCount(0)
        self.setColumnCount(len(self.colHeaders))
        self.setHorizontalHeaderLabels(self.colHeaders)

        palette = self.palette()
        hightlight_brush = palette.brush(QPalette.Highlight)
        hightlight_brush.setColor(QColor('white'))
        palette.setBrush(QPalette.Highlight, hightlight_brush)

        palette.setColor(QPalette.HighlightedText, (QColor('black')))
        self.setPalette(palette)

        self.featForm = None

    ## \brief Dialog with question: Delete object?
    #
    # \param 
    # @returns
    def showDialog(self):

        button = self.sender()
        if button:
            row = self.indexAt(button.pos()).row()

            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("Wollen Sie das Objekt wirklich löschen? Es wird ebenfalls aus dem Eingabelayer entfernt!")
            msgBox.setWindowTitle("Löschen")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

            returnValue = msgBox.exec()
            if returnValue == QMessageBox.Ok:
                self.removeRow(row)
                self.pup.publish('removeFeatureByUuid', button.uuid)

    ## \brief Start edit dialog
    #
    # \param 
    # @returns
    def editDialog(self):

        button = self.sender()
        self.pup.publish('editFeatureAttributes', button.uuid)

    ## \brief Insert into table
    #
    # \param dataObj
    # @returns
    def insertFeature(self, dataObj):

        tableHeader = self.horizontalHeader()

        rowPosition = self.rowCount()
        self.insertRow(rowPosition)

        # UUID
        self.setItem(rowPosition, 0, QTableWidgetItem(str(dataObj['obj_uuid'])))
        self.setColumnHidden(0, True)

        # ID
        if "id" in dataObj:
            idItem = QTableWidgetItem(str(dataObj['id']))
        else:
            idItem = QTableWidgetItem('NULL')

        idItem.setFlags(Qt.ItemIsEnabled)
        self.setItem(rowPosition, 1, idItem)
        # Objekttyp
        if "obj_typ" in dataObj:
            typeItem = QTableWidgetItem(str(dataObj['obj_typ']))
        else:
            typeItem = QTableWidgetItem('NULL')

        typeItem.setFlags(Qt.ItemIsEnabled)
        self.setItem(rowPosition, 2, typeItem)
        tableHeader.setSectionResizeMode(2, QHeaderView.Stretch)
        # Objektart
        if "obj_art" in dataObj:
            artItem = QTableWidgetItem(str(dataObj['obj_art']))
        else:
            artItem = QTableWidgetItem('NULL')

        artItem.setFlags(Qt.ItemIsEnabled)
        self.setItem(rowPosition, 3, artItem)
        tableHeader.setSectionResizeMode(3, QHeaderView.Stretch)
        # Befundnr.
        if "bef_nr" in dataObj:
            befItem = QTableWidgetItem(str(dataObj['bef_nr']))
        else:
            befItem = QTableWidgetItem('NULL')

        befItem.setFlags(Qt.ItemIsEnabled)
        self.setItem(rowPosition, 4, befItem)
        tableHeader.setSectionResizeMode(4, QHeaderView.Stretch)
        # Probennr.
        if "prob_nr" in dataObj:
            probItem = QTableWidgetItem(str(dataObj['prob_nr']))
        else:
            probItem = QTableWidgetItem('NULL')

        probItem.setFlags(Qt.ItemIsEnabled)
        self.setItem(rowPosition, 5, probItem)
        tableHeader.setSectionResizeMode(5, QHeaderView.Stretch)
        # Fundnr..
        if "fund_nr" in dataObj:
            fundItem = QTableWidgetItem(str(dataObj['fund_nr']))
        else:
            fundItem = QTableWidgetItem('NULL')

        fundItem.setFlags(Qt.ItemIsEnabled)
        self.setItem(rowPosition, 6, fundItem)
        tableHeader.setSectionResizeMode(6, QHeaderView.Stretch)
        # Bemerkung
        if "bemerkung" in dataObj:
            bemerkungItem = QTableWidgetItem(str(dataObj['bemerkung']))
        else:
            bemerkungItem = QTableWidgetItem('NULL')

        bemerkungItem.setFlags(Qt.ItemIsEnabled)
        self.setItem(rowPosition, 7, bemerkungItem)            
        tableHeader.setSectionResizeMode(7, QHeaderView.Stretch)

        # Layer
        if "layer" in dataObj:
            layerItem = QTableWidgetItem(str(dataObj['layer']))
        else:
            layerItem = QTableWidgetItem('NULL')

        layerItem.setFlags(Qt.ItemIsEnabled)
        self.setItem(rowPosition, 8, layerItem)   
        tableHeader.setSectionResizeMode(8, QHeaderView.Stretch)

        #Bearbeiten
        iconEdit = QIcon(os.path.join(self.iconpath, 'mActionToggleEditing.png'))

        editBtn = QPushButton()
        editBtn.setIcon(iconEdit)
        editBtn.uuid = dataObj['uuid']
        editBtn.setStyleSheet("margin-left:50%; margin-right:50%; bsckground-color:transparent; border:none;");
        self.setCellWidget(rowPosition, 9, editBtn)
        editBtn.clicked.connect(self.editDialog)
        tableHeader.setSectionResizeMode(9, QHeaderView.ResizeToContents)

        #Löschen
        iconDel = QIcon(os.path.join(self.iconpath, 'trash_icon.png'))

        deleteBtn = QPushButton()
        deleteBtn.setIcon(iconDel)
        deleteBtn.uuid = dataObj['uuid']
        deleteBtn.setStyleSheet("margin-left:50%; margin-right:50%; bsckground-color:transparent; border:none;");
        self.setCellWidget(rowPosition, 10, deleteBtn)
        deleteBtn.clicked.connect(self.showDialog)
        tableHeader.setSectionResizeMode(10, QHeaderView.ResizeToContents)

    ## \brief Update feature attributes in table
    #
    # \param dataObj
    # @returns

    def updateFeature(self, dataObj):

        self.hide()

        rowCount = self.rowCount()
        columnCount = self.columnCount()

        for i in range(0, rowCount):

            tblUuid = None

            for j in range(0, columnCount):

                head = self.horizontalHeaderItem(j).text()

                if head == 'UUID':
                    tblUuid = self.item(i, j).text()

            #in Zelle der Tabelle eintragen
            for j in range(0, columnCount):
                head = self.horizontalHeaderItem(j).text()

                if dataObj['uuid'] == tblUuid:

                    if head == 'Objekttyp':
                        if "obj_typ" in dataObj:
                            self.item(i, j).setText(str(dataObj['obj_typ']))

                    if head == 'Objektart':
                        if "obj_art" in dataObj:
                            self.item(i, j).setText(str(dataObj['obj_art']))

                    if head == 'Befundnr.':
                        if "bef_nr" in dataObj:
                            self.item(i, j).setText(str(dataObj['bef_nr']))

                    if head == 'Probennr.':
                        if "prob_nr" in dataObj:
                            self.item(i, j).setText(str(dataObj['prob_nr']))

                    if head == 'Fundnr.':
                        if "fund_nr" in dataObj:
                            self.item(i, j).setText(str(dataObj['fund_nr']))

                    if head == 'Bemerkung':
                        if "bemerkung" in dataObj:
                            self.item(i, j).setText(str(dataObj['bemerkung']))

        self.show()

