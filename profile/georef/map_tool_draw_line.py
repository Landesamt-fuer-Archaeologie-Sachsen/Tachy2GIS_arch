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
        self.markers2 = []
        self.lastMapCoord = None
        self.isFinished = False
        self.isSelecting = False
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
                "head_length": "2",
                "head_thickness": "0.8",
                "color": "red",
            }
        )
        self.symbol.changeSymbolLayer(0, arrow)

        self.tempRubberBand = QgsRubberBand(self.canvas)
        self.resetTempRubber()
        self.closingRubberBand = QgsRubberBand(self.canvas)
        self.resetClosingRubber()
        self.rubberBand = QgsRubberBand(self.canvas)
        self.rubberBand.setSymbol(self.symbol)

        self.reset_polygon()

    def reset_polygon(self):
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

        self.polygon_drawn.emit(QgsGeometry())

    def get_polygon(self):
        return self.rubberBand.asGeometry()

    def finish_polygon(self):
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

        self.polygon_drawn.emit(self.get_polygon())

    def undo_last_point(self):
        if self.isSelecting:
            self.recover_to_normal_mode()

        if self.isFinished:
            self.symbol.setColor(Qt.red)
            self.isFinished = False
            self.polygon_drawn.emit(QgsGeometry())

        self.rubberBand.removeLastPoint()
        if len(self.markers) > 0:
            self.canvas.scene().removeItem(self.markers[-1])
            del self.markers[-1]

        if self.isSplit:
            if len(self.markers) > 0:
                self.tempRubberBand.movePoint(self.markers[-1].center())
                self.closingRubberBand.movePoint(self.markers[-1].center())
            else:
                self.tempRubberBand.movePoint(self.markers2[0].center())
                self.closingRubberBand.movePoint(self.markers2[0].center())
        else:
            self.resetTempRubber()
            if len(self.markers) > 0:
                self.resetTempRubber()
                self.tempRubberBand.addPoint(self.markers[-1].center())
                self.tempRubberBand.addPoint(self.lastMapCoord)

        self.handleMove()

    def select_mode(self):
        if len(self.markers) < 2:
            return

        self.finish_polygon()
        self.symbol.setColor(Qt.red)
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
            rotate_amount = index_list[0] + 1
            # rotate markers inside list so that blue one is now last:
            self.markers2 = self.markers[rotate_amount:]
            self.markers = self.markers[:rotate_amount]
            # clear and fill rubberband so that the point to remove is last:
            self.rubberBand.reset(QgsWkbTypes.LineGeometry)
            for marker in self.markers:
                self.rubberBand.addPoint(marker.center())
            self.isSplit = True
            self.isFinished = False
            self.isSelecting = False

            # remove last point and vertex with undo function:
            self.undo_last_point()

            self.resetClosingRubber()
            self.resetTempRubber()
            for marker in reversed(self.markers2):
                self.closingRubberBand.addPoint(marker.center())

            if len(self.markers) == 0:
                self.rubberBand.reset(QgsWkbTypes.LineGeometry)
                self.tempRubberBand.addPoint(self.markers2[0].center())
                self.tempRubberBand.addPoint(self.lastMapCoord)
                self.tempRubberBand.addPoint(self.markers2[0].center())
                self.closingRubberBand.addPoint(self.markers2[0].center())
            elif len(self.markers2) == 0:
                self.isSplit = False
                self.tempRubberBand.addPoint(self.markers[-1].center())
                self.tempRubberBand.addPoint(self.lastMapCoord)
            else:
                self.tempRubberBand.addPoint(self.markers2[0].center())
                self.tempRubberBand.addPoint(self.lastMapCoord)
                self.tempRubberBand.addPoint(self.markers[-1].center())
                self.closingRubberBand.addPoint(self.markers[-1].center())

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

        self.rubberBand.addPoint(click_point)
        vertexMarker = QgsVertexMarker(self.canvas)
        vertexMarker.setCenter(click_point)
        vertexMarker.setColor(Qt.black)
        vertexMarker.setFillColor(Qt.red)
        vertexMarker.setIconSize(7)
        vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
        vertexMarker.setPenWidth(1)
        self.markers.append(vertexMarker)

        if self.isSplit:
            self.tempRubberBand.movePoint(click_point)
        else:
            self.resetTempRubber()
            self.tempRubberBand.addPoint(self.markers[-1].center())
            self.tempRubberBand.addPoint(self.lastMapCoord)
        self.closingRubberBand.movePoint(click_point)

    def canvasMoveEvent(self, e):
        self.lastMapCoord = self.toMapCoordinates(e.pos())
        self.handleMove()

    def handleMove(self):
        # print(
        #     "m1",
        #     len(self.markers),
        #     "rb",
        #     self.rubberBand.numberOfVertices(),
        #     "m2",
        #     len(self.markers2),
        #     "cr",
        #     self.closingRubberBand.numberOfVertices(),
        #     "tr",
        #     self.tempRubberBand.numberOfVertices(),
        #     "fin" if self.isFinished else "",
        #     "sel" if self.isSelecting else "",
        #     "sna" if self.isSnapping else "",
        #     "spl" if self.isSplit else "",
        #     # self.rubberBand.asGeometry()
        # )
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

        if not self.isSplit and (self.isFinished or len(self.markers) < 1):
            return

        movingPoint = self.lastMapCoord
        if self.isSnapping:
            snappingMarker = self.getSnappingMarker()
            if snappingMarker:
                movingPoint = snappingMarker.center()
                # mark nearest vertex yellow:
                snappingMarker.setColor(Qt.yellow)
                snappingMarker.setIconSize(9)
                snappingMarker.setPenWidth(3)

        # draw a temporary point at mouse pointer while moving:
        if self.isSplit:
            self.tempRubberBand.movePoint(1, movingPoint)
        else:
            self.tempRubberBand.movePoint(movingPoint)

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

    def resetTempRubber(self):
        self.tempRubberBand.reset(QgsWkbTypes.LineGeometry)
        self.tempRubberBand.setLineStyle(Qt.DotLine)
        self.tempRubberBand.setStrokeColor(Qt.white)
        self.tempRubberBand.setSecondaryStrokeColor(QColor(0, 0, 255, 100))
        self.tempRubberBand.setWidth(1)

    def resetClosingRubber(self):
        self.closingRubberBand.reset(QgsWkbTypes.LineGeometry)
        self.closingRubberBand.setLineStyle(Qt.DashLine)
        self.closingRubberBand.setStrokeColor(Qt.black)
        self.closingRubberBand.setSecondaryStrokeColor(QColor(255, 0, 0, 100))
        self.closingRubberBand.setWidth(1)
