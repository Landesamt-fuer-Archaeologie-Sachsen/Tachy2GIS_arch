"""Plan tab of the arch dock: exports a georeferenced profile into the
profildata_* tables of the project GeoPackage.

The work is split over this folder:
- profile_meta.py       reads the .meta file of the profile image
- profildata_schema.py  defines the tables
- profildata_tables.py  creates, extends and writes the tables
- plan_export.py        selects, rotates and writes the profile's objects
"""
import logging

from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt
from qgis.utils import iface

from ..rotation_coords import RotationCoords
from ....common.utils import layers_not_in_edit_mode
from .plan_export import export_profile, find_input_layers
from .profile_meta import ProfileMeta
from .profildata_tables import PlanExportError, vsi_cache_disabled

LOGGER = logging.getLogger(__name__)


class Plan:

    def __init__(self, arch_dock):
        LOGGER.debug("init plan")
        self.__dockwidget = arch_dock
        self.rotationCoords = RotationCoords()

    def setup(self):
        self.__dockwidget.profilePlanSelect.setFilter("Images (*.jpg)")
        self.__dockwidget.startPlanBtn.clicked.connect(self.__startPlanCreation)
        self.__dockwidget.check_profile_buffer.stateChanged.connect(self.handle_check_profile_buffer)
        self.handle_check_profile_buffer(Qt.CheckState.Unchecked)

    def handle_check_profile_buffer(self, state):
        visible = state == Qt.CheckState.Checked
        self.__dockwidget.profileBufferSpinBox.setVisible(visible)
        self.__dockwidget.label_profileBuffer.setVisible(visible)

    def __startPlanCreation(self):
        if not layers_not_in_edit_mode(["E_Point", "E_Line", "E_Polygon", "Messpunkte"]):
            iface.messageBar().pushMessage(
                "Error", "Bitte den Editiermodus der Eingabelayer beenden.", level=Qgis.MessageLevel.Warning, duration=3
            )
            return

        try:
            meta = ProfileMeta.load(self.__dockwidget.profilePlanSelect.filePath())
        except ValueError as err:
            iface.messageBar().pushMessage("Error", str(err), level=Qgis.MessageLevel.Warning, duration=3)
            return

        self.rotationCoords.setAarTransformationParams(meta.transform_params)
        buffer_geometry = self.rotationCoords.profileBuffer(
            self.__dockwidget.profileBufferSpinBox.value(), meta.aar_direction
        )

        try:
            with vsi_cache_disabled():
                summary = export_profile(
                    meta,
                    find_input_layers(),
                    self.rotationCoords,
                    buffer_geometry,
                    use_profile_buffer=self.__dockwidget.check_profile_buffer.isChecked(),
                )
        except PlanExportError as err:
            LOGGER.error(f"Plan-Export abgebrochen: {err}")
            iface.messageBar().pushMessage(
                "Fehler beim Plan-Export", str(err), level=Qgis.MessageLevel.Critical, duration=15
            )
            return

        LOGGER.info(f"Plan-Export für Profil {meta.prof_nr} ({meta.aar_direction}): {summary}")
        iface.messageBar().pushMessage(
            "Hinweis",
            f"Profil {meta.prof_nr} in den (unregistrierten) Tabellen profildata_* des Projekt-GeoPackages abgelegt: "
            f"{summary}",
            level=Qgis.MessageLevel.Success,
            duration=8,
        )
