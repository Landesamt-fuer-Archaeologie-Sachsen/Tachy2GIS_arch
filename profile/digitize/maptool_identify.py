from PyQt5.QtCore import Qt, QPoint, pyqtSlot, pyqtSignal, QCoreApplication, QEvent, QObject
from qgis.core import QgsPointXY, QgsGeometry, QgsFeature
from qgis.gui import QgsAttributeDialog, QgsAttributeEditorContext, QgsMapTool

from ..publisher import Publisher

## @brief With the MapToolIdentify class a map tool for identify feature attributes is realized
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
        self.search_features = []
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
        if self.lastFeature[1]["geo_quelle"] != "profile_object":
            self.__iface.messageBar().pushMessage("Error", "Dieses Feature ist nicht editierbar!", level=1, duration=5)
            return
        if self.only_points:
            self.points_feature_selected_for_edit.emit(self.lastFeature[1])
        elif self.only_lines:
            self.lines_feature_selected_for_edit.emit(self.lastFeature[1])
        elif self.only_polygons:
            self.polygons_feature_selected_for_edit.emit(self.lastFeature[1])

    def setDigiPointLayer(self, digiPointLayer):
        self.digiPointLayer = digiPointLayer

    def setDigiLineLayer(self, digiLineLayer):
        self.digiLineLayer = digiLineLayer

    def setDigiPolygonLayer(self, digiPolygonLayer):
        self.digiPolygonLayer = digiPolygonLayer

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
        self._set_search_features()

    def set_for_feat_form(self):
        self.only_points = False
        self.only_lines = False
        self.only_polygons = False
        self.do_action_select_instead = False
        self.setCursor(Qt.WhatsThisCursor)
        self._set_search_features()

    def _set_search_features(self):
        if self.only_points:
            search_layers = [self.digiPointLayer]
        elif self.only_lines:
            search_layers = [self.digiLineLayer]
        elif self.only_polygons:
            search_layers = [self.digiPolygonLayer]
        else:
            search_layers = [self.digiPointLayer, self.digiLineLayer, self.digiPolygonLayer]

        self.search_features = [
            {
                "layer": layer,
                "feature": feature
            }
            for layer in search_layers
            for feature in layer.getFeatures()
        ]

        if self.do_action_select_instead:
            # in edit mode allow only "profile_object"
            self.search_features = list(filter(
                lambda f: f["feature"]["geo_quelle"] == "profile_object",
                self.search_features
            ))

    def close_form(self, event):
        self.pup.publish("removeHoverFeatures", {})

    def canvasMoveEvent(self, e):
        self.got_moved.emit(QPoint(e.pos().x(), e.pos().y()))

    @pyqtSlot(QPoint)
    def handleMove(self, q_point):
        def getDistance(geometry: QgsGeometry, point: QgsPointXY):
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

        if len(self.search_features) == 0:
            return

        map_point = self.toMapCoordinates(q_point)
        closest_distances = [getDistance(f["feature"].geometry(), map_point) for f in self.search_features]
        index_of_nearest = min(range(len(closest_distances)), key=closest_distances.__getitem__)

        vicinity = self.canvas.mapUnitsPerPixel() * 10
        squared_distance = vicinity * vicinity
        if closest_distances[index_of_nearest] > squared_distance:
            if self.lastUUID is not None:
                self.lastUUID = None
                self.lastFeature = None
                self.pup.publish("removeHoverFeatures", {})
            return

        final_result = self.search_features[index_of_nearest]
        if final_result["feature"]["obj_uuid"] == self.lastUUID:
            return

        self.lastUUID = final_result["feature"]["obj_uuid"]
        self.lastFeature = (
            final_result["layer"],
            final_result["feature"]
        )
        self.pup.publish("removeHoverFeatures", {})
        self.pup.publish(
            "addHoverFeatures",
            {"layer": final_result["layer"], "features": [final_result["feature"]]}
        )
