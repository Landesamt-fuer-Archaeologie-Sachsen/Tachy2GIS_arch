import logging

from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsProject

from .layers import is_project_type_of_t2g_arch
from .utils import ArchProjectConfig, is_network_path, set_vsi_cached

LOGGER = logging.getLogger(__name__)


class ProjectValidator:
    """Validates the currently loaded QGIS project against the T2G-Arch requirements
    and notifies registered callbacks when the valid/invalid state changes.

    Usage (in toolbar or anywhere else):
        validator = ProjectValidator()
        validator.on_became_valid = lambda: ...
        validator.on_became_invalid = lambda: ...
        validator.setup()   # connects to QgsProject signals
        validator.teardown()  # call on plugin unload
    """

    def __init__(self):
        self.on_became_valid: callable = None
        self.on_became_invalid: callable = None

    def setup(self):
        QgsProject.instance().readProject.connect(self._on_project_read)
        QgsProject.instance().cleared.connect(self._on_project_cleared)

    def teardown(self):
        try:
            QgsProject.instance().readProject.disconnect(self._on_project_read)
            QgsProject.instance().cleared.disconnect(self._on_project_cleared)
        except RuntimeError:
            pass  # signals may already be gone during QGIS shutdown

    def validate(self) -> bool:
        """Run the full project check. Returns True if the project is valid.

        Shows error dialogs on failure and resets the ArchProjectConfig singleton
        so __init__ always re-reads the current project path.
        """
        answer = is_project_type_of_t2g_arch()
        if answer != 'yes':
            message = ("Bitte Projekt vom Typ t2g_arch mit Geopackage laden und erneut versuchen.\n"
                       "Das geladene QGIS-Projekt entspricht nicht der vorgegebenen Projektstruktur.\n"
                       "Es können Fehler oder ein Datenverlust auftreten!\n\n"
                       f"Fehler:\n{answer}")
            LOGGER.warning(message)
            return False

        ArchProjectConfig.clear()
        config = ArchProjectConfig()
        try:
            config.check_config()
        except FileNotFoundError as e:
            LOGGER.debug("Config file not found: %s", e)
            QMessageBox.critical(None, "Critical", f"Konfigurationsdatei nicht gefunden. {e}")
            return False
        except ValueError as e:
            LOGGER.debug("Config file invalid: %s", e)
            QMessageBox.critical(None, "Critical", f"Fehler in der Konfigurationsdatei. {e}")
            return False

        return True

    def _on_project_read(self):
        if self.validate():
            LOGGER.debug("Valid T2G project loaded")
            isNetwork = is_network_path(QgsProject.instance().fileName())
            set_vsi_cached(isNetwork)
            if self.on_became_valid:
                self.on_became_valid()
        else:
            set_vsi_cached(False)
            if self.on_became_invalid:
                self.on_became_invalid()

    def _on_project_cleared(self):
        LOGGER.debug("Project cleared")
        ArchProjectConfig.clear()
        set_vsi_cached(False)
        if self.on_became_invalid:
            self.on_became_invalid()
