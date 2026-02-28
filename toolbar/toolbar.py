import logging
import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QWidget, QToolBar
from qgis.core import QgsMessageLog, Qgis
from qgis.utils import iface

from .actions import OpenProjectFolderAction, BackupProjectAction, AutoBackupProjectAction, MenuPointsImportAction, SettingsAction, AboutAction, ManualAction
from ..arch_dock.messen.autoattributes import clearAutoAttributeProjectVariables
from ..arch_dock.widgets import T2GArchDockWidget
from ..common.autosave import AutosaveManager
from ..common.layers import T2gLayers
from ..common.utils import setCustomProjectVariable, delSelectFeature, repairUuidsInLayers
from ..settings import PLUGIN_NAME
from ..vtk_viewer.widgets import VtkViewer
from ..common.project_validator import ProjectValidator

LOGGER = logging.getLogger(__name__)
ICONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'icons')


class T2GToolbar(QToolBar):
    def __init__(self, parent: QWidget = None):
        super().__init__("T2G-Archäologie Toolbar", parent)
        self.setObjectName("T2G-Archäologie Toolbar")

        self.autosave_manager = AutosaveManager()

        self.vtk_viewer = VtkViewer()
        iface.addDockWidget(Qt.BottomDockWidgetArea, self.vtk_viewer)
        self.t2g_action = self.vtk_viewer.toggleViewAction()
        t2g_icon = QIcon(os.path.join(ICONS_DIR, 'tachymeter.png'))
        self.t2g_action.setIcon(t2g_icon)
        self.addAction(self.t2g_action)

        self.arch_dock = T2GArchDockWidget()
        iface.addDockWidget(Qt.RightDockWidgetArea, self.arch_dock)
        self.arch_dock_action = self.arch_dock.toggleViewAction()
        arch_icon = QIcon(os.path.join(ICONS_DIR, 'plugin_icon.png'))
        self.arch_dock_action.setIcon(arch_icon)
        self.addAction(self.arch_dock_action)

        self.openProjectFolderAction = OpenProjectFolderAction(self)
        self.addAction(self.openProjectFolderAction)

        self.addSeparator()

        self.backupAction = BackupProjectAction(self)
        self.addAction(self.backupAction)

        self.autoBackupAction = AutoBackupProjectAction(self.autosave_manager, self)
        self.addAction(self.autoBackupAction)

        self.settingsAction = SettingsAction(self.autosave_manager, self)
        self.addAction(self.settingsAction)

        self.pointImportMenu = MenuPointsImportAction(self)
        self.addWidget(self.pointImportMenu)

        self.addSeparator()

        self.manualAction = ManualAction(self)
        self.addAction(self.manualAction)

        self.aboutAction = AboutAction(self)
        self.addAction(self.aboutAction)

        # Disable until a valid project is confirmed
        self.arch_dock_action.setEnabled(False)
        self.arch_dock.hide()

        self.project_validator = ProjectValidator()
        self.project_validator.on_became_valid = self._on_project_became_valid
        self.project_validator.on_became_invalid = self._on_project_became_invalid
        self.project_validator.setup()

        # Check immediately in case a project is already open
        self.project_validator.validate() and self._on_project_became_valid()

    def _set_project_actions_enabled(self, enabled: bool):
        self.backupAction.setEnabled(enabled)
        self.autoBackupAction.setEnabled(enabled)
        self.settingsAction.setEnabled(enabled)
        self.pointImportMenu.setEnabled(enabled)
        self.openProjectFolderAction.setEnabled(enabled)
        self.manualAction.setEnabled(enabled)

    def _on_project_became_valid(self):
        LOGGER.debug("Valid T2G project – enabling arch dock")
        self.initProjectVariables()

        self.arch_dock.reload()
        self.arch_dock_action.setEnabled(True)

        self.autosave_manager.setup()
        self.autoBackupAction.setChecked(self.autosave_manager.is_enabled)
        self._set_project_actions_enabled(True)

        iface.setActiveLayer(T2gLayers.getPointLayer())

        QgsMessageLog.logMessage("Aufsatz Archäologie für T2G ist einsatzbereit.", PLUGIN_NAME, Qgis.Info)

        delSelectFeature()
        repairUuidsInLayers(T2gLayers.getEditLayers() + [T2gLayers.getMesspunkteLayer()])

        iface.actionSelectRectangle().trigger()

    def _on_project_became_invalid(self):
        LOGGER.debug("Invalid / no T2G project – disabling arch dock")
        self.arch_dock_action.setEnabled(False)
        self.arch_dock.hide()
        self.arch_dock.unload()

        self.autosave_manager.teardown()
        self.autoBackupAction.setChecked(False)
        self._set_project_actions_enabled(False)

    def deleteLater(self):
        self.project_validator.teardown()
        self.project_validator = None

        iface.removeDockWidget(self.vtk_viewer)
        self.vtk_viewer.deleteLater()

        iface.removeDockWidget(self.arch_dock)
        self.arch_dock.unload()
        self.arch_dock.deleteLater()

        super().deleteLater()

    def initProjectVariables(self):
        clearAutoAttributeProjectVariables()
        setCustomProjectVariable("autoAttribute", False)
        setCustomProjectVariable("autoZahl", False)