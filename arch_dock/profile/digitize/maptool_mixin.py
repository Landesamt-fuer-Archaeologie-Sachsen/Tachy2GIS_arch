import uuid

from qgis.core import QgsProject, QgsExpression, QgsExpressionContextUtils, QgsMessageLog, Qgis

from ....settings import PLUGIN_NAME
from ....common.utils import ArchProjectConfig


class MapToolMixin:
    def getCustomProjectVariable(self, variableName):
        project = QgsProject.instance()
        variable = QgsExpressionContextUtils.projectScope(project).variable(variableName)
        # NULL is a falsy QVariant on PyQt5 and None on PyQt6; str() would differ ("NULL" vs "None")
        if not variable:
            return ""
        return variable

    def setPlaceholders(self, feature, prof_nr):
        # uuid to identify feature
        feature_uuid = uuid.uuid4()
        feature["obj_uuid"] = str(feature_uuid)

        # Type of digitize
        feature["geo_quelle"] = "profile_object"
        ## set current date
        e = QgsExpression(" $now ")
        feature["erf_datum"] = e.evaluate()

        # aktCode
        try:
            aktcode = self.getCustomProjectVariable("aktcode")
            feature["aktcode"] = aktcode
        except Exception as e:
            QgsMessageLog.logMessage(
                message="MapToolMixin->setPlaceholders: no aktcode: " + str(e),
                tag=PLUGIN_NAME,
                level=Qgis.MessageLevel.Warning,
            )

        # obj_type
        # feature["obj_typ"] = "Befund"
        feature["obj_typ"] = ArchProjectConfig().get("Digitize_Befund_ObjTyp")

        # prf_nr
        feature["prof_nr"] = prof_nr
