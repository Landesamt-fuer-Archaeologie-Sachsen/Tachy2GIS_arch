# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox, QRadioButton
from PyQt5.QtCore import Qt

from .publisher import Publisher
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

    def __init__(self, dialogInstance):

        super(GeorefTable, self).__init__()

        self.pup = Publisher()

        self.dialogInstance = dialogInstance

        #allows selection of image coordinates in canvasImage
        self.activePoint = ''

        self.viewDirection = None
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


    def getTableData(self):

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
                    pointObj['usage'] = self.item(i, j)

            pointObj['sourcePoints'] = pointArraySource
            pointObj['targetPoints'] = pointArrayTarget
            tableData.append(pointObj)

        return tableData

    ## \brief Update der GCP-Tabelle
    #
    # \param gcpTarget
    # @returns
    def updateGeorefTable(self, gcpTarget):

        self.viewDirection = gcpTarget['viewDirection']
        self.profileNumber = gcpTarget['profileNumber']
        print('gcpTarget', gcpTarget)
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
            georefTableHeader.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            # ID
            idItem = QTableWidgetItem(str(pointObj['id']))
            idItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 2, idItem)
            georefTableHeader.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            # Quelle X
            qxItem = QTableWidgetItem(str(-99999))
            qxItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 3, qxItem)
            georefTableHeader.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            # Quelle Y
            #qyItem = QTableWidgetItem()
            #qyItem.setFlags(Qt.ItemIsEnabled)
            #self.setItem(rowPosition, 4, qyItem)
            #georefTableHeader.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            # Quelle Z
            qzItem = QTableWidgetItem(str(-99999))
            qzItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 4, qzItem)
            georefTableHeader.setSectionResizeMode(4, QHeaderView.ResizeToContents)

            # Ziel X
            txItem = QTableWidgetItem(str(round(pointObj['x'], 3)))
            txItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 5, txItem)
            georefTableHeader.setSectionResizeMode(5, QHeaderView.ResizeToContents)


            # Ziel Y
            tyItem = QTableWidgetItem(str(round(pointObj['y'], 3)))
            tyItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 6, tyItem)
            georefTableHeader.setSectionResizeMode(6, QHeaderView.ResizeToContents)

            # Ziel Z
            tzItem = QTableWidgetItem(str(round(pointObj['z'], 3)))
            tzItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 7, tzItem)
            georefTableHeader.setSectionResizeMode(7, QHeaderView.ResizeToContents)

            #Error XY
            errorXyItem = QTableWidgetItem(str(-99999))
            errorXyItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 8, errorXyItem)
            georefTableHeader.setSectionResizeMode(8, QHeaderView.ResizeToContents)
            #Error Z
            #errorZItem = QTableWidgetItem(str(-99999))
            #errorZItem.setFlags(Qt.ItemIsEnabled)
            #self.setItem(rowPosition, 10, errorZItem)
            #georefTableHeader.setSectionResizeMode(10, QHeaderView.ResizeToContents)

            # Punkt verwenden
            usageCheck = QCheckBox()
            usageCheck.setChecked(True)
            usageCheck.setStyleSheet("margin-left:50%; margin-right:50%;");
            self.setCellWidget(rowPosition, 9, usageCheck)
            georefTableHeader.setSectionResizeMode(9, QHeaderView.ResizeToContents)

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

            self.pup.publish('activatePoint', {'uuid': activeUUID})

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

    def prepareData(self, tableData):
        """Prepare table data for transformation"""

        points = []
        for tblObj in tableData:

            points.append([
                tblObj['targetPoints'][0], tblObj['targetPoints'][1], tblObj['targetPoints'][2], self.viewDirection, self.profileNumber, 1
            ])

        metaInfos = {
        	'method': 'projected',
        	'direction': 'original'
        }

        return points, metaInfos

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

        tableData = self.getTableData()

        print('tableData', tableData)

        data = self.prepareData(tableData)

        print('dataaaaaa', data)

        input_data = {
            'transformation' : {
                'method': 'projected',
                'direction': 'original'
            },
            'profiles' :
            [
                {
                    'profile_nr' : '65',
                    'view_direction' : 'E',
                    'points' : [

                         {
                            'point_nr' : 'AZB-15_1',
                            'x': 4577323.717,
                            'y': 5709834.986,
                            'z': 85.156,
                            'used_points': 1
                        },
                        {
                            'point_nr' : 'AZB-15_2',
                            'x': 4577324.677,
                            'y': 5709836.283,
                            'z': 85.161,
                            'used_points': 1
                        },
                        {
                            'point_nr' : 'AZB-15_3',
                            'x': 4577325.64,
                            'y': 5709837.479,
                            'z': 85.154,
                            'used_points': 1
                        },
                        {
                            'point_nr' : 'AZB-15_4',
                            'x': 4577325.762,
                            'y': 5709837.307,
                            'z': 84.157,
                            'used_points': 1
                        },
                        {
                            'point_nr' : 'AZB-15_5',
                            'x': 4577325.203,
                            'y': 5709836.573,
                            'z': 84.203,
                            'used_points': 1
                        },
                        {
                            'point_nr' : 'AZB-15_6',
                            'x': 4577324.658,
                            'y': 5709835.968,
                            'z': 84.276,
                            'used_points': 1
                        },
                        {
                            'point_nr' : 'AZB-15_7',
                            'x': 4577324.517,
                            'y': 5709835.918,
                            'z': 84.796,
                            'used_points': 1
                        },
                        {
                            'point_nr' : 'AZB-15_8',
                            'x': 4577323.818,
                            'y': 5709834.986,
                            'z': 84.836,
                            'used_points': 1
                        }

                    ]
                }
            ]
        }

        self.pup.publish('dataChanged', data)
