from PyQt5.QtCore import Qt, QPoint, pyqtSlot, pyqtSignal, QCoreApplication, QEvent, QObject
from PyQt5.QtWidgets import QApplication
from qgis.core import QgsPointXY, QgsGeometry, QgsFeature
from qgis.gui import QgsMapToolIdentify, QgsAttributeDialog, QgsAttributeEditorContext, QgsMapTool

from ..publisher import Publisher

## @brief With the MapToolIdentify class a map tool for identify feature attributes is realized
#
# The class inherits form QgsMapToolIdentify and MapToolMixin
#
# @author Mario Uhlig, VisDat geodatentechnologie GmbH, mario.uhlig@visdat.de
# @date 2022-28-09


# https://stackoverflow.com/questions/20866996/how-to-compress-slot-calls-when-using-queued-connection-in-qt/21006207#21006207
class CompressorProxy(QObject):
    signal = pyqtSignal()
    signal_point = pyqtSignal(QPoint)

    def emitCheck(self, flag):
        flag[0] = True
        QCoreApplication.sendPostedEvents(self, QEvent.MetaCall)
        result = flag[0]
        flag[0] = False
        return result

    @pyqtSlot()
    def slot(self):
        if self.emitCheck(self.m_slot):
            self.signal.emit()

    @pyqtSlot(QPoint)
    def slot_point(self, arg1):
        if self.emitCheck(self.m_slot_point):
            self.signal_point.emit(arg1)

    def __init__(self, parent):
        super(CompressorProxy, self).__init__(parent)
        self.m_slot = [False]
        self.m_slot_point = [False]


class MapToolIdentify(QgsMapTool):
    # darf nicht in den Konstruktor:
    got_moved = pyqtSignal(QPoint)
    points_feature_selected_for_edit = pyqtSignal(QgsFeature)
    lines_feature_selected_for_edit = pyqtSignal(QgsFeature)
    polygons_feature_selected_for_edit = pyqtSignal(QgsFeature)

    def __init__(self, canvas, iFace):
        self.do_action_select_instead = False
        self.__iface = iFace
        self.pup = Publisher()
        self.canvas = canvas
        self.digiPointLayer = None
        self.digiLineLayer = None
        self.digiPolygonLayer = None
        self.only_points = False
        self.only_lines = False
        self.only_polygons = False
        QgsMapTool.__init__(self, self.canvas)
        self.id_tool = QgsMapToolIdentify(self.canvas)
        self.featForm = None
        self.lastUUID = None
        self.lastFeature = None
        proxy = CompressorProxy(self)
        self.got_moved.connect(proxy.slot_point, Qt.QueuedConnection)  # queued is important
        proxy.signal_point.connect(self.handleMove)

    def canvasPressEvent(self, event):
        if not self.lastFeature:
            return

        if self.do_action_select_instead:
            self.do_action_select_for_edit()
        else:
            self.do_action_feat_form()

    def do_action_feat_form(self):
        if isinstance(self.featForm, QgsAttributeDialog):
            self.featForm.close()
        self.featForm = QgsAttributeDialog(
            vl=self.lastFeature[0],
            thepFeature=self.lastFeature[1],
            parent=self.canvas,
            featureOwner=False,
            showDialogButtons=False,
            context=QgsAttributeEditorContext(),
        )
        self.featForm.closeEvent = self.close_form
        self.featForm.setWindowTitle("Feature Eigenschaften")
        self.featForm.show()

    def do_action_select_for_edit(self):
        self.pup.publish("removeHoverFeatures", {})
        if self.only_points:
            self.points_feature_selected_for_edit.emit(self.lastFeature[1])
        elif self.only_lines:
            self.lines_feature_selected_for_edit.emit(self.lastFeature[1])
        elif self.only_polygons:
            self.polygons_feature_selected_for_edit.emit(self.lastFeature[1])

    def set_for_select_action(self, the_only_geom=""):
        self.only_points = False
        self.only_lines = False
        self.only_polygons = False
        self.do_action_select_instead = True
        self.setCursor(Qt.PointingHandCursor)
        if the_only_geom == "points":
            self.only_points = True
        elif the_only_geom == "lines":
            self.only_lines = True
        elif the_only_geom == "polygons":
            self.only_polygons = True

    def set_for_feat_form(self):
        self.only_points = False
        self.only_lines = False
        self.only_polygons = False
        self.do_action_select_instead = False
        self.setCursor(Qt.WhatsThisCursor)

    def close_form(self, event):
        self.pup.publish("removeHoverFeatures", {})

    def setDigiPointLayer(self, digiPointLayer):
        self.digiPointLayer = digiPointLayer

    def setDigiLineLayer(self, digiLineLayer):
        self.digiLineLayer = digiLineLayer

    def setDigiPolygonLayer(self, digiPolygonLayer):
        self.digiPolygonLayer = digiPolygonLayer

    def canvasMoveEvent(self, e):
        self.got_moved.emit(QPoint(e.pos().x(), e.pos().y()))

    @pyqtSlot(QPoint)
    def handleMove(self, q_point):
        if self.only_points:
            search_layers = [self.digiPointLayer]
        elif self.only_lines:
            search_layers = [self.digiLineLayer]
        elif self.only_polygons:
            search_layers = [self.digiPolygonLayer]
        else:
            search_layers = [self.digiPointLayer, self.digiLineLayer, self.digiPolygonLayer]

        results = self.id_tool.identify(q_point.x(), q_point.y(), search_layers, QgsMapToolIdentify.TopDownAll)

        if len(results) == 0:
            if self.lastUUID is not None:
                self.lastUUID = None
                self.lastFeature = None
                self.pup.publish("removeHoverFeatures", {})
            return

        final_result = results[0]
        if len(results) > 1:
            map_point = self.toMapCoordinates(q_point)
            closest_distances = [self.getDistance(r.mFeature.geometry(), map_point) for r in results]
            index_of_nearest = min(range(len(closest_distances)), key=closest_distances.__getitem__)
            final_result = results[index_of_nearest]

        if final_result.mFeature["uuid"] != self.lastUUID:
            self.lastUUID = final_result.mFeature["uuid"]
            self.lastFeature = (final_result.mLayer, final_result.mFeature)
            linkObj = {"layer": final_result.mLayer, "features": [final_result.mFeature]}
            self.pup.publish("removeHoverFeatures", {})
            self.pup.publish("addHoverFeatures", linkObj)

    def getDistance(self, geometry: QgsGeometry, point: QgsPointXY):
        vertex_distance = geometry.closestVertexWithContext(point)[0]
        segment_distance = geometry.closestSegmentWithContext(point)[0]
        if vertex_distance < 0:
            vertex_distance = float("inf")
        if segment_distance < 0:
            segment_distance = float("inf")
        if segment_distance < vertex_distance:
            return segment_distance
        else:
            return vertex_distance
