from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QMessageBox, QApplication
from qgis.core import Qgis, QgsMessageLog, QgsProject

from .config_file import Configfile, get_config_ini_path
from .utils import ArchProjectConfig, any2bool, project_backup

LOGGER_TAG = "T2G Archäologie"


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

        enabled = any2bool(ArchProjectConfig().get("AutoSave_enabled"))
        self.enable(enabled)

    def enable(self, state: bool):
        """Toggle autosave on/off at runtime (e.g. from toolbar button)."""
        if self.autosaveTimer is None:
            return
        if state:
            interval_min = int(ArchProjectConfig().get("AutoSave_interval_in_min"))
            self.autosaveTimer.start(interval_min * 60000)
            QgsMessageLog.logMessage(f"Auto Backup: An, Takt {interval_min} min", LOGGER_TAG, Qgis.Info)
            # run one backup immediately
            self._on_timer()
        else:
            self.autosaveTimer.stop()
            QgsMessageLog.logMessage("Auto Backup: Aus", LOGGER_TAG, Qgis.Info)

    def teardown(self):
        if self.autosaveTimer is None:
            return
        self.autosaveTimer.stop()
        self.autosaveTimer.timeout.disconnect(self._on_timer)
        self.autosaveTimer = None

    def _on_timer(self):
        keep_last_n_backups = int(ArchProjectConfig().get("AutoSave_keep_last_n_backups", 10))
        success = project_backup("automatisch", keep_last_n_backups)
        if success:
            self.number_of_unsuccessful_auto_backups = 0
            return

        self.number_of_unsuccessful_auto_backups += 1

        if self.number_of_unsuccessful_auto_backups > 1:
            interval_min = int(ArchProjectConfig().get("AutoSave_interval_in_min"))
            zeit = self.number_of_unsuccessful_auto_backups * interval_min
            result = QMessageBox.question(
                None,
                "Jetzt speichern und Backup erstellen?",
                f"Das letzte Backup ist schon {zeit} Minuten her.\nJetzt speichern und Backup erstellen?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result == QMessageBox.Yes:
                QgsProject.instance().write()
                QApplication.processEvents()
                self._on_timer()
