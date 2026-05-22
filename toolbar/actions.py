import math
import operator
import os

from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton, QMessageBox, QFileDialog, QInputDialog
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsMessageLog,
    QgsPoint,
    Qgis,
    QgsFeatureRequest,
    QgsExpression,
    QgsVectorLayer,
    QgsField,
    QgsFeature,
    QgsGeometry,
    QgsLayerTreeLayer,
    QgsWkbTypes,
)
from qgis.utils import iface

from ..common.points_io import importPoints, exportPoints, exportProfilePoints
from ..common.config_file import Configfile, get_config_ini_path
from ..common.layers import T2gLayers, findLayerInProject
from ..common.utils import (
    openProjectFolder,
    saveProject,
    merge_icons,
    color_shift_icon,
    openManual,
    ProgressBar,
    fileLineCount,
    addPoint3D,
    delSelectFeature,
    delLayer,
)
from ..icons import ICON_PATHS
from ..settings import PLUGIN_NAME


class OpenProjectFolderAction(QAction):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Projektverzeichnis öffnen")
        self.setIcon(QIcon(ICON_PATHS["ordner-open"]))
        self.setEnabled(False)
        self.triggered.connect(self.callback)

    def callback(self):
        openProjectFolder()


class BackupProjectAction(QAction):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Backup erstellen")
        self.setIcon(QIcon(QgsApplication.iconPath("mActionFileSave.svg")))
        self.setEnabled(False)
        self.triggered.connect(self.callback)

    def callback(self):
        saveProject()


class AutoBackupProjectAction(QAction):
    def __init__(self, autosave_manager, parent=None):
        super().__init__(parent)
        self._autosave_manager = autosave_manager
        self.setText("Auto-Backup")
        self.setIcon(self.getIcon())
        self.setCheckable(True)
        self.setChecked(False)
        self.setEnabled(False)
        self.triggered.connect(self._autosave_manager.enable)

    def getIcon(self):
        icon_save_on = merge_icons(
            QIcon(QgsApplication.iconPath("mActionFileSave.svg")),
            QIcon(QgsApplication.iconPath("mIconHistory.svg")),
        )
        icon_save_off = color_shift_icon(icon_save_on, QColor(128, 128, 128, 170))
        icon_auto_backup = QIcon()
        icon_auto_backup.addPixmap(icon_save_on.pixmap(64, 64), QIcon.Normal, QIcon.On)
        icon_auto_backup.addPixmap(icon_save_off.pixmap(64, 64), QIcon.Normal, QIcon.Off)
        return icon_auto_backup


class SettingsAction(QAction):
    def __init__(self, autosave_manager, parent=None):
        super().__init__(QIcon(ICON_PATHS["Einstellungen"]), "Einstellungen", parent)
        self._autosave_manager = autosave_manager
        self._dialog = None
        self.setEnabled(False)
        self.triggered.connect(self._open)

    def _open(self):
        from .widgets import DlgSettings  # local import to avoid circular dependency

        config = Configfile(get_config_ini_path())
        self._dialog = DlgSettings(config, self._autosave_manager)
        self._dialog.setup()
        self._dialog.show()


class AboutAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["Frage"]), "Über dieses Plugin", parent)
        self._dialog = None
        self.triggered.connect(self._open)

    def _open(self):
        from .widgets import AboutDialog  # local import to avoid circular dependency

        self._dialog = AboutDialog(self.parent())
        self._dialog.exec()


class ManualAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["Formular"]), "Dokumentation", parent)
        self.triggered.connect(openManual)


class ImportPointsAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["points_import"]), "Punkt Import", parent)
        self.triggered.connect(importPoints)


class ExportPointsAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["points_export"]), "Punkt Export", parent)
        self.triggered.connect(exportPoints)


class ExportProfilePointsAction(QAction):
    def __init__(self, parent=None):
        super().__init__(QIcon(ICON_PATHS["points_export_profile"]), "Profilentzerrpunkte Export", parent)
        self.triggered.connect(exportProfilePoints)


class MenuPointsImportAction(QToolButton):
    """A toolbar button that opens a dropdown menu with point import/export actions."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.action_import = ImportPointsAction(self)
        self.action_export = ExportPointsAction(self)
        self.action_export_profile = ExportProfilePointsAction(self)

        menu = QMenu(self)
        menu.addActions([self.action_import, self.action_export, self.action_export_profile])

        self.setMenu(menu)
        self.setDefaultAction(self.action_import)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.setEnabled(False)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.action_import.setEnabled(enabled)
        self.action_export.setEnabled(enabled)
        self.action_export_profile.setEnabled(enabled)

