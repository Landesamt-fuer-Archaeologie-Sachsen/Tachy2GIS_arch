import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QWidget, QPushButton, QComboBox, QInputDialog, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsExpression, QgsMessageLog, QgsFeatureRequest, Qgis, QgsWkbTypes
from qgis.utils import iface

from .geometry_check_dockwidget import GeometryCheckDockWidget
from ..utils.functions import isNumber
from ..utils.layers import T2gLayers
from ..Icons import ICON_PATHS


WIDGET, BASE = uic.loadUiType(os.path.join(os.path.dirname(__file__), "tools_allgemein.ui"))


class ToolsAllgemeinTab(BASE, WIDGET):
    butObjFind: QPushButton
    cboSuche: QComboBox

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setupUi(self)
        self.butObjFind.setIcon(QIcon(ICON_PATHS["suchen"]))
        self.cboSuche.setToolTip("Suchen")

        self.setupConnections()

    def setupConnections(self):
        self.butObjFind.clicked.connect(self.ozoom_1_ok)
        self.btnCheckHeights.clicked.connect(self.dlgFeatureCheckShow)

    def ozoom_1_ok(self):
        iface.activeLayer().removeSelection()
        layerLine = T2gLayers.getLineLayer()
        layerPoly = T2gLayers.getPolygonLayer()
        layerPoint = T2gLayers.getPointLayer()
        layerlist = [layerLine, layerPoly, layerPoint]
        labellist = [self.labE_Line, self.labE_Poly, self.labE_Poi]
        suchstr, ok = QInputDialog.getText(None, "Suchen", "Nummer eingeben")
        if not ok:
            return
        if suchstr[0] == "":
            return
        if self.cboSuche.currentText() == "Befund":
            fieldName = "bef_nr"
        if self.cboSuche.currentText() == "Fund":
            fieldName = "fund_nr"
        if self.cboSuche.currentText() == "Profil":
            fieldName = "prof_nr"
        if self.cboSuche.currentText() == "Probe":
            fieldName = "probe_nr"
        if isNumber(suchstr[0]):
            suchstr = fieldName + "=" + suchstr
        else:
            suchstr = fieldName + "=" + "'" + suchstr + "'"
        expr = QgsExpression(suchstr)  # QgsExpression("befNr='120'")
        a = 0
        meldung = True
        for layer in layerlist:
            a = a + 1
            QgsMessageLog.logMessage(str(suchstr), "T2G Archäologie", Qgis.Info)
            it = layer.getFeatures(QgsFeatureRequest(expr))
            ids = [i.id() for i in it]
            layer.selectByIds(ids)

            if layer.selectedFeatureCount() > 0:
                iface.mapCanvas().zoomToSelected(layer)
                if not layer.geometryType() == QgsWkbTypes.PointGeometry:
                    iface.mapCanvas().zoomByFactor(5)
                iface.mapCanvas().refresh()
                meldung = False
            labellist[a - 1].setText(str(layer.selectedFeatureCount()))

        if meldung:
            QMessageBox.warning(None, "Meldung", "Keine Objekte gefunden!")

    def dlgFeatureCheckShow(self):
        dlgFeatureCheck = GeometryCheckDockWidget(iface.mapCanvas())  # mainWindow()
        dlgFeatureCheck.setAutoFillBackground(True)
        dlgFeatureCheck.show()
