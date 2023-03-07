# -*- coding: utf-8 -*-
import os
import csv
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QMainWindow, QAction, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from qgis.gui import QgsMessageBar

from .transformation_dialog_table import TransformationDialogTable
from .transformation_dialog_parambar import TransformationDialogParambar
from .transformation_dialog_canvas import TransformationDialogCanvas
from .transformation_calculations import TransformationCalculations

## @brief With the TransformationDialog class a dialog window for the calculation of transformation parameters is realized
#
# The class inherits form QMainWindow
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2020-10-19

class TransformationDialog(QMainWindow):

    def __init__(self, t2GArchInstance):

        super(TransformationDialog, self).__init__()

        self.iconpath = os.path.join(os.path.dirname(__file__), 'Icons')

        self.t2GArchInstance = t2GArchInstance
        self.colNameGcpSource = t2GArchInstance.colNameGcpSource

        self.gcpTable = None
        self.canvasTransform = None
        self.transformationParamsBar = None

        self.zAngle = None
        self.translationX = None
        self.translationY = None
        self.translationZ = None
        self.globalError2D = None
        self.globalErrorZ = None
        self.GcpDataResiduals = None
        self.targetCrs = None
        self.gcpTarget = None

        self.rememberExportTxtFolder = '.'

        self.createMenu()
        self.createComponents()
        self.createLayout()
        self.createConnects()

    ## \brief Create different menus
    #
    #
    # creates the menuBar at upper part of the window and statusBar in the lower part
    #
    def createMenu(self):

        self.statusBar()

        self.statusBar().reformat()
        self.statusBar().setStyleSheet('background-color: #FFF8DC;')
        self.statusBar().setStyleSheet("QStatusBar::item {border: none;}")

        exitAct = QAction(QIcon(os.path.join(self.iconpath , 'Ok_grau.png')), 'Exit', self)

        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Anwendung schließen')
        exitAct.triggered.connect(self.close)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Datei')
        fileMenu.addAction(exitAct)

    ## \brief ECreates the components of the window
    #
    # - MessageBar to give hints
    # - Parameterbar to show the results of the transformation, instantiate class TransformationDialogParambar() as self.transformationParamsBar
    # - Canvas component for layer display, instantiate class TransformationDialogCanvas as self.canvasTransform
    # - Table with the GCPs, instantiate class TransformationDialogTable() as self.gcpTable
    # - Coordinates in statusBar
    # - instantiate class TransformationCalculations as self.paramCalc

    # @returns
    def createComponents(self):

        #messageBar
        self.messageBar = QgsMessageBar()

        #Canvas Element
        self.canvasTransform = TransformationDialogCanvas(self)

        #Actions
        self.createActions()

        #Toolbars
        self.createToolbars()

        #Coordinates in statusBar
        self.createStatusBar()

        #TransformationParamsBar
        self.transformationParamsBar = TransformationDialogParambar(self)

        #GcpTable
        self.gcpTable = TransformationDialogTable(self)

        #paramCalc
        self.paramCalc = TransformationCalculations(self)

    ## \brief Event connections
    #

    def createConnects(self):

        self.actionExport.triggered.connect(self.exportTxt)
        self.actionImport.triggered.connect(self.importTxt)
        self.takeParametersBtn.clicked.connect(self.takeTransformParams)

    ## \brief create actions
    #
    def createActions(self):

        #Export
        iconExport = QIcon(os.path.join(self.iconpath, 'mActionSaveGCPpointsAs.png'))
        self.actionExport = QAction(iconExport, "Export data", self)

        #Import
        iconImport = QIcon(os.path.join(self.iconpath, 'mActionLoadGCPpoints.png'))
        self.actionImport = QAction(iconImport, "Import data", self)

    ## \brief create toolbars
    #
    # - toolbarMap
    # - toolbarExchange
    def createToolbars(self):

        #Toolbar Kartennavigation
        self.toolbarMap = self.addToolBar("Kartennavigation")
        self.toolbarMap.addAction(self.canvasTransform.actionPan)
        self.toolbarMap.addAction(self.canvasTransform.actionZoomIn)
        self.toolbarMap.addAction(self.canvasTransform.actionZoomOut)
        self.toolbarMap.addAction(self.canvasTransform.actionExtent)

        #Toolbar Datenaustausch
        self.toolbarExchange = self.addToolBar("Datenaustausch")
        self.toolbarExchange.addAction(self.actionExport)
        self.toolbarExchange.addAction(self.actionImport)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbarExchange.addWidget(spacer)
        self.takeParametersBtn = QPushButton("Transformationsparameter übernehmen", self)
        self.toolbarExchange.addWidget(self.takeParametersBtn)

    ## \brief create coordinate line edit in statusBar
    #
    def createStatusBar(self):

        self.coordLabel = QLabel("Koordinate ")
        self.coordLineEdit = QLineEdit()
        self.coordLineEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.coordLineEdit.setReadOnly(True)
        self.coordLineEdit.setMinimumWidth(150);
        self.coordLineEdit.setAlignment(Qt.AlignCenter)
        self.statusBar().addPermanentWidget(self.coordLabel)
        self.statusBar().addPermanentWidget(self.coordLineEdit)

    ## \brief Creates the layout for the window and assigns the created components
    #

    def createLayout(self):

        widgetCentral = QWidget()

        grid = QVBoxLayout()
        grid.setContentsMargins(0,0,0,0)
        widgetCentral.setLayout(grid)
        self.setCentralWidget(widgetCentral)

        grid.addWidget(self.messageBar)
        grid.addWidget(self.transformationParamsBar)
        grid.addWidget(self.canvasTransform)
        grid.addWidget(self.gcpTable)

    ## \brief Starts the estimation of the transformation paramters
    #
    # - Read data from the gcpTable TransformationDialogTable.getGcpTableData()
    # - check the conditions for the transformation checkTransformationConditions()
    # - calculate transformation parameters TransformationCalculations.calcTransformationParams()
    # - update results in parambar TransformationDialogParambar.showTransformationParamsMessage()
    # - update the point residuals in the gcpTable TransformationDialogTable.updateGcpTableResiduals()

    def estimateParameters(self):

        GcpData = self.gcpTable.getGcpTableData()
        conditionsValid = self.checkTransformationConditions(GcpData)

        if conditionsValid == True:
            zAngle, translationX, translationY, globalError2D, translationZ, GcpDataResiduals, globalErrorZ = self.paramCalc.calcTransformationParams(GcpData)
            self.zAngle = zAngle
            self.translationX = translationX
            self.translationY = translationY
            self.translationZ = translationZ
            self.globalError2D = globalError2D
            self.globalErrorZ = globalErrorZ
            self.GcpDataResiduals = GcpDataResiduals

            self.transformationParamsBar.showTransformationParamsMessage(zAngle, translationX, translationY, globalError2D, translationZ, globalErrorZ)
            self.gcpTable.updateGcpTableResiduals(GcpDataResiduals)

            self.takeParametersBtn.setEnabled(True)

        else:
            self.zAngle = None
            self.translationX = None
            self.translationY = None
            self.translationZ = None
            self.globalError2D = None
            self.globalErrorZ = None
            self.GcpDataResiduals = None

            self.takeParametersBtn.setEnabled(False)

            self.transformationParamsBar.setEmptyTransformationParamsBar()

    ## \brief Check the conditions for the transformation
    #
    # - at least two XY- point pairs
    # - at least two height values
    #
    # \param GcpData Dictionary of the table data
    # @returns conditionValid - could be True or False

    def checkTransformationConditions(self, GcpData):

        #mindestens zwei XY- Punktpaare
        #mindestens zwei Höhenwerte
        conditionsValid = False

        if len(GcpData) < 3:
            conditionsValid = False
            self.messageBar.pushMessage("Error", "Zu geringe Anzahl an Georeferenzierungspunkten!", level=1, duration=5)
        else:
            conditionsValid = True

            countXY = 0
            countZ = 0
            arrayZ = []

            for pointObj in GcpData:
                if pointObj['usage'] == '3D' or pointObj['usage'] == '2D':
                    countXY += 1

                if pointObj['usage'] == '3D' or pointObj['usage'] == 'Z':
                    arrayZ.append(pointObj['sourcePoints'][2])

                if pointObj['usage'] == '3D' or pointObj['usage'] == 'Z':
                    countZ += 1

            #Pruefung auf Anzahl XY-Werte >=2
            if countXY < 2:
                conditionsValid = False
                self.messageBar.pushMessage("Error", "Zu geringe Anzahl an XY-Georeferenzierungspunkten für eine 2D Transformation!", level=1, duration=5)

            #Pruefung auf Anzahl Z-Werte >= 2
            if countZ < 2:
                conditionsValid = False
                self.messageBar.pushMessage("Error", "Zu geringe Anzahl an Z-Georeferenzierungspunkten für die 1D Höhentransformation!", level=1, duration=5)

        return conditionsValid

    ## \brief Sets the coordinates in the statusbar
    #
    # \param x x-coordinate
    # \param y y-coordinate

    def setCoordinatesOnStatusBar(self, x, y):
        self.coordLineEdit.setText(str(round(x, 2))+','+str(round(y, 2)))

    ## \brief Import a textfile with GCP-Data
    #

    def importTxt(self):

        dialog = QFileDialog(self)
        dialog.setNameFilter("Text Files (*.txt)")
        openFileName = dialog.getOpenFileName()[0]
        print('Import GCP Data from '+openFileName)

        if openFileName:

            ######## loadedGcpData - Parameter selection #############
            loadedGcpData = []
            startLineSelection = 0
            with open(openFileName, 'r', newline='') as csvfile:

                reader = csv.reader(csvfile, delimiter='\t', quotechar='|')

                for row in reader:
                    startLineSelection += 1
                    if row[0] == 'Parameter selection':
                        break

            csvfile.close()

            with open(openFileName, 'r') as csvfile:

                for i in range(startLineSelection):
                    next(csvfile)

                reader = csv.DictReader(csvfile, delimiter='\t')
                for row in reader:
                    loadedGcpData.append({'uuid': row['UUID'], 'ptnr': row['PTNR'], 'target_x_ptnr': row['TargetX PTNR'], 'target_y_ptnr': row['TargetY PTNR'], 'target_z_ptnr': row['TargetZ PTNR'], 'id': int(row['ID']), 'error_xy': float(row['Error XY']), 'error_z': float(row['Error Z']), 'usage': row['Punkt verwenden'], 'sourcePoints': [float(row['Quelle X']), float(row['Quelle Y']), float(row['Quelle Z'])], 'targetPoints': [float(row['Ziel X']), float(row['Ziel Y']), float(row['Ziel Z'])]})


            ######## loadedTargetGcp - TargetGCPs #############
            loadedTargetGcp = []

            startLineTargetGCP = 0
            with open(openFileName, 'r', newline='') as csvfile:

                reader = csv.reader(csvfile, delimiter='\t', quotechar='|')

                for row in reader:
                    startLineTargetGCP += 1
                    if row[0] == 'TargetGCPs':
                        break

            csvfile.close()

            with open(openFileName, 'r') as csvfile:

                lineCounter = 0
                for line in csvfile:

                    if (lineCounter > startLineTargetGCP) and (lineCounter < startLineSelection - 1):
                        lineArray = line.split('\t')
                        loadedTargetGcp.append({'ptnr': lineArray[0], 'x': float(lineArray[1]), 'y': float(lineArray[2]), 'z': float(lineArray[3])})

                    lineCounter += 1


            print('Finish load GCP Data from '+openFileName)

            self.gcpTable.updateGcpTableFromImport(loadedGcpData, loadedTargetGcp)

    ## \brief Export GCP-Data in a textfile
    #
    def exportTxt(self):

        dialog = QFileDialog(self)
        saveFile = QFileDialog.getSaveFileName(dialog, "Speichern unter", self.rememberExportTxtFolder, "Textdatei(*.txt)")
        saveFileName = saveFile[0]

        #Just to remember last loacation of the last saved file
        self.rememberExportTxtFolder = os.path.dirname(saveFileName)

        GcpData = self.gcpTable.getGcpTableData()

        if saveFileName:

            #transformationParameters
            with open(saveFileName, 'w', newline='') as csvfile:
                csvWriter = csv.writer(csvfile, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                csvWriter.writerow(['TransformationParameters'])
                csvWriter.writerow(['Rotation', 'Translation X', 'Translation Y', 'Translation Z', 'Error 2D', 'Error Z'])
                csvWriter.writerow([self.zAngle, self.translationX, self.translationY, self.translationZ, self.globalError2D, self.globalErrorZ])
            #TargetGCPs
            with open(saveFileName, 'a', newline='') as csvfile:
                csvWriter = csv.writer(csvfile, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                csvWriter.writerow(['TargetGCPs'])

                csvWriter.writerow(['PTNR', 'Ziel X', 'Ziel Y', 'Ziel Z'])

                for pointObj in self.gcpTarget['points']:
                    csvWriter.writerow([pointObj['ptnr'], pointObj['x'], pointObj['y'], pointObj['z']])
            #Parameter selection
            with open(saveFileName, 'a', newline='') as csvfile:
                csvWriter = csv.writer(csvfile, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                csvWriter.writerow(['Parameter selection'])
                exportHeaders = self.gcpTable.colHeaders.copy()
                exportHeaders.append('TargetX PTNR')
                exportHeaders.append('TargetY PTNR')
                exportHeaders.append('TargetZ PTNR')
                csvWriter.writerow(exportHeaders)

                for gcpObj in GcpData:
                    rowArray = []
                    rowArray.append(gcpObj['uuid'])             #UUID
                    rowArray.append(gcpObj['ptnr'])             #PTNR
                    rowArray.append(gcpObj['id'])               #ID
                    rowArray.append(gcpObj['sourcePoints'][0])  #Quelle X
                    rowArray.append(gcpObj['sourcePoints'][1])  #Quelle Y
                    rowArray.append(gcpObj['sourcePoints'][2])  #Quelle Z
                    rowArray.append(gcpObj['targetPoints'][0])  #Ziel X
                    rowArray.append(gcpObj['targetPoints'][1])  #Ziel Y
                    rowArray.append(gcpObj['targetPoints'][2])  #Ziel Z
                    rowArray.append(gcpObj['error_xy'])         #Error XY
                    rowArray.append(gcpObj['error_z'])          #Error Z
                    rowArray.append(gcpObj['usage'])            #Punkt verwenden
                    rowArray.append(gcpObj['target_x_ptnr'])    #Target PTNR
                    rowArray.append(gcpObj['target_y_ptnr'])    #Target PTNR
                    rowArray.append(gcpObj['target_z_ptnr'])    #Target PTNR

                    csvWriter.writerow(rowArray)

            print('Finish write GCP Data to '+saveFileName)

    ## \brief Function to output current parameters
    #
    def takeTransformParams(self):
        self.t2GArchInstance.setTransformationParameters(self.translationX, self.translationY, self.translationZ, self.zAngle, self.targetCrs)
        self.close()

    ## \brief Function to restore the complete window
    #
    # \param sourceLayer
    # \param inputLayers
    # \param targetCrs
    # \param gcpSource
    # \param gcpTarget

    def restore(self, sourceLayer, inputLayers, targetCrs, gcpSource, gcpTarget):

        self.gcpTable.cleanGcpTable()
        self.targetCrs = targetCrs
        self.gcpTarget = gcpTarget
        self.canvasTransform.updateCanvas(sourceLayer, inputLayers)
        self.gcpTable.updateGcpTable(gcpSource, gcpTarget)
        self.adjustSize()
        self.show()
        self.resize(1000, 700)
        self.estimateParameters()

    ## \brief Open up the transformation dialog
    #
    # calls the funcion restore()
    #
    # \param sourceLayer
    # \param inputLayers
    # \param targetCrs
    # \param sourceGCP
    # \param targetGCP

    def showTransformationDialog(self, sourceLayer, inputLayers, targetCrs, sourceGCP, targetGCP):
        self.restore(sourceLayer, inputLayers, targetCrs, sourceGCP, targetGCP)
