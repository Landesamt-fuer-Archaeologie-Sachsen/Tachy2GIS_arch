from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QColor
from qgis.core import QgsGeometry, QgsWkbTypes, QgsArrowSymbolLayer, QgsSymbol
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker


class PolygonMapTool(QgsMapToolEmitPoint):
    # darf nicht in den Konstruktor:
    polygon_drawn = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        self.canvas = canvas
        super().__init__(self.canvas)

        self.markers = []
        self.lastMapCoord = None
        self.isFinished = False
        self.isSelecting = False
        self.isSnapping = False

        self.reset_polygon()

    def reset_polygon(self):
        # remove all vertices:
        for marker in self.markers:
            self.canvas.scene().removeItem(marker)
        self.markers = []

        self.isFinished = False
        self.isSelecting = False

        self.polygon_drawn.emit(QgsGeometry())

    def get_polygon(self):
        rubberBand = QgsRubberBand(self.canvas)
        rubberBand.addPoint(self.markers[0].center())
        return rubberBand.asGeometry()

    def finish_polygon(self):
        if self.isFinished or len(self.markers) < 1:
            return

        self.isFinished = True

        self.polygon_drawn.emit(self.get_polygon())

    def undo_last_point(self):
        if self.isSelecting:
            self.recover_to_normal_mode()

        if self.isFinished:
            self.isFinished = False
            self.polygon_drawn.emit(QgsGeometry())

        if len(self.markers) > 0:
            self.canvas.scene().removeItem(self.markers[-1])
            del self.markers[-1]

        self.handleMove()

    def select_mode(self):
        if len(self.markers) < 1:
            return

        self.finish_polygon()
        self.isSelecting = True

    def recover_to_normal_mode(self):
        for vertex in self.markers:
            vertex.setColor(Qt.black)
            vertex.setIconSize(7)
            vertex.setPenWidth(1)
        self.isSelecting = False
        self.isFinished = False
        self.finish_polygon()

    def keyPressEvent(self, e):
        # pressing ESC:
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

            # find indexes of vertices which are blue:
            index_list = [i for i, m in enumerate(self.markers) if m.color() == Qt.blue]
            if len(index_list) != 1:
                # either no vertex was blue or more than one were
                return
            self.isFinished = False
            self.isSelecting = False

            # remove last point and vertex with undo function:
            self.undo_last_point()

            # as we are now in normal mode this now draws a temporary point:
            self.handleMove()
            return

        if self.isFinished:
            return

        if e.button() == Qt.RightButton:
            self.finish_polygon()
            return
        elif e.button() != Qt.LeftButton:
            return

        # use correct clicking point for adding:
        click_point = self.toMapCoordinates(e.pos())
        if self.isSnapping:
            snappingMarker = self.getSnappingMarker()
            if snappingMarker:
                click_point = snappingMarker.center()

        self.reset_polygon()
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
        # reset styling:
        for vertex in self.markers:
            vertex.setColor(Qt.black)
            vertex.setIconSize(7)
            vertex.setPenWidth(1)

        if self.isSelecting:
            snappingMarker = self.getSnappingMarker()
            if snappingMarker:
                # mark nearest vertex blue:
                snappingMarker.setColor(Qt.blue)
                snappingMarker.setIconSize(9)
                snappingMarker.setPenWidth(3)
            return

        if self.isFinished or len(self.markers) < 1:
            return

        if self.isSnapping:
            snappingMarker = self.getSnappingMarker()
            if snappingMarker:
                # mark nearest vertex yellow:
                snappingMarker.setColor(Qt.yellow)
                snappingMarker.setIconSize(9)
                snappingMarker.setPenWidth(3)

    def getSnappingMarker(self):
        if len(self.markers) < 1:
            return None

        move_point = self.lastMapCoord
        x = move_point.x()
        y = move_point.y()
        distances = [p.center().distance(x, y) for p in self.markers]
        index_of_nearest = min(range(len(distances)), key=distances.__getitem__)

        # tolerance needs to be recalculated as user can zoom while moving
        pt1 = QPoint(x, y)
        pt2 = QPoint(x + 20, y)
        layerPt1 = self.toLayerCoordinates(self.canvas.layer(0), pt1)
        layerPt2 = self.toLayerCoordinates(self.canvas.layer(0), pt2)
        tolerance = layerPt2.x() - layerPt1.x()
        if distances[index_of_nearest] > tolerance:
            return None

        return self.markers[index_of_nearest]
