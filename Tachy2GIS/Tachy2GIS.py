# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Tachy2Gis
                                 A QGIS plugin
 This plugin allows to create geometries directly with a connected tachymeter
                              -------------------
        begin                : 2017-11-26
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Christian Trapp
        email                : mail@christiantrapp.net
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from cmath import log
from os.path import basename
from unittest import result

#from T2G.gc_constants import TMC_DoMeasure
from . import resources
"""
import pydevd
try:
    pydevd.settrace('localhost',
                    port=6565,
                    stdoutToServer=True,
                    stderrToServer=True,
                    suspend=False)
except ConnectionRefusedError:
    pass
"""
import os, sys, glob
import gc as garbagecollector
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import QAction, QHeaderView, QDialog, QFileDialog, QSizePolicy, QVBoxLayout, QLineEdit,\
    QPushButton, QProgressDialog, QProgressBar, qApp, QLabel
from PyQt5.QtCore import QSettings, QItemSelectionModel, QTranslator, QCoreApplication, QThread, qVersion, Qt,\
    QEvent, QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
from qgis.utils import iface
from qgis.core import Qgis, QgsMapLayerProxyModel, QgsProject, QgsMapLayerType, QgsWkbTypes, QgsLayerTreeGroup,\
    QgsLayerTreeLayer, QgsGeometry, QgsVectorDataProvider, QgsFeature, QgsExpression, QgsExpressionContext, QgsExpressionContextUtils , \
    QgsVectorLayer
from qgis.gui import QgsMapToolPan

import vtk
from PyQt5 import QtCore, QtWidgets

from .T2G.TachyReader import AvailabilityWatchdog
from .FieldDialog import FieldDialog
from .Tachy2GIS_dialog import Tachy2GisDialog
# from .T2G.autoZoomer import ExtentProvider, AutoZoomer
from .T2G.geo_com import connect_beep
from .T2G.visualization import VtkWidget, VtkMouseInteractorStyle, VtkPointCloudLayer

from tachyconnect.ReplyHandler import ReplyHandler
from tachyconnect.ts_control import MessageQueue, Dispatcher, CommunicationConstants
from tachyconnect.GSI_Parser import make_vertex
from tachyconnect.TachyRequest import TMC_GetCoordinate, TMC_DoMeasure, TMC_GetHeight, TMC_SetHeight
from tachyconnect.TachyJoystick import TachyJoystick
import tachyconnect.gc_constants as gc

def make_axes_actor(scale, xyzLabels):
    axes = vtk.vtkAxesActor()
    axes.SetScale(scale[0], scale[1], scale[2])
    axes.SetShaftTypeToCylinder()
    axes.SetXAxisLabelText(xyzLabels[0])
    axes.SetYAxisLabelText(xyzLabels[1])
    axes.SetZAxisLabelText(xyzLabels[2])
    axes.SetCylinderRadius(0.5 * axes.GetCylinderRadius())
    axes.SetConeRadius(1.025 * axes.GetConeRadius())
    axes.SetSphereRadius(1.5 * axes.GetSphereRadius())
    tprop = axes.GetXAxisCaptionActor2D().GetCaptionTextProperty()
    tprop.ItalicOn()
    tprop.ShadowOn()
    tprop.SetFontFamilyToTimes()
    # Use the same text properties on the other two axes.
    axes.GetYAxisCaptionActor2D().GetCaptionTextProperty().ShallowCopy(tprop)
    axes.GetZAxisCaptionActor2D().GetCaptionTextProperty().ShallowCopy(tprop)
    return axes


class Tachy2Gis:
    NO_PORT = 'Select tachymeter USB port'
    REF_HEIGHT_PAUSED = '🟠'
    REF_HEIGHT_DISCONNECTED = '🔴'
    REF_HEIGHT_IDLE = '🟡'
    REF_HEIGHT_CONNECTED = '🟢'
    REF_HEIGHT_CHANGED = '⚠️'
    SERIAL_CONNECTED = '🔗'

    """QGIS Plugin Implementation."""
    # Custom methods go here:

    ## Constructor
    #  @param iface An interface instance that will be passed to this class
    #  which provides the hook by which you can manipulate the QGIS
    #  application at run time.
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Tachy2Gis_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&Tachy2GIS')
        # remove empty toolbar
        # self.toolbar = self.iface.addToolBar('Tachy2Gis')
        # self.toolbar.setObjectName('Tachy2Gis')

        # From here: Own additions
        self.dlg = Tachy2GisDialog()
        self.vtk_mouse_interactor_style = VtkMouseInteractorStyle()
        self.render_container_layout = QVBoxLayout()
        self.markerWidget = vtk.vtkOrientationMarkerWidget()
        self.vtk_widget = VtkWidget(self.dlg.vtk_frame)
        self.vtk_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.render_container_layout.addWidget(self.vtk_widget)
        self.dlg.vtk_frame.setLayout(self.render_container_layout)
        # The interactorStyle is instantiated explicitly so it can be connected to
        # events
        self.vtk_widget.SetInteractorStyle(self.vtk_mouse_interactor_style)
        self.vtk_mouse_interactor_style.SetCurrentRenderer(self.vtk_widget.renderer)
        # Setup axes
        self.markerWidget.SetOrientationMarker(self.vtk_widget.axes)
        self.markerWidget.SetInteractor(self.vtk_widget.renderer.GetRenderWindow().GetInteractor())
        self.markerWidget.SetViewport(0.0, 0.0, 0.1, 0.3)
        self.markerWidget.EnabledOn()
        self.markerWidget.InteractiveOff()

        self.reply_handler = ReplyHandler()
        self.dispatcher = Dispatcher(MessageQueue(1),
                                     MessageQueue(7),
                                     self.reply_handler)
        # self.reply_handler.register_command(TMC_GetCoordinate, self.coordinates_received)
        # self.reply_handler.register_command(TMC_DoMeasure, self.request_coordinates)
        # self.reply_handler.register_command(TMC_GetHeight, self.dlg_set_ref_height)


        #tachyJoystick
        self.tachy_joystick_dlg = TachyJoystick(self.dispatcher, self.dlg, Qt.Dialog | Qt.Tool)
        # custom QLineEdit
        self.refHeightLineEdit = SignalizingLineEdit()
        self.refHeightLineEdit.hide()
        self.refHeightLineEdit.setMinimumSize(50, 26)
        self.refHeightLineEdit.setMaximumSize(50, 26)
        self.refHeightLineEdit.setToolTip(self.tr("Reflektorhöhe eingeben und mit Enter bestätigen"))

        # label for Refheight status
        self.refHeightStatusLabel = QLabel()
        self.refHeightStatusLabel.hide()
        self.refHeightStatusLabel.setAlignment(Qt.AlignCenter)
        self.refHeightStatusLabel.setMinimumSize(26, 26)
        self.refHeightStatusLabel.setMaximumSize(26, 26)
        self.refHeightStatusLabel.setText(self.REF_HEIGHT_DISCONNECTED)
        self.refHeightStatusLabel.setToolTip(self.tr("Zeigt an, ob die Reflektorhöhe ausgelesen wird"))

        self.availability_watchdog = AvailabilityWatchdog()
        self.dlg.zoomModeComboBox.addItems([self.tr('Letzter Punkt'),
                                            self.tr('Layer'),
                                            self.tr('Letztes feature'),
                                            self.tr('Letzte 2 features'),
                                            self.tr('Letzte 4 features'),
                                            self.tr('Letzte 8 features'),
                                            self.tr('Aus')
                                            ])

        self.refHeightStatus = RefHeightStatus()
        self.refHeightPollingThread = QThread()
        self.refHeightStatus.moveToThread(self.refHeightPollingThread)

        # self.pollingThread = QThread()
        # self.tachyReader.moveToThread(self.pollingThread)
        # self.pollingThread.start()
        self.pluginIsActive = False

    def request_coordinates(self, *args):
        self.dispatcher.send(TMC_GetCoordinate(args=('1000', '1')).get_geocom_command())

    def coordinates_received(self, *args):
        print("Args: ", args)
        log_file_name = self.dlg.select_log_file.toolTip()
        if log_file_name and not log_file_name.startswith('Log-Datei'):
            with open(log_file_name, 'a') as log_file:
                log_file.write(f"{str(args)}\n")
        retcode = int(args[0])

        if retcode == gc.GRC_OK:
            # %R1P,0,0:RC,E[double],N[double],H[double],CoordTime[long],
            # E-Cont[double],N-Cont[double],H-Cont[double],CoordContTime[long]
            new_vtx = list(map(float, args[1:4]))

            self.vtk_mouse_interactor_style.add_vertex(new_vtx)
            self.dlg.coords.setText(f"{new_vtx}")
            self.vtk_mouse_interactor_style.draw()
            self.autozoom(0)
        else:
            message = gc.MESSAGES[retcode]
            self.dlg.coords.setText(message)
            iface.messageBar().pushMessage(self.tr("Warnung: "), self.tr(f"Tachy Fehler: {message}"), Qgis.Warning, 10)

        #self.dispatcher.send(TMC_DoMeasure(args=(gc.TMC_MEASURE_PRG.TMC_CLEAR, gc.TMC_INCLINE_PRG.TMC_AUTO_INC)).get_geocom_command())

    def trigger_measurement(self):
        self.dispatcher.send(TMC_DoMeasure(args=(gc.TMC_MEASURE_PRG.TMC_DEF_DIST.value, gc.TMC_INCLINE_PRG.TMC_AUTO_INC.value)).get_geocom_command())

    def vertex_received(self, line):
        print(line)
        if line.startswith(CommunicationConstants.GEOCOM_REPLY_PREFIX):
                return
        log_file_name = self.dlg.select_log_file.toolTip()
        if log_file_name and not log_file_name.startswith('Log-Datei'):
            with open(log_file_name, 'a') as log_file:
                log_file.write(line)
        new_vtx = make_vertex(line)
        self.vtk_mouse_interactor_style.add_vertex(new_vtx)
        self.dlg.coords.setText(f"{new_vtx}")
        self.vtk_mouse_interactor_style.draw()
        self.autozoom(0)

    def tachy_connected(self, text, portName):
        if self.availability_watchdog.pollingTimer.isActive():
            self.availability_watchdog.shutDown()
        self.dlg.tachy_connect_button.setText(text)
        self.dlg.tachy_connect_button.setToolTip(self.tr(f"Verbunden mit {portName}"))
        self.refHeightStatusLabel.setText(self.REF_HEIGHT_CONNECTED)
        # show controls
        self.refHeightLineEdit.show()
        self.refHeightStatusLabel.show()
        self.dlg.tachyJoystick.show()
        # start requesting reflector height
        self.refHeightStatus.start()

    def tachy_disconnected(self, text, portName):
        if not self.availability_watchdog.pollingTimer.isActive():
            self.availability_watchdog.start()
        self.dlg.tachy_connect_button.setText(text)
        self.dlg.tachy_connect_button.setToolTip(self.tr("Keine Verbindung"))
        self.refHeightStatusLabel.setText(self.REF_HEIGHT_DISCONNECTED)
        # hide controls when disconnected
        self.refHeightLineEdit.hide()
        self.refHeightStatusLabel.hide()
        self.dlg.tachyJoystick.hide()
        # stop requesting reflector height
        self.refHeightStatus.stop()

    def tachy_available(self, text):
        self.dlg.tachy_connect_button.setText(text)
        self.dlg.tachy_connect_button.setToolTip(self.tr("Tachy verbinden"))

    def dump(self):
        vertices = self.vtk_mouse_interactor_style.vertices
        if len(vertices) == 0:
            iface.messageBar().pushMessage(self.tr("Fehler: "), self.tr("Keine Punkte vorhanden!"), Qgis.Warning, 5)
            return

        targetLayer = self.dlg.targetLayerComboBox.currentLayer()
        vtk_layer = self.vtk_widget.layers[targetLayer.id()]
        if vtk_layer.add_feature(vertices) == -1:
            return
        # clear picked vertices and remove them from renderer
        self.vtk_mouse_interactor_style.vertices = []
        self.vtk_mouse_interactor_style.draw()
        # remove vtk layer and update renderer
        self.rerenderVtkLayer([targetLayer.id()])
        self.autozoom(self.dlg.zoomModeComboBox.currentIndex())

    # Used after dump and layerRemoved/added signal which return the layer ids as list
    # featuresDeleted returns feature ids (int) instead of layer id so activeLayer().id() is used
    def rerenderVtkLayer(self, layerIds=(0,)):
        # todo: featureAdded triggering for every feature added, calling update_renderer multiple times on save
        # featureAdded
        if isinstance(layerIds, int):
            layerIds = [layerIds]
        # featuresDeleted
        if isinstance(layerIds[0], int):
            if type(self.vtk_widget.layers[iface.activeLayer().id()].vtkActor) == tuple:
                for actor in self.vtk_widget.layers[iface.activeLayer().id()].vtkActor:
                    self.vtk_widget.renderer.RemoveActor(actor)
            else:
                self.vtk_widget.renderer.RemoveActor(self.vtk_widget.layers[iface.activeLayer().id()].vtkActor)
            self.vtk_widget.layers.pop(iface.activeLayer().id())
            self.update_renderer()
            return
        # legendLayersAdded/ layerRemoved
        for layerId in layerIds:
            if layerId in self.vtk_widget.layers:
                if type(self.vtk_widget.layers[layerId].vtkActor) == tuple:
                    for actor in self.vtk_widget.layers[layerId].vtkActor:
                        self.vtk_widget.renderer.RemoveActor(actor)
                else:
                    self.vtk_widget.renderer.RemoveActor(self.vtk_widget.layers[layerId].vtkActor)
                self.vtk_widget.layers.pop(layerId)
        self.update_renderer()

    # Disconnect Signals and stop QThreads
    def onCloseCleanup(self):
        self.vtk_widget.renderer.GetRenderWindow().Finalize()  # Renderer does not crash anymore after plugin reload
        self.dlg.closingPlugin.disconnect(self.onCloseCleanup)
        # disconnect setupControls
        self.dlg.tachy_connect_button.clicked.disconnect()
        self.dlg.select_log_file.clicked.disconnect()
        self.dlg.dumpButton.clicked.disconnect()
        self.dlg.traceButton.clicked.disconnect()
        self.dlg.deleteVertexButton.clicked.disconnect()
        self.vtk_mouse_interactor_style.point_added.signal.disconnect(self.point_added)
        #self.dlg.setRefHeight.returnPressed.disconnect()
        self.dlg.zoomResetButton.clicked.disconnect()
        self.availability_watchdog.serial_available.disconnect()
        self.dlg.loadPointCloud.clicked.disconnect()
        self.dlg.sourceLayerComboBox.layerChanged.disconnect()
        self.dlg.targetLayerComboBox.layerChanged.disconnect()
        self.dlg.zoomModeComboBox.activated.disconnect(self.autozoom)
        QgsProject.instance().layerTreeRoot().visibilityChanged.disconnect(self.update_renderer)
        QgsProject.instance().legendLayersAdded.disconnect(self.rerenderVtkLayer)
        QgsProject.instance().legendLayersAdded.disconnect(self.connectAddedMapLayers)
        QgsProject.instance().layersRemoved.disconnect(self.rerenderVtkLayer)
        self.disconnectMapLayers()
        # self.dlg.request_mirror.clicked.disconnect()
        # self.dlg.deleteAllButton.clicked.disconnect()
        # self.vertexList.layoutChanged.disconnect()

        self.dispatcher.non_requested_data.disconnect()

        self.availability_watchdog.shutDown()
        self.dispatcher.stop()
        self.refHeightStatus.stop()
        # todo?: needed?
        self.refHeightPollingThread.quit()
        self.pluginIsActive = False
        garbagecollector.collect()
        print('Signals disconnected!')

    # switch target layer to source layer when changing source layer
    def switchTargetLayer(self):
        self.dlg.targetLayerComboBox.setLayer(self.dlg.sourceLayerComboBox.currentLayer())

    def setActiveLayer(self):
        if Qt is None:
            return
        activeLayer = self.dlg.targetLayerComboBox.currentLayer()
        if activeLayer is None:
            return
        self.iface.setActiveLayer(activeLayer)

    # TODO: Remove?
    # def toggleEdit(self):
    #     iface.actionToggleEditing().trigger()

    def connectSerial(self):
        port = self.dlg.portComboBox.currentText()
        if not port == Tachy2Gis.NO_PORT:
            pass
            # TODO: How does tachyconnect handle this?
            # self.tachyReader.setPort(port)
            # connect_beep(port)

    # TODO: Log default path QgsProject.instance().homePath()?
    def set_log(self):
        logFileName = QFileDialog.getSaveFileName(None,
                                                  self.tr('Log-Datei speichern...'),
                                                  QgsProject.instance().homePath(),
                                                  'Text (*.txt)',
                                                  '*.txt')[0]
        self.dlg.select_log_file.setToolTip(logFileName)
        # self.tachyReader.setLogfile(logFileName)

    def dumpEnabled(self):
        verticesAvailable = (len(self.vtk_mouse_interactor_style.vertices) > 0)
        # Selecting a target layer while there are no vertices in the vertex list may cause segfaults. To avoid this,
        # the 'Dump' button is disabled as long there are none:
        self.dlg.dumpButton.setEnabled(verticesAvailable)

    def zoom_full_extent(self):
        canvas = iface.mapCanvas()
        canvas.zoomToFullExtent()
        canvas.refresh()

    def autozoom(self, *args):
        index = self.dlg.zoomModeComboBox.currentIndex()
        if index == 6: # Off
            return

        if self.dlg.sourceLayerComboBox.currentLayer() == self.dlg.targetLayerComboBox.currentLayer():
            current_layer = self.dlg.sourceLayerComboBox.currentLayer()
        else:
            current_layer = self.dlg.targetLayerComboBox.currentLayer()
        if current_layer is None:
            return
        if "⛅" in current_layer.name() and index == 1:
            self.vtk_widget.renderer.GetActiveCamera().SetViewUp(0, 1, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetPosition(0, 0, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetFocalPoint(0, 0, -1)
            self.vtk_widget.renderer.ResetCamera(*self.vtk_widget.layers[current_layer.id()].vtkActor.GetBounds())
            self.vtk_widget.renderer.GetRenderWindow().Render()
            self.vtk_widget.renderer.ResetCameraClippingRange()
            self.dlg.zoomModeComboBox.setCurrentIndex(1)
            return
        feats = [f for f in current_layer.getFeatures()]
        if index == 0:  # Track last point
            if self.dlg.zoomModeComboBox.currentIndex() == 0:
                if self.vtk_mouse_interactor_style.vertices:
                    self.vtk_widget.renderer.ResetCamera(self.vtk_mouse_interactor_style.vertices[-1][0],
                                                         self.vtk_mouse_interactor_style.vertices[-1][0],
                                                         self.vtk_mouse_interactor_style.vertices[-1][1],
                                                         self.vtk_mouse_interactor_style.vertices[-1][1],
                                                         self.vtk_mouse_interactor_style.vertices[-1][2],
                                                         self.vtk_mouse_interactor_style.vertices[-1][2])
                    self.vtk_widget.renderer.GetActiveCamera().Zoom(3)
                    self.vtk_widget.renderer.ResetCameraClippingRange()
                    self.vtk_widget.renderer.GetRenderWindow().Render()
        elif index == 1:  # Layer
            if not feats:
                return
            zVtx = []  # get zMin/zMax
            for feat in feats:
                for vtx in feat.geometry().vertices():
                    if not vtx.z() == vtx.z():  # 0 if nan
                        zVtx.append(0)
                        continue
                    zVtx.append(vtx.z())
            self.vtk_widget.renderer.GetActiveCamera().SetViewUp(0, 1, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetPosition(0, 0, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetFocalPoint(0, 0, -1)
            self.vtk_widget.renderer.ResetCamera(current_layer.extent().xMinimum(),
                                                 current_layer.extent().xMaximum(),
                                                 current_layer.extent().yMinimum(),
                                                 current_layer.extent().yMaximum(),
                                                 min(zVtx), max(zVtx))
            self.vtk_widget.renderer.ResetCameraClippingRange()
            self.vtk_widget.renderer.GetRenderWindow().Render()

        else:  # 1-8 last features
            if not feats:
                self.dlg.zoomModeComboBox.setCurrentIndex(1)
                self.autozoom(1)
                return
            featIds = [f.id() for f in feats]
            count = {2: 1,
                     3: 2,
                     4: 4,
                     5: 8}
            zoom_to = count[index]

            buffered = sorted(filter(lambda id: id < 0, featIds))
            to_focus = buffered[:zoom_to]
            remaining = zoom_to - len(to_focus)
            if remaining:
                to_focus += featIds[-remaining:]

            featIndices = [featIds.index(id) for id in to_focus]

            xMin, xMax, yMin, yMax, zVtx = [], [], [], [], []

            for idx in featIndices:
                xMin.append(feats[idx].geometry().boundingBox().xMinimum())
                yMin.append(feats[idx].geometry().boundingBox().yMinimum())
                xMax.append(feats[idx].geometry().boundingBox().xMaximum())
                yMax.append(feats[idx].geometry().boundingBox().yMaximum())
                for vtx in feats[idx].geometry().vertices():
                    if not vtx.z() == vtx.z():
                        zVtx.append(0)
                        continue
                    zVtx.append(vtx.z())
            self.vtk_widget.renderer.GetActiveCamera().SetViewUp(0, 1, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetPosition(0, 0, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetFocalPoint(0, 0, -1)
            self.vtk_widget.renderer.ResetCamera(min(xMin), max(xMax),
                                                 min(yMin), max(yMax),
                                                 min(zVtx), max(zVtx))
            self.vtk_widget.renderer.ResetCameraClippingRange()
            self.vtk_widget.renderer.GetRenderWindow().Render()

    def point_added(self):
        if self.dlg.zoomModeComboBox.currentIndex() == 0:
            self.autozoom()

    def set_tachy_button_text(self, txt):
        self.dlg.tachy_connect_button.text = txt

    # currently unused
    def resetVtkCamera(self):
        self.vtk_widget.renderer.ResetCamera()
        self.vtk_widget.renderer.GetRenderWindow().Render()

    # TODO: Other views?
    def resetVtkCameraTop(self):
        active_camera = self.vtk_widget.renderer.GetActiveCamera()
        active_camera.SetViewUp(0, 1, 0)
        active_camera.SetPosition(0, 0, 0)
        active_camera.SetFocalPoint(0, 0, -1)
        self.vtk_widget.renderer.ResetCamera(iface.mapCanvas().extent().xMinimum(),
                                             iface.mapCanvas().extent().xMaximum(),
                                             iface.mapCanvas().extent().yMinimum(),
                                             iface.mapCanvas().extent().yMaximum(),
                                             self.vtk_widget.renderer.ComputeVisiblePropBounds()[-2],
                                             self.vtk_widget.renderer.ComputeVisiblePropBounds()[-1])
        active_camera.Zoom(3)
        self.vtk_widget.renderer.ResetCameraClippingRange()
        self.vtk_widget.renderer.GetRenderWindow().Render()

    def setCoords(self, coord):
        self.dlg.coords.setText(*coord)

    # todo: old - remove
    def setRefHeight(self):
        pass
        #refHeight = self.dlg.setRefHeight.text()
        # self.tachyReader.setReflectorHeight(refHeight)

    def getRefHeight(self):
        # self.dlg.setRefHeight.setText(self.tachyReader.getRefHeight)
        pass

    # Testline XYZRGB: 32565837.246360727 5933518.657366993 2.063523623769514 255 255 255
    def loadPointCloud(self, cloudFileName=None):
        if not cloudFileName:
            cloudFileName = QFileDialog.getOpenFileName(None,
                                                        self.tr('PointCloud laden...'),
                                                        QgsProject.instance().homePath(),
                                                        'XYZRGB (*.xyz);;Text (*.txt)',
                                                        '*.xyz;;*.txt')[0]
            if cloudFileName == '':
                return
        progress = QProgressDialog(self.tr("Lade PointCloud..."), self.tr("Abbrechen"), 0, 0)
        progress.setWindowTitle(self.tr("PointCloud laden..."))
        progress.setCancelButton(None)
        progress.show()

        pcLayer = QgsVectorLayer("PointZ", "⛅ " + basename(cloudFileName), "memory")
        QgsExpressionContextUtils.setLayerVariable(pcLayer, 'cloud_path', cloudFileName)
        cloud_layer = VtkPointCloudLayer(cloudFileName, pcLayer)
        self.vtk_widget.layers[cloud_layer.id] = cloud_layer
        self.vtk_widget.renderer.AddActor(cloud_layer.vtkActor)
        self.vtk_widget.renderer.ResetCameraClippingRange()
        self.vtk_widget.renderer.GetRenderWindow().Render()
        QgsProject.instance().addMapLayer(pcLayer)
        del progress

    def setPickable(self):
        source_layer = self.dlg.sourceLayerComboBox.currentLayer()
        if source_layer is None:
            return
        for stuff in self.vtk_widget.layers.items():
            qgs_id, layer = stuff[:2]
            if len(stuff) > 2:
                raise ValueError(f"Too much stuff: {str(stuff)} in {str(self.vtk_widget.layers)}")
            if " ⛅   " + qgs_id in source_layer.id():
                layer.PickableOn()
                continue
            if source_layer.type() == QgsMapLayerType.RasterLayer:  # skip raster
                continue
            if source_layer.geometryType() == QgsWkbTypes.NullGeometry:  # excel sheet
                continue

            layer.set_pickability(qgs_id == source_layer.id())
            layer.set_highlight(qgs_id == source_layer.id())

        self.vtk_widget.refresh_content()

    def request_ref_height(self):
        self.dispatcher.send(TMC_GetHeight(args=()).get_geocom_command())

    # read reflector height
    def dlg_set_ref_height(self, *args):
        refHeight = f'{float(args[-1][:6]):<06}'
        retcode = int(args[0])
        if retcode == gc.GRC_OK:
            if self.refHeightLineEdit.text():
                # check if ref height changed
                if refHeight != self.refHeightLineEdit.text():
                    self.refHeightStatusLabel.setText(self.REF_HEIGHT_CHANGED)
                    iface.messageBar().pushMessage(self.tr("Warnung: "), self.tr("Reflektorhöhe wurde geändert!"), Qgis.Warning, 30)
                    # todo?: stop poll and wait for new input?
                    # give warning but show new ref height and continue
                    self.refHeightLineEdit.setText(refHeight)
                else:
                    if self.refHeightStatusLabel.text() == self.REF_HEIGHT_PAUSED:
                        self.refHeightStatusLabel.setText(self.REF_HEIGHT_IDLE)
                    else:
                        self.refHeightStatusLabel.setText(self.REF_HEIGHT_CONNECTED)
                        self.refHeightLineEdit.setText(refHeight)
            # put ref height into LineEdit if empty
            else:
                self.refHeightLineEdit.setText(f'{args[-1][:6]}')

        else:
            self.refHeightStatusLabel.setText(self.REF_HEIGHT_DISCONNECTED)
            iface.messageBar().pushMessage(self.tr("Warnung: "), self.tr(f"Tachy Fehler: {gc.MESSAGES[retcode]}"), Qgis.Warning, 10)

    # set reflector height on returnPressed
    def set_ref_height(self):
        try:
            refHeight = f"{float(self.refHeightLineEdit.text().replace(',', '.')):<06}"
            # format if user enters a single digit
            self.refHeightLineEdit.setText(refHeight)
        except:
            iface.messageBar().pushMessage(self.tr("Fehler: "), self.tr("Ungültiger Wert"), Qgis.Critical, 10)
            return
        self.dispatcher.send(TMC_SetHeight(args = ([refHeight])).get_geocom_command())
        # start ref height status poll again
        self.refHeightStatus.start()

    def show_joystick(self):
        self.tachy_joystick_dlg.show()

    def ref_height_stop_poll(self):
        self.refHeightStatus.stop()
        self.refHeightStatusLabel.setText(self.REF_HEIGHT_PAUSED)

    # Interface code goes here:
    def setupControls(self):
        """This method connects all controls in the UI to their callbacks.
        It is called in add_action"""
        self.dlg.closingPlugin.connect(self.onCloseCleanup)

        # register commands
        self.reply_handler.register_command(TMC_GetCoordinate, self.coordinates_received)
        self.reply_handler.register_command(TMC_DoMeasure, self.request_coordinates)
        self.reply_handler.register_command(TMC_GetHeight, self.dlg_set_ref_height)

        self.dlg.select_log_file.clicked.connect(self.set_log)
        # stop polling on LineEdit focus
        self.refHeightLineEdit.got_focus.connect(self.ref_height_stop_poll)
        self.refHeightStatus.ref_height_get.connect(self.request_ref_height)
        self.refHeightLineEdit.returnPressed.connect(self.set_ref_height)
        self.vtk_mouse_interactor_style.point_added.signal.connect(self.point_added)
        self.dlg.doMeasure.clicked.connect(self.trigger_measurement)

        # self.dlg.deleteAllButton.clicked.connect(self.clearCanvas)
        # self.dlg.finished.connect(self.mapTool.clear)
        self.dlg.dumpButton.clicked.connect(self.dump)
        self.dlg.deleteVertexButton.clicked.connect(self.vtk_mouse_interactor_style.remove_selected)
        self.dlg.loadPointCloud.clicked.connect(self.loadPointCloud)
        self.dlg.traceButton.clicked.connect(self.vtk_mouse_interactor_style.trace)

        # self.dlg.vertexTableView.setModel(self.vertexList)
        # self.dlg.vertexTableView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # self.dlg.vertexTableView.setSelectionModel(QItemSelectionModel(self.vertexList))
        # self.dlg.vertexTableView.selectionModel().selectionChanged.connect(self.mapTool.selectVertex)

        self.dlg.sourceLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer | QgsMapLayerProxyModel.WritableLayer)
        self.dlg.sourceLayerComboBox.setExcludedProviders(["delimitedtext"])
        self.dlg.sourceLayerComboBox.setLayer(self.iface.activeLayer())
        self.dlg.sourceLayerComboBox.layerChanged.connect(self.setPickable)
        self.dlg.sourceLayerComboBox.layerChanged.connect(self.switchTargetLayer)
        self.dlg.sourceLayerComboBox.layerChanged.connect(self.autozoom)

        self.dlg.targetLayerComboBox.layerChanged.connect(self.setActiveLayer)
        self.dlg.targetLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.dlg.targetLayerComboBox.setLayer(self.iface.activeLayer())
        self.dlg.targetLayerComboBox.setExcludedProviders(["delimitedtext"])
        self.dlg.zoomResetButton.clicked.connect(self.resetVtkCameraTop)

        self.dlg.zoomModeComboBox.activated.connect(self.autozoom)
        self.dlg.zoomModeComboBox.setCurrentIndex(6)  # start with autozoom off

        self.availability_watchdog.serial_available.connect(self.tachy_available)

        self.dispatcher.non_requested_data.connect(self.vertex_received)
        self.dispatcher.serial_connected.connect(self.request_ref_height)
        self.dispatcher.serial_connected.connect(self.tachy_connected)
        self.dispatcher.serial_disconnected.connect(self.tachy_disconnected)
        self.dlg.tachy_connect_button.clicked.connect(self.dispatcher.hook_up)
        self.dlg.tachyJoystick.clicked.connect(self.show_joystick)

        # custom QLineEdit with focus event
        self.dlg.horizontalLayout.insertWidget(10, self.refHeightLineEdit)
        self.dlg.horizontalLayout.insertWidget(11, self.refHeightStatusLabel)

        # self.vtk_widget.resizeEvent().connect(self.renderer.resize)
        # Connect signals for existing layers
        self.connectMapLayers()
        QgsProject.instance().layerTreeRoot().visibilityChanged.connect(self.update_renderer)
        QgsProject.instance().legendLayersAdded.connect(self.rerenderVtkLayer)
        QgsProject.instance().legendLayersAdded.connect(self.connectAddedMapLayers)
        QgsProject.instance().layersRemoved.connect(self.rerenderVtkLayer)

        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

    def disconnectMapLayers(self):
        for layer in QgsProject.instance().layerTreeRoot().findLayers():
            if layer.layer().type() == QgsMapLayerType.RasterLayer:
                continue
            if layer.layer().geometryType() == QgsWkbTypes.NullGeometry:
                continue
            layer.layer().featuresDeleted.disconnect(self.rerenderVtkLayer)
            layer.layer().featureAdded.disconnect(self.rerenderVtkLayer)
            layer.layer().afterRollBack.disconnect(self.rerenderVtkLayer)

    # connect existing QgsMapLayers
    def connectMapLayers(self):
        for layer in QgsProject.instance().layerTreeRoot().findLayers():
            if layer.layer().type() == QgsMapLayerType.RasterLayer:
                continue
            if layer.layer().geometryType() == QgsWkbTypes.NullGeometry:
                continue
            layer.layer().featuresDeleted.connect(self.rerenderVtkLayer)
            layer.layer().featureAdded.connect(self.rerenderVtkLayer)
            layer.layer().afterRollBack.connect(self.rerenderVtkLayer)

    def connectAddedMapLayers(self, QgsMapLayers):
        for layer in QgsMapLayers:
            if layer.type() == QgsMapLayerType.RasterLayer:
                continue
            if layer.geometryType() == QgsWkbTypes.NullGeometry:
                continue
            layer.featuresDeleted.connect(self.rerenderVtkLayer)
            layer.featureAdded.connect(self.rerenderVtkLayer)
            layer.afterRollBack.connect(self.rerenderVtkLayer)

    def update_renderer(self):
        self.vtkLayerCleanUp()
        for layer in QgsProject.instance().layerTreeRoot().findLayers():
            if not layer.layer():
                continue
            if layer.layer().type() == QgsMapLayerType.RasterLayer:
                continue
            if layer.layer().geometryType == QgsWkbTypes.NullGeometry:
                continue
            if layer.isVisible():
                if "⛅" in layer.layer().name():
                    self.vtk_widget.layers[layer.layer().id()].vtkActor.VisibilityOn()
                elif layer.layer().id() not in self.vtk_widget.layers:
                    self.vtk_widget.switch_layer(layer.layer())
            else:  # remove actor from renderer and vtk_widget.layers{}
                if layer.layer().id() in self.vtk_widget.layers:
                    if "⛅" in layer.layer().name():
                        self.vtk_widget.layers[layer.layer().id()].vtkActor.VisibilityOff()
                        continue
                    if type(self.vtk_widget.layers[layer.layer().id()].vtkActor) == tuple:
                        for actor in self.vtk_widget.layers[layer.layer().id()].vtkActor:
                            self.vtk_widget.renderer.RemoveActor(actor)
                        self.vtk_widget.layers.pop(layer.layer().id())
                    else:
                        self.vtk_widget.renderer.RemoveActor(self.vtk_widget.layers[layer.layer().id()].vtkActor)
                        self.vtk_widget.layers.pop(layer.layer().id())
        self.vtk_widget.refresh_content()
        self.vtk_widget.renderer.ResetCameraClippingRange()
        self.setPickable()

    # remove layers if they are not in the layer legend
    def vtkLayerCleanUp(self):
        qgsLayerIds = QgsProject.instance().layerTreeRoot().findLayerIds()
        vtkDict = self.vtk_widget.layers.copy()
        for vtkLayerId, actor in vtkDict.items():
            if vtkLayerId not in qgsLayerIds:
                if type(self.vtk_widget.layers[vtkLayerId].vtkActor) == tuple:
                    for a in actor.vtkActor:
                        self.vtk_widget.renderer.RemoveActor(a)
                    self.vtk_widget.layers.pop(vtkLayerId)
                else:
                    self.vtk_widget.renderer.RemoveActor(self.vtk_widget.layers[vtkLayerId].vtkActor)
                    self.vtk_widget.layers.pop(vtkLayerId)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Tachy2Gis', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        # self.dlg = Tachy2GisDialog()
        # self.setupControls()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Tachy2Gis/icon.png'
        self.add_action(
            icon_path,
            text=self.tr('Tachy2GIS'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&Tachy2GIS'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        # del self.toolbarminec

    def run(self):
        """Run method that performs all the real work"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # # Create the dialog (after translation) and keep reference
            if self.dlg is None:
                self.dlg = Tachy2GisDialog()
                self.render_container_layout = QVBoxLayout()
                self.vtk_widget = VtkWidget(self.dlg.vtk_frame)
                self.vtk_widget.refresh_content()
                self.setupControls()

            self.setupControls()

            # hide joystick until connected
            self.dlg.tachyJoystick.hide()

            self.availability_watchdog.start()
            # self.tachyReader.beginListening()
            self.setActiveLayer()
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.dlg)
            # Start with top view with QGIS map canvas extents
            self.resetVtkCameraTop()  # todo: resets with 1/-1 bounds because renderer was not yet interacted with
            self.update_renderer()
            self.dlg.show()


# Custom QLineEdit with focusInEvent
class SignalizingLineEdit(QLineEdit):
    got_focus = pyqtSignal()

    def focusInEvent(self, event):
        print("Stop")
        self.got_focus.emit()
        super(SignalizingLineEdit, self).focusInEvent(event)


# Polling for ref height
class RefHeightStatus(QObject):
    ref_height_get = pyqtSignal()
    register_ref_height = pyqtSignal()

    def __init__(self):
        self.pollingTimer = QTimer()
        self.pollingTimer.timeout.connect(self.poll)
        super().__init__()

    def start(self):
        self.pollingTimer.start(2000)
        self.register_ref_height.emit()
        #self.parent.reply_handler.register_command(TMC_GetHeight, self.parent.dlg_set_ref_height)

    def stop(self):
        self.pollingTimer.stop()

    def poll(self):
        print("Ref height poll")
        self.ref_height_get.emit()
        #self.parent.request_ref_height()
