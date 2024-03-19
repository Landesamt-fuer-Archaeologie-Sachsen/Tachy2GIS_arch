import uuid

from qgis.core import QgsProject, QgsExpression, QgsExpressionContextUtils, QgsMessageLog, Qgis


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
        feature["erf_datum"] = e.evaluate()

        # aktCode
        try:
            aktcode = self.getCustomProjectVariable("aktcode")
            feature["aktcode"] = aktcode
        except Exception as e:
            QgsMessageLog.logMessage(message='MapToolMixin->setPlaceholders: no aktcode: ' + str(e), tag='T2G Archäologie', level=Qgis.MessageLevel.Warning)

        # obj_type
        feature["obj_typ"] = "Befund"

        # prf_nr
        feature["prof_nr"] = prof_nr
