# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Tachy2GisDialog
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
import logging
import os

import vtk
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget, QFrame, QVBoxLayout, QLineEdit, QLabel, QFileDialog, QProgressDialog, QMenu
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtSerialPort import QSerialPortInfo
from qgis.core import (
    Qgis,
    QgsWkbTypes,
    QgsProject,
    QgsVectorLayer,
    QgsExpressionContextUtils,
    QgsMapLayerType,
    QgsMapLayerProxyModel,
)
from qgis.utils import iface
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from .TachyReader import AvailabilityWatchdog, RefHeightStatus
from .visualization import (
    VtkPolygonLayer,
    VtkPolygonMLayer,
    VtkPolygonZLayer,
    VtkPolygonZMLayer,
    VtkMultiPolygonLayer,
    VtkMultiPolygonZLayer,
    VtkMultiPolygonMLayer,
    VtkMultiPolygonZMLayer,
    VtkLineStringLayer,
    VtkLineStringMLayer,
    VtkLineStringZLayer,
    VtkLineStringZMLayer,
    VtkMultiLineStringLayer,
    VtkMultiLineStringMLayer,
    VtkMultiLineStringZLayer,
    VtkMultiLineStringZMLayer,
    VtkPointLayer,
    ColourProvider,
    VtkMouseInteractorStyle,
    VtkPointCloudLayer,
)
from ..common.layers import isLayerVisible
from ..common.signal_tracker import SignalTracker
from ..common.utils import write_measurement_log
from ..tachyconnect_t2g import gc_constants
from ..tachyconnect_t2g.GSI_Parser import make_vertex
from ..tachyconnect_t2g.ReplyHandler import ReplyHandler
from ..tachyconnect_t2g.TachyJoystick import TachyJoystick
from ..tachyconnect_t2g.TachyRequest import TMC_GetCoordinate, TMC_GetHeight, TMC_SetHeight, TMC_DoMeasure
from ..tachyconnect_t2g.ts_control import Dispatcher, MessageQueue, CommunicationConstants

LOGGER = logging.getLogger(__name__)

UI_FILE_NAME = "forms/t2g_widget.ui"
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), UI_FILE_NAME))


# Custom QLineEdit with focusInEvent
class SignalizingLineEdit(QLineEdit):
    got_focus = pyqtSignal()

    def focusInEvent(self, event):
        self.got_focus.emit()
        super(SignalizingLineEdit, self).focusInEvent(event)


class VtkViewer(QDockWidget, FORM_CLASS):
    vtk_frame: QFrame

    NO_PORT = "Select tachymeter USB port"
    REF_HEIGHT_PAUSED = "🟠"
    REF_HEIGHT_DISCONNECTED = "🔴"
    REF_HEIGHT_IDLE = "🟡"
    REF_HEIGHT_CONNECTED = "🟢"
    REF_HEIGHT_CHANGED = "⚠️"
    SERIAL_CONNECTED = "🔗"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.setObjectName("VtkViewer")

        self._signal_tracker = SignalTracker(disconnect_on_destroyed=self)
        self._port_menu_tracker = SignalTracker(disconnect_on_destroyed=self)

        # log file is now written automatically, manual selection is no longer needed
        self.select_log_file.hide()

        self.render_container_layout = QVBoxLayout()
        self.vtk_widget = VtkWidget(self.vtk_frame)
        self.render_container_layout.addWidget(self.vtk_widget)
        self.vtk_frame.setLayout(self.render_container_layout)
        self.vtk_widget.refresh_content()

        self.vtk_mouse_interactor_style = VtkMouseInteractorStyle()
        self.markerWidget = vtk.vtkOrientationMarkerWidget()

        self.vtk_widget.SetInteractorStyle(self.vtk_mouse_interactor_style)
        self.vtk_mouse_interactor_style.SetCurrentRenderer(self.vtk_widget.renderer)
        # Setup axes
        self.markerWidget.SetOrientationMarker(self.vtk_widget.axes)
        self.markerWidget.SetInteractor(self.vtk_widget.renderer.GetRenderWindow().GetInteractor())
        self.markerWidget.SetViewport(0.0, 0.0, 0.1, 0.3)
        self.markerWidget.EnabledOn()
        self.markerWidget.InteractiveOff()

        self.reply_handler = ReplyHandler()
        self.dispatcher = Dispatcher(MessageQueue(1), MessageQueue(7), self.reply_handler)

        # tachyJoystick
        self.tachy_joystick_dlg = TachyJoystick(self.dispatcher, self, Qt.Dialog | Qt.Tool)
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
        self.zoomModeComboBox.addItems(
            [
                self.tr("Letzter Punkt"),
                self.tr("Layer"),
                self.tr("Letztes feature"),
                self.tr("Letzte 2 features"),
                self.tr("Letzte 4 features"),
                self.tr("Letzte 8 features"),
                self.tr("Aus"),
            ]
        )

        self.refHeightStatus = RefHeightStatus()

        self.setupControls()
        self.availability_watchdog.start()
        self.setActiveLayer()
        # hide joystick until connected
        self.tachyJoystick.hide()
        # Start with top view with QGIS map canvas extents
        self.resetVtkCameraTop()  # todo: resets with 1/-1 bounds because renderer was not yet interacted with
        self.update_renderer()

    def setupControls(self):
        """This method connects all controls in the UI to their callbacks.
        It is called in add_action"""
        # register commands
        self.reply_handler.register_command(TMC_GetCoordinate, self.coordinates_received)
        self.reply_handler.register_command(TMC_DoMeasure, self.request_coordinates)
        self.reply_handler.register_command(TMC_GetHeight, self.dlg_set_ref_height)

        # stop polling on LineEdit focus
        self.refHeightLineEdit.got_focus.connect(self.ref_height_stop_poll)
        self.refHeightStatus.ref_height_get.connect(self.request_ref_height)
        self.refHeightLineEdit.returnPressed.connect(self.set_ref_height)
        self.vtk_mouse_interactor_style.point_added.signal.connect(self.point_added)
        self.doMeasure.clicked.connect(self.trigger_measurement)

        self.dumpButton.clicked.connect(self.dump)
        self.deleteVertexButton.clicked.connect(self.vtk_mouse_interactor_style.remove_selected)
        self.loadPointCloud.clicked.connect(self._onLoadPointCloudClicked)
        self.traceButton.clicked.connect(self.vtk_mouse_interactor_style.trace)

        self.sourceLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer | QgsMapLayerProxyModel.WritableLayer)
        self.sourceLayerComboBox.setExcludedProviders(["delimitedtext"])
        self.sourceLayerComboBox.setLayer(iface.activeLayer())
        self.sourceLayerComboBox.layerChanged.connect(self.setPickable)
        self.sourceLayerComboBox.layerChanged.connect(self.switchTargetLayer)
        self.sourceLayerComboBox.layerChanged.connect(self.autozoom)

        self.targetLayerComboBox.layerChanged.connect(self.setActiveLayer)
        self.targetLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.targetLayerComboBox.setLayer(iface.activeLayer())
        self.targetLayerComboBox.setExcludedProviders(["delimitedtext"])
        self.zoomResetButton.clicked.connect(self.resetVtkCameraTop)

        self.zoomModeComboBox.activated.connect(self.autozoom)
        self.zoomModeComboBox.setCurrentIndex(6)  # start with autozoom off

        self.availability_watchdog.serial_available.connect(self.tachy_available)

        self.dispatcher.non_requested_data.connect(self.vertex_received)
        self.dispatcher.serial_connected.connect(self.request_ref_height)
        self.dispatcher.serial_connected.connect(self.tachy_connected)
        self.dispatcher.serial_disconnected.connect(self.tachy_disconnected)
        self.tachy_connect_button.clicked.connect(self.dispatcher.hook_up)
        tachy_menu = QMenu(self.tachy_connect_button)
        tachy_menu.addAction(self.tr("Tachy verbinden"), self.dispatcher.hook_up)
        self._signal_tracker.track_connect(
            tachy_menu.aboutToShow, lambda: self._rebuild_port_menu(tachy_menu)
        )
        self.tachy_connect_button.setMenu(tachy_menu)
        self.tachyJoystick.clicked.connect(self.show_joystick)

        # custom QLineEdit with focus event
        self.horizontalLayout.insertWidget(10, self.refHeightLineEdit)
        self.horizontalLayout.insertWidget(11, self.refHeightStatusLabel)

        # self.vtk_widget.resizeEvent().connect(self.renderer.resize)
        # Connect signals for existing layers
        # self.connectMapLayers()
        QgsProject.instance().layerTreeRoot().visibilityChanged.connect(self.update_renderer)
        QgsProject.instance().legendLayersAdded.connect(self.connectAddedMapLayers)
        QgsProject.instance().layersRemoved.connect(self.rerenderVtkLayer)

        self.vtk_widget.Initialize()
        self.vtk_widget.Start()

    def coordinates_received(self, *args):
        write_measurement_log(f"{str(args)}\n")
        retcode = int(args[0])

        if retcode == gc_constants.GRC_OK:
            # %R1P,0,0:RC,E[double],N[double],H[double],CoordTime[long],
            # E-Cont[double],N-Cont[double],H-Cont[double],CoordContTime[long]
            new_vtx = list(map(float, args[1:4]))

            self.vtk_mouse_interactor_style.add_vertex(new_vtx)
            self.coords.setText(f"{new_vtx}")
            self.vtk_mouse_interactor_style.draw()
            self.autozoom(0)
        else:
            message = gc_constants.MESSAGES[retcode]
            self.coords.setText(message)
            iface.messageBar().pushMessage(self.tr("Warnung: "), self.tr(f"Tachy Fehler: {message}"), Qgis.Warning, 10)

    def request_coordinates(self, *args):
        self.dispatcher.send(TMC_GetCoordinate(args=("1000", "1")).get_geocom_command())

    def dlg_set_ref_height(self, *args):
        refHeight = f"{float(args[-1][:6]):<06}"
        retcode = int(args[0])
        if retcode == gc_constants.GRC_OK:
            if self.refHeightLineEdit.text():
                # check if ref height changed
                if refHeight != self.refHeightLineEdit.text():
                    self.refHeightStatusLabel.setText(self.REF_HEIGHT_CHANGED)
                    iface.messageBar().pushMessage(
                        self.tr("Warnung: "), self.tr("Reflektorhöhe wurde geändert!"), Qgis.Warning, 30
                    )
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
                self.refHeightLineEdit.setText(f"{args[-1][:6]}")

        else:
            self.refHeightStatusLabel.setText(self.REF_HEIGHT_DISCONNECTED)
            iface.messageBar().pushMessage(
                self.tr("Warnung: "), self.tr(f"Tachy Fehler: {gc_constants.MESSAGES[retcode]}"), Qgis.Warning, 10
            )

    def ref_height_stop_poll(self):
        self.refHeightStatus.stop()
        self.refHeightStatusLabel.setText(self.REF_HEIGHT_PAUSED)

    def request_ref_height(self):
        self.dispatcher.send(TMC_GetHeight(args=()).get_geocom_command())

    def set_ref_height(self):
        try:
            refHeight = f"{float(self.refHeightLineEdit.text().replace(',', '.')):<06}"
            # format if user enters a single digit
            self.refHeightLineEdit.setText(refHeight)
        except:
            iface.messageBar().pushMessage(self.tr("Fehler: "), self.tr("Ungültiger Wert"), Qgis.Critical, 10)
            return
        self.dispatcher.send(TMC_SetHeight(args=([refHeight])).get_geocom_command())
        # start ref height status poll again
        self.refHeightStatus.start()

    def point_added(self):
        if self.zoomModeComboBox.currentIndex() == 0:
            self.autozoom()

    def trigger_measurement(self):
        measure = TMC_DoMeasure(
            args=(gc_constants.TMC_MEASURE_PRG.TMC_DEF_DIST.value, gc_constants.TMC_INCLINE_PRG.TMC_AUTO_INC.value)
        )
        self.dispatcher.send(measure.get_geocom_command())

    def dump(self):
        vertices = self.vtk_mouse_interactor_style.vertices
        if len(vertices) == 0:
            iface.messageBar().pushMessage(self.tr("Fehler: "), self.tr("Keine Punkte vorhanden!"), Qgis.Warning, 5)
            return

        targetLayer = self.targetLayerComboBox.currentLayer()
        vtk_layer = self.vtk_widget.layers[targetLayer.id()]
        if vtk_layer.add_feature(vertices) == -1:
            return
        # clear picked vertices and remove them from renderer
        self.vtk_mouse_interactor_style.vertices = []
        self.vtk_mouse_interactor_style.draw()
        # remove vtk layer and update renderer
        self.rerenderVtkLayer([targetLayer.id()])
        self.autozoom(self.zoomModeComboBox.currentIndex())

    def _onLoadPointCloudClicked(self, cloudFileName=None):
        if not cloudFileName:
            cloudFileName = QFileDialog.getOpenFileName(
                None,
                self.tr("PointCloud laden..."),
                QgsProject.instance().homePath(),
                "XYZRGB (*.xyz);;Text (*.txt)",
                "*.xyz;;*.txt",
            )[0]
            if cloudFileName == "":
                return
        progress = QProgressDialog(self.tr("Lade PointCloud..."), self.tr("Abbrechen"), 0, 0)
        progress.setWindowTitle(self.tr("PointCloud laden..."))
        progress.setCancelButton(None)
        progress.show()

        pcLayer = QgsVectorLayer("PointZ", "⛅ " + os.path.basename(cloudFileName), "memory")
        QgsExpressionContextUtils.setLayerVariable(pcLayer, "cloud_path", cloudFileName)
        cloud_layer = VtkPointCloudLayer(cloudFileName, pcLayer)
        self.vtk_widget.layers[cloud_layer.id] = cloud_layer
        self.vtk_widget.renderer.AddActor(cloud_layer.vtkActor)
        self.vtk_widget.renderer.ResetCameraClippingRange()
        self.vtk_widget.renderer.GetRenderWindow().Render()
        QgsProject.instance().addMapLayer(pcLayer)
        del progress

    def setPickable(self):
        source_layer = self.sourceLayerComboBox.currentLayer()
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

    def switchTargetLayer(self):
        self.targetLayerComboBox.setLayer(self.sourceLayerComboBox.currentLayer())

    def autozoom(self, *args):
        index = self.zoomModeComboBox.currentIndex()
        if index == 6:  # Off
            return

        if self.sourceLayerComboBox.currentLayer() == self.targetLayerComboBox.currentLayer():
            current_layer = self.sourceLayerComboBox.currentLayer()
        else:
            current_layer = self.targetLayerComboBox.currentLayer()
        if current_layer is None:
            return
        if "⛅" in current_layer.name() and index == 1:
            self.vtk_widget.renderer.GetActiveCamera().SetViewUp(0, 1, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetPosition(0, 0, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetFocalPoint(0, 0, -1)
            self.vtk_widget.renderer.ResetCamera(*self.vtk_widget.layers[current_layer.id()].vtkActor.GetBounds())
            self.vtk_widget.renderer.GetRenderWindow().Render()
            self.vtk_widget.renderer.ResetCameraClippingRange()
            self.zoomModeComboBox.setCurrentIndex(1)
            return
        feats = [f for f in current_layer.getFeatures()]
        if index == 0:  # Track last point
            if self.zoomModeComboBox.currentIndex() == 0:
                if self.vtk_mouse_interactor_style.vertices:
                    self.vtk_widget.renderer.ResetCamera(
                        self.vtk_mouse_interactor_style.vertices[-1][0],
                        self.vtk_mouse_interactor_style.vertices[-1][0],
                        self.vtk_mouse_interactor_style.vertices[-1][1],
                        self.vtk_mouse_interactor_style.vertices[-1][1],
                        self.vtk_mouse_interactor_style.vertices[-1][2],
                        self.vtk_mouse_interactor_style.vertices[-1][2],
                    )
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
            zMin = min(zVtx) if zVtx else 0
            zMax = max(zVtx) if zVtx else 0
            self.vtk_widget.renderer.GetActiveCamera().SetViewUp(0, 1, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetPosition(0, 0, 0)
            self.vtk_widget.renderer.GetActiveCamera().SetFocalPoint(0, 0, -1)
            self.vtk_widget.renderer.ResetCamera(
                current_layer.extent().xMinimum(),
                current_layer.extent().xMaximum(),
                current_layer.extent().yMinimum(),
                current_layer.extent().yMaximum(),
                zMin,
                zMax,
            )
            self.vtk_widget.renderer.ResetCameraClippingRange()
            self.vtk_widget.renderer.GetRenderWindow().Render()

        else:  # 1-8 last features
            if not feats:
                self.zoomModeComboBox.setCurrentIndex(1)
                self.autozoom(1)
                return
            featIds = [f.id() for f in feats]
            count = {2: 1, 3: 2, 4: 4, 5: 8}
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
            self.vtk_widget.renderer.ResetCamera(
                min(xMin), max(xMax), min(yMin), max(yMax), min(zVtx) if zVtx else 0, max(zVtx) if zVtx else 0
            )
            self.vtk_widget.renderer.ResetCameraClippingRange()
            self.vtk_widget.renderer.GetRenderWindow().Render()

    def setActiveLayer(self):
        if Qt is None:
            return
        activeLayer = self.targetLayerComboBox.currentLayer()
        if activeLayer is None:
            return
        iface.setActiveLayer(activeLayer)

    def resetVtkCameraTop(self):
        active_camera = self.vtk_widget.renderer.GetActiveCamera()
        active_camera.SetViewUp(0, 1, 0)
        active_camera.SetPosition(0, 0, 0)
        active_camera.SetFocalPoint(0, 0, -1)
        extent = iface.mapCanvas().extent()
        self.vtk_widget.renderer.ResetCamera(
            extent.xMinimum(),
            extent.xMaximum(),
            extent.yMinimum(),
            extent.yMaximum(),
            self.vtk_widget.renderer.ComputeVisiblePropBounds()[-2],
            self.vtk_widget.renderer.ComputeVisiblePropBounds()[-1],
        )
        active_camera.Zoom(3)
        self.vtk_widget.renderer.ResetCameraClippingRange()
        self.vtk_widget.renderer.GetRenderWindow().Render()

    def tachy_available(self, text):
        self.tachy_connect_button.setText(text)
        self.tachy_connect_button.setToolTip(self.tr("Tachy verbinden"))

    def _rebuild_port_menu(self, menu: QMenu):
        """Rebuild the COM-port submenu entries to reflect currently available ports."""
        self._port_menu_tracker.disconnect_all()
        # Remove all port-specific actions (keep the first "Tachy verbinden" entry)
        for action in menu.actions()[1:]:
            menu.removeAction(action)
        available_ports = [port.portName() for port in QSerialPortInfo.availablePorts()]
        for port_name in available_ports:
            action = menu.addAction(self.tr(f"Mit {port_name} verbinden"))
            self._port_menu_tracker.track_connect(
                action.triggered,
                lambda checked=False, p=port_name: self.dispatcher.manual_hook_up(p),
            )

    def vertex_received(self, line):
        if line.startswith(CommunicationConstants.GEOCOM_REPLY_PREFIX):
            return
        write_measurement_log(line)
        new_vtx = make_vertex(line)
        self.vtk_mouse_interactor_style.add_vertex(new_vtx)
        self.coords.setText(f"{new_vtx}")
        self.vtk_mouse_interactor_style.draw()
        self.autozoom(0)

    def tachy_connected(self, text, portName):
        if self.availability_watchdog.pollingTimer.isActive():
            self.availability_watchdog.shutDown()
        self.tachy_connect_button.setText(text)
        self.tachy_connect_button.setToolTip(self.tr(f"Verbunden mit {portName}"))
        self.refHeightStatusLabel.setText(self.REF_HEIGHT_CONNECTED)
        # show controls
        self.refHeightLineEdit.show()
        self.refHeightStatusLabel.show()
        self.tachyJoystick.show()
        # start requesting reflector height
        self.refHeightStatus.start()

    def tachy_disconnected(self, text, portName):
        if not self.availability_watchdog.pollingTimer.isActive():
            self.availability_watchdog.start()
        self.tachy_connect_button.setText(text)
        self.tachy_connect_button.setToolTip(self.tr("Keine Verbindung"))
        self.refHeightStatusLabel.setText(self.REF_HEIGHT_DISCONNECTED)
        # hide controls when disconnected
        self.refHeightLineEdit.hide()
        self.refHeightStatusLabel.hide()
        self.tachyJoystick.hide()
        # stop requesting reflector height
        self.refHeightStatus.stop()

    def show_joystick(self):
        self.tachy_joystick_dlg.show()

    def connectAddedMapLayers(self, layers):
        if not layers:
            return

        for layer in layers:
            if layer.type() == QgsMapLayerType.RasterLayer:
                continue
            if layer.geometryType() == QgsWkbTypes.NullGeometry:
                continue
            layer.featuresDeleted.connect(self.rerenderVtkLayer)
            layer.featureAdded.connect(self.rerenderVtkLayer)
            layer.afterRollBack.connect(self.rerenderVtkLayer)

        self.rerenderVtkLayer([layer.id() for layer in layers])

    # connect existing QgsMapLayers
    def connectMapLayers(self):
        self.connectAddedMapLayers(QgsProject.instance().mapLayers().values())

    def update_renderer(self):
        self.vtkLayerCleanUp()
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayerType.RasterLayer:
                continue
            if layer.geometryType() == QgsWkbTypes.NullGeometry:
                continue

            if isLayerVisible(layer):
                if "⛅" in layer.name():
                    self.vtk_widget.layers[layer.id()].vtkActor.VisibilityOn()
                elif layer.id() not in self.vtk_widget.layers:
                    self.vtk_widget.switch_layer(layer)
            else:  # remove actor from renderer and vtk_widget.layers{}
                if layer.id() in self.vtk_widget.layers:
                    if "⛅" in layer.name():
                        self.vtk_widget.layers[layer.id()].vtkActor.VisibilityOff()
                        continue
                    if type(self.vtk_widget.layers[layer.id()].vtkActor) == tuple:
                        for actor in self.vtk_widget.layers[layer.id()].vtkActor:
                            self.vtk_widget.renderer.RemoveActor(actor)
                        self.vtk_widget.layers.pop(layer.id())
                    else:
                        self.vtk_widget.renderer.RemoveActor(self.vtk_widget.layers[layer.id()].vtkActor)
                        self.vtk_widget.layers.pop(layer.id())

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
                    self.vtk_widget.renderer.RemoveActor(self.layers[vtkLayerId].vtkActor)
                    self.vtk_widget.layers.pop(vtkLayerId)

    # Used after dump and layerRemoved/added signal which return the layer ids as list
    # featuresDeleted returns feature ids (int) instead of layer id so activeLayer().id() is used
    def rerenderVtkLayer(self, layerIds=(0,)):
        # todo: featureAdded triggering for every feature added, calling update_renderer multiple times on save
        # featureAdded
        if isinstance(layerIds, int):
            layerIds = [layerIds]
        # featuresDeleted
        if isinstance(layerIds[0], int):
            active_layer_id = iface.activeLayer().id()
            if active_layer_id not in self.vtk_widget.layers:
                return
            if type(self.vtk_widget.layers[active_layer_id].vtkActor) == tuple:
                for actor in self.vtk_widget.layers[active_layer_id].vtkActor:
                    self.vtk_widget.renderer.RemoveActor(actor)
            else:
                self.vtk_widget.renderer.RemoveActor(self.vtk_widget.layers[active_layer_id].vtkActor)
            self.vtk_widget.layers.pop(active_layer_id)
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
        # self.closingPlugin.disconnect(self.onCloseCleanup)
        # disconnect setupControls
        self.tachy_connect_button.clicked.disconnect()
        self.dumpButton.clicked.disconnect()
        self.traceButton.clicked.disconnect()
        self.deleteVertexButton.clicked.disconnect()
        self.vtk_mouse_interactor_style.point_added.signal.disconnect(self.point_added)
        # self.dlg.setRefHeight.returnPressed.disconnect()
        self.zoomResetButton.clicked.disconnect()
        self.availability_watchdog.serial_available.disconnect()
        self.loadPointCloud.clicked.disconnect()
        self.sourceLayerComboBox.layerChanged.disconnect()
        self.targetLayerComboBox.layerChanged.disconnect()
        self.zoomModeComboBox.activated.disconnect(self.autozoom)
        QgsProject.instance().layerTreeRoot().visibilityChanged.disconnect(self.update_renderer)
        QgsProject.instance().legendLayersAdded.disconnect(self.connectAddedMapLayers)
        QgsProject.instance().layersRemoved.disconnect(self.rerenderVtkLayer)

        self.vtk_mouse_interactor_style.shut_down()
        self.dispatcher.stop()
        self.dispatcher.deleteLater()
        for queue in self.dispatcher.queues.values():
            queue.deleteLater()
        self.reply_handler.deleteLater()
        self.availability_watchdog.shutDown()
        self.availability_watchdog.deleteLater()
        self.refHeightStatus.stop()
        self.refHeightStatus.deleteLater()
        self.vtk_widget.layers.clear()


class VtkWidget(QVTKRenderWindowInteractor):
    layer_type_map = {
        "Polygon": VtkPolygonLayer,
        "PolygonM": VtkPolygonMLayer,
        "PolygonZ": VtkPolygonZLayer,
        "PolygonZM": VtkPolygonZMLayer,
        "MultiPolygon": VtkMultiPolygonLayer,
        "MultiPolygonZ": VtkMultiPolygonZLayer,
        "MultiPolygonM": VtkMultiPolygonMLayer,
        "MultiPolygonZM": VtkMultiPolygonZMLayer,
        "LineString": VtkLineStringLayer,
        "LineStringM": VtkLineStringMLayer,
        "LineStringZ": VtkLineStringZLayer,
        "LineStringZM": VtkLineStringZMLayer,
        "MultiLineString": VtkMultiLineStringLayer,
        "MultiLineStringM": VtkMultiLineStringMLayer,
        "MultiLineStringZ": VtkMultiLineStringZLayer,
        "MultiLineStringZM": VtkMultiLineStringZMLayer,
        "Point": VtkPointLayer,
        "PointM": VtkPointLayer,
        "PointZ": VtkPointLayer,
        "PointZM": VtkPointLayer,
        "MultiPoint": VtkPointLayer,
        "MultiPointM": VtkPointLayer,
        "MultiPointZ": VtkPointLayer,
        "MultiPointZM": VtkPointLayer,
    }

    def __init__(self, widget):
        super().__init__(widget)
        self.axes = vtk.vtkAxesActor()
        self.axes.PickableOff()
        self.colour_provider = ColourProvider()
        self.renderer = vtk.vtkRenderer()
        self.GetRenderWindow().AddRenderer(self.renderer)
        self.layers = {}

    def switch_layer(self, qgis_layer):
        layer_id = qgis_layer.id()
        type_name = QgsWkbTypes.displayString(qgis_layer.wkbType())
        if type_name in VtkWidget.layer_type_map.keys():
            if layer_id not in self.layers.keys():
                layer_type = VtkWidget.layer_type_map[type_name]
                created = layer_type(qgs_layer=qgis_layer)
                # created.update()
                self.layers[layer_id] = created
                for actor in created.get_actors(self.colour_provider.next()):
                    self.renderer.AddActor(actor)

        self.refresh_content()

    def refresh_content(self):
        # The mapper is responsible for pushing the geometry into the graphics
        # library. It may also do color mapping, if scalars or other
        # attributes are defined.

        # Create the graphics structure. The renderer renders into the render
        # window. The render window interactor captures mouse events and will
        # perform appropriate camera or actor manipulation depending on the
        # nature of the events.

        ren = self.renderer
        renWin = self.GetRenderWindow()
        # no visible difference
        # renWin.PointSmoothingOn()  # Point Cloud test
        # renWin.PolygonSmoothingOn()
        # renWin.LineSmoothingOn()
        iren = renWin.GetInteractor()
        iren.SetRenderWindow(renWin)

        # Add the actors to the renderer, set the background and size
        ren.SetBackground(vtk.vtkNamedColors().GetColor3d("light_grey"))

        # This allows the interactor to initalize itself. It has to be
        # called before an event loop.
        iren.Initialize()

        # We'll zoom in a little by accessing the camera and invoking a "Zoom"
        # method on it.
        # ren.ResetCamera()
        # ren.GetActiveCamera().Zoom(1.5)
        renWin.Render()
