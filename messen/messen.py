## @package QGIS geoEdit extension..
import shutil, uuid
import winsound
from datetime import datetime, date
import os, math
from PyQt5 import QtWidgets, uic, QtCore, QtGui
#from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QMainWindow, QVBoxLayout
from PyQt5.QtCore import QCoreApplication, QTimer
from qgis.core import Qgis, QgsSnappingUtils, QgsMessageLog, QgsProject, QgsCircle, QgsGeometry, QgsWkbTypes, QgsVectorLayer, QgsApplication, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsRectangle, QgsVectorFileWriter
from qgis.utils import plugins, active_plugins
from qgis.gui import QgsMapToolIdentify,QgsMapTip
from ..functions import *
from ..geoEdit.geo_edit_calculations import GeoEditCalculations
from configparser import ConfigParser
from ..ExtDialoge.myDlgSettings import Configfile

# @author Daniel Timmel, LfA Dresden
# @date 2022-20-04

class Measurement():
    ## The constructor.
    #  Defines attributes for the Measurement
    #
    #  @param dockWidget pointer to the dockwidget
    #  @param iFace pointer to the iface class
    def __init__(self, t2gArchInstance, iFace):
        self.__iconpath = os.path.join(os.path.dirname(__file__), 'Icons')
        self.__qgisDateiPfad = QgsProject.instance().readPath('./')
        self.__projPfad = os.path.abspath(os.path.join(self.__qgisDateiPfad, "./.."))
        self.__t2gArchInstance = t2gArchInstance
        self.__dockwidget = t2gArchInstance.dockwidget
        self.__iface = iFace
        self.__config = None
        self.__canvas_clicked = ClickedPoint(self.__iface.mapCanvas(),self.__dockwidget)
        self.__iface.mapCanvas().setMapTool(self.__canvas_clicked)
        self.__canvas_clicked.keyPressSignal.connect(self.__keyPress)
        self.__dockwidget.closingPlugin.connect(self.__closeEvent)
        self.__dialogMeldung = MyMeldung()
        self.setup()

    ## @brief Initializes the functionality for Measurement modul
    def setup(self):
        #Setup "messen"
        self.__dockwidget.butT2GStart.setToolTip('Tachy2GIS 3d starten')
        self.__dockwidget.butT2GStart.setIcon(QIcon(os.path.join(self.__iconpath, 'icon.png')))
        self.__dockwidget.butT2GStart.clicked.connect(self.__t2gInstanceStart)

        self.__dockwidget.butT2GVis.setToolTip('Tachy2GIS 3d verstecken')
        self.__dockwidget.butT2GVis.setIcon(QIcon(os.path.join(self.__iconpath, 'Sichtbar_an.gif')))
        self.__dockwidget.butT2GVis.clicked.connect(self.__t2gWindowSetVisible)

        self.__dockwidget.butNewPoly.setToolTip('E_Polygon activ setzen')
        self.__dockwidget.butNewPoly.setIcon(QIcon(os.path.join(self.__iconpath, 'mActionCapturePolygon.png')))
        self.__dockwidget.butNewPoly.clicked.connect(self.__setPolygonlayerActiv)

        self.__dockwidget.butNewLine.setToolTip('E_Line activ setzen')
        self.__dockwidget.butNewLine.setIcon(QIcon(os.path.join(self.__iconpath, 'mActionCaptureLine.png')))
        self.__dockwidget.butNewLine.clicked.connect(self.__setLinelayerActiv)

        self.__dockwidget.butNewPoint.setToolTip('E_Point activ setzen')
        self.__dockwidget.butNewPoint.setIcon(QIcon(os.path.join(self.__iconpath, 'mActionCapturePoint.png')))
        self.__dockwidget.butNewPoint.clicked.connect(self.__setPointlayerActiv)

        self.__dockwidget.cboobjTyp.currentIndexChanged.connect(self.__fillcboobjArt)
        self.__dockwidget.cboobjTyp.setStyleSheet("font: bold 12px ;")
        self.__dockwidget.cboobjArt.setStyleSheet("font: bold 12px ;")


        self.__dockwidget.butCreateFeature.setToolTip('Geometrie erstellen')
        #self.__dockwidget.butCreateFeature.setIcon(QIcon(os.path.join(self.__iconpath, 'mActionCapturePoint.png')))
        self.__dockwidget.butCreateFeature.clicked.connect(self.__geometryIdentify)
        #self.__dockwidget.butCreateFeature.setEnabled(False)
        self.__dockwidget.butCreateFeature.setShortcut('Enter')

        items = ["Frei", "Kreis mit 2 Punkten (Radius)", "Kreis mit 2 Punkten (Durchmesser)", "Rechteck"]
        self.__dockwidget.cboFigur.addItems(items)
        icon0 = QIcon(os.path.join(self.__iconpath, 'Frei.gif'))
        icon1 = QIcon(os.path.join(self.__iconpath, 'Circle2PR.gif'))
        icon2 = QIcon(os.path.join(self.__iconpath, 'Circle2P.gif'))
        icon3 = QIcon(os.path.join(self.__iconpath, 'Rectangle.gif'))
        self.__dockwidget.cboFigur.setItemIcon(0, icon0)
        self.__dockwidget.cboFigur.setItemIcon(1, icon1)
        self.__dockwidget.cboFigur.setItemIcon(2, icon2)
        self.__dockwidget.cboFigur.setItemIcon(3, icon3)
        self.__dockwidget.cboFigur.currentIndexChanged.connect(self.__geometrycheck)

        self.__dockwidget.butG.setToolTip('Größer')
        self.__dockwidget.butG.clicked.connect(self.__koordTableShow)

        self.__dockwidget.butClear.clicked.connect(self.__koordtableClear)
        self.__dockwidget.tabWidget_2.currentChanged.connect(self.__watchEventStop)

        #print(active_plugins)
        # active_plugins enthält einmal:
        # ['firstaid', 'plugin_reloader', 'Tachy2GIS', 'Tachy2GIS_arch', 'grassprovider', 'processing']
        # und einmal: (nach einem plugin reload)
        # ['firstaid', 'plugin_reloader', 'Tachy2GIS_arch', 'grassprovider', 'processing', 'Tachy2GIS']
        # und einmal: (nach einem plugin reload)
        # ['firstaid', 'plugin_reloader', 'Tachy2GIS_arch', 'grassprovider', 'processing', 'Tachy2GIS-3D_viewer']
        # Es soll entweder das Tachy2GIS oder das Tachy2GIS-3D_viewer Plugin verwendet werden aber nicht das Tachy2GIS_arch Plugin
        self.__t2gInstance = plugins.get([s for s in active_plugins if "Tachy2GIS" in s and "Tachy2GIS_arch" != s][0])
        self.__t2gInstance.dlg.closingPlugin.connect(self.__t2gInstanceClose)

        self.__vertices = []#self.__t2gInstance.vtk_mouse_interactor_style.vertices

        self.__watch = QTimer()
        self.__watch.timeout.connect(self.__watchEvent)
        self.__verticesCount = 0
        #self.__targetLayer = None

        #self.__koordTable = None#KoordTable(self.__dockwidget.tableWidget)#self.__iface.mainWindow()
        #self.__koordList = []

        self.__dockwidget.butT2GVis.setEnabled(False)

        self.__dockwidget.tableWidget.setMouseTracking(True)
        self.__dockwidget.tableWidget.setAutoScrollMargin(30)
        self.__dockwidget.tableWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.__dockwidget.tableWidget.itemSelectionChanged.connect(self.__setTempMaker)
        self.__dockwidget.tableWidget.customContextMenuRequested.connect(self.__on_customContextMenu)


        self.__vertexMaker = makerAndRubberbands()
        self.__vertexMaker.setMakerType(QgsVertexMarker.ICON_BOX)

        self.__rubberBand = makerAndRubberbands()
        self.__pointMaker = makerAndRubberbands()
        self.__pointMaker.setMakerType(QgsVertexMarker.ICON_X)
        self.__pointMaker.setColor(QColor(0, 255, 0))

        self.__makerTemp = makerAndRubberbands()
        self.__makerTemp.setColor(QColor(0, 0, 255))
        self.__makerTemp.setMakerType(QgsVertexMarker.ICON_X)

        self.__dockwidget.txtPoint_2.textChanged.connect(self.__setMarker2)
        self.__lastVertexHeight = 0.0

        self.__activLayer = None
        self.__lastNewFeatures = []
        self.__wkbTypeName = None
        self.__isMulti = None

        #self.__setPolygonlayerActiv()
        #self.__fillcboobjTyp()
        self.__dockwidget.butClear_2.clicked.connect(self.__delAutoAttribut)
        self.__dockwidget.chbAttributtable.setToolTip('Attributtabelle einblenden')
        self.__dockwidget.butAttributtable.clicked.connect(self.__lastGeometryShow)

        #self.__dockwidget.tabWidget.setTabVisible(0, False)

        self.__dockwidget.butTips.clicked.connect(self.__tips)

        self.__dockwidget.txtZKoord.textChanged.connect(self.__zKoordChanged)
        self.__dockwidget.txtAkt.setText(getCustomProjectVariable("aktcode"))
        #self.__saveAktcode()
        self.__dockwidget.txtAkt.textChanged.connect(self.__saveAktcode)
        self.__measurementActiv = False
        self.__dockwidget.chbAutoAtt.stateChanged.connect(self.__autoAttributOnOff)
        self.__dockwidget.chbAutoAtt.setChecked(False)
        self.__lastMeasurments = []
        self.__dockwidget.tableWidget_2.cellClicked.connect(self.on_cellClicked)
        self.__attWidget = None

        self.__dockwidget.chbbefZ.setStyleSheet("""QCheckBox{} QCheckBox:checked{border: 0px solid green;background-color: green}
        QCheckBox:unchecked{border: 0px solid white;background-color: white}""")
        self.__dockwidget.chbFundZ.setStyleSheet("""QCheckBox{} QCheckBox:checked{border: 0px solid green;background-color: green}
        QCheckBox:unchecked{border: 0px solid white;background-color: white}""")
        self.__dockwidget.chbProfZ.setStyleSheet("""QCheckBox{} QCheckBox:checked{border: 0px solid green;background-color: green}
        QCheckBox:unchecked{border: 0px solid white;background-color: white}""")
        self.__dockwidget.chbProbeZ.setStyleSheet("""QCheckBox{} QCheckBox:checked{border: 0px solid green;background-color: green}
        QCheckBox:unchecked{border: 0px solid white;background-color: white}""")
        self.__dockwidget.chbptnrZ.setStyleSheet("""QCheckBox{} QCheckBox:checked{border: 0px solid green;background-color: green}
        QCheckBox:unchecked{border: 0px solid white;background-color: white}""")

        self.__dockwidget.butBefundLabel.clicked.connect(self.__befundLabel_n)
        self.__dockwidget.butBefundLabel.setIcon(QIcon(os.path.join(self.__iconpath, 'Befundnr.gif')))
        self.__abbruch = False

        self.__insertPos = None
        self.__dockwidget.tableWidget_2.viewport().installEventFilter(self.__dockwidget.tableWidget_2)
        self.__dockwidget.tableWidget.cellChanged.connect(self.koord_cellChanged)
        #self.__dockwidget.tableWidget_2.keyPressEvent(self.__keyPress)
        self.clipboard = []
        #Tooltip Tastenkürzel setzen
        datei = open(os.path.join(os.path.dirname(__file__), 'Tips.htm'),'r')
        text = datei.read()
        datei.close()
        self.__dockwidget.butTips.setToolTip(text)

        self.__dockwidget.butLaden.clicked.connect(self.__autributteLoad)
        self.__dockwidget.butLaden.setShortcut('Key-L')


    def setconfig(self,config):
        self.__config = config

    ## @brief Start process to move features forward
    # - Get input values
    # - Check validity of the sourcelayer
    # - Connects elements in the geoEdit dockwidget to related functions
    def __t2gWindowSetVisible(self):
        #if self.__t2gInstance is None:
        #    return
        #QgsMessageLog.logMessage('unsichtbar', 'T2G Archäologie', Qgis.Info)
        #self.__t2gInstanceStart()
        if self.__t2gInstance.pluginIsActive == True:
            if self.__t2gInstance.dlg.isVisible():
                self.__t2gInstance.dlg.hide()
                self.__dockwidget.butT2GVis.setIcon(QIcon(os.path.join(self.__iconpath, 'Sichtbar_aus.gif')))
            else:
                self.__t2gInstance.dlg.show()
                self.__dockwidget.butT2GVis.setIcon(QIcon(os.path.join(self.__iconpath, 'Sichtbar_an.gif')))

    def __saveAktcode(self):
        self.__config.updateValue('Projekt','aktivität', self.__dockwidget.txtAkt.text())
        setCustomProjectVariable('aktcode', self.__dockwidget.txtAkt.text())
        self.__config.saveFile()

    def __lastGeometryShow(self):
        self.__lastGeometry(self.__activLayer, self.__lastNewFeatures)

    def __lastGeometry(self,layer,ids):
        try:
            if self.__attWidget is not None:
                self.__attWidget.close()
        except:
            pass
        layer.removeSelection()
        layer.selectByIds(ids)
        self.__iface.actionSelectRectangle().trigger()
        layer.startEditing()
        if len(ids) == 1:
            query = "$id = " + str(ids [0])
        else:
            query = "$id >= " + str(ids [0])
        self.__attWidget = self.__iface.showAttributeTable(layer, query)
        self.__attWidget.exec_()
        layer.commitChanges()
        self.__iface.mapCanvas().setMapTool(self.__canvas_clicked)
        #self.__canvas_clicked.setMouseInfoVisible(True)
        layer.removeSelection()

    def __t2gInstanceStart(self):
        if self.__measurementActiv == False:
            self.__measurementActiv = True
            if self.__t2gInstance.pluginIsActive == False:
                QgsMessageLog.logMessage('watchEventStart', 'T2G Archäologie', Qgis.Info)

                text = """
                <html>
                <style type="text/css">
                b {color: black}
                </style>
                <body>
                <b>Bitte warten.</b>
                <b>Programm wird vorbereitet.</b>
                </body>
                </html>"""
                self.__dialogMeldung.run(None,text,230,90)
                QApplication.processEvents()
                self.__t2gInstance.run()
                self.__t2gInstance.setPickable()
                self.__watch.start(150)
                self.__verticesCount = 0
                self.__setTableHeader()
                self.__dockwidget.tableWidget.setRowCount(0)
                self.__dockwidget.butT2GVis.setEnabled(True)
                #self.__iface.mapCanvas().setMapTool(self.__canvas_clicked)
                self.__dialogMeldung.close()
            else:
                self.__iface.actionSelectRectangle().trigger()
                self.__dockwidget.butT2GStart.setStyleSheet("")
            self.__dockwidget.butT2GStart.setStyleSheet("border-style: outset ; border-width: 5px ; border-color: green")
            self.__dockwidget.label_26.setStyleSheet("background-color:green")
            self.__iface.mapCanvas().setMapTool(self.__canvas_clicked)
            self.__setPolygonlayerActiv()
        else:
            self.__measurementActiv = False
            self.__iface.actionSelectRectangle().trigger()
            self.__dockwidget.butT2GStart.setStyleSheet("")
            self.__dockwidget.label_26.setStyleSheet("")
            #self.__watchEventStop(1)


    def __t2gInstanceClose(self):
        QgsMessageLog.logMessage('watchEventStop', 'T2G Archäologie', Qgis.Info)
        self.__watch.stop()
        self.__dockwidget.tableWidget.setRowCount(0)
        self.__dockwidget.butT2GStart.setStyleSheet("")
        self.__dockwidget.butT2GVis.setEnabled(False)

        #self.__t2gInstance.onCloseCleanup()
        self.__koordtableClear()
        self.__iface.actionSelectRectangle().trigger()

    def __watchEvent(self):
        self.__vertices = self.__t2gInstance.vtk_mouse_interactor_style.vertices
        #QgsMessageLog.logMessage(str(len(self.__vertices))+'  '+ str(self.__verticesCount), 'T2G Archäologie', Qgis.Info)
        if len(self.__vertices) > self.__verticesCount:
            row = self.__verticesCount
            self.__dockwidget.tableWidget.insertRow(row)
            self.__dockwidget.tableWidget.setRowHeight(row,25)
            self.__dockwidget.tableWidget.setItem(row, 0, QTableWidgetItem(str(row)))
            self.__dockwidget.tableWidget.setItem(row, 1, QTableWidgetItem(str(round(self.__vertices[row][0],3))))
            self.__dockwidget.tableWidget.setItem(row, 2, QTableWidgetItem(str(round(self.__vertices[row][1],3))))
            self.__dockwidget.tableWidget.setItem(row, 3, QTableWidgetItem(str(round(self.__vertices[row][2],3))))
            self.__verticesCount = row + 1
            self.__dockwidget.labPointCount.setText(str(self.__verticesCount)+' Punkte')

            #self.__koordList.append({str(row),str(self.__vertices[row][0]),str(self.__vertices[row][1]),str(self.__vertices[row][2])})
            #self.__dockwidget.tableWidget.scrollToItem(self.__verticesCount)
            self.__lastVertexHeight = self.__vertices[row][2]

            self.__rubberbandClean()
            self.__setVertexMarker(self.__vertices)
            #Einfügeposition prüfen und markieren
            if self.__insertPos != None:
                self.__dockwidget.tableWidget.selectRow(self.__insertPos-1)
                self.__insertPos = None
            else:
                self.__dockwidget.tableWidget.scrollToItem(self.__dockwidget.tableWidget.selectRow(row))

            self.__iface.mapCanvas().setFocus()
            self.__beep_AddKoord()

    def __beep_AddKoord(self):
        if  self.__dockwidget.chbSound.isChecked():
            winsound.Beep(1000, 100)

    def __beep_AddGeometry(self):
        if  self.__dockwidget.chbSound.isChecked():
            #winsound.PlaySound('SystemAsterisk', winsound.SND_ASYNC)
            winsound.Beep(1000, 100)
            winsound.Beep(5000, 100)

    def __watchEventStop(self, index):
        QgsMessageLog.logMessage('watchEventStop', 'T2G Archäologie', Qgis.Info)
        if index == 0:
            #self.__dockwidget.toolBox.setItemVisible(1,False)
            pass
        else:
            self.__iface.actionSelectRectangle().trigger()
            pass
        if self.__t2gInstance.pluginIsActive == True:
            if index == 0:
                self.__watch.start(150)
                self.__iface.mapCanvas().setMapTool(self.__canvas_clicked)
            else:
                self.__watch.stop()

    def __koordTableShow(self):
        if self.__dockwidget.butG.toolTip() == 'Größer':
            self.__dockwidget.butG.setToolTip('Kleiner')
            self.__dockwidget.butG.setText('>')
            self.__dockwidget.setFixedWidth(390)
            self.__dockwidget.tableWidget.setFixedWidth(345)
            self.__dockwidget.tableWidget_2.setFixedWidth(345)
            self.__dockwidget.tabWidget.setFixedWidth(380)
        else:
            self.__dockwidget.butG.setToolTip('Größer')
            self.__dockwidget.butG.setText('<')
            self.__dockwidget.setFixedWidth(233)
            self.__dockwidget.tableWidget.setFixedWidth(190)
            self.__dockwidget.tableWidget_2.setFixedWidth(190)
            self.__dockwidget.tabWidget.setFixedWidth(190)

    def __mesurementsShow(self):
        #self.__dockwidget.tabWidget.setTabVisible(2, True)
        self.__dockwidget.tabWidget.setCurrentIndex(2)

    def __lastMeasurmentsAdd(self):
        #for geometry in self.__lastNewFeatures:
        for i in range(len(self.__lastNewFeatures)):
            #self.__lastMeasurments.append()
            id = self.__lastNewFeatures[i]
            aktdate = str(datetime.now().strftime("%H:%M:%S"))
            row = self.__dockwidget.tableWidget_2.rowCount()
            self.__dockwidget.tableWidget_2.insertRow(row)
            self.__dockwidget.tableWidget_2.setItem(row, 0, QTableWidgetItem(str(aktdate)))
            self.__dockwidget.tableWidget_2.setItem(row, 1, QTableWidgetItem(str(self.__activLayer.name())))
            self.__dockwidget.tableWidget_2.setItem(row, 2, QTableWidgetItem(str(id)))
            self.__dockwidget.tableWidget_2.scrollToItem(self.__dockwidget.tableWidget_2.selectRow(row))

    def on_cellClicked(self,row,column):
        layername = self.__dockwidget.tableWidget_2.item(row, 1).text()
        id = self.__dockwidget.tableWidget_2.item(row, 2).text()
        layer = QgsProject().instance().mapLayersByName(layername)[0]
        ids = []
        ids.append(int(id))
        self.__lastGeometry(layer, ids)
        pass

    def __koordtableClear(self):
        self.__dockwidget.tableWidget.setRowCount(0)
        self.__t2gInstance.vtk_mouse_interactor_style.vertices = []
        self.__t2gInstance.vtk_mouse_interactor_style.draw()
        if self.__t2gInstance.dlg.isVisible():
            # remove vtk layer and update renderer
            self.__t2gInstance.rerenderVtkLayer([self.__iface.activeLayer().id()])

        self.__dockwidget.labPointCount.setText('0 Punkte')
        self.__verticesCount = 0
        self.__vertices = []

        self.__rubberbandClean()
        #self.__dockwidget.butCreateFeature.setEnabled(False)

    def __setTableHeader(self):
        self.__dockwidget.tableWidget.setColumnCount(4)
        header = self.__dockwidget.tableWidget.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.__dockwidget.tableWidget.setHorizontalHeaderLabels(('id', 'x', 'y', 'z'))
        self.__dockwidget.tableWidget_2.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

    def __autributteLoad(self):
        self.__readAutoAttributeToSettigs()

    def __setPolygonlayerActiv(self):
        activeLayer = QgsProject().instance().mapLayersByName('E_Polygon')[0]
        self.__iface.setActiveLayer(activeLayer)
        self.__activLayer = activeLayer
        self.__wkbTypeName = QgsWkbTypes.displayString(self.__activLayer.wkbType())
        self.__isMulti = QgsWkbTypes.isMultiType(self.__activLayer.wkbType())
        self.__dockwidget.label_9.setText('E_Polygon')
        self.__dockwidget.label_37.setStyleSheet("background-color:green")
        self.__t2gInstance.dlg.targetLayerComboBox.setCurrentText('E_Polygon')
        self.__t2gInstance.dlg.sourceLayerComboBox.setCurrentText('E_Polygon')
        self.__dockwidget.butNewPoly.setStyleSheet("border-style: outset ; border-width: 3px ; border-color: green")
        self.__dockwidget.butNewLine.setStyleSheet("")
        self.__dockwidget.butNewPoint.setStyleSheet("")
        self.__dockwidget.label_38.setStyleSheet("")
        self.__dockwidget.label_39.setStyleSheet("")
        self.__fillcboobjTyp()
        self.__t2gInstance.setPickable()
        #self.__readAutoAttributeToSettigs()
        self. __delAutoAttribut()
        self.__dockwidget.txtptnr.setEnabled(False)
        self.__dockwidget.chbptnrZ.setEnabled(False)

    def __setLinelayerActiv(self):
        activeLayer = QgsProject().instance().mapLayersByName('E_Line')[0]
        self.__iface.setActiveLayer(activeLayer)
        self.__activLayer = activeLayer
        self.__dockwidget.label_9.setText('E_Line')
        self.__dockwidget.label_38.setStyleSheet("background-color:green")
        self.__t2gInstance.dlg.targetLayerComboBox.setCurrentText('E_Line')
        self.__t2gInstance.dlg.sourceLayerComboBox.setCurrentText('E_Line')
        self.__dockwidget.butNewLine.setStyleSheet("border-style: outset ; border-width: 3px ; border-color: green")
        self.__dockwidget.butNewPoly.setStyleSheet("")
        self.__dockwidget.butNewPoint.setStyleSheet("")
        self.__dockwidget.label_37.setStyleSheet("")
        self.__dockwidget.label_39.setStyleSheet("")
        self.__fillcboobjTyp()
        self.__t2gInstance.setPickable()
        #self.__readAutoAttributeToSettigs()
        self. __delAutoAttribut()
        self.__dockwidget.txtptnr.setEnabled(False)
        self.__dockwidget.chbptnrZ.setEnabled(False)

    def __setPointlayerActiv(self):
        activeLayer = QgsProject().instance().mapLayersByName('E_Point')[0]
        self.__iface.setActiveLayer(activeLayer)
        self.__activLayer = activeLayer
        self.__dockwidget.label_9.setText('E_Point')
        self.__dockwidget.label_39.setStyleSheet("background-color:green")
        self.__t2gInstance.dlg.targetLayerComboBox.setCurrentText('E_Point')
        self.__t2gInstance.dlg.sourceLayerComboBox.setCurrentText('E_Point')
        self.__dockwidget.butNewPoint.setStyleSheet("border-style: outset ; border-width: 3px ; border-color: green")
        self.__dockwidget.butNewLine.setStyleSheet("")
        self.__dockwidget.butNewPoly.setStyleSheet("")
        self.__dockwidget.label_37.setStyleSheet("")
        self.__dockwidget.label_38.setStyleSheet("")
        self.__fillcboobjTyp()
        self.__t2gInstance.setPickable()
        #self.__readAutoAttributeToSettigs()
        self. __delAutoAttribut()
        self.__dockwidget.txtptnr.setEnabled(True)
        self.__dockwidget.chbptnrZ.setEnabled(True)

    def __on_customContextMenu(self, pos):
        contextMenu = QtWidgets.QMenu()
        delVertex = contextMenu.addAction(
            QtGui.QIcon(os.path.join(self.__iconpath, 'delVertex.png')), " Vertex löschen")
        delVertex.triggered.connect(self.__delVertex)
        addVertex = contextMenu.addAction(
            QtGui.QIcon(os.path.join(self.__iconpath, 'addVertex.png')), " Vertex hinzufügen")
        addVertex.triggered.connect(self.__addVertex)
        hoeheKor = contextMenu.addAction(
            QtGui.QIcon(os.path.join(self.__iconpath, 'ZCoordMove.gif')), " Z Korrektur")
        hoeheKor.triggered.connect(self.__zKorr)

        contextMenu.exec_(QtGui.QCursor.pos())

    def eventFilter(self, source, event):
        QgsMessageLog.logMessage('key press', 'T2G Archäologie', Qgis.Info)

    def copySelection(self):
        # clear the current contents of the clipboard
        QgsMessageLog.logMessage('Copy', 'T2G Archäologie', Qgis.Info)
        self.clipboard.clear()
        selected = self.__dockwidget.tableWidget.selectedIndexes()
        rows = []
        columns = []
        # cycle all selected items to get the minimum row and column, so that the
        # reference will always be [0, 0]
        for index in selected:
            rows.append(index.row())
            columns.append(index.column())

        minRow = min(rows)
        minCol = min(columns)
        for index in selected:
            # append the data of each selected index
            self.clipboard.append((index.row() - minRow, index.column() - minCol, index.data()))
            QgsMessageLog.logMessage(str(index.row() - minRow)+','+str(index.column() - minCol)+','+str(index.data()), 'T2G Archäologie', Qgis.Info)

    def pasteSelection(self):
        QgsMessageLog.logMessage('Past', 'T2G Archäologie', Qgis.Info)
        if not self.clipboard:
            return
        selected = self.__dockwidget.tableWidget.selectedIndexes()
        srows = []
        scolumns = []
        for index in selected:
            srows.append(index.row())
            scolumns.append(index.column())

        firstRow = min(srows)
        lastRow = max(srows)
        firstColumn = min(scolumns)
        lastColumn = max(scolumns)
        QgsMessageLog.logMessage(str(len(srows)), 'T2G Archäologie', Qgis.Info)

        if len(self.clipboard)==1:
            QgsMessageLog.logMessage(str(len(srows)), 'T2G Archäologie', Qgis.Info)
            for i in range(len(srows)):
                for row, column, data in self.clipboard:
                    self.__dockwidget.tableWidget.setItem(firstRow + row + i, firstColumn + column, QTableWidgetItem(data))

        elif len(self.clipboard)>1:
            for row, column, data in self.clipboard:
                # get the index, with rows and columns relative to the current
                self.__dockwidget.tableWidget.setItem(firstRow + row, firstColumn + column, QTableWidgetItem(data))


    def __delVertex(self):
        selected = self.__dockwidget.tableWidget.selectedIndexes()
        rows = []
        for index in selected:
            if index.row() not in rows:
                rows.append(index.row())

        if len(rows) > 1:
            self.__iface.messageBar().pushMessage(u"T2G Archäologie: ", u"Nur einen Vertex zum löschen wählen!",
                                           level=Qgis.Info)
            return

        for row in rows:
            self.__dockwidget.tableWidget.removeRow(row)
            self.__t2gInstance.vtk_mouse_interactor_style.vertices.pop(row)

        self.__dockwidget.labPointCount.setText(str(self.__dockwidget.tableWidget.rowCount()))

        self.__t2gInstance.vtk_mouse_interactor_style.draw()
        self.__verticesCount = self.__dockwidget.tableWidget.rowCount()

        self.__setVertexMarker(self.__vertices)

    def koord_cellChanged(self,row,column):
        QgsMessageLog.logMessage(str(row)+str(column), 'T2G Archäologie', Qgis.Info)
        if column >= 1 and column <= 3:
            #self.__vertices[row][column] = float(self.__dockwidget.tableWidget.item(row, column).text())

            x = self.__vertices[row][0]
            y = self.__vertices[row][1]
            z = self.__vertices[row][2]
            if column == 1:
                x = float(self.__dockwidget.tableWidget.item(row, column).text())
            elif column == 2:
                y = float(self.__dockwidget.tableWidget.item(row, column).text())
            elif column == 3:
                z = float(self.__dockwidget.tableWidget.item(row, column).text())

            value = (x, y, z)
            self.__vertices[row] = value
            self.__t2gInstance.vtk_mouse_interactor_style.draw()
            self.__setVertexMarker(self.__vertices)

    def __zKoordChanged(self):
        if len(self.__dockwidget.txtZKoord.text()) > 0:
            self.__dockwidget.txtZKoord.setStyleSheet("border-style: outset ; border-width: 4px ; border-color: red")
        else:
            self.__dockwidget.txtZKoord.setStyleSheet("")

    def __addVertex(self):
        index = self.__dockwidget.tableWidget.currentIndex()
        self.__insertPos = None
        row = index.row()
        self.__insertPos = row + 1
        QgsMessageLog.logMessage(str(row), 'T2G Archäologie', Qgis.Info)
        #self.__dockwidget.tableWidget.insertRow(row)

        pass

    def __zKorr(self):
        val, ok = QInputDialog.getText(None,'Z-Koorektur', 'Absoluter Wert oder +/- Wert zu erhöhen oder zu senken.')
        if ok:

            for item in self.__dockwidget.tableWidget.selectedItems():
                #QgsMessageLog.logMessage(str(item.text()), 'T2G Archäologie', Qgis.Info)
                row = item.row()
                column = 3
                x = self.__vertices[row][0]
                y = self.__vertices[row][1]
                z = self.__vertices[row][2]

                zorg = z
                #z = float(self.__dockwidget.tableWidget.item(row, column).text())
                z = z + float(val)
                self.__dockwidget.tableWidget.item(row, column).setText(str(z))
                value = (x, y, z)
                self.__vertices[row] = value
            self.__t2gInstance.vtk_mouse_interactor_style.draw()
            self.__setVertexMarker(self.__vertices)
        pass

    def __rubberbandClean(self):
        self.__rubberBand.rubberBandClean()
        self.__vertexMaker.makerClean()
        self.__makerTemp.makerClean()

    def __setVertexMarker(self,vertices):
        self.__rubberbandClean()
        self.__rubberBand.setRubberBandPoly(vertices, 2)
        #for i in range(len(vertices)):
        #    self.__vertexMaker.setMarker(vertices[i][0], vertices[i][1],10,1)

    def __setTempMaker(self):
        self.__pointMaker.makerClean()
        for item in self.__dockwidget.tableWidget.selectedItems():
            #QgsMessageLog.logMessage(str(item.text()), 'T2G Archäologie', Qgis.Info)
            row = item.row()
            self.__pointMaker.setMarker(self.__vertices[row][0], self.__vertices[row][1],12,2)

        #self.__geometrycheck()

    def __setMarker2(self):
        if self.__activLayer is None:
            self.__iface.messageBar().pushMessage(u"T2G Archäologie: ", u"Kein Messlayer gewählt!",
                                           level=Qgis.Critical)
            return
        self.__makerTemp.makerClean()
        #self.__vertices = self.__t2gInstance.vtk_mouse_interactor_style.vertices
        text = self.__dockwidget.txtPoint_2.text().split(',')
        row = self.__verticesCount
        x = float(text[0])
        y = float(text[1])
        z = 0.0
        if self.__verticesCount == 0:
            if len(self.__dockwidget.txtZKoord.text()) > 0:
                z = float(self.__dockwidget.txtZKoord.text())
        if self.__verticesCount > 0:
            z = float(self.__vertices[row-1][2])

        self.__makerTemp.setMarker(x, y,10,1)

        value = (x, y, z)
        # Einfügeposition prüfen
        if self.__insertPos == None:
            self.__vertices.append(value)
        else:
            self.__vertices.insert(self.__insertPos-1,value)
            #self.__insertPos = None

        self.__t2gInstance.vtk_mouse_interactor_style.draw()

    def __geometryIdentify(self):
        if self.__zcheck() is False:
            return

        if self.__geometrycheck() is False:
            iface.messageBar().pushMessage(u"T2G Archäologie: ", u"Geometrie nicht möglich.",
                                           level=Qgis.Critical)
            return
        x = self.__dockwidget.cboFigur.currentIndex()
        ##@ freihe Geometry
        if x == 0:
            features = self.__greateFreeGeometry()
            self.__greateFeature(features)
        ##@ Kreis mit Mittelpunkt und Radius
        elif x == 1:
            features = self.__greateCircleMRGeometry()
            self.__greateFeature(features)
            id = self.__activLayer.featureCount()-1
            self.__lastNewFeatures = []
        ##@ Kreis mit 2 Punkten
        elif x == 2:
            features = self.__greateCircle2PGeometry()
            self.__greateFeature(features)
            id = self.__activLayer.featureCount()-1
            self.__lastNewFeatures = []
        ##@ Rechteck
        elif x == 3:
            features = self.__greateRectangleGeometry()
            self.__greateFeature(features)
            id = self.__activLayer.featureCount()-1
            self.__lastNewFeatures = []

    def __greateFreeGeometry(self):
                features = []
                self.__setAutoAttributeToQgisVariable()
                UUid = self.__activLayer.dataProvider().fieldNameIndex('uuid')
                archgeoid = self.__activLayer.dataProvider().fieldNameIndex('geo-arch')
                archgeoval = self.__dockwidget.cboArchGeo.currentText()
                ##@ Punktgeometrie
                if self.__activLayer.geometryType() == 0:
                    for i in range(len(self.__vertices)):
                        self.__setAutoAttributeToQgisVariable()
                        attL = {UUid: '{' + str(uuid.uuid4()) + '}', archgeoid : archgeoval}
                        # QgsMessageLog.logMessage(str(item.text()), 'T2G Archäologie', Qgis.Info)
                        pt = QgsPoint(float(self.__vertices[i][0]), float(self.__vertices[i][1]), float(self.__vertices[i][2]))
                        features.append(QgsVectorLayerUtils.createFeature(self.__activLayer,
                                                                              QgsGeometry(pt),
                                                                              attL,
                                                                              self.__activLayer.createExpressionContext()))
                        self.__zaehlung()
                ##@ Liniengeometrie
                elif self.__activLayer.geometryType() == 1:
                    wktGeo = self.make_wkt(self.__vertices)
                    attL = {UUid: '{' + str(uuid.uuid4()) + '}', archgeoid : archgeoval}
                    geometry = QgsGeometry.fromWkt(wktGeo)
                    features.append(QgsVectorLayerUtils.createFeature(self.__activLayer,
                                                                             geometry,
                                                                             attL,
                                                                             self.__activLayer.createExpressionContext()))
                    self.__zaehlung()
                ##@ Polygongeometrie
                elif self.__activLayer.geometryType() == 2:
                    features = []
                    self.__vertices.append(self.__vertices[0])
                    wktGeo = self.make_wkt(self.__vertices)
                    attL = {UUid: '{' + str(uuid.uuid4()) + '}', archgeoid : archgeoval}
                    geometry = QgsGeometry.fromWkt(wktGeo)
                    features = [QgsVectorLayerUtils.createFeature(self.__activLayer,
                                                          geometry,
                                                          attL,
                                                          self.__activLayer.createExpressionContext())]
                    self.__zaehlung()
                self.__writeAutoAttributeToSettigs()
                return features


    def __greateCircleMRGeometry(self):
        self.__setAutoAttributeToQgisVariable()
        UUid = self.__activLayer.dataProvider().fieldNameIndex('uuid')
        features = []
        if self.__activLayer.geometryType() == 1 or self.__activLayer.geometryType() == 2:
            ##@ Kreis Mittelpunkt und Radius
            z = 0
            for i in range(len(self.__vertices)):
                point1 = QgsPoint(float(self.__vertices[z][0]),float(self.__vertices[z][1]),float(self.__vertices[z][2]))
                point2 = QgsPoint(float(self.__vertices[z+1][0]),float(self.__vertices[z+1][1]),float(self.__vertices[z+1][2]))
                radius = point1.distance(point2)
                if radius < 1:
                    segments = 30
                else:
                    segments = int(radius*20)
                geometry = self.__circle_geometry(point1, radius, segments)
                wktGeo = self.make_wkt(geometry)
                attL = {UUid: '{' + str(uuid.uuid4()) + '}'}
                geometry = QgsGeometry.fromWkt(wktGeo)
                features.append (QgsVectorLayerUtils.createFeature(self.__activLayer,
                                                      geometry,
                                                      attL,
                                                      self.__activLayer.createExpressionContext()))
                self.__zaehlung()
                z = z + 2
                if z == len(self.__vertices):
                    break
            self.__writeAutoAttributeToSettigs()
            return features

    def __greateCircle2PGeometry(self):
        self.__setAutoAttributeToQgisVariable()
        UUid = self.__activLayer.dataProvider().fieldNameIndex('uuid')
        features = []
        if self.__activLayer.geometryType() == 1 or self.__activLayer.geometryType() == 2:
            ##@ Kreis 2 Punkte
            z = 0
            for i in range(len(self.__vertices)):
                point1 = QgsPoint(float(self.__vertices[z][0]),float(self.__vertices[z][1]),float(self.__vertices[z][2]))
                point2 = QgsPoint(float(self.__vertices[z+1][0]),float(self.__vertices[z+1][1]),float(self.__vertices[z+1][2]))
                x = (point1.x()+point2.x())/2
                y = (point1.y()+point2.y())/2
                center = QgsPoint((point1.x()+point2.x())/2,(point1.y()+point2.y())/2,float(self.__vertices[0][2]))
                radius = point1.distance(center)
                if radius < 1:
                    segments = 30
                else:
                    segments = int(radius*20)
                geometry = self.__circle_geometry(center, radius, segments)
                wktGeo = self.make_wkt(geometry)
                attL = {UUid: '{' + str(uuid.uuid4()) + '}'}
                geometry = QgsGeometry.fromWkt(wktGeo)
                features.append (QgsVectorLayerUtils.createFeature(self.__activLayer,
                                                      geometry,
                                                      attL,
                                                      self.__activLayer.createExpressionContext()))
                self.__zaehlung()
                z = z + 2
                if z == len(self.__vertices):
                    break
            self.__writeAutoAttributeToSettigs()
            return features

    def __greateRectangleGeometry(self):
        self.__setAutoAttributeToQgisVariable()
        UUid = self.__activLayer.dataProvider().fieldNameIndex('uuid')
        ##@ Kreis Mittelpunkt und Radius
        if self.__activLayer.geometryType() == 1 or self.__activLayer.geometryType() == 2:
            features = []
            point1 = QgsPoint(float(self.__vertices[0][0]),float(self.__vertices[0][1]),float(self.__vertices[0][2]))
            point2 = QgsPoint(float(self.__vertices[1][0]),float(self.__vertices[1][1]),float(self.__vertices[0][2]))
            rect = QgsRectangle(point1.x(), point1.y(), point2.x(), point2.y())

            geometry = QgsGeometry.fromRect(rect)
            attL = {UUid: '{' + str(uuid.uuid4()) + '}'}
            features.append(QgsVectorLayerUtils.createFeature(self.__activLayer,
                                                                    geometry,
                                                                     attL,
                                                                     self.__activLayer.createExpressionContext()))
            self.__zaehlung()
            self.__writeAutoAttributeToSettigs()
            return features

    def __circle_geometry(self, pt, radius=0, segments=0):
        pts = []
        for i in range(segments):
            theta = i * (2.0 * math.pi / segments)
            p = [pt.x() + radius * math.cos(theta),
                         pt.y() + radius * math.sin(theta),pt.z()]
            pts.append(p)
        pts.append(pts[0])
        return pts #QgsGeometry.fromPolyline(pts)

    def __geometrycheck(self):
        #self.__dockwidget.butCreateFeature.setEnabled(False)
        value = False
        ##@ Polygongeometrie
        if self.__activLayer.geometryType() == 2 and len(self.__vertices) >= 3:
            #self.__dockwidget.butCreateFeature.setEnabled(True)
            value = True
        ##@ Liniengeometrie
        elif self.__activLayer.geometryType() == 1 and len(self.__vertices) >= 2:
            #self.__dockwidget.butCreateFeature.setEnabled(True)
            value = True
        ##@ Punktgeometrie
        elif self.__activLayer.geometryType() == 0 and len(self.__vertices) >= 1:
            #self.__dockwidget.butCreateFeature.setEnabled(True)
            value = True
        x = self.__dockwidget.cboFigur.currentIndex()

        if x >= 1 and len(self.__vertices) == 2:
            #self.__dockwidget.butCreateFeature.setEnabled(False)
            value = False
            if self.__activLayer.geometryType() == 0:
                iface.messageBar().pushMessage(u"T2G Archäologie: ", u"Auf Punktlayer nicht möglich.",
                                               level=Qgis.Info)
                #return
                value = False
            #self.__dockwidget.butCreateFeature.setEnabled(True)
        return value

    def __greateFeature(self,features):
        self.__activLayer.commitChanges()
        if features is None:
            #self.__koordtableClear()
            return
        self.__activLayer.commitChanges()
        nextFeatId = self.__activLayer.featureCount()
        self.__lastNewFeatures = []
        self.__activLayer.startEditing()

        for feat in features:
            feat.setId(nextFeatId)
            self.__activLayer.dataProvider().addFeatures([feat])
            #self.__activLayer.featureAdded.emit(nextFeatId)
            #self.__activLayer.attributeValueChanged.emit()
            nextFeatId += 1  # next id for multiple points
            self.__lastNewFeatures.append(feat.id())
        self.__activLayer.commitChanges()
        self.__messpunktAdd()
        self.__koordtableClear()
        self.__beep_AddGeometry()

        if self.__dockwidget.chbAttributtable.isChecked():
            self.__iface.actionSelectRectangle().trigger()
            self.__activLayer.startEditing()
            query = "$id >= " + str(self.__lastNewFeatures [0])
            box = self.__iface.showAttributeTable(self.__activLayer, query)
            box.exec_()
        self.__activLayer.commitChanges()
        self.__iface.mapCanvas().setMapTool(self.__canvas_clicked)
        mapCanvasRefresh()
        # Attributwerte in __config schreiben
        self.__writeAutoAttributeToSettigs()
        self.__lastMeasurmentsAdd()

    def __zcheck(self):
        zh = []
        for i in range(len(self.__vertices)):
            # QgsMessageLog.logMessage(str(item.text()), 'T2G Archäologie', Qgis.Info)
            zkoord = float(self.__vertices[i][2])
            zh.append(zkoord)
        QgsMessageLog.logMessage(str(min(zh)) + '  ' + str(max(zh)), '1', Qgis.Info)
        #diff = max(zh) - min(zh)
        #QgsMessageLog.logMessage(str(diff) , '1', Qgis.Info)
        if min(zh) == 0 :
           msgBox = QMessageBox()
           msgBox.setIcon(QMessageBox.Information)
           msgBox.setText("Geometrie enthält Nullhöhen. Fortfahren?")
           #msgBox.setWindowTitle("QMessageBox Example")
           msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
           #msgBox.buttonClicked.connect(msgButtonClick)

           returnValue = msgBox.exec()
           if returnValue == QMessageBox.Ok:
               return True
           else:
               return False



    def __keyPress(self, key):
        if key == Qt.Key_Enter or key == Qt.Key_Return:
            self.__geometryIdentify()
        elif key == Qt.Key_L:
            self.__koordtableClear()
        elif key == Qt.Key_Z:
            row = self.__verticesCount-1
            self.__delVertex()
            self.__dockwidget.tableWidget.selectRow(row)
        elif key == Qt.Key_K:
            self.__dockwidget.tabWidget.setCurrentIndex(1)
        elif key == Qt.Key_A:
            self.__dockwidget.tabWidget.setCurrentIndex(0)
        elif key == Qt.Key_M:
            self.__mesurementsShow()

    def __fillcboobjTyp(self):
        self.__dockwidget.cboFigur.setCurrentIndex(0)  # auf freie Geometry schalten
        if self.__activLayer.name() == 'E_Point' or self.__activLayer.name() == 'E_Line':
            self.__dockwidget.cboFigur.setCurrentIndex(0)
            self.__dockwidget.cboFigur.model().item(1).setEnabled(False)
            self.__dockwidget.cboFigur.model().item(2).setEnabled(False)
            self.__dockwidget.cboFigur.model().item(3).setEnabled(False)
        else:
            self.__dockwidget.cboFigur.model().item(1).setEnabled(True)
            self.__dockwidget.cboFigur.model().item(2).setEnabled(True)
            self.__dockwidget.cboFigur.model().item(3).setEnabled(True)
        self.__dockwidget.cboobjTyp.clear()
        if self.__activLayer.name() == 'E_Point':
            swert='Punkt'
        else:
            swert='Linie'
        self.__dockwidget.cboobjTyp.addItem('')
        self.__dockwidget.cboobjTyp.addItems(csvListfilter(os.path.join(self.__projPfad, 'Listen\Objekttypen.csv'), 0, 4, swert,''))

    def __fillcboobjArt(self):
        swert = '|' + self.__dockwidget.cboobjTyp.currentText() + '|'
        self.__dockwidget.cboobjArt.clear()
        self.__dockwidget.cboMaterial.clear()
        self.__dockwidget.cboobjArt.addItem('')
        self.__dockwidget.cboMaterial.addItem('')
        if self.__activLayer.name() == 'E_Point':
            self.__dockwidget.cboobjArt.addItems(csvListfilter(os.path.join(self.__projPfad ,'Listen\Objektarten.csv'), 0, 1, swert,''))
        else:
            self.__dockwidget.cboobjArt.addItems(csvListfilter(os.path.join(self.__projPfad, 'Listen\Objektarten.csv'), 0, 1, swert,''))
        self.__dockwidget.cboMaterial.addItems(csvListfilter(os.path.join(self.__projPfad, 'Listen\Material.csv'), 0, 1, swert,''))

    def __delAutoAttribut(self):
        self.__dockwidget.cboobjTyp.setCurrentText('')
        self.__dockwidget.cboobjArt.setCurrentText('')
        self.__dockwidget.txtSchnittNr.setText('')
        self.__dockwidget.txtBefNr.setText('')
        self.__dockwidget.txtPlanum.setText('')
        self.__dockwidget.txtFundNr.setText('')
        self.__dockwidget.txtProbeNr.setText('')
        self.__dockwidget.txtProfilNr.setText('')
        self.__dockwidget.txtptnr.setText('')
        self.__dockwidget.cboMaterial.setCurrentText('')
        self.__dockwidget.chbbefZ.setChecked(False)
        self.__dockwidget.chbFundZ.setChecked(False)
        self.__dockwidget.chbProfZ.setChecked(False)
        self.__dockwidget.chbProbeZ.setChecked(False)
        self.__dockwidget.chbptnrZ.setChecked(False)

    def __closeEvent(self):
        if self.__config is not None:
            self.__config.saveFile()
        self.__t2gInstance.dlg.close()

    def __messpunktAdd(self):
        features = []
        layer = QgsProject.instance().mapLayersByName('Messpunkte')[0]
        layer.startEditing()
        aktdate = str(date.today())
        for i in range(len(self.__vertices)):
            x = str(self.__vertices[i][0])
            y = str(self.__vertices[i][1])
            z = str(self.__vertices[i][2])
            uuId = '{' + str(uuid.uuid4()) + '}'
            attL = {1: aktdate, 4: x, 5: y, 6: z, 8: uuId}

            pt = QgsPoint(float(self.__vertices[i][0]), float(self.__vertices[i][1]), float(self.__vertices[i][2]))
            features.append(QgsVectorLayerUtils.createFeature(layer,
                                                                  QgsGeometry(pt),
                                                                  attL,
                                                                  layer.createExpressionContext()))
        nextFeatId = self.__activLayer.featureCount()
        for feat in features:
            feat.setId(nextFeatId)
            layer.dataProvider().addFeatures([feat])
            #self.__activLayer.featureAdded.emit(nextFeatId)
            nextFeatId += 1  # next id for multiple points
            QgsMessageLog.logMessage(str(x)+'|'+str(y)+'|'+str(z), 'Messpunkte', Qgis.Info)

        layer.commitChanges()

    def __autoAttributOnOff(self):
        if  self.__dockwidget.chbAutoAtt.isChecked():
            #self.__dockwidget.tabWidget.setTabVisible(0, True)
            self.__dockwidget.chbAutoAtt.setStyleSheet("color: red")

            self.__dockwidget.tabWidget.setCurrentIndex(0)
            setCustomProjectVariable('autoAttribute', 'True')
        else:
            #self.__dockwidget.tabWidget.setTabVisible(0, False)
            self.__dockwidget.chbAutoAtt.setStyleSheet("")

            setCustomProjectVariable('autoAttribute', 'False')

    def __setAutoAttributeToQgisVariable(self):
        setCustomProjectVariable('aktcode', self.__dockwidget.txtAkt.text())
        bol = 'True' if self.__dockwidget.chbAutoAtt.isChecked() else 'False'
        setCustomProjectVariable('autoAttribute', bol)
        setCustomProjectVariable('geo-arch', str(self.__dockwidget.cboArchGeo.currentText()))
        setCustomProjectVariable('obj_type', self.__dockwidget.cboobjTyp.currentText())
        setCustomProjectVariable('obj_art', self.__dockwidget.cboobjArt.currentText())
        setCustomProjectVariable('schnitt_nr', self.__dockwidget.txtSchnittNr.text())
        setCustomProjectVariable('bef_nr', self.__dockwidget.txtBefNr.text())
        setCustomProjectVariable('planum', self.__dockwidget.txtPlanum.text())
        setCustomProjectVariable('fund_nr', self.__dockwidget.txtFundNr.text())
        setCustomProjectVariable('prob_nr', self.__dockwidget.txtProbeNr.text())
        setCustomProjectVariable('prof_nr', self.__dockwidget.txtProfilNr.text())
        setCustomProjectVariable('ptnr', self.__dockwidget.txtptnr.text())
        setCustomProjectVariable('material', self.__dockwidget.cboMaterial.currentText())
        self.__nextValue() # naechste Nummer

    def __writeAutoAttributeToSettigs(self):
        sectionlist = ['AttPoint','AttLine','AttPoly']
        section = sectionlist[self.__activLayer.geometryType()]
        self.__config.updateValue('Projekt','aktivität', self.__dockwidget.txtAkt.text())
        self.__config.updateValue(section,'geoart', str(self.__dockwidget.cboFigur.currentIndex()))
        self.__config.updateValue(section,'tabelleVisible', str(self.__dockwidget.chbAttributtable.isChecked()))
        self.__config.updateValue(section,'autoAttrOnOff', str(self.__dockwidget.chbAutoAtt.isChecked()))
        self.__config.updateValue(section,'objecttyp', self.__dockwidget.cboobjTyp.currentText())
        self.__config.updateValue(section,'objectart', self.__dockwidget.cboobjArt.currentText())
        self.__config.updateValue(section,'schnitt', self.__dockwidget.txtSchnittNr.text())
        self.__config.updateValue(section,'planum', self.__dockwidget.txtPlanum.text())
        self.__config.updateValue(section,'befnr', self.__dockwidget.txtBefNr.text())
        self.__config.updateValue(section,'fundnr', self.__dockwidget.txtFundNr.text())
        self.__config.updateValue(section,'profilnr', self.__dockwidget.txtProfilNr.text())
        self.__config.updateValue(section,'probenr', self.__dockwidget.txtProbeNr.text())
        self.__config.updateValue(section,'punktnr', self.__dockwidget.txtptnr.text())
        self.__config.updateValue(section,'material', self.__dockwidget.cboMaterial.currentText())
        self.__config.updateValue(section,'archgeo', str(self.__dockwidget.cboArchGeo.currentIndex()))

    def __readAutoAttributeToSettigs(self):
        sectionlist = ['AttPoint','AttLine','AttPoly']
        section = sectionlist[self.__activLayer.geometryType()]
        if self.__config is None:
            pass
        self.__dockwidget.txtAkt.setText(self.__config.getValue('Projekt',"aktivität",''))
        self.__dockwidget.cboFigur.setCurrentIndex(int(self.__config.getValue(section,"geoart",'0')))
        self.__dockwidget.chbAttributtable.setChecked(str2bool(self.__config.getValue(section,"tabelleVisible",'True')))
        self.__dockwidget.chbAutoAtt.setChecked(str2bool(self.__config.getValue(section,"autoAttrOnOff",'True')))
        self.__dockwidget.cboobjTyp.setCurrentText(self.__config.getValue(section,"objecttyp",''))
        self.__dockwidget.cboobjArt.setCurrentText(self.__config.getValue(section,"objectart",''))
        self.__dockwidget.txtSchnittNr.setText(self.__config.getValue(section,"schnitt",''))
        self.__dockwidget.txtPlanum.setText(self.__config.getValue(section,"planum",''))
        self.__dockwidget.txtBefNr.setText(self.__config.getValue(section,"befnr",''))
        self.__dockwidget.txtFundNr.setText(self.__config.getValue(section,"fundnr",''))
        self.__dockwidget.txtProfilNr.setText(self.__config.getValue(section,"profilnr",''))
        self.__dockwidget.txtProbeNr.setText(self.__config.getValue(section,"probenr",''))
        self.__dockwidget.txtptnr.setText(self.__config.getValue(section,"punktnr",''))
        self.__dockwidget.cboMaterial.setCurrentText(self.__config.getValue(section,"material",''))
        self.__dockwidget.cboArchGeo.setCurrentIndex(int(self.__config.getValue(section,"archgeo",'0')))

    # Naechster Unterwert (z.bsp. 2_1,2_2,2_3)
    def __zaehlung(self):
        dlg = self.__dockwidget
        if dlg.chbbefZ.isChecked() and dlg.txtBefNr.text() != '':
            x = dlg.txtBefNr.text().split('_')
            s1 = ''
            for i in range(len(x)-1):
                s1 = s1 + x[i]+'_'
            dlg.txtBefNr.setText(s1 + str(int(x[len(x)-1])+1))
        if dlg.chbFundZ.isChecked() and dlg.txtFundNr.text() != '':
            x = dlg.txtFundNr.text().split('_')
            s1 = ''
            for i in range(len(x)-1):
                s1 = s1 + x[i]+'_'
            dlg.txtFundNr.setText(s1 + str(int(x[len(x)-1])+1))

        if dlg.chbProfZ.isChecked() and dlg.txtProfilNr.text() != '':
            x = dlg.txtProfilNr.text().split('_')
            s1 = ''
            for i in range(len(x)-1):
                s1 = s1 + x[i]+'_'
            dlg.txtProfilNr.setText(s1 + str(int(x[len(x)-1])+1))

        if dlg.chbProbeZ.isChecked() and dlg.txtProbeNr.text() != '':
            x = dlg.txtProbeNr.text().split('_')
            s1 = ''
            for i in range(len(x)-1):
                s1 = s1 + x[i]+'_'
            dlg.txtProbeNr.setText(s1 + str(int(x[len(x)-1])+1))

        if dlg.chbptnrZ.isChecked() and dlg.txtptnr.text() != '':
            x = dlg.txtptnr.text().split('_')
            s1 = ''
            for i in range(len(x)-1):
                s1 = s1 + x[i]+'_'
            dlg.txtptnr.setText(s1 + str(int(x[len(x)-1])+1))
    # Naechster Wert (z.bsp. 1,2,3)
    def __nextValue(self):
        dlg = self.__dockwidget
        #if self.__dockwidget.chbAutoAtt.isChecked():
        #    dlg = self.__dockwidget
        if dlg.txtBefNr.text() != '':
            try:
                if int(dlg.txtBefNr.text()) >= int(dlg.txtNextBef.text()) and not '_' in dlg.txtBefNr.text():
                    dlg.txtNextBef.setText(str(int(dlg.txtBefNr.text())+1))
            except:pass
        if dlg.txtFundNr.text() != '':
            try:
                if int(dlg.txtFundNr.text()) >= int(dlg.txtNextFund.text() and not '_' in dlg.txtFundNr.text()):
                    dlg.txtNextFund.setText(str(int(dlg.txtFundNr.text())+1))
            except:pass
        if dlg.txtProfilNr.text() != '':
            try:
                if int(dlg.txtProfilNr.text()) >= int(dlg.txtNextProf.text() and not '_' in dlg.txtProfilNr.text()):
                    dlg.txtNextProf.setText(str(int(dlg.txtProfilNr.text())+1))
            except:pass
        if dlg.txtProbeNr.text() != '':
            try:
                if int(dlg.txtProbeNr.text()) >= int(dlg.txtNextProb.text() and not '_' in dlg.txtProbeNr.text()):
                    dlg.txtNextProb.setText(str(int(dlg.txtProbeNr.text())+1))
            except:pass


    def __tips(self):
        pfad = os.path.join(os.path.dirname(__file__), 'Tips.htm')

        #self.__dialogMeldung.setText(pfad)
        self.__dialogMeldung.run(pfad,None,280,300)

    def __setAbbruch(self):
        self.__abbruch = True
        iface.messageBar().clearWidgets()

    def __befundLabel_n(self):
        self.__abbruch = False
        iface.messageBar().clearWidgets()
        widgetMessage = iface.messageBar().createMessage('Befundlabel setzen abrechen.')
        button = QPushButton(widgetMessage)
        button.setText("Abbruch")
        button.pressed.connect(self.__setAbbruch)
        widgetMessage.layout().addWidget(button)
        iface.messageBar().pushWidget(widgetMessage, Qgis.Info)

        self.__dockwidget.butBefundLabel.setStyleSheet("border-style: outset ; border-width: 3px ; border-color: green")

        self.__setPointlayerActiv()
        self.__delAutoAttribut()
        self.__koordtableClear()
        self.__dockwidget.chbAutoAtt.setChecked(True)
        self.__dockwidget.chbAttributtable.setChecked(False)
        self.__dockwidget.chbbefZ.setChecked(False)
        self.__dockwidget.cboobjTyp.setCurrentText('Kartenbeschriftung')
        self.__dockwidget.cboobjArt.setCurrentText('Befund')
        self.__dockwidget.txtBefNr.setText('')
        #return
        var = 0
        while self.__abbruch == False:
            if not self.__dockwidget.chbbefZ.isChecked():
                while self.__verticesCount == 0:
                    QApplication.processEvents()
                    pass
                if self.__abbruch == True:
                    break
                self.__watchEvent()
                befnr, ok = QInputDialog().getText(None, '', 'Befund Nr. eingeben')
                if ok:
                    self.__dockwidget.txtBefNr.setText(befnr)
                    self.__geometryIdentify()
                    if not self.__dockwidget.chbbefZ.isChecked() and var == 0:
                        box = QMessageBox()
                        box.setIcon(QMessageBox.Question)
                        box.setText('Soll die Befundnummer hochgezählt werden?')
                        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                        buttonY = box.button(QMessageBox.Yes)
                        buttonY.setText('Ja')
                        buttonN = box.button(QMessageBox.No)
                        buttonN.setText('Nein')
                        box.exec_()
                        var = 1
                        if box.clickedButton() == buttonY:
                            self.__dockwidget.chbbefZ.setChecked(True)
                            self.__dockwidget.txtBefNr.setText(str(int(befnr)+1))
                else:
                    self.__abbruch = True
                    iface.messageBar().popWidget()
            QApplication.processEvents()
        self.__dockwidget.butBefundLabel.setStyleSheet("")

    def make_wkt(self, vertices):
        if ('Z' or 'M') not in self.__wkbTypeName[-2:]:
            vertexts = [f'({v[0]} {v[1]})' for v in vertices]
        elif self.__wkbTypeName[-2:] == 'ZM':
            vertexts = [f'{v[0]} {v[1]} {v[2]} {0.0}' for v in vertices]
        elif self.__wkbTypeName[-1] == 'M':
            vertexts = [f'({v[0]} {v[1]} {0.0})' for v in vertices]
        else:
            vertexts = [f'({v[0]} {v[1]} {v[2]})' for v in vertices]
        if self.__isMulti:
            wkt = '{0}({1})))'.format(self.__wkbTypeName + '((', ', '.join(vertexts))
        else:
            wkt = []
            for v in vertexts:
                wkt.append('{0}{1}'.format(self.__wkbTypeName, v))
        QgsMessageLog.logMessage(str(wkt), 'T2G Archäologie', Qgis.Info)
        return wkt


class ClickedPoint(QgsMapTool):

    keyPressSignal = pyqtSignal(int)

    def __init__(self,canvas,dlg):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.dlg = dlg
        self.l = iface.activeLayer()
        self.i = QgsSnapIndicator(self.canvas)
        self.u = self.canvas.snappingUtils()
        self.mouseInfoOn = False
        self.begMouseInfo = False
        self.attrList = []
        toolTipWidget = QLabel()
        toolTipWidget.setFrameShape(QFrame.StyledPanel)
        toolTipWidget.setWindowFlags(QtCore.Qt.ToolTip)
        toolTipWidget.setWindowOpacity(0.7)
        toolTipWidget.hide()
        self.toolTipWidget = toolTipWidget

        self.activated.connect(self.setMouseInfoVisibleTrue)
        self.deactivated.connect(self.setMouseInfoVisibleFalse)

    def setMouseInfoText(self,text):
        self.mouseInfoText = text
        self.toolTipWidget.setText(self.mouseInfoText)

    def setMouseInfoOnOff(self,onOff):
        self.mouseInfoOn = onOff

    def setMouseInfoVisibleTrue(self):
        #self.toolTipWidget.show()
        pass

    def setMouseInfoVisibleFalse(self):
        self.toolTipWidget.hide()

    def canvasMoveEvent( self, e ):
        m = self.u.snapToMap(e.pos())
        self.i.setMatch(m)
        try:
            point = self.toMapCoordinates(self.canvas.mouseLastXY())
            point = e.originalMapPoint()
            point = e.snapPoint()
            #self.dlg.activateWindow()
            self.dlg.txtPointTemp_2.setText(str(point.x())+','+str(point.y()))
        except:
            pass
        if self.mouseInfoOn:
            self.showToolTip(e.originalMapPoint())
            pass

    def showToolTip(self,point):

        pointx = str(round(point.x(),3))
        pointy = str(round(point.y(),3))
        #bz = ''
        info = ("Typ:&nbsp;&nbsp;&nbsp;&nbsp;<font color =BLACK><b>" + self.dlg.cboobjTyp.currentText() + "</font color =BLACK><\b><br/>" +
                "Art:&nbsp;&nbsp;&nbsp;&nbsp;<font color =BLACK><b>" + self.dlg.cboobjArt.currentText() + "</font color =BLACK><\b><br/>" +
                "Schnitt: <font color =BLACK><b>" + self.dlg.txtSchnittNr.text() + "</font color =BLACK><\b>" +
                    " | Planum: <font color =BLACK><b>" + self.dlg.txtPlanum.text() + "</font color =BLACK><\b><br/>"
                "<font color =RED><b>" + 'A' +' ' "</font color =RED><\b>" +
                    "<font color =RED><b>" + 'Z' +'&ensp;' "</font color =RED><\b>" +
                        "Befund: <font color =BLACK><b>" + self.dlg.txtBefNr.text() + "</font color =BLACK><\b><br/>" +
                "<font color =RED><b>" + 'A' +' ' "</font color =RED><\b>" +
                    "<font color =RED><b>" + 'Z' +'&ensp;' "</font color =RED><\b>" +
                        "Fund: <font color =BLACK><b>" + self.dlg.txtFundNr.text() + "</font color =BLACK><\b><br/>" +
                "<font color =RED><b>" + 'A' +' ' "</font color =RED><\b>" +
                    "<font color =RED><b>" + 'Z' +'&ensp;' "</font color =RED><\b>" +
                        "Profil: <font color =BLACK><b>" + self.dlg.txtProfilNr.text() + "</font color =BLACK><\b><br/>" +
                "<font color =RED><b>" + 'A' +' ' "</font color =RED><\b>" +
                    "<font color =RED><b>" + 'Z' +'&ensp;' "</font color =RED><\b>" +
                        "Probe: <font color =BLACK><b>" + self.dlg.txtProbeNr.text() + "</font color =BLACK><\b><br/>" +
                "<font color =RED><b>" + 'A' +' ' "</font color =RED><\b>" +
                    "<font color =RED><b>" + 'Z' +'&ensp;' "</font color =RED><\b>" +
                        "PunktNr: <font color =BLACK><b>" + self.dlg.txtptnr.text() + "</font color =BLACK><\b><br/>" +
                "<font color =BLUE><b>" + 'x:&ensp;' + pointx + "</font color =BLUE><\b><br/>" +
                "<font color =BLUE><b>" + 'y:&ensp;' + pointy + "</font color =BLUE><\b>")

        self.setMouseInfoText(info)
        self.toolTipWidget.show()
        if self.canvas.underMouse():
            p = self.canvas.mapToGlobal( self.canvas.mouseLastXY() )
            #self.toolTipWidget.setText(info)
            self.toolTipWidget.move(p + QtCore.QPoint(5, 5))
            self.toolTipWidget.adjustSize()
            self.toolTipWidget.show()
        else:
            self.toolTipWidget.hide()

    def canvasPressEvent( self, e ):
        #try:
        point = e.snapPoint()
        p1 = QgsPoint(point.x(), point.y())
        #point3d = self.toLayerCoordinates(e.originalMapPoint())
        #self.dlg.activateWindow()
        #self.dlg.txtPoint_2.setText(str(point3d.x())+','+str(point3d.y())+','+str(point3d.z()))
        self.dlg.txtPoint_2.setText(str(point.x())+','+str(point.y()))
        #except Exception:
        #QgsMessageLog.logMessage(str(Exception), 'T2G Archäologie', Qgis.Info)
        #    pass
        #QgsMessageLog.logMessage(str(point), 'T2G Archäologie', Qgis.Info)
    def canvasClicked( self, point, button):
        QgsMessageLog.logMessage(str(point), 'T2G Archäologie', Qgis.Info)

    def keyPressEvent(self, event):
        self.keyPressSignal.emit(event.key())
