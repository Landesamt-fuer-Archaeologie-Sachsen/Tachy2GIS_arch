import logging

from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QMessageBox, QApplication
from qgis.core import Qgis, QgsMessageLog, QgsProject

from ..settings import PLUGIN_NAME
from .config_file import Configfile, get_config_ini_path
from .utils import any2bool, project_backup


LOGGER = logging.getLogger(__name__)

_AUTOSAVE_SECTION = "AutoSave"
_DEFAULT_ENABLED = "off"
_DEFAULT_INTERVAL_MIN = "15"
_DEFAULT_KEEP_LAST_N = "10"


class AutosaveManager:
    def __init__(self):
        self.autosaveTimer = None
        self.number_of_unsuccessful_auto_backups = 0

    @property
    def is_enabled(self) -> bool:
        return self.autosaveTimer is not None and self.autosaveTimer.isActive()

    def _config(self) -> Configfile:
        return Configfile(get_config_ini_path())

    def setup(self):
        """Called when a valid project is loaded. Reads config and starts timer if enabled."""
        self.number_of_unsuccessful_auto_backups = 0
        self.autosaveTimer = QTimer()
        self.autosaveTimer.timeout.connect(self._on_timer)

        config = self._config()
        enabled = any2bool(config.getValue(_AUTOSAVE_SECTION, "enabled", _DEFAULT_ENABLED))
        LOGGER.debug(f"Auto Backup enabled in config: {enabled}")
        self.enable(enabled)

    def enable(self, state: bool):
        """Toggle autosave on/off at runtime (e.g. from toolbar button)."""
        if self.autosaveTimer is None:
            return
        if state:
            interval_min = int(self._config().getValue(_AUTOSAVE_SECTION, "interval_in_min", _DEFAULT_INTERVAL_MIN))
            self.autosaveTimer.start(interval_min * 60000)
            QgsMessageLog.logMessage(f"Auto Backup: An, Takt {interval_min} min", PLUGIN_NAME, Qgis.Info)
            # run one backup immediately
            self._on_timer()
        else:
            self.autosaveTimer.stop()
            QgsMessageLog.logMessage("Auto Backup: Aus", PLUGIN_NAME, Qgis.Info)

    def teardown(self):
        if self.autosaveTimer is None:
            return
        self.autosaveTimer.stop()
        self.autosaveTimer.timeout.disconnect(self._on_timer)
        self.autosaveTimer = None

    def _on_timer(self):
        keep_last_n_backups = int(
            self._config().getValue(_AUTOSAVE_SECTION, "keep_last_n_backups", _DEFAULT_KEEP_LAST_N)
        )
        success = project_backup("automatisch", keep_last_n_backups)
        if success:
            self.number_of_unsuccessful_auto_backups = 0
            return

        self.number_of_unsuccessful_auto_backups += 1

        if self.number_of_unsuccessful_auto_backups > 1:
            interval_min = int(self._config().getValue(_AUTOSAVE_SECTION, "interval_in_min", _DEFAULT_INTERVAL_MIN))
            zeit = self.number_of_unsuccessful_auto_backups * interval_min
            result = QMessageBox.question(
                None,
                "Jetzt speichern und Backup erstellen?",
                f"Das letzte Backup ist schon {zeit} Minuten her.\nJetzt speichern und Backup erstellen?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result == QMessageBox.Yes:
                project = QgsProject.instance()
                uncommitted = []
                for layer in project.mapLayers().values():
                    if layer.type() == layer.VectorLayer and layer.isEditable():
                        if not layer.commitChanges():
                            uncommitted.append(layer.name())

                if uncommitted:
                    QMessageBox.warning(
                        None,
                        "Backup nicht möglich",
                        "Folgende Layer konnten nicht gespeichert werden:\n"
                        + "\n".join(uncommitted)
                        + "\n\nBitte beenden Sie den Bearbeitungsmodus manuell.",
                    )
                    return

                project.write()
                QApplication.processEvents()
                self._on_timer()
