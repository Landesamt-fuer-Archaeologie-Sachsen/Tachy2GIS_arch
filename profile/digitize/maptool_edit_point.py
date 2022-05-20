import math
from qgis.gui import QgsMapToolIdentify, QgsMapToolIdentifyFeature
from qgis.core import QgsGeometry

from ..publisher import Publisher
from .maptool_mixin import MapToolMixin

class MapToolEditPoint(QgsMapToolIdentifyFeature, MapToolMixin):
    def __init__(self, canvas, iFace, rotationCoords):
        self.__iface = iFace

        self.pup = Publisher()

        self.digiPointLayer = None

        self.dragging = False
        self.feature = None

        self.rotationCoords = rotationCoords

        self.canvas = canvas

        self.snapping = False

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

            if self.snapping is True:
                pointXY, position = self.snapToNearestVertex(self.canvas, event.pos())
            else:
                pointXY = self.canvas.getCoordinateTransform().toMapCoordinates(event.x(), event.y())

            geometry = QgsGeometry.fromPointXY(pointXY)

            self.digiPointLayer.changeGeometry(self.feature.id(), geometry)

            self.canvas.refresh()

    def canvasReleaseEvent(self, event):
        self.dragging = False
        self.feature = None

    def setDigiPointLayer(self, digiPointLayer):
        self.digiPointLayer = digiPointLayer

    def setSnapping(self, enableSnapping):
        if enableSnapping is True:
            self.snapping = True
        else:
            self.snapping = False