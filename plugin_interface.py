import os

from PyQt5.QtGui import QPixmap
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QAction,
    QMenu,
    QToolBar,
    QToolButton,
)
from qgis.gui import QgisInterface
from qgis.core import QgsProject

from .t2g_arch import T2G_Arch


class PluginInterface:
    def __init__(self, iface: QgisInterface):
        """
        Diese Methode wird von QGIS einmalig aufgerufen.
        (Development: Das Plugin "Plugin Reloader" bewirkt einen erneuten Aufruf.)
        """
        self.iface = iface
        self.toolbar = None
        self.actions = None
        self.list_of_actions_disabled_per_default = None
        self.t2g_arch_instance = None

    def initGui(self):
        """
        Diese Methode wird von QGIS aufgerufen, wenn das Plugin geladen wird.
        Hier können Sie die Benutzeroberfläche des Plugins erstellen und Aktionen hinzufügen.
        """
        self.setupToolbar()
        QgsProject.instance().readProject.connect(self.onNewProjectLoaded)
        QgsProject.instance().cleared.connect(self.onProjectClosed)

    def unload(self):
        """
        Diese Methode wird von QGIS aufgerufen, wenn das Plugin entladen wird.
        Hier müssen alle Ressourcen (auch connects durch disconnect()) freigegeben werden,
            die bei einem erneuten Laden des Plugins erneut erstellt werden.
        Sollen Ressourcen das Entladen des Plugins überdauern,
            muss/kann beim Erstellen der Ressource geprüft werden, ob sie schon existiert.
        Auf den Python Garbage Collector kann man sich nur verlassen,
            wenn es keine Referenzen auf die Ressourcen mehr gibt. [1]
        Referenzen werden zum Beispiel weitergegeben durch: das Subscriber-Pattern (hier die Klasse Publisher
            mit der Methode register()), Qts connect() [2] und Qts Parent-Referenz aller Qt-Klassen [3].
        Durch Nutzung der Parent-Referenz zerstört Qt alle Kind-Objekte und löst auch alle betroffenen connects auf,
            wenn eine Instanz einer QObject-Klasse zerstört wird.
        [1] https://www.riverbankcomputing.com/static/Docs/PyQt5/gotchas.html#garbage-collection
        [2] https://www.riverbankcomputing.com/static/Docs/PyQt5/signals_slots.html
        [3] https://www.riverbankcomputing.com/static/Docs/PyQt5/api/qtcore/qobject.html#description
        """
        self.resetToolbar()
        if self.toolbar is not None:
            self.toolbar.deleteLater()
            self.toolbar = None
        self.list_of_actions_disabled_per_default = None
        if self.actions is not None:
            if len(self.actions) > 0:
                self.iface.removePluginMenu("&T2G Archäologie", self.actions[0])
            for action in self.actions:
                action.deleteLater()
            self.actions = None

        QgsProject.instance().readProject.disconnect(self.onNewProjectLoaded)
        QgsProject.instance().cleared.disconnect(self.onProjectClosed)

    def setupToolbar(self):
        iconPaths = {
            "plugin_icon": "plugin_icon.png",
            "visible_true": "Sichtbar_an.gif",
            "visible_false": "Sichtbar_aus.gif",
            "open_folder": "ordner-open.png",
            "save_project": "media-floppy.png",
            "points_import": "PunktImp.gif",
            "points_export": "PunktExp.gif",
            "points_export_profile": "ProfPunktExp.gif",
            "reverse_line": "LineRe.gif",
            "expand_geometry": "butContactClip.gif",
            "raster_overview": "Thumbs.gif",
        }

        plugin_dir = os.path.dirname(__file__)
        for iconDescription, iconPath in iconPaths.items():
            iconPaths[iconDescription] = os.path.join(plugin_dir, "Icons", iconPath)

        self.list_of_actions_disabled_per_default = []
        self.toolbar = QToolBar(self.iface.mainWindow())
        self.toolbar.setObjectName("T2G_Arch")
        self.toolbar.setWindowTitle("T2G-Archäologie Toolbar")
        self.iface.mainWindow().addToolBar(self.toolbar)

        actionStartPlugin = QAction(QIcon(iconPaths["plugin_icon"]), "T2G-Archäologie", self.iface.mainWindow())
        actionStartPlugin.triggered.connect(self.onActionStartPlugin)
        actionStartPlugin.setCheckable(True)
        self.toolbar.addAction(actionStartPlugin)
        self.iface.addPluginToMenu("&T2G Archäologie", actionStartPlugin)

        icon_show_hide = QIcon()
        icon_show_hide.addPixmap(QPixmap(iconPaths["visible_false"]), QIcon.Normal, QIcon.On)
        icon_show_hide.addPixmap(QPixmap(iconPaths["visible_true"]), QIcon.Normal, QIcon.Off)
        actionShowHideDockwidget = QAction(
            icon_show_hide, "Plugin Sichtbarkeit", self.iface.mainWindow()
        )
        actionShowHideDockwidget.triggered.connect(self.onActionShowHideDockwidget)
        actionShowHideDockwidget.setCheckable(True)
        self.toolbar.addAction(actionShowHideDockwidget)
        self.list_of_actions_disabled_per_default.append(actionShowHideDockwidget)

        actionOpenProjectFolder = QAction(
            QIcon(iconPaths["open_folder"]), "Projektexplorer öffnen", self.iface.mainWindow()
        )
        actionOpenProjectFolder.triggered.connect(self.onActionOpenProjectFolder)
        self.toolbar.addAction(actionOpenProjectFolder)
        self.list_of_actions_disabled_per_default.append(actionOpenProjectFolder)

        self.toolbar.addSeparator()

        actionSaveProject = QAction(QIcon(iconPaths["save_project"]), "Tagesprojekt sichern", self.iface.mainWindow())
        actionSaveProject.triggered.connect(self.onActionSaveProject)
        self.toolbar.addAction(actionSaveProject)
        self.list_of_actions_disabled_per_default.append(actionSaveProject)

        menuPointsImport = QMenu()
        actionImportPoints = QAction(QIcon(iconPaths["points_import"]), "Punkt Import", self.iface.mainWindow())
        actionImportPoints.triggered.connect(self.onActionImportPoints)
        actionExportPoints = QAction(QIcon(iconPaths["points_export"]), "Punkt Export", self.iface.mainWindow())
        actionExportPoints.triggered.connect(self.onActionExportPoints)
        actionProfileExportPoints = QAction(
            QIcon(iconPaths["points_export_profile"]), "Profilentzerrpunkte Export", self.iface.mainWindow()
        )
        actionProfileExportPoints.triggered.connect(self.onActionProfileExportPoints)
        menuPointsImport.addActions([actionImportPoints, actionExportPoints, actionProfileExportPoints])
        self.list_of_actions_disabled_per_default.extend(
            [actionImportPoints, actionExportPoints, actionProfileExportPoints]
        )

        toolButtonPointsImport = QToolButton(self.iface.mainWindow())
        toolButtonPointsImport.setMenu(menuPointsImport)
        toolButtonPointsImport.setDefaultAction(actionImportPoints)
        toolButtonPointsImport.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolbar.addWidget(toolButtonPointsImport)

        self.actions = [actionStartPlugin] + self.list_of_actions_disabled_per_default

        self.resetToolbar()

    def resetToolbar(self):
        for action in self.list_of_actions_disabled_per_default:
            action.setEnabled(False)
            self.iface.removePluginMenu("&T2G Archäologie", action)
        self.actions[0].setChecked(False)

    def activateActions(self):
        for action in self.list_of_actions_disabled_per_default:
            action.setEnabled(True)
            self.iface.addPluginToMenu("&T2G Archäologie", action)

    def onNewProjectLoaded(self):
        print("Ein neues Projekt wurde geladen!")

    def onProjectClosed(self):
        print("Projekt wurde geschlossen!")

    def onActionStartPlugin(self, checked):
        if checked:
            if not self.t2g_arch_instance:
                self.t2g_arch_instance = T2G_Arch(self.iface)
                self.t2g_arch_instance.initGui()
            if self.t2g_arch_instance.startAndStopPlugin(start=True):
                self.activateActions()
            else:
                self.onActionStartPlugin(False)
        else:
            if self.t2g_arch_instance:
                self.t2g_arch_instance.startAndStopPlugin(start=False)
                self.t2g_arch_instance.unload()
                self.t2g_arch_instance = None
            self.resetToolbar()

    def onActionShowHideDockwidget(self, checked):
        # todo self.openDockWidget
        pass

    def onActionOpenProjectFolder(self, checked):
        # self.actionOpenProjectFolder.triggered.connect(openProjectFolder)
        pass

    def onActionSaveProject(self, checked):
        # self.actionSaveProject.triggered.connect(saveProject)
        pass

    def onActionImportPoints(self, checked):
        # self.actionImportPoints.triggered.connect(self.importPoints)
        pass

    def onActionExportPoints(self, checked):
        # self.actionExportPoints.triggered.connect(self.exportPoints)
        pass

    def onActionProfileExportPoints(self, checked):
        # self.actionProfileExportPoints.triggered.connect(self.exportProfilePoints)
        pass
