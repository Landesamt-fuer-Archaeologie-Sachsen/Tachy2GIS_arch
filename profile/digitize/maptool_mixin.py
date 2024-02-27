import uuid

from qgis.core import QgsProject, QgsExpression, QgsExpressionContextUtils


class MapToolMixin:
    def getCustomProjectVariable(self, variableName):
        project = QgsProject.instance()
        if str(QgsExpressionContextUtils.projectScope(project).variable(variableName)) == "NULL":
            return str("")
        else:
            return QgsExpressionContextUtils.projectScope(project).variable(variableName)

    def setPlaceholders(self, feature, prof_nr):
        # uuid to identify feature
        feature_uuid = uuid.uuid4()
        feature["obj_uuid"] = str(feature_uuid)

        # Type of digitize
        feature["geo_quelle"] = "profile_object"
        ## set current date
        e = QgsExpression(" $now ")
        feature["messdatum"] = e.evaluate()

        # aktCode
        try:
            aktcode = self.getCustomProjectVariable("aktcode")
            feature["aktcode"] = aktcode
        except:
            pass

        # obj_type
        feature["obj_typ"] = "Befund"

        # prf_nr
        feature["prof_nr"] = prof_nr
