import re

from qgis.core import QgsFeatureRequest, QgsVectorLayer, QgsProject


def getComboboxModelFromLayerConfig(layer: QgsVectorLayer, field_name: str, current_values: dict = None) -> dict:
    if not current_values:
        current_values = {}
    field_idx = layer.fields().indexFromName(field_name)
    if field_idx == -1:
        print(f"Field '{field_name}' not found in layer '{layer.name()}'.")
        return {}
    editor_config = layer.fields().field(field_idx).editorWidgetSetup().config()
    if not editor_config:
        print(f"No editor config found for field '{field_name}' in layer '{layer.name()}'.")
        return {}
    layer_id = editor_config["Layer"]
    key_field = editor_config["Key"]
    value_field = editor_config["Value"]
    layer_filter_expression = editor_config.get("FilterExpression", "")
    filter_expression = replace_current_values(layer_filter_expression, current_values)
    rel_layer = QgsProject.instance().mapLayer(layer_id)
    if not rel_layer:
        print(f"Related layer with ID '{layer_id}' not found in the project.")
        return {}
    return getLookupDict(rel_layer, key_field, value_field, filter_expression)


def replace_current_values(expr: str, values: dict) -> str:
    """Replaces occurrences of current_value('field_name') in the expression with the corresponding value from the
    values dictionary {'field_name': value}. Values can be None, int, float, or str.
    Introduced to handle expressions that include current_value() and deal with the optional whitespace.
    """
    _PATTERN = re.compile(
        r"current_value?\s*\(\s*(['\"])(?P<field_name>[^'\"]+)\1\s*\)",
        re.IGNORECASE,
    )

    def quote(v):
        if v is None:
            return "NULL"
        if isinstance(v, (int, float)):
            return str(v)
        return "'" + str(v).replace("'", "''") + "'"

    return _PATTERN.sub(lambda m: quote(values.get(m.group("field_name"))), expr or "")


def getLookupDict(layer, keyColumn, valueColumn, filterExpression=""):
    lookupDict = {}
    if layer.fields().indexOf(keyColumn) == -1 or layer.fields().indexOf(valueColumn) == -1:
        return lookupDict
    request = QgsFeatureRequest()
    if filterExpression:
        request.setFilterExpression(filterExpression)
    for feature in layer.getFeatures(request):
        lookupDict[feature.attribute(keyColumn)] = feature.attribute(valueColumn)
    return lookupDict
