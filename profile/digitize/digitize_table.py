# -*- coding: utf-8 -*-
import os
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QPushButton, QMessageBox
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import Qt

from ..publisher import Publisher
## @brief With the TransformationDialogTable class a table based on QTableWidget is realized
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-10-19

class DigitizeTable(QTableWidget):

    ## The constructor.
    # Defines attributes for the table
    # - Tableheaders
    # - The number of columns
    #
    #  Event connections
    # - click in cell of the table
    # - click on row
    #
    #  @param dialogInstance pointer to the dialogInstance

    def __init__(self, dialogInstance):

        super(DigitizeTable, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), '..', 'Icons')

        self.pup = Publisher()

        self.dialogInstance = dialogInstance

        self.colHeaders = ['ID', 'Objekttyp', 'Objektart', 'Zeit', 'Material', 'Bemerkung', 'Layer', 'Löschen']

        self.setObjectName("georefTable")
        self.setRowCount(0)
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(self.colHeaders)

        palette = self.palette()
        hightlight_brush = palette.brush(QPalette.Highlight)
        hightlight_brush.setColor(QColor('white'))
        palette.setBrush(QPalette.Highlight, hightlight_brush)

        palette.setColor(QPalette.HighlightedText, (QColor('black')))
        self.setPalette(palette)
        #self.setStyleSheet("QTableWidget::item { padding: 4px } QTableWidget::item:selected{ background-color: rgba(255, 255, 255, 100%) }");

        #click in Tabellenzelle
        #self.clicked.connect(self.georefTableCellClick)
        #click auf row
        #self.verticalHeader().sectionClicked.connect(self.georefTableRowClick)

    def showDialog(self):

        print('removeFeature')
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

    ## \brief Update der Tabelle
    #
    # \param dataObj
    # @returns
    def insertFeature(self, dataObj):


        #self.colHeaders = ['ID', 'Objekttyp', 'Objektart', 'Zeit', 'Material', 'Bemerkung', 'Layer', 'Löschen']

        tableHeader = self.horizontalHeader()

        #for item in dataObj:

        rowPosition = self.rowCount()
        self.insertRow(rowPosition)
        # ID
        if "id" in dataObj:
            self.setItem(rowPosition, 0, QTableWidgetItem(str(dataObj['id'])))
        else:
            self.setItem(rowPosition, 0, QTableWidgetItem('NULL'))
        # Objekttyp
        if "obj_type" in dataObj:
            self.setItem(rowPosition, 1, QTableWidgetItem(str(dataObj['obj_type'])))
        else:
            self.setItem(rowPosition, 1, QTableWidgetItem('NULL'))
        tableHeader.setSectionResizeMode(1, QHeaderView.Stretch)
        # Objektart
        if "obj_art" in dataObj:
            self.setItem(rowPosition, 2, QTableWidgetItem(str(dataObj['obj_art'])))
        else:
            self.setItem(rowPosition, 2, QTableWidgetItem('NULL'))
        tableHeader.setSectionResizeMode(2, QHeaderView.Stretch)
        # Zeit
        if "zeit" in dataObj:
            self.setItem(rowPosition, 3, QTableWidgetItem(str(dataObj['zeit'])))
        else:
            self.setItem(rowPosition, 3, QTableWidgetItem('NULL'))
        tableHeader.setSectionResizeMode(3, QHeaderView.Stretch)
        # Material
        if "material" in dataObj:
            self.setItem(rowPosition, 4, QTableWidgetItem(str(dataObj['material'])))
        else:
            self.setItem(rowPosition, 4, QTableWidgetItem('NULL'))
        tableHeader.setSectionResizeMode(4, QHeaderView.Stretch)
        # Bemerkung
        if "bemerkung" in dataObj:
            self.setItem(rowPosition, 5, QTableWidgetItem(str(dataObj['bemerkung'])))
        else:
            self.setItem(rowPosition, 5, QTableWidgetItem('NULL'))
        tableHeader.setSectionResizeMode(5, QHeaderView.Stretch)

        # Bemerkung
        if "layer" in dataObj:
            self.setItem(rowPosition, 6, QTableWidgetItem(str(dataObj['layer'])))
        else:
            self.setItem(rowPosition, 6, QTableWidgetItem('NULL'))
        tableHeader.setSectionResizeMode(6, QHeaderView.Stretch)

        #Löschen
        iconDel = QIcon(os.path.join(self.iconpath, 'trash_icon.png'))

        deleteBtn = QPushButton()
        deleteBtn.setIcon(iconDel)
        deleteBtn.uuid = dataObj['uuid']
        deleteBtn.setStyleSheet("margin-left:50%; margin-right:50%; bsckground-color:transparent; border:none;");
        self.setCellWidget(rowPosition, 7, deleteBtn)
        deleteBtn.clicked.connect(self.showDialog)
        tableHeader.setSectionResizeMode(7, QHeaderView.ResizeToContents)
