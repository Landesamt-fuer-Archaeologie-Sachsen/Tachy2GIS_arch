import re

from qgis.core import QgsFeatureRequest, QgsVectorLayer, QgsProject


def getComboboxModelFromLayerConfig(layer: QgsVectorLayer, fieldName: str, currentValues: dict = None) -> dict:
    if not currentValues:
        currentValues = {}
    fieldIdx = layer.fields().indexFromName(fieldName)
    if fieldIdx == -1:
        print(f"Field '{fieldName}' not found in layer '{layer.name()}'.")
        return {}
    editorConfig = layer.fields().field(fieldIdx).editorWidgetSetup().config()
    if not editorConfig:
        print(f"No editor config found for field '{fieldName}' in layer '{layer.name()}'.")
        return {}
    layerId = editorConfig["Layer"]
    keyField = editorConfig["Key"]
    valueField = editorConfig["Value"]
    layerFilterExpression = editorConfig.get("FilterExpression", "")
    filterExpression = replaceCurrentValues(layerFilterExpression, currentValues)
    relLayer = QgsProject.instance().mapLayer(layerId)
    if not relLayer:
        print(f"Related layer with ID '{layerId}' not found in the project.")
        return {}
    return getLookupDict(relLayer, keyField, valueField, filterExpression)


def replaceCurrentValues(expr: str, values: dict) -> str:
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
