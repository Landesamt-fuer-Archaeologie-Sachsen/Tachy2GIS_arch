"""Export of one georeferenced profile into the profildata_* tables.

Semantics: the profile's objects, rotated into the plan, and its ground control
points are appended; rows they replace are deleted first. By profile number
that is every row of the same profile number (all aar directions); with the
profile buffer, which exports whatever lies inside the buffer regardless of
profile number, it is every row of the same objects (obj_uuid). The ground
control points are always replaced per profile number. The fid is assigned by
the GeoPackage and carries no meaning.
"""
import logging

from qgis.core import (
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsPoint,
    QgsPointXY,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)

from ..rotation_coords import RotationCoords
from .profile_meta import ProfileMeta
from .profildata_schema import GCP_COLUMNS, GCP_TABLE_NAME, PROFILDATA_PREFIX, gcp_fields, profildata_fields
from .profildata_tables import (
    PlanExportError,
    append_rows,
    delete_object_rows,
    delete_profile_rows,
    open_table,
    table_feature,
)

LOGGER = logging.getLogger(__name__)

INPUT_LAYER_NAMES = ("E_Point", "E_Line", "E_Polygon")


def find_input_layers() -> dict:
    """E_Point, E_Line and E_Polygon from the "Eingabelayer" group of the layer tree."""
    layers = {}
    root = QgsProject.instance().layerTreeRoot()
    for group in root.children():
        if isinstance(group, QgsLayerTreeGroup) and group.name() == "Eingabelayer":
            for child in group.children():
                layer = child.layer() if isinstance(child, QgsLayerTreeLayer) else None
                if isinstance(layer, QgsVectorLayer) and layer.name() in INPUT_LAYER_NAMES:
                    layers[layer.name()] = layer
    missing = [name for name in INPUT_LAYER_NAMES if name not in layers]
    if missing:
        raise PlanExportError(f"Eingabelayer nicht gefunden: {', '.join(missing)}")
    return layers


def export_profile(
    meta: ProfileMeta,
    input_layers: dict,
    rotation: RotationCoords,
    buffer_geometry: QgsGeometry,
    use_profile_buffer: bool,
) -> str:
    """Write the profile into the four profildata_* tables of the E_ layers' GeoPackage.

    Objects are selected by profile number, or by the profile buffer when
    use_profile_buffer is set. Returns a summary like "profildata_E_Point 12, ...".
    """
    point_layer = input_layers["E_Point"]
    gpkg_path = point_layer.dataProvider().dataSourceUri().split("|")[0]
    crs = point_layer.crs()
    profile_number = None if use_profile_buffer else meta.prof_nr

    results = []
    for name in INPUT_LAYER_NAMES:
        layer = input_layers[name]
        table = open_table(gpkg_path, PROFILDATA_PREFIX + name, profildata_fields(layer), layer.wkbType(), crs)
        objects = list(_profile_objects(layer, meta, rotation, buffer_geometry, profile_number))
        features = [table_feature(table, geometry, values) for geometry, values in objects]
        if use_profile_buffer:
            deleted = delete_object_rows(table, (values.get("obj_uuid") for _, values in objects))
        else:
            deleted = delete_profile_rows(table, meta.prof_nr)
        results.append(_append(table, deleted, features))

    gcp_table = open_table(gpkg_path, GCP_TABLE_NAME, gcp_fields(), QgsWkbTypes.Point, crs)
    gcp_features = [table_feature(gcp_table, geometry, values) for geometry, values in _gcp_objects(meta)]
    results.append(_append(gcp_table, delete_profile_rows(gcp_table, meta.prof_nr), gcp_features))

    return ", ".join(results)


def _append(table: QgsVectorLayer, deleted: int, features: list) -> str:
    appended = append_rows(table, features)
    LOGGER.debug(f"{table.name()}: {deleted} Zeilen gelöscht, {appended} angehängt")
    return f"{table.name()} {appended}"


def _profile_objects(
    layer: QgsVectorLayer,
    meta: ProfileMeta,
    rotation: RotationCoords,
    buffer_geometry: QgsGeometry,
    profile_number,
):
    """Profile objects of an E_ layer rotated into the plan: (geometry, attributes by name)."""
    if profile_number:
        candidates = layer.getFeatures()
    else:
        candidates = layer.getFeatures(QgsFeatureRequest().setFilterRect(buffer_geometry.boundingBox()))

    for feature in candidates:
        if feature["geo_quelle"] != "profile_object":
            continue
        if profile_number:
            if feature["prof_nr"] != profile_number:
                continue
        elif not feature.geometry().within(buffer_geometry):
            continue

        values = feature.attributeMap()
        values["aar_direction"] = meta.aar_direction
        yield _rotated_geometry(rotation, feature, layer.geometryType(), meta.aar_direction), values


def _rotated_geometry(rotation: RotationCoords, feature: QgsFeature, geometry_type, aar_direction: str) -> QgsGeometry:
    if geometry_type == QgsWkbTypes.PointGeometry:
        rotated = rotation.rotatePointFeatureFromOrg(feature, aar_direction)
        return QgsGeometry(QgsPoint(rotated["x_trans"], rotated["z_trans"], rotated["z_trans"]))
    if geometry_type == QgsWkbTypes.LineGeometry:
        return rotation.rotateLineFeatureFromOrg(feature, aar_direction)
    return rotation.rotatePolygonFeatureFromOrg(feature, aar_direction)


def _gcp_objects(meta: ProfileMeta):
    """Ground control points from the .meta file: (geometry, attributes by name)."""
    for gcp in meta.gcps:
        values = {name: gcp.get(key) for name, key in GCP_COLUMNS}
        values["aar_direction"] = meta.aar_direction
        values["prof_nr"] = meta.prof_nr
        yield QgsGeometry.fromPointXY(QgsPointXY(gcp["aar_x"], gcp["aar_z"])), values
