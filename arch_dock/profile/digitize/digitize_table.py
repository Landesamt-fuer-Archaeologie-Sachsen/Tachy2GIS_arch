# -*- coding: utf-8 -*-

import logging

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon, QPalette, QColor
from qgis.PyQt.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QMessageBox
from qgis.core import QgsApplication

from ..publisher import Publisher
from ....icons import ICON_PATHS
from ....common.utils import null_to_text

LOGGER = logging.getLogger(__name__)

THESAURUS_FIELDS = ("obj_typ", "obj_art")


def representThesaurusValues(layer, dataObj):
    for fieldName in THESAURUS_FIELDS:
        fieldIdx = layer.fields().indexFromName(fieldName)
        if fieldName not in dataObj or fieldIdx == -1:
            continue
        setup = layer.editorWidgetSetup(fieldIdx)
        formatter = QgsApplication.fieldFormatterRegistry().fieldFormatter(setup.type())
        dataObj[fieldName] = formatter.representValue(layer, fieldIdx, setup.config(), None, dataObj[fieldName])


## @brief With the DigitizeTable class a table based on QTableWidget is realized
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2022-10-11


class DigitizeTable(QTableWidget):

    def __init__(self, dialogInstance):

        super(DigitizeTable, self).__init__()

        self.pup = Publisher()

        self.dialogInstance = dialogInstance

        self.colHeaders = [
            "UUID",
            "ID",
            "Objekttyp",
            "Objektart",
            "Befundnr.",
            "Probennr.",
            "Fundnr.",
            "Bemerkung",
            "Layer",
            "Bearbeiten",
            "Löschen",
        ]

        self.setObjectName("georefTable")
        self.setRowCount(0)
        self.setColumnCount(len(self.colHeaders))
        self.setHorizontalHeaderLabels(self.colHeaders)

        palette = self.palette()
        hightlight_brush = palette.brush(QPalette.ColorRole.Highlight)
        hightlight_brush.setColor(QColor("white"))
        palette.setBrush(QPalette.ColorRole.Highlight, hightlight_brush)

        palette.setColor(QPalette.ColorRole.HighlightedText, (QColor("black")))
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
            msgBox.setIcon(QMessageBox.Icon.Information)
            msgBox.setText("Wollen Sie das Objekt wirklich löschen? Es wird ebenfalls aus dem Eingabelayer entfernt!")
            msgBox.setWindowTitle("Löschen")
            msgBox.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

            returnValue = msgBox.exec()
            if returnValue == QMessageBox.StandardButton.Ok:
                self.removeRow(row)
                self.pup.publish("removeFeatureByUuid", button.obj_uuid)

    ## \brief Start edit dialog
    #
    # \param
    # @returns
    def editDialog(self):

        button = self.sender()
        self.pup.publish("editFeatureAttributes", button.obj_uuid)

    ## \brief Insert into table
    #
    # \param dataObj
    # @returns
    def insertFeature(self, dataObj):

        tableHeader = self.horizontalHeader()

        rowPosition = self.rowCount()
        self.insertRow(rowPosition)

        # UUID
        self.setItem(rowPosition, 0, QTableWidgetItem(str(dataObj["obj_uuid"])))
        self.setColumnHidden(0, True)

        # ID
        if "fid" in dataObj:
            idItem = QTableWidgetItem(null_to_text(dataObj["fid"]))
        else:
            idItem = QTableWidgetItem("NULL")

        idItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(rowPosition, 1, idItem)
        # Objekttyp
        if "obj_typ" in dataObj:
            typeItem = QTableWidgetItem(null_to_text(dataObj["obj_typ"]))
        else:
            typeItem = QTableWidgetItem("NULL")

        typeItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(rowPosition, 2, typeItem)
        tableHeader.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # Objektart
        if "obj_art" in dataObj:
            artItem = QTableWidgetItem(null_to_text(dataObj["obj_art"]))
        else:
            artItem = QTableWidgetItem("NULL")

        artItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(rowPosition, 3, artItem)
        tableHeader.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        # Befundnr.
        if "bef_nr" in dataObj:
            befItem = QTableWidgetItem(null_to_text(dataObj["bef_nr"]))
        else:
            befItem = QTableWidgetItem("NULL")

        befItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(rowPosition, 4, befItem)
        tableHeader.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        # Probennr.
        if "probe_nr" in dataObj:
            probItem = QTableWidgetItem(null_to_text(dataObj["probe_nr"]))
        else:
            probItem = QTableWidgetItem("NULL")

        probItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(rowPosition, 5, probItem)
        tableHeader.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        # Fundnr..
        if "fund_nr" in dataObj:
            fundItem = QTableWidgetItem(null_to_text(dataObj["fund_nr"]))
        else:
            fundItem = QTableWidgetItem("NULL")

        fundItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(rowPosition, 6, fundItem)
        tableHeader.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        # Bemerkung
        if "bemerkung" in dataObj:
            bemerkungItem = QTableWidgetItem(null_to_text(dataObj["bemerkung"]))
        else:
            bemerkungItem = QTableWidgetItem("NULL")

        bemerkungItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(rowPosition, 7, bemerkungItem)
        tableHeader.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        # Layer
        if "layer" in dataObj:
            layerItem = QTableWidgetItem(null_to_text(dataObj["layer"]))
        else:
            layerItem = QTableWidgetItem("NULL")

        layerItem.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.setItem(rowPosition, 8, layerItem)
        tableHeader.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)

        # Bearbeiten
        iconEdit = QIcon(QgsApplication.iconPath("mActionToggleEditing"))

        editBtn = QPushButton()
        editBtn.setIcon(iconEdit)
        editBtn.obj_uuid = dataObj["obj_uuid"]
        editBtn.setStyleSheet("margin-left:50%; margin-right:50%; bsckground-color:transparent; border:none;")
        self.setCellWidget(rowPosition, 9, editBtn)
        editBtn.clicked.connect(self.editDialog)
        tableHeader.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)

        # Löschen
        iconDel = QIcon(ICON_PATHS["trash_icon"])

        deleteBtn = QPushButton()
        deleteBtn.setIcon(iconDel)
        deleteBtn.obj_uuid = dataObj["obj_uuid"]
        deleteBtn.setStyleSheet("margin-left:50%; margin-right:50%; bsckground-color:transparent; border:none;")
        self.setCellWidget(rowPosition, 10, deleteBtn)
        deleteBtn.clicked.connect(self.showDialog)
        tableHeader.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)

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

                if head == "UUID":
                    tblUuid = self.item(i, j).text()

            # in Zelle der Tabelle eintragen
            for j in range(0, columnCount):
                head = self.horizontalHeaderItem(j).text()

                if dataObj["obj_uuid"] == tblUuid:

                    if head == "ID" and "fid" in dataObj:
                        LOGGER.debug(f"dataObj: {dataObj}")
                        self.item(i, j).setText(null_to_text(dataObj["fid"]))

                    if head == "Objekttyp" and "obj_typ" in dataObj:
                        self.item(i, j).setText(null_to_text(dataObj["obj_typ"]))

                    if head == "Objektart" and "obj_art" in dataObj:
                        self.item(i, j).setText(null_to_text(dataObj["obj_art"]))

                    if head == "Befundnr." and "bef_nr" in dataObj:
                        self.item(i, j).setText(null_to_text(dataObj["bef_nr"]))

                    if head == "Probennr." and "probe_nr" in dataObj:
                        self.item(i, j).setText(null_to_text(dataObj["probe_nr"]))

                    if head == "Fundnr." and "fund_nr" in dataObj:
                        self.item(i, j).setText(null_to_text(dataObj["fund_nr"]))

                    if head == "Bemerkung" and "bemerkung" in dataObj:
                        self.item(i, j).setText(null_to_text(dataObj["bemerkung"]))

        self.show()
