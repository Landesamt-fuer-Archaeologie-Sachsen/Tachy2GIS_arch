from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QSizePolicy, QAction
from qgis.core import QgsGeometry, QgsRasterLayer
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker


class DrawPolygonWindow(QMainWindow):
    """!
    for testing PolygonMapTool
    """

    def __init__(self):
        super().__init__()

        self.canvas = QgsMapCanvas()
        self.canvas.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.canvas.setCanvasColor(Qt.white)
        self.canvas.enableAntiAliasing(True)

        self.imageLayer = None

        self.setCentralWidget(self.canvas)

        self.actionConnect = QAction("Linienzug schließen", self)
        self.actionClear = QAction("Reset", self)
        self.actionReady = QAction("Fertig", self)

        self.actionClear.triggered.connect(self.clear)
        self.actionConnect.triggered.connect(self.finish_polygon)

        self.toolbar = self.addToolBar("Canvas actions")
        # ensure user can't close the toolbar
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)

        self.toolbar.addAction(self.actionConnect)
        self.toolbar.addAction(self.actionClear)
        self.toolbar.addAction(self.actionReady)

        self.toolPan = QgsMapToolPan(self.canvas)

        self.toolDraw = PolygonMapTool(self.canvas)

        # set draw tool by default
        self.canvas.setMapTool(self.toolDraw)

    def clear(self):
        self.toolDraw.reset()

    def finish_polygon(self):
        self.toolDraw.finishPolygon()

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
        # rubberband class gives the user visual feedback of the drawing
        self.rubberBand = QgsRubberBand(self.canvas)

        self.rubberBand.setStrokeColor(Qt.red)
        # RGB color values, last value indicates transparency (0-255)
        self.rubberBand.setFillColor(QColor(255, 255, 255, 60))
        self.rubberBand.setWidth(3)

        self.points = []
        self.markers = []
        # a flag indicating when a single polygon is finished
        self.finished = False
        self.poly_bbox = False
        self.double_click_flag = False
        self.reset()

    def reset(self):
        """Empties the canvas and the points gathered thus far"""
        self.rubberBand.reset()
        self.poly_bbox = False
        self.points.clear()
        for marker in self.markers:
            self.canvas.scene().removeItem(marker)
        self.rubberBand.setStrokeColor(Qt.red)
        self.polygon_drawn.emit(QgsGeometry())

    def keyPressEvent(self, e):
        """Pressing ESC resets the canvas. Pressing enter connects the polygon"""
        if e.key() == 16777216:
            self.reset()
        if e.key() == 16777220:
            self.finishPolygon()

    def canvasDoubleClickEvent(self, e):
        """Finishes the polygon on double click"""
        self.double_click_flag = True
        self.finishPolygon()

    def canvasReleaseEvent(self, e):
        if self.double_click_flag:
            self.double_click_flag = False
            return

        # if the finished flag is activated, the canvas will be reset
        # for a new polygon
        if self.finished:
            self.reset()
            self.finished = False

        click_point = self.toMapCoordinates(e.pos())
        self.rubberBand.addPoint(click_point, True)
        self.points.append(click_point)
        self.rubberBand.show()

        vertexMarker = QgsVertexMarker(self.canvas)
        vertexMarker.setCenter(click_point)
        vertexMarker.setColor(Qt.red)
        vertexMarker.setIconSize(5)
        vertexMarker.setIconType(QgsVertexMarker.IconType.ICON_BOX)
        vertexMarker.setPenWidth(3)
        self.markers.append(vertexMarker)

        if e.button() == Qt.RightButton:
            self.finishPolygon()

    def finishPolygon(self):
        if self.finished:
            return

        self.finished = True
        self.rubberBand.setStrokeColor(Qt.darkGreen)

        if len(self.points) > 2:
            first_point = self.points[0]
            self.points.append(first_point)
            self.rubberBand.closePoints()
            self.rubberBand.addPoint(first_point, True)
            # a polygon is created and added to the map for visual purposes
            map_polygon = QgsGeometry.fromPolygonXY([self.points])
            self.rubberBand.setToGeometry(map_polygon)
            # get the bounding box of this new polygon
            self.poly_bbox = self.rubberBand.asGeometry().boundingBox()

        self.polygon_drawn.emit(self.getPolygon())

    def getPoints(self):
        return self.points

    def getPolygon(self):
        return self.rubberBand.asGeometry()
