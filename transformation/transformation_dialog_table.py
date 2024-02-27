# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QComboBox
from qgis.PyQt.QtCore import Qt

## @brief With the TransformationDialogTable class a table based on QTableWidget is realized
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-10-19

class TransformationDialogTable(QTableWidget):

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

        super(TransformationDialogTable, self).__init__()

        self.dialogInstance = dialogInstance

        self.colHeaders = ['UUID', 'PTNR', 'ID', 'Quelle X', 'Quelle Y', 'Quelle Z', 'Ziel X', 'Ziel Y', 'Ziel Z', 'Error XY', 'Error Z', 'Punkt verwenden']

        self.setObjectName("gcpTable")
        self.setRowCount(0)
        self.setColumnCount(12)
        self.setHorizontalHeaderLabels(self.colHeaders)
        self.setStyleSheet("QTableWidget::item { padding: 4px } QTableWidget::item:selected{ background-color: rgba(255, 255, 255, 100%) }");

        #click in Tabellenzelle
        self.clicked.connect(self.gcpTableCellClick)
        #click auf row
        self.verticalHeader().sectionClicked.connect(self.gcpTableRowClick)

    ## \brief Get data of the GCP-Tabelle
    #
    # @returns GcpData is a dictionary of the table data e.G.:
    #  \code{.py}
    #    [{
    #    	'uuid': '{c81ce552-9466-417a-a1fd-2305f81c3051}',
    #    	'ptnr': 'ALT_01',
    #    	'id': 0,
    #    	'target_x_ptnr': 'ALT_01',
    #    	'target_y_ptnr': 'ALT_01',
    #    	'target_z_ptnr': 'ALT_01',
    #    	'error_xy': 404.735,
    #    	'error_z': -0.092,
    #    	'usage': '3D',
    #    	'sourcePoints': [451.157, 956.485, 102.518],
    #    	'targetPoints': [5460004.38, 5700036.8, 50.0]
    #    }, {
    #    	'uuid': '{0689dab2-f5fa-4db7-a3ff-6c5e343054d9}',
    #    	'ptnr': 'ALT_12',
    #    	'id': 1,
    #    	'target_x_ptnr': 'ALT_12',
    #    	'target_y_ptnr': 'ALT_12',
    #    	'target_z_ptnr': 'ALT_12',
    #    	'error_xy': 404.735,
    #    	'error_z': 0.092,
    #    	'usage': '3D',
    #    	'sourcePoints': [483.943, 1002.806, 102.334],
    #    	'targetPoints': [5460046.429, 5700901.998, 80.0]
    #    }]
    #  \endcode
    #


    def getGcpTableData(self):

        GcpData = []

        rowCount = self.rowCount()
        columnCount = self.columnCount()

        for i in range(0, rowCount):
            pointObj = {}
            pointArraySource = [0] * 3
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
                if head == 'Quelle Y':
                    pointArraySource [1] = float(self.item(i, j).text())
                if head == 'Quelle Z':
                    pointArraySource [2] = float(self.item(i, j).text())

                if head == 'Ziel X':
                    pointArrayTarget [0] = float(self.cellWidget(i, j).currentText().split(' | ')[1])
                    pointObj['target_x_ptnr'] = str(self.cellWidget(i, j).currentText().split(' | ')[0])
                if head == 'Ziel Y':
                    pointArrayTarget [1] = float(self.cellWidget(i, j).currentText().split(' | ')[1])
                    pointObj['target_y_ptnr'] = str(self.cellWidget(i, j).currentText().split(' | ')[0])
                if head == 'Ziel Z':
                    pointArrayTarget [2] = float(self.cellWidget(i, j).currentText().split(' | ')[1])
                    pointObj['target_z_ptnr'] = str(self.cellWidget(i, j).currentText().split(' | ')[0])
                if head == 'Error XY':
                    pointObj['error_xy'] = float(self.item(i, j).text())
                if head == 'Error Z':
                    pointObj['error_z'] = float(self.item(i, j).text())
                if head == 'Punkt verwenden':
                    pointObj['usage'] = self.cellWidget(i, j).currentText()

            pointObj['sourcePoints'] = pointArraySource
            pointObj['targetPoints'] = pointArrayTarget
            GcpData.append(pointObj)

        return GcpData

    ## \brief Residuals columns in table will be updated
    #
    # \param GcpDataResiduals
    # @returns
    def updateGcpTableResiduals(self, GcpDataResiduals):

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

                for pointObj in GcpDataResiduals:
                    if pointObj['uuid'] == tblPointUuid:
                        if head == 'Error XY':
                            self.item(i, j).setText(str(round(pointObj['errorXY'], 3)))
                        if head == 'Error Z':
                            self.item(i, j).setText(str(round(pointObj['errorZ'], 3)))
                        break
        self.show()


    ## \brief Update der GCP-Tabelle
    #
    # \param gcpSource
    # \param gcpTarget
    # @returns
    def updateGcpTable(self, gcpSource, gcpTarget):

        #colHeaders = ['ID', 'Quelle X', 'Quelle Y', 'Quelle Z', 'Ziel X', 'Ziel Y', 'Ziel Z', 'Error XY', 'Error Z', 'Punkt verwenden']
        targetX = []
        targetY = []
        targetZ = []

        gcpTableHeader = self.horizontalHeader()

        usage = ['3D', '2D', 'Z', 'nein']
        for point in gcpTarget['points']:

            if len(point['ptnr']) > 0:
                targetX.append(point['ptnr']+' | '+str(round(point['x'], 3)))
                targetY.append(point['ptnr']+' | '+str(round(point['y'], 3)))
                targetZ.append(point['ptnr']+' | '+str(round(point['z'], 3)))
            else:
                targetX.append(str(round(point['x'], 3)))
                targetY.append(str(round(point['y'], 3)))
                targetZ.append(str(round(point['z'], 3)))

        for pointObj in gcpSource:

            rowPosition = self.rowCount()
            self.insertRow(rowPosition)
            # UUID
            self.setItem(rowPosition, 0, QTableWidgetItem(pointObj['uuid']))
            # PTNR
            ptnrItem = QTableWidgetItem(str(pointObj['ptnr']))
            ptnrItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 1, ptnrItem)
            gcpTableHeader.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            # ID
            idItem = QTableWidgetItem(str(pointObj['id']))
            idItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 2, idItem)
            gcpTableHeader.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            # Quelle X
            qxItem = QTableWidgetItem(str(round(pointObj['x'], 3)))
            qxItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 3, qxItem)
            gcpTableHeader.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            # Quelle Y
            qyItem = QTableWidgetItem(str(round(pointObj['y'], 3)))
            qyItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 4, qyItem)
            gcpTableHeader.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            # Quelle Z
            qzItem = QTableWidgetItem(str(round(pointObj['z'], 3)))
            qzItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 5, qzItem)
            gcpTableHeader.setSectionResizeMode(5, QHeaderView.ResizeToContents)

            # Ziel X
            targetComboX = QComboBox()
            targetComboX.setObjectName("cb_"+str(pointObj['id'])+"_x")
            targetComboX.addItems(targetX)
            for point in gcpTarget['points']:
                if pointObj['ptnr'] == point['ptnr']:
                    idx = targetComboX.findText(point['ptnr']+' | '+str(round(point['x'], 3)))
                    if idx >= 0:
                        targetComboX.setCurrentIndex(idx)
            targetComboX.wheelEvent = lambda event: None
            targetComboX.currentTextChanged.connect(self.onComboboxChanged)
            self.setCellWidget(rowPosition, 6, targetComboX)
            gcpTableHeader.setSectionResizeMode(6, QHeaderView.Stretch)

            # Ziel Y
            targetComboY = QComboBox()
            targetComboY.setObjectName("cb_"+str(pointObj['id'])+"_y")
            targetComboY.addItems(targetY)
            for point in gcpTarget['points']:
                if pointObj['ptnr'] == point['ptnr']:
                    idx = targetComboY.findText(point['ptnr']+' | '+str(round(point['y'], 3)))
                    if idx >= 0:
                        targetComboY.setCurrentIndex(idx)
            targetComboY.wheelEvent = lambda event: None
            targetComboY.currentTextChanged.connect(self.onComboboxChanged)
            self.setCellWidget(rowPosition, 7, targetComboY)
            gcpTableHeader.setSectionResizeMode(7, QHeaderView.Stretch)

            # Ziel Z
            targetComboZ = QComboBox()
            targetComboZ.setObjectName("cb_"+str(pointObj['id'])+"_z")
            targetComboZ.addItems(targetZ)
            for point in gcpTarget['points']:
                if pointObj['ptnr'] == point['ptnr']:
                    idx = targetComboZ.findText(point['ptnr']+' | '+str(round(point['z'], 3)))
                    if idx >= 0:
                        targetComboZ.setCurrentIndex(idx)
            targetComboZ.wheelEvent = lambda event: None
            targetComboZ.currentTextChanged.connect(self.onComboboxChanged)
            self.setCellWidget(rowPosition, 8, targetComboZ)
            gcpTableHeader.setSectionResizeMode(8, QHeaderView.Stretch)

            #Error XY
            errorXyItem = QTableWidgetItem(str(-99999))
            errorXyItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 9, errorXyItem)
            gcpTableHeader.setSectionResizeMode(9, QHeaderView.ResizeToContents)
            #Error Z
            errorZItem = QTableWidgetItem(str(-99999))
            errorZItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 10, errorZItem)
            gcpTableHeader.setSectionResizeMode(10, QHeaderView.ResizeToContents)

            # Punkt verwenden
            usageCombo = QComboBox()
            usageCombo.setObjectName("cb_"+str(pointObj['id'])+"_usage")
            usageCombo.addItems(usage)
            idx = usageCombo.findText('nein')
            if idx >= 0:
                usageCombo.setCurrentIndex(idx)
            for point in gcpTarget['points']:
                if pointObj['ptnr'] == point['ptnr']:
                    idx = usageCombo.findText('3D')
                    if idx >= 0:
                        usageCombo.setCurrentIndex(idx)
            usageCombo.wheelEvent = lambda event: None
            usageCombo.currentTextChanged.connect(self.onComboboxChanged)
            self.setCellWidget(rowPosition, 11, usageCombo)
            gcpTableHeader.setSectionResizeMode(11, QHeaderView.Stretch)

        #hide column with ugly uuid
        self.setColumnHidden(0, True)

    ## \brief Table will be updated with respect to the loaded import textfile
    #
    # \param loadedGCPData
    # \param loadedTargetGcp
    # @returns

    def updateGcpTableFromImport(self, loadedGCPData, loadedTargetGcp):

        self.hide()
        self.cleanGcpTable()

        targetX = []
        targetY = []
        targetZ = []

        gcpTableHeader = self.horizontalHeader()

        usage = ['3D', '2D', 'Z', 'nein']
        for point in loadedTargetGcp:

            targetX.append(point['ptnr']+' | '+str(round(point['x'], 3)))
            targetY.append(point['ptnr']+' | '+str(round(point['y'], 3)))
            targetZ.append(point['ptnr']+' | '+str(round(point['z'], 3)))


        for pointObj in loadedGCPData:

            rowPosition = self.rowCount()
            self.insertRow(rowPosition)
            self.setItem(rowPosition, 0, QTableWidgetItem(pointObj['uuid'])) # uuid

            # PTNR
            ptnrItem = QTableWidgetItem(str(pointObj['ptnr']))
            ptnrItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 1, ptnrItem)
            gcpTableHeader.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            # ID
            idItem = QTableWidgetItem(str(pointObj['id']))
            idItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 2, idItem)
            gcpTableHeader.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            # Quelle X
            qxItem = QTableWidgetItem(str(round(pointObj['sourcePoints'][0], 3)))
            qxItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 3, qxItem)
            gcpTableHeader.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            # Quelle Y
            qyItem = QTableWidgetItem(str(round(pointObj['sourcePoints'][1], 3)))
            qyItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 4, qyItem)
            gcpTableHeader.setSectionResizeMode(4, QHeaderView.ResizeToContents)
            # Quelle Z
            qzItem = QTableWidgetItem(str(round(pointObj['sourcePoints'][2], 3)))
            qzItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 5, qzItem)
            gcpTableHeader.setSectionResizeMode(5, QHeaderView.ResizeToContents)

            # Ziel X
            targetComboX = QComboBox()
            targetComboX.setObjectName("cb_"+str(pointObj['id'])+"_x")
            targetComboX.addItems(targetX)
            idx = targetComboX.findText(pointObj['target_x_ptnr']+' | '+str(round(pointObj['targetPoints'][0], 3)))
            if idx >= 0:
                targetComboX.setCurrentIndex(idx)

            targetComboX.wheelEvent = lambda event: None
            targetComboX.currentTextChanged.connect(self.onComboboxChanged)
            self.setCellWidget(rowPosition, 6, targetComboX)
            gcpTableHeader.setSectionResizeMode(6, QHeaderView.Stretch)

            # Ziel Y
            targetComboY = QComboBox()
            targetComboY.setObjectName("cb_"+str(pointObj['id'])+"_y")
            targetComboY.addItems(targetY)
            idx = targetComboY.findText(pointObj['target_y_ptnr']+' | '+str(round(pointObj['targetPoints'][1], 3)))
            if idx >= 0:
                targetComboY.setCurrentIndex(idx)
            targetComboY.wheelEvent = lambda event: None
            targetComboY.currentTextChanged.connect(self.onComboboxChanged)
            self.setCellWidget(rowPosition, 7, targetComboY)
            gcpTableHeader.setSectionResizeMode(7, QHeaderView.Stretch)

            # Ziel Z
            targetComboZ = QComboBox()
            targetComboZ.setObjectName("cb_"+str(pointObj['id'])+"_z")
            targetComboZ.addItems(targetZ)
            idx = targetComboZ.findText(pointObj['target_z_ptnr']+' | '+str(round(pointObj['targetPoints'][2], 3)))
            if idx >= 0:
                targetComboZ.setCurrentIndex(idx)
            targetComboZ.wheelEvent = lambda event: None
            targetComboZ.currentTextChanged.connect(self.onComboboxChanged)
            self.setCellWidget(rowPosition, 8, targetComboZ)
            gcpTableHeader.setSectionResizeMode(8, QHeaderView.Stretch)

            #Error XY
            errorXyItem = QTableWidgetItem(str(round(pointObj['error_xy'], 3)))
            errorXyItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 9, errorXyItem)
            gcpTableHeader.setSectionResizeMode(9, QHeaderView.ResizeToContents)
            #Error Z
            errorZItem = QTableWidgetItem(str(round(pointObj['error_z'], 3)))
            errorZItem.setFlags(Qt.ItemIsEnabled)
            self.setItem(rowPosition, 10, errorZItem)
            gcpTableHeader.setSectionResizeMode(10, QHeaderView.ResizeToContents)

            # Punkt verwenden
            usageCombo = QComboBox()
            usageCombo.setObjectName("cb_"+str(pointObj['id'])+"_usage")
            usageCombo.addItems(usage)
            idx = usageCombo.findText(pointObj['usage'])
            if idx >= 0:
                usageCombo.setCurrentIndex(idx)
            usageCombo.wheelEvent = lambda event: None
            usageCombo.currentTextChanged.connect(self.onComboboxChanged)
            self.setCellWidget(rowPosition, 11, usageCombo)
            gcpTableHeader.setSectionResizeMode(11, QHeaderView.Stretch)

        #hide column with ugly uuid
        self.setColumnHidden(0, True)
        self.show()

        self.dialogInstance.estimateParameters()


    ## \brief Remove all cells in table
    #
    # \param
    # @returns

    def cleanGcpTable(self):

        #gcpTable
        rowTotal = self.rowCount()
        for row in range(rowTotal,-1, -1):
            self.removeRow(row)

    ## \brief If a combobox in the table is changed a new calculation of the transformation parameters is executed
    #
    # That happends in the parent dialog instance TransformationGui.estimateParameters()
    #
    def onComboboxChanged(self):

        self.dialogInstance.estimateParameters()

    ## \brief If a cell in the table is clicked the corresponding uuid value is searched to used in highlight sourcelayer feature
    #
    # the Function TransformationDialogCanvas.highlightSourceLayer(uuidValue) is called
    #
    def gcpTableCellClick(self):

        index=(self.selectionModel().currentIndex())
        uuidValue=index.sibling(index.row(),0).data()

        self.dialogInstance.canvasTransform.highlightSourceLayer(uuidValue)

    ## \brief If a row in the table is clicked the corresponding uuid value is searched to used in highlight sourcelayer feature
    #
    # the Function TransformationDialogCanvas.highlightSourceLayer(uuidValue) is called
    #
    # \param rowId - is the index of the row
    #
    def gcpTableRowClick(self, rowId):

        index=(self.selectionModel().currentIndex())
        uuidValue=index.sibling(rowId,0).data()

        self.dialogInstance.canvasTransform.highlightSourceLayer(uuidValue)
