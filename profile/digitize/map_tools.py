from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QColor
from qgis.core import (
    QgsGeometry,
    QgsWkbTypes,
    QgsArrowSymbolLayer,
    QgsSymbol,
    QgsPointXY,
)
from qgis.gui import QgsMapTool, QgsRubberBand, QgsVertexMarker


class PolygonMapTool(QgsMapTool):
    # darf nicht in den Konstruktor:
    finished_geometry = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        self.canvas = canvas
        super().__init__(self.canvas)

        self.markers = []
        self.list_of_snapping_points = None
        self.snappingMarker = None
        self.selectingMarker = None
        self.lastMapCoord = None
        self.isFinished = False
        self.isSelecting = False
        self.setCursor(Qt.CrossCursor)
        self.isSnapping = False

        self.symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
        arrow = QgsArrowSymbolLayer.create(
            {
                "arrow_type": "0",
                "head_type": "0",
                "is_curved": "0",
                "arrow_start_width": "0.5",
                "arrow_width": "0.5",
                "head_length": "3",
                "head_thickness": "1.5",
                "color": "red",
            }
        )
        self.symbol.changeSymbolLayer(0, arrow)

        self.symbol_tmp = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
        arrow_tmp = QgsArrowSymbolLayer.create(
            {
                "arrow_type": "0",
                "head_type": "0",
                "is_curved": "0",
                "arrow_start_width": "0.5",
                "arrow_width": "0.5",
                "head_length": "3",
                "head_thickness": "1.5",
                "color": QColor(0, 150, 255, 100),
            }
        )
        self.symbol_tmp.changeSymbolLayer(0, arrow_tmp)

        self.tempRubberBand = QgsRubberBand(self.canvas)
        self.tempRubberBand.setSymbol(self.symbol_tmp)
        self.resetTempRubber()
        self.closingRubberBand = QgsRubberBand(self.canvas)
        self.resetClosingRubber()
        self.rubberBand = QgsRubberBand(self.canvas)
        self.rubberBand.setSymbol(self.symbol)

        self.reset_geometry()

    def draw_helper_rubbers(self):
        self.resetTempRubber()
        self.resetClosingRubber()
        num_markers = len(self.markers)

        moving_point = self.lastMapCoord
        if self.isSnapping and self.snappingMarker:
            moving_point = self.snappingMarker.center()

        if num_markers == 1:
            self.tempRubberBand.addPoint(self.markers[0].center())
            self.tempRubberBand.addPoint(moving_point)
        elif num_markers > 1:
            self.tempRubberBand.addPoint(self.markers[-1].center())
            self.tempRubberBand.addPoint(moving_point)
            self.tempRubberBand.addPoint(self.markers[0].center())
            if num_markers > 2:
                self.closingRubberBand.addPoint(self.markers[0].center())
                self.closingRubberBand.addPoint(self.markers[-1].center())

    def reverse_points(self):
        if len(self.markers) < 2:
            return

        self.markers.reverse()
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        for marker in self.markers:
            self.rubberBand.addPoint(marker.center())
        if self.isFinished:
            self.rubberBand.closePoints()
        for rubber in (self.closingRubberBand, self.tempRubberBand):
            for i in range(rubber.numberOfVertices()):
                if rubber.getPoint(0, i) == self.markers[0].center():
                    rubber.movePoint(i, self.markers[-1].center())
                elif rubber.getPoint(0, i) == self.markers[-1].center():
                    rubber.movePoint(i, self.markers[0].center())
            rubber.updateCanvas()

    def reset_geometry(self):
        # clear points of rubber band:
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        self.resetTempRubber()
        self.resetClosingRubber()

        # remove all vertices:
        for marker in self.markers:
            self.canvas.scene().removeItem(marker)
        self.markers = []

        self.symbol.setColor(Qt.red)
        self.isFinished = False
        self.isSelecting = False
        self.setCursor(Qt.CrossCursor)

        self.finished_geometry.emit(QgsGeometry())

    def get_geometry(self):
        return self.rubberBand.asGeometry()

    def set_geometry_for_editing(self, geometry: QgsGeometry):
        self.reset_geometry()
        for vertex in geometry.vertices():
            point = QgsPointXY(vertex.x(), vertex.y())
            self.rubberBand.addPoint(point)
            vertexMarker = QgsVertexMarker(self.canvas)
            vertexMarker.setCenter(point)
            vertexMarker.setColor(Qt.black)
            vertexMarker.setFillColor(Qt.red)
            vertexMarker.setIconSize(7)
            vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
            vertexMarker.setPenWidth(1)
            self.markers.append(vertexMarker)
        self.select_mode()

    def finish_geometry(self, not_really_finished=False):
        if self.isFinished or len(self.markers) < 3:
            return

        self.isFinished = True
        self.symbol.setColor(Qt.darkGreen)
        self.rubberBand.closePoints()

        self.resetClosingRubber()
        self.resetTempRubber()

        # if last marker was set on first marker
        # remove last marker as this class expects
        # one marker less than vertices in a closed rubberband
        if self.rubberBand.numberOfVertices() == len(self.markers):
            if len(self.markers) > 0:
                self.canvas.scene().removeItem(self.markers[-1])
                del self.markers[-1]

        if not not_really_finished:
            self.finished_geometry.emit(self.get_geometry())

    def undo_last_point(self):
        if self.isSelecting:
            self.recover_to_normal_mode()

        if self.isFinished:
            # remove closing point:
            self.rubberBand.removeLastPoint()
            self.symbol.setColor(Qt.red)
            self.isFinished = False
            self.finished_geometry.emit(QgsGeometry())

        self.rubberBand.removeLastPoint()
        if len(self.markers) > 0:
            self.canvas.scene().removeItem(self.markers[-1])
            del self.markers[-1]

        self.draw_helper_rubbers()

        self.handleMove()

    def select_mode(self):
        if len(self.markers) < 2:
            return

        self.finish_geometry(not_really_finished=True)
        self.symbol.setColor(Qt.red)
        self.rubberBand.updateCanvas()
        self.isSelecting = True
        self.setCursor(Qt.OpenHandCursor)

    def recover_to_normal_mode(self):
        if self.snappingMarker:
            self.canvas.scene().removeItem(self.snappingMarker)
        if self.selectingMarker:
            self.canvas.scene().removeItem(self.selectingMarker)

        self.isSelecting = False
        self.setCursor(Qt.CrossCursor)
        self.isFinished = False
        self.finish_geometry()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.undo_last_point()

        if e.key() == Qt.Key_R:
            self.reverse_points()

        if e.key() == Qt.Key_Control:
            self.isSnapping = True
            self.handleMove()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Control:
            self.isSnapping = False
            self.handleMove()

    def canvasReleaseEvent(self, e):
        if self.isSelecting:
            if e.button() == Qt.RightButton:
                self.recover_to_normal_mode()
                return
            elif e.button() != Qt.LeftButton:
                return

            if not self.selectingMarker:
                return

            # find indexes of vertices:
            index_list = [
                i
                for i, m in enumerate(self.markers)
                if m.center() == self.selectingMarker.center()
            ]
            if len(index_list) < 1:
                return
            rotate_amount = index_list[0] + 1
            # rotate markers inside list so that blue one is now last:
            self.markers = self.markers[rotate_amount:] + self.markers[:rotate_amount]
            # clear and fill rubberband so that the point to remove is last:
            self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
            for marker in self.markers:
                self.rubberBand.addPoint(marker.center())
            self.isFinished = False
            self.isSelecting = False
            self.setCursor(Qt.CrossCursor)

            # remove last point and vertex with undo function:
            self.undo_last_point()

            self.draw_helper_rubbers()

            # as we are now in normal mode this now draws a temporary point:
            self.handleMove()
            return

        if self.isFinished:
            return

        if e.button() == Qt.RightButton:
            self.finish_geometry()
            return
        elif e.button() != Qt.LeftButton:
            return

        # use correct clicking point for adding:
        click_point = self.toMapCoordinates(e.pos())
        if self.isSnapping:
            snappingPoint = self.getSnappingPoint()
            if snappingPoint:
                click_point = snappingPoint

        self.rubberBand.addPoint(click_point)
        vertexMarker = QgsVertexMarker(self.canvas)
        vertexMarker.setCenter(click_point)
        vertexMarker.setColor(Qt.black)
        vertexMarker.setFillColor(Qt.red)
        vertexMarker.setIconSize(7)
        vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
        vertexMarker.setPenWidth(1)
        self.markers.append(vertexMarker)

        self.draw_helper_rubbers()

    def canvasMoveEvent(self, e):
        self.lastMapCoord = self.toMapCoordinates(e.pos())
        self.handleMove()

    def handleMove(self):
        if self.snappingMarker:
            self.canvas.scene().removeItem(self.snappingMarker)
            self.snappingMarker = None
        if self.selectingMarker:
            self.canvas.scene().removeItem(self.selectingMarker)
            self.selectingMarker = None

        if self.isSelecting:
            snappingPoint = self.getSnappingPoint()
            if snappingPoint:
                # mark nearest vertex blue:
                self.selectingMarker = QgsVertexMarker(self.canvas)
                self.selectingMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
                self.selectingMarker.setCenter(snappingPoint)
                self.selectingMarker.setColor(Qt.blue)
                self.selectingMarker.setFillColor(Qt.red)
                self.selectingMarker.setIconSize(9)
                self.selectingMarker.setPenWidth(3)
            return

        if self.isFinished or len(self.markers) < 1:
            return

        if self.isSnapping:
            snappingPoint = self.getSnappingPoint()
            if snappingPoint:
                # mark nearest vertex yellow:
                self.snappingMarker = QgsVertexMarker(self.canvas)
                self.snappingMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
                self.snappingMarker.setCenter(snappingPoint)
                self.snappingMarker.setColor(Qt.yellow)
                self.snappingMarker.setFillColor(Qt.red)
                self.snappingMarker.setIconSize(9)
                self.snappingMarker.setPenWidth(3)

        # draw a temporary point at mouse pointer while moving:
        self.draw_helper_rubbers()

    def setSnappingPoints(self, list_of_points):
        self.list_of_snapping_points = list_of_points

    def getSnappingPoint(self):
        if self.isSelecting:
            if not self.markers or len(self.markers) < 1:
                return None
            points_list = [vertex.center() for vertex in self.markers]
        else:
            if (
                not self.list_of_snapping_points
                or len(self.list_of_snapping_points) < 1
            ):
                return None
            points_list = self.list_of_snapping_points

        move_point = self.lastMapCoord
        x = move_point.x()
        y = move_point.y()
        distances = [p.distance(x, y) for p in points_list]
        index_of_nearest = min(range(len(distances)), key=distances.__getitem__)

        # tolerance needs to be recalculated as user can zoom while moving
        pt1 = QPoint(x, y)
        pt2 = QPoint(x + 20, y)
        layerPt1 = self.toLayerCoordinates(self.canvas.layer(0), pt1)
        layerPt2 = self.toLayerCoordinates(self.canvas.layer(0), pt2)
        tolerance = layerPt2.x() - layerPt1.x()
        if distances[index_of_nearest] > tolerance:
            return None

        return points_list[index_of_nearest]

    def resetTempRubber(self):
        self.tempRubberBand.reset(QgsWkbTypes.LineGeometry)

    def resetClosingRubber(self):
        self.closingRubberBand.reset(QgsWkbTypes.LineGeometry)
        self.closingRubberBand.setLineStyle(Qt.DashLine)
        self.closingRubberBand.setStrokeColor(Qt.black)
        self.closingRubberBand.setSecondaryStrokeColor(QColor(255, 0, 0, 100))
        self.closingRubberBand.setWidth(1)


class MultilineMapTool(QgsMapTool):
    # darf nicht in den Konstruktor:
    finished_geometry = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        self.canvas = canvas
        super().__init__(self.canvas)

        self.markers = []
        self.markers2 = []
        self.list_of_snapping_points = None
        self.snappingMarker = None
        self.selectingMarker = None
        self.lastMapCoord = None
        self.isFinished = False
        self.isSelecting = False
        self.setCursor(Qt.CrossCursor)
        self.isSnapping = False
        self.isSplit = False

        self.symbol = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
        arrow = QgsArrowSymbolLayer.create(
            {
                "arrow_type": "0",
                "head_type": "0",
                "is_curved": "0",
                "arrow_start_width": "0.5",
                "arrow_width": "0.5",
                "head_length": "3",
                "head_thickness": "1.5",
                "color": "red",
            }
        )
        self.symbol.changeSymbolLayer(0, arrow)

        self.symbol_tmp = QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
        arrow = QgsArrowSymbolLayer.create(
            {
                "arrow_type": "0",
                "head_type": "0",
                "is_curved": "0",
                "arrow_start_width": "0.5",
                "arrow_width": "0.5",
                "head_length": "3",
                "head_thickness": "1.5",
                "color": QColor(0, 150, 255, 100),
            }
        )
        self.symbol_tmp.changeSymbolLayer(0, arrow)

        self.tempRubberBand = QgsRubberBand(self.canvas)
        self.tempRubberBand.setSymbol(self.symbol_tmp)
        self.resetTempRubber()
        self.closingRubberBand = QgsRubberBand(self.canvas)
        self.resetClosingRubber()
        self.rubberBand = QgsRubberBand(self.canvas)
        self.rubberBand.setSymbol(self.symbol)

        self.reset_geometry()

    def reverse_points(self):
        if len(self.markers) < 1:
            return

        if self.isSplit:
            self.markers, self.markers2 = self.markers2, self.markers

        self.markers.reverse()
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        for marker in self.markers:
            self.rubberBand.addPoint(marker.center())

        if self.isSplit:
            self.markers2.reverse()
            self.closingRubberBand.reset(QgsWkbTypes.LineGeometry)
            for marker in reversed(self.markers2):
                self.closingRubberBand.addPoint(marker.center())
            self.closingRubberBand.addPoint(self.markers[-1].center())
            self.closingRubberBand.updateCanvas()

        for i in range(self.tempRubberBand.numberOfVertices()):
            if self.isSplit:
                if self.tempRubberBand.getPoint(0, i) == self.markers2[0].center():
                    self.tempRubberBand.movePoint(i, self.markers[-1].center())
                elif self.tempRubberBand.getPoint(0, i) == self.markers[-1].center():
                    self.tempRubberBand.movePoint(i, self.markers2[0].center())
            else:
                if self.tempRubberBand.getPoint(0, i) == self.markers[0].center():
                    self.tempRubberBand.movePoint(i, self.markers[-1].center())
                elif self.tempRubberBand.getPoint(0, i) == self.markers[-1].center():
                    self.tempRubberBand.movePoint(i, self.markers[0].center())

        self.tempRubberBand.updateCanvas()

    def reset_geometry(self):
        # clear points of rubber band:
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        self.resetTempRubber()
        self.resetClosingRubber()

        # remove all vertices:
        for marker in self.markers:
            self.canvas.scene().removeItem(marker)
        self.markers = []
        for marker in self.markers2:
            self.canvas.scene().removeItem(marker)
        self.markers2 = []

        self.symbol.setColor(Qt.red)
        self.isFinished = False
        self.isSelecting = False
        self.setCursor(Qt.CrossCursor)

        self.finished_geometry.emit(QgsGeometry())

    def get_geometry(self):
        return self.rubberBand.asGeometry()

    def set_geometry_for_editing(self, geometry: QgsGeometry):
        self.reset_geometry()
        for vertex in geometry.vertices():
            point = QgsPointXY(vertex.x(), vertex.y())
            self.rubberBand.addPoint(point)
            vertexMarker = QgsVertexMarker(self.canvas)
            vertexMarker.setCenter(point)
            vertexMarker.setColor(Qt.black)
            vertexMarker.setFillColor(Qt.red)
            vertexMarker.setIconSize(7)
            vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
            vertexMarker.setPenWidth(1)
            self.markers.append(vertexMarker)
        self.select_mode()

    def finish_geometry(self, not_really_finished=False):
        if self.isFinished or len(self.markers) + len(self.markers2) < 2:
            return

        self.isFinished = True
        self.symbol.setColor(Qt.darkGreen)
        self.rubberBand.updateCanvas()

        if self.isSplit:
            self.isSplit = False
            self.resetClosingRubber()
            self.markers.extend(self.markers2)
            self.markers2 = []
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
            for marker in self.markers:
                self.rubberBand.addPoint(marker.center())

        self.resetClosingRubber()
        self.resetTempRubber()

        if not not_really_finished:
            self.finished_geometry.emit(self.get_geometry())

    def undo_last_point(self):
        if len(self.markers) < 1:
            return

        if self.isSelecting:
            self.recover_to_normal_mode()

        if self.isFinished:
            self.symbol.setColor(Qt.red)
            self.isFinished = False
            self.finished_geometry.emit(QgsGeometry())

        self.rubberBand.removeLastPoint()
        self.canvas.scene().removeItem(self.markers[-1])
        del self.markers[-1]

        if len(self.markers) < 1:
            self.tempRubberBand.reset(QgsWkbTypes.LineGeometry)
            if self.isSplit:
                self.finish_geometry(not_really_finished=True)
                self.symbol.setColor(Qt.red)
                self.isFinished = False
                self.reverse_points()
                self.tempRubberBand.addPoint(self.markers[-1].center())
                self.tempRubberBand.addPoint(self.lastMapCoord)
        else:
            self.tempRubberBand.movePoint(0, self.markers[-1].center())

        if self.isSplit:
            self.closingRubberBand.movePoint(self.markers[-1].center())

        self.handleMove()

    def select_mode(self):
        if len(self.markers) < 2:
            return

        self.finish_geometry(not_really_finished=True)
        self.symbol.setColor(Qt.red)
        self.rubberBand.updateCanvas()
        self.isSelecting = True
        self.setCursor(Qt.OpenHandCursor)

    def recover_to_normal_mode(self):
        if self.snappingMarker:
            self.canvas.scene().removeItem(self.snappingMarker)
        if self.selectingMarker:
            self.canvas.scene().removeItem(self.selectingMarker)

        self.isSelecting = False
        self.setCursor(Qt.CrossCursor)
        self.isFinished = False
        self.finish_geometry()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.undo_last_point()

        if e.key() == Qt.Key_R:
            self.reverse_points()

        if e.key() == Qt.Key_Control:
            self.isSnapping = True
            self.handleMove()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Control:
            self.isSnapping = False
            self.handleMove()

    def canvasReleaseEvent(self, e):
        if self.isSelecting:
            if e.button() == Qt.RightButton:
                self.recover_to_normal_mode()
                return
            elif e.button() != Qt.LeftButton:
                return

            if not self.selectingMarker or len(self.markers) < 1:
                return

            if self.markers[0].center() == self.selectingMarker.center():
                self.reverse_points()

            # find indexes of vertices:
            index_list = [
                i
                for i, m in enumerate(self.markers)
                if m.center() == self.selectingMarker.center()
            ]
            if len(index_list) < 1:
                return
            rotate_amount = index_list[0] + 1
            # rotate markers inside list so that blue one is now last:
            self.markers2 = self.markers[rotate_amount:]
            self.markers = self.markers[:rotate_amount]
            # clear and fill rubberband so that the point to remove is last:
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
            for marker in self.markers:
                self.rubberBand.addPoint(marker.center())

            self.isFinished = False
            self.isSelecting = False
            self.setCursor(Qt.CrossCursor)

            # remove last point and vertex with undo function:
            self.undo_last_point()

            self.isSplit = True

            self.resetClosingRubber()
            self.resetTempRubber()
            for marker in reversed(self.markers2):
                self.closingRubberBand.addPoint(marker.center())

            if len(self.markers2) == 0:
                self.isSplit = False
                self.tempRubberBand.addPoint(self.markers[-1].center())
                self.tempRubberBand.addPoint(self.lastMapCoord)
            else:
                self.tempRubberBand.addPoint(self.markers[-1].center())
                self.tempRubberBand.addPoint(self.lastMapCoord)
                self.tempRubberBand.addPoint(self.markers2[0].center())
                self.closingRubberBand.addPoint(self.markers[-1].center())

            # as we are now in normal mode this now draws a temporary point:
            self.handleMove()
            return

        if self.isFinished:
            return

        if e.button() == Qt.RightButton:
            self.finish_geometry()
            return
        elif e.button() != Qt.LeftButton:
            return

        # use correct clicking point for adding:
        click_point = self.toMapCoordinates(e.pos())
        if self.isSnapping:
            snappingPoint = self.getSnappingPoint()
            if snappingPoint:
                click_point = snappingPoint.center()

        self.rubberBand.addPoint(click_point)
        vertexMarker = QgsVertexMarker(self.canvas)
        vertexMarker.setCenter(click_point)
        vertexMarker.setColor(Qt.black)
        vertexMarker.setFillColor(Qt.red)
        vertexMarker.setIconSize(7)
        vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
        vertexMarker.setPenWidth(1)
        self.markers.append(vertexMarker)

        if self.tempRubberBand.numberOfVertices() < 1:
            self.tempRubberBand.addPoint(self.markers[-1].center())
            self.tempRubberBand.addPoint(click_point)

        self.tempRubberBand.movePoint(0, click_point)
        self.closingRubberBand.movePoint(click_point)

    def canvasMoveEvent(self, e):
        self.lastMapCoord = self.toMapCoordinates(e.pos())
        self.handleMove()

    def handleMove(self):
        if self.snappingMarker:
            self.canvas.scene().removeItem(self.snappingMarker)
        if self.selectingMarker:
            self.canvas.scene().removeItem(self.selectingMarker)

        if self.isSelecting:
            snappingPoint = self.getSnappingPoint()
            if snappingPoint:
                # mark nearest vertex blue:
                self.selectingMarker = QgsVertexMarker(self.canvas)
                self.selectingMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
                self.selectingMarker.setCenter(snappingPoint)
                self.selectingMarker.setColor(Qt.blue)
                self.selectingMarker.setFillColor(Qt.red)
                self.selectingMarker.setIconSize(9)
                self.selectingMarker.setPenWidth(3)
            return

        if not self.isSplit and (self.isFinished or len(self.markers) < 1):
            return

        movingPoint = self.lastMapCoord
        if self.isSnapping:
            snappingPoint = self.getSnappingPoint()
            if snappingPoint:
                movingPoint = snappingPoint
                # mark nearest vertex yellow:
                self.snappingMarker = QgsVertexMarker(self.canvas)
                self.snappingMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
                self.snappingMarker.setCenter(snappingPoint)
                self.snappingMarker.setColor(Qt.yellow)
                self.snappingMarker.setFillColor(Qt.red)
                self.snappingMarker.setIconSize(9)
                self.snappingMarker.setPenWidth(3)

        # draw a temporary point at mouse pointer while moving:
        if self.isSplit:
            self.tempRubberBand.movePoint(1, movingPoint)
        else:
            self.tempRubberBand.movePoint(movingPoint)

    def setSnappingPoints(self, list_of_points):
        self.list_of_snapping_points = list_of_points

    def getSnappingPoint(self):
        if self.isSelecting:
            if not self.markers or len(self.markers) < 1:
                return None
            points_list = [vertex.center() for vertex in self.markers]
        else:
            if (
                not self.list_of_snapping_points
                or len(self.list_of_snapping_points) < 1
            ):
                return None
            points_list = self.list_of_snapping_points

        move_point = self.lastMapCoord
        x = move_point.x()
        y = move_point.y()
        distances = [p.distance(x, y) for p in points_list]
        index_of_nearest = min(range(len(distances)), key=distances.__getitem__)

        # tolerance needs to be recalculated as user can zoom while moving
        pt1 = QPoint(x, y)
        pt2 = QPoint(x + 20, y)
        layerPt1 = self.toLayerCoordinates(self.canvas.layer(0), pt1)
        layerPt2 = self.toLayerCoordinates(self.canvas.layer(0), pt2)
        tolerance = layerPt2.x() - layerPt1.x()
        if distances[index_of_nearest] > tolerance:
            return None

        return points_list[index_of_nearest]

    def resetTempRubber(self):
        self.tempRubberBand.reset(QgsWkbTypes.LineGeometry)

    def resetClosingRubber(self):
        self.closingRubberBand.reset(QgsWkbTypes.LineGeometry)
        self.closingRubberBand.setLineStyle(Qt.DashLine)
        self.closingRubberBand.setStrokeColor(Qt.black)
        self.closingRubberBand.setSecondaryStrokeColor(QColor(255, 0, 0, 100))
        self.closingRubberBand.setWidth(1)


class PointMapTool(QgsMapTool):
    # darf nicht in den Konstruktor:
    finished_geometry = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        self.canvas = canvas
        super().__init__(self.canvas)

        self.markers = []
        self.list_of_snapping_points = None
        self.snappingMarker = None
        self.selectingMarker = None
        self.lastMapCoord = None
        self.isFinished = False
        self.isSelecting = False
        self.setCursor(Qt.CrossCursor)
        self.isSnapping = False

        self.reset_geometry()

    def reset_geometry(self):
        # remove all vertices:
        for marker in self.markers:
            self.canvas.scene().removeItem(marker)
        self.markers = []

        self.isFinished = False
        self.isSelecting = False
        self.setCursor(Qt.CrossCursor)

        self.finished_geometry.emit(QgsGeometry())

    def get_geometry(self):
        return QgsGeometry.fromPointXY(self.markers[0].center())

    def set_geometry_for_editing(self, geometry: QgsGeometry):
        self.reset_geometry()
        for vertex in geometry.vertices():
            point = QgsPointXY(vertex.x(), vertex.y())
            vertexMarker = QgsVertexMarker(self.canvas)
            vertexMarker.setCenter(point)
            vertexMarker.setColor(Qt.black)
            vertexMarker.setFillColor(Qt.red)
            vertexMarker.setIconSize(7)
            vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
            vertexMarker.setPenWidth(1)
            self.markers.append(vertexMarker)
        self.undo_last_point()

    def finish_geometry(self, not_really_finished=False):
        if self.isFinished or len(self.markers) < 1:
            return

        self.isFinished = True

        if not not_really_finished:
            self.finished_geometry.emit(self.get_geometry())

    def undo_last_point(self):
        if self.isSelecting:
            self.recover_to_normal_mode()

        if self.isFinished:
            self.isFinished = False
            self.finished_geometry.emit(QgsGeometry())

        if len(self.markers) > 0:
            self.canvas.scene().removeItem(self.markers[-1])
            del self.markers[-1]

        self.handleMove()

    def select_mode(self):
        if len(self.markers) < 1:
            return

        self.finish_geometry(not_really_finished=True)
        self.isSelecting = True
        self.setCursor(Qt.OpenHandCursor)

    def recover_to_normal_mode(self):
        if self.snappingMarker:
            self.canvas.scene().removeItem(self.snappingMarker)
        if self.selectingMarker:
            self.canvas.scene().removeItem(self.selectingMarker)

        self.isSelecting = False
        self.setCursor(Qt.CrossCursor)
        self.isFinished = False
        self.finish_geometry()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.undo_last_point()

        if e.key() == Qt.Key_Control:
            self.isSnapping = True
            self.handleMove()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Control:
            self.isSnapping = False
            self.handleMove()

    def canvasReleaseEvent(self, e):
        if self.isSelecting:
            if e.button() == Qt.RightButton:
                self.recover_to_normal_mode()
                return
            elif e.button() != Qt.LeftButton:
                return

            if not self.selectingMarker:
                return

            # find indexes of vertices:
            index_list = [
                i
                for i, m in enumerate(self.markers)
                if m.center() == self.selectingMarker.center()
            ]
            if len(index_list) < 1:
                return
            self.isFinished = False
            self.isSelecting = False
            self.setCursor(Qt.CrossCursor)

            # remove last point and vertex with undo function:
            self.undo_last_point()

            # as we are now in normal mode this now draws a temporary point:
            self.handleMove()
            return

        if self.isFinished:
            return

        if e.button() == Qt.RightButton:
            self.finish_geometry()
            return
        elif e.button() != Qt.LeftButton:
            return

        # use correct clicking point for adding:
        click_point = self.toMapCoordinates(e.pos())
        if self.isSnapping:
            snappingPoint = self.getSnappingPoint()
            if snappingPoint:
                click_point = snappingPoint.center()

        self.reset_geometry()
        vertexMarker = QgsVertexMarker(self.canvas)
        vertexMarker.setCenter(click_point)
        vertexMarker.setColor(Qt.black)
        vertexMarker.setFillColor(Qt.red)
        vertexMarker.setIconSize(7)
        vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
        vertexMarker.setPenWidth(1)
        self.markers.append(vertexMarker)

    def canvasMoveEvent(self, e):
        self.lastMapCoord = self.toMapCoordinates(e.pos())
        self.handleMove()

    def handleMove(self):
        if self.snappingMarker:
            self.canvas.scene().removeItem(self.snappingMarker)
        if self.selectingMarker:
            self.canvas.scene().removeItem(self.selectingMarker)

        if self.isSelecting:
            snappingPoint = self.getSnappingPoint()
            if snappingPoint:
                # mark nearest vertex blue:
                self.selectingMarker = QgsVertexMarker(self.canvas)
                self.selectingMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
                self.selectingMarker.setCenter(snappingPoint)
                self.selectingMarker.setColor(Qt.blue)
                self.selectingMarker.setFillColor(Qt.red)
                self.selectingMarker.setIconSize(9)
                self.selectingMarker.setPenWidth(3)
            return

        if self.isFinished or len(self.markers) < 1:
            return

        if self.isSnapping:
            snappingPoint = self.getSnappingPoint()
            if snappingPoint:
                # mark nearest vertex yellow:
                self.snappingMarker = QgsVertexMarker(self.canvas)
                self.snappingMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
                self.snappingMarker.setCenter(snappingPoint)
                self.snappingMarker.setColor(Qt.yellow)
                self.snappingMarker.setFillColor(Qt.red)
                self.snappingMarker.setIconSize(9)
                self.snappingMarker.setPenWidth(3)

    def setSnappingPoints(self, list_of_points):
        self.list_of_snapping_points = list_of_points

    def getSnappingPoint(self):
        if self.isSelecting:
            if not self.markers or len(self.markers) < 1:
                return None
            points_list = [vertex.center() for vertex in self.markers]
        else:
            if (
                not self.list_of_snapping_points
                or len(self.list_of_snapping_points) < 1
            ):
                return None
            points_list = self.list_of_snapping_points

        move_point = self.lastMapCoord
        x = move_point.x()
        y = move_point.y()
        distances = [p.distance(x, y) for p in points_list]
        index_of_nearest = min(range(len(distances)), key=distances.__getitem__)

        # tolerance needs to be recalculated as user can zoom while moving
        pt1 = QPoint(x, y)
        pt2 = QPoint(x + 20, y)
        layerPt1 = self.toLayerCoordinates(self.canvas.layer(0), pt1)
        layerPt2 = self.toLayerCoordinates(self.canvas.layer(0), pt2)
        tolerance = layerPt2.x() - layerPt1.x()
        if distances[index_of_nearest] > tolerance:
            return None

        return points_list[index_of_nearest]
