import logging

from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtGui import QCursor
from qgis.core import QgsVectorLayer, QgsFeature
from qgis.gui import QgsMapToolIdentify

LOGGER = logging.getLogger(__name__)


class IdentifyGeometry(QgsMapToolIdentify):
    geomIdentified = pyqtSignal(QgsVectorLayer, QgsFeature)

    def __init__(self, canvas, layerType="AllLayers"):
        self.layerType = getattr(QgsMapToolIdentify, layerType)
        self.canvas = canvas
        QgsMapToolIdentify.__init__(self, canvas)
        self.setCursor(QCursor(Qt.WhatsThisCursor))

    def canvasReleaseEvent(self, mouseEvent):
        try:
            results = self.identify(mouseEvent.x(), mouseEvent.y(), self.LayerSelection, self.layerType)
        except Exception as e:
            LOGGER.error("IdentifyGeometry: identify failed: %s", e)
            results = []
        if len(results) > 0:
            LOGGER.debug("IdentifyGeometry picked: %s", results[0].mFeature.attributes())
            self.geomIdentified.emit(results[0].mLayer, QgsFeature(results[0].mFeature))
