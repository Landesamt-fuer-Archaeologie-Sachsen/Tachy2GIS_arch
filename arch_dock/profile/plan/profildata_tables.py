"""Access to the profildata_* tables of the project GeoPackage.

Knows nothing about the schema: field definitions come in as parameters.
Existing columns are never changed or removed, the fid is assigned by the
GeoPackage, attributes are matched by field name.
"""
import logging
from contextlib import contextmanager

from qgis.core import (
    QgsExpression,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)

from ....common.utils import is_vsi_cached, set_vsi_cached

LOGGER = logging.getLogger(__name__)


class PlanExportError(Exception):
    """A table could not be prepared or written; the message is meant for the user."""


@contextmanager
def vsi_cache_disabled():
    """GDAL's VSI cache must be off while the GeoPackage is written (network drives)."""
    was_cached = is_vsi_cached()
    if was_cached:
        set_vsi_cached(False)
    try:
        yield
    finally:
        if was_cached:
            set_vsi_cached(True)


def geopackage_table_names(gpkg_path: str) -> list:
    container = QgsVectorLayer(gpkg_path, "", "ogr")
    if not container.isValid():
        raise PlanExportError(f"GeoPackage {gpkg_path} konnte nicht geöffnet werden.")
    return [entry.split("!!::!!")[1] for entry in container.dataProvider().subLayers()]


def create_table(gpkg_path: str, table_name: str, fields: list, wkb_type, crs) -> None:
    """Create an empty table with the given schema in the GeoPackage."""
    template = QgsVectorLayer(QgsWkbTypes.displayString(wkb_type), table_name, "memory")
    template.setCrs(crs)
    template.dataProvider().addAttributes(fields)
    template.updateFields()

    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = table_name
    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    result = QgsVectorFileWriter.writeAsVectorFormatV3(
        template, gpkg_path, QgsProject.instance().transformContext(), options
    )
    if result[0] != QgsVectorFileWriter.NoError:
        raise PlanExportError(f"Tabelle {table_name} konnte nicht angelegt werden: {result[1]}")
    LOGGER.info(f"Tabelle {table_name} im GeoPackage angelegt")


def open_table(gpkg_path: str, table_name: str, fields: list, wkb_type, crs) -> QgsVectorLayer:
    """Open a profildata table, creating it if missing and adding missing columns.

    A different geometry type aborts with a message.
    """
    if table_name not in geopackage_table_names(gpkg_path):
        create_table(gpkg_path, table_name, fields, wkb_type, crs)

    table = QgsVectorLayer(f"{gpkg_path}|layername={table_name}", table_name, "ogr")
    if not table.isValid():
        raise PlanExportError(f"Tabelle {table_name} konnte nicht geöffnet werden: {table.dataProvider().lastError()}")

    if table.geometryType() != QgsWkbTypes.geometryType(wkb_type):
        raise PlanExportError(
            f"Tabelle {table_name} hat den Geometrietyp {QgsWkbTypes.displayString(table.wkbType())}, "
            f"erwartet wird {QgsWkbTypes.displayString(wkb_type)}. Bitte die Tabelle löschen, sie wird neu angelegt."
        )

    existing = set(table.fields().names())
    missing = [field for field in fields if field.name() not in existing]
    if missing:
        names = ", ".join(field.name() for field in missing)
        if not table.dataProvider().addAttributes(missing):
            raise PlanExportError(
                f"Tabelle {table_name}: fehlende Spalten ({names}) konnten nicht ergänzt werden: "
                f"{table.dataProvider().lastError()}"
            )
        table.updateFields()
        LOGGER.warning(f"Tabelle {table_name}: fehlende Spalten ergänzt: {names}")
    return table


def delete_profile_rows(table: QgsVectorLayer, prof_nr: str) -> int:
    """Remove all rows of the given profile number (every aar direction)."""
    if table.fields().indexOf("prof_nr") < 0:
        return 0
    expression = QgsExpression.createFieldEqualityExpression("prof_nr", prof_nr)
    return _delete_where(table, expression, f"Profil {prof_nr}")


def delete_object_rows(table: QgsVectorLayer, obj_uuids) -> int:
    """Remove the rows of the given objects (obj_uuid), e.g. before they are exported again."""
    uuids = sorted({uuid for uuid in obj_uuids if uuid})
    if not uuids or table.fields().indexOf("obj_uuid") < 0:
        return 0
    column = QgsExpression.quotedColumnRef("obj_uuid")
    deleted = 0
    for start in range(0, len(uuids), 500):  # keep the IN list of one request moderate
        values = ", ".join(QgsExpression.quotedValue(uuid) for uuid in uuids[start:start + 500])
        deleted += _delete_where(table, f"{column} IN ({values})", f"{len(uuids)} Objekte")
    return deleted


def _delete_where(table: QgsVectorLayer, expression: str, what: str) -> int:
    ids = [feature.id() for feature in table.getFeatures(QgsFeatureRequest().setFilterExpression(expression))]
    if ids and not table.dataProvider().deleteFeatures(ids):
        raise PlanExportError(
            f"Tabelle {table.name()}: alte Zeilen ({what}) konnten nicht gelöscht werden: "
            f"{table.dataProvider().lastError()}"
        )
    return len(ids)


def table_feature(table: QgsVectorLayer, geometry: QgsGeometry, values: dict) -> QgsFeature:
    """Feature for the table with attributes matched by name; the primary key stays
    unset so that the GeoPackage assigns the fid."""
    fields = table.fields()
    pk_indexes = set(table.dataProvider().pkAttributeIndexes())
    feature = QgsFeature(fields)
    feature.setGeometry(geometry)
    for name, value in values.items():
        index = fields.indexOf(name)
        if index >= 0 and index not in pk_indexes:
            feature.setAttribute(index, value)
    return feature


def append_rows(table: QgsVectorLayer, features: list) -> int:
    if not features:
        return 0
    ok, _ = table.dataProvider().addFeatures(features)
    if not ok:
        raise PlanExportError(
            f"Tabelle {table.name()}: Zeilen konnten nicht angehängt werden: {table.dataProvider().lastError()}"
        )
    return len(features)
