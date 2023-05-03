from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QSizePolicy, QAction
from qgis.core import QgsGeometry, QgsRasterLayer, QgsWkbTypes
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker


class DrawPolygonWindow(QMainWindow):
    """!
    for testing PolygonMapTool
    """

    def __init__(self):
        super().__init__()

        self.canvas = QgsMapCanvas()
        self.canvas.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.canvas.setCanvasColor(Qt.lightGray)
        self.canvas.enableAntiAliasing(True)

        self.imageLayer = None

        self.setCentralWidget(self.canvas)

        self.actionConnect = QAction("Linienzug schließen", self)
        self.actionReset = QAction("Reset", self)
        self.actionUndo = QAction("remove last vertex ESC", self)

        self.actionConnect.triggered.connect(self.finish_polygon)
        self.actionReset.triggered.connect(self.reset)
        self.actionUndo.triggered.connect(self.undo)

        self.toolbar = self.addToolBar("Canvas actions")
        # ensure user can't close the toolbar
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)

        self.toolbar.addAction(self.actionConnect)
        self.toolbar.addAction(self.actionReset)
        self.toolbar.addAction(self.actionUndo)

        self.toolPan = QgsMapToolPan(self.canvas)

        self.toolDraw = PolygonMapTool(self.canvas)

        # set draw tool by default
        self.canvas.setMapTool(self.toolDraw)

    def finish_polygon(self):
        self.toolDraw.finish_polygon()

    def reset(self):
        self.toolDraw.reset()

    def undo(self):
        self.toolDraw.undo()

    def showWindow(self, raster_image_path: str):
        self.imageLayer = QgsRasterLayer(raster_image_path, "Profile image")
        if self.imageLayer.isValid():
            self.canvas.setDestinationCrs(self.imageLayer.crs())
            self.canvas.setExtent(self.imageLayer.extent())
            self.canvas.setLayers([self.imageLayer])

        self.show()


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
        # a flag indicating when a single polygon is finished
        self.finished = False
        self.isMoving = False

        self.reset()

    def reset(self):
        """Empties the canvas and the points gathered thus far"""
        self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        for marker in self.markers:
            self.canvas.scene().removeItem(marker)
        self.markers = []
        self.rubberBand.setStrokeColor(Qt.red)

        self.finished = False
        self.isMoving = False

        self.polygon_drawn.emit(QgsGeometry())

    def keyPressEvent(self, e):
        """Pressing ESC undo. Pressing enter connects the polygon"""
        if e.key() == 16777216:
            self.undo()
        elif e.key() == 16777220:
            self.finish_polygon()

    def undo(self):
        if self.finished:
            self.finished = False
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

    def canvasReleaseEvent(self, e):
        if self.finished:
            return

        if e.button() == Qt.RightButton:
            self.finish_polygon()
            return

        if self.isMoving:
            self.rubberBand.removeLastPoint()
            self.isMoving = False

        click_point = self.toMapCoordinates(e.pos())
        self.rubberBand.addPoint(click_point, True)
        vertexMarker = QgsVertexMarker(self.canvas)
        vertexMarker.setCenter(click_point)
        vertexMarker.setColor(Qt.red)
        vertexMarker.setIconSize(5)
        vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_BOX)
        vertexMarker.setPenWidth(3)
        self.markers.append(vertexMarker)

        self.rubberBand.show()

    def canvasMoveEvent(self, e):
        if self.finished or self.rubberBand.numberOfVertices() < 1:
            return

        if self.isMoving:
            self.rubberBand.removeLastPoint()

        move_point = self.toMapCoordinates(e.pos())
        self.rubberBand.addPoint(move_point, True)
        self.isMoving = True

        self.rubberBand.show()

    def finish_polygon(self):
        if self.finished:
            return

        if self.isMoving:
            self.rubberBand.removeLastPoint()
            self.isMoving = False

        self.finished = True
        self.rubberBand.setStrokeColor(Qt.darkGreen)

        if self.rubberBand.numberOfVertices() > 2:
            self.rubberBand.closePoints()

        self.polygon_drawn.emit(self.getPolygon())
        print(self.getPolygon())

    def getPolygon(self):
        return self.rubberBand.asGeometry()
