from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from qgis.core import QgsGeometry, QgsWkbTypes
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker


class PolygonMapTool(QgsMapToolEmitPoint):
    # darf nicht in den Konstruktor:
    polygon_drawn = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        self.canvas = canvas
        super().__init__(self.canvas)
        self.rubberBand = QgsRubberBand(self.canvas)

        # RGB color values, last value indicates transparency (0-255)
        self.rubberBand.setFillColor(QColor(255, 255, 255, 60))
        self.rubberBand.setWidth(3)

        self.markers = []
        self.isFinished = False
        self.isMoving = False
        self.isSelecting = False

        self.reset_polygon()

    def reset_polygon(self):
        # clear points of rubber band:
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        # remove all vertices:
        for marker in self.markers:
            self.canvas.scene().removeItem(marker)
        self.markers = []

        self.rubberBand.setStrokeColor(Qt.red)
        self.isFinished = False

        self.isMoving = False
        self.isSelecting = False

        self.polygon_drawn.emit(QgsGeometry())

    def get_polygon(self):
        return self.rubberBand.asGeometry()

    def finish_polygon(self):
        if self.isFinished:
            return

        if self.isMoving:
            self.rubberBand.removeLastPoint()
            self.isMoving = False

        if self.rubberBand.numberOfVertices() < 2:
            return

        self.isFinished = True
        self.rubberBand.setStrokeColor(Qt.darkGreen)
        self.rubberBand.closePoints()

        self.polygon_drawn.emit(self.get_polygon())

    def undo_last_point(self):
        if self.isFinished:
            # remove closing point:
            self.isFinished = False
            self.rubberBand.removeLastPoint()
            self.rubberBand.setStrokeColor(Qt.red)
            self.polygon_drawn.emit(QgsGeometry())

        if self.isMoving:
            self.rubberBand.removePoint(-2)
        else:
            self.rubberBand.removeLastPoint()

        if len(self.markers) > 0:
            self.canvas.scene().removeItem(self.markers[-1])
            del self.markers[-1]

    def select_mode(self):
        if self.rubberBand.numberOfVertices() < 2:
            return

        self.finish_polygon()
        self.rubberBand.setStrokeColor(Qt.red)
        self.rubberBand.updateCanvas()
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
        if self.isSelecting:
            return

        # pressing ESC:
        if e.key() == 16777216:
            self.undo_last_point()

    def canvasReleaseEvent(self, e):
        if self.isSelecting:
            if e.button() == Qt.RightButton:
                self.recover_to_normal_mode()
                return

            if e.button() != Qt.LeftButton:
                return

            # find indexes of vertices which are blue:
            index_list = [i for i, m in enumerate(self.markers) if m.color() == Qt.blue]
            if len(index_list) != 1:
                # either no vertex was blue or more than one were
                return
            rotate_amount = index_list[0] + 1
            # rotate markers inside list so that blue one is now last:
            self.markers = self.markers[rotate_amount:] + self.markers[:rotate_amount]
            # clear and fill rubberband so that the point to remove is last:
            self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
            for marker in self.markers:
                self.rubberBand.addPoint(marker.center(), False)
            self.rubberBand.show()
            self.isFinished = False
            self.isSelecting = False
            # remove last point and vertex with undo function:
            self.undo_last_point()
            # as we are now in normal mode this now draws a temporary point:
            self.canvasMoveEvent(e)
            return

        if self.isFinished:
            return

        if e.button() == Qt.RightButton:
            self.finish_polygon()
            return

        if self.isMoving:
            # remove temporary point:
            self.rubberBand.removeLastPoint()
            self.isMoving = False

        # use correct clicking point for adding:
        click_point = self.toMapCoordinates(e.pos())
        self.rubberBand.addPoint(click_point, False)
        vertexMarker = QgsVertexMarker(self.canvas)
        vertexMarker.setCenter(click_point)
        vertexMarker.setColor(Qt.black)
        vertexMarker.setFillColor(Qt.red)
        vertexMarker.setIconSize(7)
        vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
        vertexMarker.setPenWidth(1)
        self.markers.append(vertexMarker)

        self.rubberBand.show()

    def canvasMoveEvent(self, e):
        move_point = self.toMapCoordinates(e.pos())

        if self.isSelecting:
            # mark nearest vertex blue:
            for vertex in self.markers:
                vertex.setColor(Qt.black)
                vertex.setIconSize(7)
                vertex.setPenWidth(1)
            x = move_point.x()
            y = move_point.y()
            distances = [p.center().distance(x, y) for p in self.markers]
            index_of_nearest = min(range(len(distances)), key=distances.__getitem__)
            self.markers[index_of_nearest].setColor(Qt.blue)
            self.markers[index_of_nearest].setIconSize(9)
            self.markers[index_of_nearest].setPenWidth(3)
            return

        if self.isFinished or self.rubberBand.numberOfVertices() < 1:
            return

        # draw a temporary point at mouse pointer while moving:
        if self.isMoving:
            self.rubberBand.removeLastPoint()

        self.rubberBand.addPoint(move_point, True)
        self.isMoving = True

        self.rubberBand.show()
