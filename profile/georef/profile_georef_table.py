# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QRadioButton
from PyQt5.QtCore import Qt
import numpy as np

from ..publisher import Publisher
from .residuals import Residuals
## @brief With the TransformationDialogTable class a table based on QTableWidget is realized
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-10-19

class GeorefTable(QTableWidget):

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

    def __init__(self, dialogInstance, dataStoreGeoref):

        super(GeorefTable, self).__init__()

        self.pup = Publisher()

        self.dialogInstance = dialogInstance

        self.dataStoreGeoref = dataStoreGeoref

        #allows selection of image coordinates in canvasImage
        self.activePoint = ''

        self.viewDirection = None
        self.directionAAR = None
        self.targetGCP = None
        self.methodAAR = None
        self.profileNumber = None

        self.colHeaders = ['UUID', 'PTNR', 'ID', 'Quelle X', 'Quelle Z', 'Ziel X', 'Ziel Y', 'Ziel Z', 'Error', 'Punkt verwenden', 'Punkt setzen']

        self.setObjectName("georefTable")
        self.setRowCount(0)
        self.setColumnCount(11)
        self.setHorizontalHeaderLabels(self.colHeaders)
        self.setStyleSheet("QTableWidget::item { padding: 4px } QTableWidget::item:selected{ background-color: rgba(255, 255, 255, 100%) }");

        #click in Tabellenzelle
        self.clicked.connect(self.georefTableCellClick)
        #click auf row
        self.verticalHeader().sectionClicked.connect(self.georefTableRowClick)

        self.res = Residuals()


    def __getTableData(self):

        tableData = []

        rowCount = self.rowCount()
        columnCount = self.columnCount()

        for i in range(0, rowCount):
            pointObj = {}
            pointArraySource = [0] * 2
            pointArrayTarget = [0] * 3
            for j in range(0, columnCount):

                head = self.horizontalHeaderItem(j).text()
                if head == 'UUID':
                    pointObj['uuid'] = self.item(i, j).text()
                if head == 'PTNR':
                    pointObj['ptnr'] = self.item(i, j).text()
                if head == 'ID':
                    pointObj['id'] = int(self.item(i, j).text())
                if head == 'Quelle X':
                    pointArraySource [0] = float(self.item(i, j).text())
                if head == 'Quelle Z':
                    pointArraySource [1] = float(self.item(i, j).text())

                if head == 'Ziel X':
                    pointArrayTarget [0] = float(self.item(i, j).text())
                if head == 'Ziel Y':
                    pointArrayTarget [1] = float(self.item(i, j).text())
                if head == 'Ziel Z':
                    pointArrayTarget [2] = float(self.item(i, j).text())
                if head == 'Error':
                    pointObj['error'] = float(self.item(i, j).text())
                if head == 'Punkt verwenden':
                    pointObj['usage'] = self.cellWidget(i, j).isChecked()

            pointObj['sourcePoints'] = pointArraySource
            pointObj['targetPoints'] = pointArrayTarget
            tableData.append(pointObj)

        return tableData

    ## \brief Update der GCP-Tabelle
    #
    # \param gcpTarget
    # @returns
    def updateGeorefTable(self, gcpTarget, aarDirection):

        self.viewDirection = gcpTarget['viewDirection']
        self.profileNumber = gcpTarget['profileNumber']
        self.targetGCP = gcpTarget['targetGCP']['points']

        horizontal = gcpTarget['horizontal']

        self.directionAAR = aarDirection

        #if horizontal == True:
        #    self.directionAAR = 'horizontal'
        #else:
        #    self.directionAAR = 'original'

        #self.colHeaders = ['UUID', 'PTNR', 'ID', 'Quelle X', 'Quelle Z', 'Ziel X', 'Ziel Y', 'Ziel Z', 'Error', 'Punkt verwenden', 'Punkt setzen']
        targetX = []
        targetY = []
        targetZ = []

        georefTableHeader = self.horizontalHeader()

        for pointObj in gcpTarget['targetGCP']['points']:

            rowPosition = self.rowCount()
            self.insertRow(rowPosition)
            # UUID
            self.setItem(rowPosition, 0, QTableWidgetItem(pointObj['uuid']))
            # PTNR
            ptnrItem = QTableWidgetItem(str(pointObj['ptnr']))
            ptnrItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 1, ptnrItem)
            georefTableHeader.setSectionResizeMode(1, QHeaderView.Stretch)
            # ID
            idItem = QTableWidgetItem(str(pointObj['id']))
            idItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 2, idItem)
            georefTableHeader.setSectionResizeMode(2, QHeaderView.Stretch)
            # Quelle X
            qxItem = QTableWidgetItem(str(-99999))
            qxItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 3, qxItem)
            georefTableHeader.setSectionResizeMode(3, QHeaderView.Stretch)
            # Quelle Z
            qzItem = QTableWidgetItem(str(-99999))
            qzItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 4, qzItem)
            georefTableHeader.setSectionResizeMode(4, QHeaderView.Stretch)

            # Ziel X
            txItem = QTableWidgetItem(str(round(pointObj['x'], 3)))
            txItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 5, txItem)
            georefTableHeader.setSectionResizeMode(5, QHeaderView.Stretch)


            # Ziel Y
            tyItem = QTableWidgetItem(str(round(pointObj['y'], 3)))
            tyItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 6, tyItem)
            georefTableHeader.setSectionResizeMode(6, QHeaderView.Stretch)

            # Ziel Z
            tzItem = QTableWidgetItem(str(round(pointObj['z'], 3)))
            tzItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 7, tzItem)
            georefTableHeader.setSectionResizeMode(7, QHeaderView.Stretch)

            #Error XY
            errorXyItem = QTableWidgetItem(str(-99999))
            errorXyItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 8, errorXyItem)
            georefTableHeader.setSectionResizeMode(8, QHeaderView.Stretch)

            # Punkt verwenden
            usageCheck = QCheckBox()
            usageCheck.setChecked(True)
            usageCheck.setStyleSheet("margin-left:50%; margin-right:50%;");
            self.setCellWidget(rowPosition, 9, usageCheck)
            georefTableHeader.setSectionResizeMode(9, QHeaderView.ResizeToContents)

            usageCheck.stateChanged.connect(self.pointUsageChanged)

            # Punkt setzen
            setPointRadio = QRadioButton()
            setPointRadio.pointUUID = pointObj['uuid']
            #usageCheck.setChecked(True)
            setPointRadio.setStyleSheet("margin-left:50%; margin-right:50%;");
            self.setCellWidget(rowPosition, 10, setPointRadio)
            setPointRadio.toggled.connect(self.onActivePoint)
            georefTableHeader.setSectionResizeMode(10, QHeaderView.ResizeToContents)

        #hide column with ugly uuid
        self.setColumnHidden(0, True)

    ## \brief Remove all cells in table
    #
    # \param
    # @returns

    def cleanGeorefTable(self):

        #georefTable
        rowTotal = self.rowCount()
        for row in range(rowTotal,-1, -1):
            self.removeRow(row)

    ## \brief If radiobutton "Punkt setzen" in the table is checked, the activePoint ist set by UUID
    #
    #
    def onActivePoint(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            activeUUID = radioButton.pointUUID
            print("UUID is %s" % (activeUUID))
            self.setActivePoint(activeUUID)

            tableData = self.__getTableData()

            pointNr = ''
            for tblObj in tableData:    
                if tblObj['uuid'] == activeUUID:
                    pointNr = tblObj['ptnr']

            self.pup.publish('activatePoint', {'uuid': activeUUID, 'ptnr': pointNr})

    ## \brief The activePoint ist set by UUID
    #
    #
    def setActivePoint(self, pointUUID):
        self.activePoint = pointUUID


    ## \brief If a cell in the table is clicked the corresponding uuid value is searched to used in highlight sourcelayer feature
    #
    # the Function TransformationDialogCanvas.highlightSourceLayer(uuidValue) is called
    #
    def georefTableCellClick(self):

        index=(self.selectionModel().currentIndex())
        uuidValue=index.sibling(index.row(),0).data()

        self.dialogInstance.canvasGcp.highlightSourceLayer(uuidValue)

    ## \brief If a row in the table is clicked the corresponding uuid value is searched to used in highlight sourcelayer feature
    #
    # the Function TransformationDialogCanvas.highlightSourceLayer(uuidValue) is called
    #
    # \param rowId - is the index of the row
    #
    def georefTableRowClick(self, rowId):

        index=(self.selectionModel().currentIndex())
        uuidValue=index.sibling(rowId,0).data()

        self.dialogInstance.canvasGcp.highlightSourceLayer(uuidValue)

    def prepareData(self, tableData, aarDirection):
        """Prepare table data for transformation"""

        points = []
        for tblObj in tableData:
            points.append([
                tblObj['targetPoints'][0], tblObj['targetPoints'][1], tblObj['targetPoints'][2], self.viewDirection, self.profileNumber, int(tblObj['usage']), tblObj['uuid']
            ])

        print('self.directionAAR', aarDirection)
        metaInfos = {
        	'method': 'projected',
        	'direction': aarDirection 
        }

        return points, metaInfos



    ## \brief Update error values in the table
    #
    # \param
    #
    def updateErrorValues(self, linkObj):

        georefData = self.dataStoreGeoref.getGeorefData(self.directionAAR)

        gcpArray = []
        for georefObj in georefData:

            for targetObj in self.targetGCP:
                if targetObj['uuid'] == georefObj['uuid']:
                    gcpArray.append([georefObj['input_x'], georefObj['input_z'], targetObj['x'], targetObj['z'], targetObj['uuid']])

        self.hide()

        rowCount = self.rowCount()
        columnCount = self.columnCount()

        if len(georefData) > 4:

            V_X, V_Y, V_XY, V_XY_uuid, mo, mox, moy = self.res.projective_trans(np.array(gcpArray))

            #print('V_X', V_X)
            #print('V_Y', V_Y)
            #print('V_XY', V_XY)
            #print('V_XY_uuid', V_XY_uuid)
            #print('mo', mo)
            #print('mox', mox)
            #print('moy', moy)

            for i in range(0, rowCount):

                tblPointUuid = None

                for j in range(0, columnCount):

                    head = self.horizontalHeaderItem(j).text()

                    if head == 'UUID':
                        tblPointUuid = self.item(i, j).text()

                #in Zelle der Tabelle eintragen
                for j in range(0, columnCount):
                    head = self.horizontalHeaderItem(j).text()

                    if head == 'Error':
                        self.item(i, j).setText(str(-99999))
                        for errorObj in V_XY_uuid:
                            if errorObj['uuid'] == tblPointUuid:
                                self.item(i, j).setText(str(round(errorObj['v_xy'], 4)))
        else:
            for i in range(0, rowCount):
                #in Zelle der Tabelle eintragen
                for j in range(0, columnCount):
                    head = self.horizontalHeaderItem(j).text()

                    if head == 'Error':
                        self.item(i, j).setText(str(-99999))

        self.show()


    ## \brief Update image coordinates for a specific point (uuid)
    #
    # \param linkObj
    #
    def updateImageCoordinates(self, linkObj):

        self.hide()
        rowCount = self.rowCount()
        columnCount = self.columnCount()

        for i in range(0, rowCount):

            tblPointUuid = None

            for j in range(0, columnCount):

                head = self.horizontalHeaderItem(j).text()

                if head == 'UUID':
                    tblPointUuid = self.item(i, j).text()

            #in Zelle der Tabelle eintragen
            for j in range(0, columnCount):
                head = self.horizontalHeaderItem(j).text()
                if linkObj['uuid'] == tblPointUuid:

                    if head == 'Quelle X':
                        self.item(i, j).setText(str(round(linkObj['x'], 3)))
                    if head == 'Quelle Z':
                        self.item(i, j).setText(str(round(linkObj['z'], 3)))

        self.show()


    def pointUsageChanged(self):

        tableData = self.__getTableData()

        data = self.prepareData(tableData, 'horizontal')
        self.pup.publish('dataChanged', data)
        self.updateErrorValues(None)

        data = self.prepareData(tableData, 'original')
        self.pup.publish('dataChanged', data)

        data = self.prepareData(tableData, 'absolute height')
        self.pup.publish('dataChanged', data)
