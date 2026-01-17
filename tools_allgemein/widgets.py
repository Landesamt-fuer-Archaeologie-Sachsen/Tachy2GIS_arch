import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QLineEdit, QWidget, QPushButton, QComboBox, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface
from qgis.core import QgsRectangle

from .geometry_check_dockwidget import GeometryCheckDockWidget
from ..utils.functions import isNumber, delSelectFeature
from ..utils.layers import T2gLayers
from ..Icons import ICON_PATHS


WIDGET, BASE = uic.loadUiType(os.path.join(os.path.dirname(__file__), "tools_allgemein.ui"))


class ToolsAllgemeinTab(BASE, WIDGET):
    butSuche: QPushButton
    cboSuche: QComboBox
    lineEditSuche: QLineEdit
    field_mapping = {
        "Befund": "bef_nr",
        "Fund": "fund_nr",
        "Profil": "prof_nr",
        "Probe": "probe_nr",
    }

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setupUi(self)
        self.butSuche.setIcon(QIcon(ICON_PATHS["suchen"]))
        self.butSuche.setToolTip("Suchen")
        for displayname, fieldname in self.field_mapping.items():
            self.cboSuche.addItem(displayname, fieldname)
        self.dlgFeatureCheck = None
        self.setupConnections()

    def setupConnections(self):
        self.lineEditSuche.textChanged.connect(self._onSearchTextChanged)
        self.butSuche.clicked.connect(self._onSearchClicked)
        self.btnCheckHeights.clicked.connect(self.dlgFeatureCheckShow)

    def _onSearchTextChanged(self):
        self.butSuche.setEnabled(bool(self.lineEditSuche.text()))

    def _onSearchClicked(self):
        delSelectFeature()
        layers = [T2gLayers.getLineLayer(), T2gLayers.getPolygonLayer(), T2gLayers.getPointLayer()]
        labels = [self.labE_Line, self.labE_Poly, self.labE_Poi]
        fieldname = self.cboSuche.currentData()
        suchText = self.lineEditSuche.text()
        exprStr = f"{fieldname}={suchText}" if isNumber(suchText) else f"{fieldname}='{suchText}'"

        total_selected = 0
        for layer, label in zip(layers, labels):
            layer.selectByExpression(exprStr)
            count = layer.selectedFeatureCount()
            label.setText(str(count))
            total_selected += count

        iface.mapCanvas().refresh()

        if total_selected == 0:
            QMessageBox.warning(None, "Meldung", "Keine Objekte gefunden!")
        else:
            self._zoomToSelection()

    def _zoomToSelection(self):
        extent = QgsRectangle()
        for layer in T2gLayers.getEditLayers():
            if layer.selectedFeatures():  # Check if features are selected in this layer
                extent.combineExtentWith(layer.boundingBoxOfSelected())

        if not extent.isNull():
            iface.mapCanvas().setExtent(extent)
            iface.mapCanvas().refresh()

    def dlgFeatureCheckShow(self):
        if self.dlgFeatureCheck:
            self.dlgFeatureCheck.close()
            self.dlgFeatureCheck = None
        self.dlgFeatureCheck = GeometryCheckDockWidget(iface.mapCanvas())
