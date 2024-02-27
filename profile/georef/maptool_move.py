from qgis.gui import QgsMapTool
from qgis.PyQt.QtCore import Qt, pyqtSignal

class MapToolMove(QgsMapTool):

    pressSignal = pyqtSignal('QgsPointXY')
    releaseSignal = pyqtSignal('QgsPointXY')
    moveSignal = pyqtSignal('QgsPointXY')

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.active = False
        self.setCursor(Qt.CrossCursor)

    def canvasPressEvent(self, event):

        self.active = True

        self.startPoint = self.toMapCoordinates(event.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True

        self.pressSignal.emit(self.startPoint)

    def canvasMoveEvent(self, event):
        if self.active == True:
            x = event.pos().x()
            y = event.pos().y()

            point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)
            self.moveSignal.emit(point)

    def canvasReleaseEvent(self, event):
        if self.active == True:
            #Get the click
            x = event.pos().x()
            y = event.pos().y()

            point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)

            self.releaseSignal.emit(point)

            self.active = False

    def activate(self):
        self.setCursor(Qt.CrossCursor)

    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.deactivated.emit()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
