import logging
from enum import Enum

from qgis._core import Qgis, QgsWkbTypes
from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer

LOGGER = logging.getLogger(__name__)


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
            lyr for lyr in [
                T2gLayers.getPointLayer(),
                T2gLayers.getLineLayer(),
                T2gLayers.getPolygonLayer(),
            ] if lyr is not None
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


def isLayerVisible(layer: QgsMapLayer):
    layer_tree_root = QgsProject.instance().layerTreeRoot()
    layer_tree_layer = layer_tree_root.findLayer(layer)
    if not layer_tree_layer:
        return False
    return layer_tree_layer.isVisible()


def is_project_type_of_t2g_arch() -> str:
    geometry_types_per_layer = {
        "E_Point": [Qgis.GeometryType.Point, Qgis.WkbType.PointZ],
        "E_Line": [Qgis.GeometryType.Line, Qgis.WkbType.LineStringZ],
        "E_Polygon": [Qgis.GeometryType.Polygon, Qgis.WkbType.PolygonZ],
    }

    project_instance = QgsProject.instance()
    if not project_instance or not project_instance.fileName():
        return "no project loaded"

    file_extension = project_instance.fileName().split(".")[-1].lower()
    if file_extension != "qgz":
        return "file extension is not qgz"

    layers_to_check = geometry_types_per_layer.keys()
    for layer_name in layers_to_check:
        list_of_layers = project_instance.mapLayersByName(layer_name)

        if not list_of_layers:
            return f"layer {layer_name} not found"

        if len(list_of_layers) > 1:
            return f"layer {layer_name} is ambiguous"

        layer = list_of_layers[0]

        if not layer.dataProvider().dataSourceUri().split("|")[0].lower().endswith(".gpkg"):
            return f"data source is no gpkg: {layer.name()} {layer.dataProvider().dataSourceUri()}"

        field_index = layer.fields().indexFromName("fid")
        if field_index == -1:
            return f"the field 'fid' was not found in the layer {layer.name()}"

        field = layer.fields().at(field_index)
        formula = field.defaultValueDefinition().expression()
        if formula != 'if (count("fid") = 0, 0, maximum("fid") + 1)':
            return (
                f"in layer {layer.name()} fid default value definition is not "
                f'if (count("fid") = 0, 0, maximum("fid") + 1) '
                f"actual value: {formula}"
            )

        general_geom = geometry_types_per_layer[layer_name][0]
        specific_geom = geometry_types_per_layer[layer_name][1]
        if layer.geometryType() != general_geom or layer.wkbType() != specific_geom:
            return (
                f"the geometry type of layer {layer.name()}\n"
                f"has to be: {QgsWkbTypes.geometryDisplayString(general_geom)} "
                f"({QgsWkbTypes.displayString(specific_geom)})\n"
                f"actual value: {QgsWkbTypes.geometryDisplayString(layer.geometryType())} "
                f"({QgsWkbTypes.displayString(layer.wkbType())})"
            )

    return "yes"


