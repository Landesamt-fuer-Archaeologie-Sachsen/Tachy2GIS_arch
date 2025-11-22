from enum import Enum

from qgis.core import QgsProject, QgsVectorLayer


class T2gLayers(Enum):
    Point = "E_Point"
    Line = "E_Line"
    Polygon = "E_Polygon"
    Messpunkte = "Messpunkte"


def findLayerInProject(name):
    mapLayers = QgsProject.instance().mapLayers()
    for lyr in mapLayers.values():
        if lyr.name() == name:
            return lyr
    return None


def layerHasPendingChanges(layer: QgsVectorLayer):
    buffer = layer.editBuffer()
    if not buffer:
        return False
    return bool(len(buffer.changedGeometries()) + len(buffer.changedAttributeValues()))
