"""Schema of the profildata_* tables in the project GeoPackage.

- profildata_E_Point, _E_Line, _E_Polygon mirror the fields of the E_ layer
  without its primary key (the fid is assigned by the GeoPackage) plus
  aar_direction.
- profildata_gcp_points has a fixed column list; the order is the documented
  layout for the plan export and is kept on purpose.
"""
from qgis.core import QgsField, QgsVectorLayer
from qgis.PyQt.QtCore import QVariant

from ....common.profile_number import PROFILE_NUMBER_MAX_LENGTH

PROFILDATA_PREFIX = "profildata_"
GCP_TABLE_NAME = PROFILDATA_PREFIX + "gcp_points"
AAR_DIRECTION_MAX_LENGTH = 20  # "original", "horizontal", "absolute height"

# (field name, key in the gcps of the .meta file)
GCP_COLUMNS = (
    ("obj_uuid", "obj_uuid"),
    ("ptnr", "ptnr"),
    ("input_x", "input_x"),
    ("input_z", "input_z"),
    ("aar_x", "aar_x"),
    ("aar_z", "aar_z"),
    ("x_orig", "original_x"),
    ("y_orig", "original_y"),
    ("z_orig", "original_z"),
    ("aar_distance", "aar_distance"),
)
GCP_TEXT_COLUMNS = ("obj_uuid", "ptnr")


def aar_direction_field() -> QgsField:
    return QgsField("aar_direction", QVariant.String, len=AAR_DIRECTION_MAX_LENGTH)


def gcp_fields() -> list:
    """Field definitions of profildata_gcp_points, in table order."""
    fields = []
    for name, _ in GCP_COLUMNS:
        if name in GCP_TEXT_COLUMNS:
            fields.append(QgsField(name, QVariant.String))
        else:
            fields.append(QgsField(name, QVariant.Double))
    fields.append(aar_direction_field())
    fields.append(QgsField("prof_nr", QVariant.String, len=PROFILE_NUMBER_MAX_LENGTH))
    return fields


def profildata_fields(source_layer: QgsVectorLayer) -> list:
    """Field definitions of profildata_<E_layer>: the E_ layer's fields without its
    primary key plus aar_direction."""
    pk_indexes = set(source_layer.dataProvider().pkAttributeIndexes())
    fields = [
        QgsField(field)
        for index, field in enumerate(source_layer.fields())
        if index not in pk_indexes and field.name() != "fid"
    ]
    fields.append(aar_direction_field())
    return fields
