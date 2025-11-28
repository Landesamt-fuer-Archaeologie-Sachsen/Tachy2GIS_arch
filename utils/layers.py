from enum import Enum

from qgis.core import QgsProject, QgsVectorLayer


class T2gLayers(Enum):
    Point = "E_Point"
    Line = "E_Line"
    Polygon = "E_Polygon"
    Messpunkte = "Messpunkte"

    @staticmethod
    def getPointLayer():
        return findLayerInProject(T2gLayers.Point.value)

    @staticmethod
    def getLineLayer():
        return findLayerInProject(T2gLayers.Line.value)

    @staticmethod
    def getPolygonLayer():
        return findLayerInProject(T2gLayers.Polygon.value)

    @staticmethod
    def getMesspunkteLayer():
        return findLayerInProject(T2gLayers.Messpunkte.value)

    @staticmethod
    def getEditLayers():
        return [
            T2gLayers.getPointLayer(),
            T2gLayers.getLineLayer(),
            T2gLayers.getPolygonLayer(),
        ]


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
