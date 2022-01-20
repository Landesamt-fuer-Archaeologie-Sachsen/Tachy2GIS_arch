import math
from PyQt5.QtCore import Qt
from qgis.gui import QgsMapToolIdentify, QgsMapToolIdentifyFeature, QgsVertexMarker
from qgis.core import QgsWkbTypes, QgsFeature, QgsGeometry
from ..publisher import Publisher

class MapToolEditPoint(QgsMapToolIdentifyFeature):
    def __init__(self, canvas, iFace, rotationCoords):
        self.__iface = iFace

        self.pup = Publisher()

        self.digiPointLayer = None

        self.dragging = False
        self.feature = None

        self.rotationCoords = rotationCoords

        self.canvas = canvas

        QgsMapToolIdentifyFeature.__init__(self, self.canvas)

        self.deactivated.connect(self.deactivateLayer)

    def deactivateLayer(self):
        if self.digiPointLayer != None:
            self.digiPointLayer.commitChanges()
            self.digiPointLayer.updateExtents()
            self.digiPointLayer.endEditCommand()

    def canvasPressEvent(self, event):

        found_features = self.identify(event.x(), event.y(), [self.digiPointLayer], QgsMapToolIdentify.TopDownAll)
        identified_features = [f.mFeature for f in found_features]
        if len(identified_features) > 0:
            self.digiPointLayer.startEditing()
            self.dragging = True
            if identified_features[0]['geo_quelle'] == 'profile_object':
                self.feature = identified_features[0]
            else:
                self.dragging = False
                self.feature = None
        else:
            self.dragging = False
            self.feature = None

    def canvasMoveEvent(self, event):
        if self.dragging:

            layerPt = self.canvas.getCoordinateTransform().toMapCoordinates(event.x(), event.y())
            geometry = QgsGeometry.fromPointXY(layerPt)

            self.digiPointLayer.changeGeometry(self.feature.id(), geometry)

            self.canvas.refresh()

    def canvasReleaseEvent(self, event):
        self.dragging = False
        self.feature = None


    def setDigiPointLayer(self, digiPointLayer):
        self.digiPointLayer = digiPointLayer
