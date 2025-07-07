import gc
from os import path as os_path

from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QAction,
    QMenu,
    QToolBar,
    QToolButton,
)
from qgis.core import QgsProject
from qgis.gui import QgisInterface

from .Icons import ICON_PATHS
from .utils.functions import set_vsi_cached, is_network_path
from .utils.t2g_arch import T2gArch
from .utils.toolbar_functions import openProjectFolder, saveProject


class PluginInterface:
    def __init__(self, iface: QgisInterface):
        """
        Diese Methode wird von QGIS einmalig beim Start von QGIS aufgerufen.
        (Development: Das Plugin "Plugin Reloader" bewirkt einen erneuten Aufruf.)
        """
        self.iface = iface
        self.toolbar = None
        self.actions = {}
        self.t2g_arch_instance = None

    def initGui(self):
        """
        Diese Methode wird von QGIS aufgerufen, wenn das Plugin geladen wird.
        Hier wird die Toolbar des Plugins erstellt und Aktionen hinzugefügt.
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
        Parent-Referenzen werden zum Beispiel durch Konstruktoren, setLayout(), setCentralWidget(), ... erzeugt und die
            Verantwortung über die Löschung wird übertragen.
        Es ist nicht empfohlen, Referenzen auf Kind-Objekte außerhalb der Parents zu halten, da die Kind-Objekte
            jederzeit gelöscht werden können. [4]
        [1] https://www.riverbankcomputing.com/static/Docs/PyQt5/gotchas.html#garbage-collection
        [2] https://www.riverbankcomputing.com/static/Docs/PyQt5/signals_slots.html
        [3] https://www.riverbankcomputing.com/static/Docs/PyQt5/api/qtcore/qobject.html#description
        [4] https://doc.qt.io/qt-5/qobject.html#dtor.QObject
        """
        self.onActionStartPlugin(False)
        self.resetToolbar()
        if self.toolbar is not None:
            self.toolbar.deleteLater()
            self.toolbar = None
        if isinstance(self.actions, dict):
            for e in self.actions.values():
                self.iface.removePluginMenu("&T2G Archäologie", e["QAction"])
                e["QAction"].deleteLater()
            self.actions = None

        QgsProject.instance().readProject.disconnect(self.onNewProjectLoaded)
        QgsProject.instance().cleared.disconnect(self.onProjectClosed)

    def setupToolbar(self):
        self.actions = {}
        self.toolbar = QToolBar(self.iface.mainWindow())
        self.toolbar.setObjectName("T2G_Arch")
        self.toolbar.setWindowTitle("T2G-Archäologie Toolbar")
        self.iface.mainWindow().addToolBar(self.toolbar)

        icon_start = QIcon()
        icon_start.addPixmap(QPixmap(ICON_PATHS["plugin_icon"]))
        icon_start.addPixmap(QPixmap(ICON_PATHS["hourglass"]), QIcon.Disabled)
        actionStartPlugin = QAction(icon_start, "T2G-Archäologie", self.iface.mainWindow())
        self.actions["actionStartPlugin"] = {
            "QAction": actionStartPlugin,
            "enabled_per_default": True,
        }
        actionStartPlugin.triggered.connect(self.onActionStartPlugin)
        actionStartPlugin.setCheckable(True)
        self.toolbar.addAction(actionStartPlugin)
        self.iface.addPluginToMenu("&T2G Archäologie", actionStartPlugin)

        icon_show_hide = QIcon()
        icon_show_hide.addPixmap(QPixmap(ICON_PATHS["Sichtbar_aus"]), QIcon.Normal, QIcon.On)
        icon_show_hide.addPixmap(QPixmap(ICON_PATHS["Sichtbar_an"]), QIcon.Normal, QIcon.Off)
        actionShowHideDockwidget = QAction(icon_show_hide, "Plugin Sichtbarkeit", self.iface.mainWindow())
        self.actions["actionShowHideDockwidget"] = {
            "QAction": actionShowHideDockwidget,
            "enabled_per_default": False,
        }
        actionShowHideDockwidget.triggered.connect(self.onActionShowHideDockwidget)
        actionShowHideDockwidget.setCheckable(True)
        self.toolbar.addAction(actionShowHideDockwidget)

        actionOpenProjectFolder = QAction(
            QIcon(ICON_PATHS["ordner-open"]), "Projektexplorer öffnen", self.iface.mainWindow()
        )
        self.actions["actionOpenProjectFolder"] = {
            "QAction": actionOpenProjectFolder,
            "enabled_per_default": False,
        }
        actionOpenProjectFolder.triggered.connect(self.onActionOpenProjectFolder)
        self.toolbar.addAction(actionOpenProjectFolder)

        self.toolbar.addSeparator()

        actionSaveProject = QAction(QIcon(ICON_PATHS["media-floppy"]), "Tagesprojekt sichern", self.iface.mainWindow())
        self.actions["actionSaveProject"] = {
            "QAction": actionSaveProject,
            "enabled_per_default": False,
        }
        actionSaveProject.triggered.connect(self.onActionSaveProject)
        self.toolbar.addAction(actionSaveProject)

        menuPointsImport = QMenu()
        actionImportPoints = QAction(QIcon(ICON_PATHS["points_import"]), "Punkt Import", self.iface.mainWindow())
        self.actions["actionImportPoints"] = {
            "QAction": actionImportPoints,
            "enabled_per_default": False,
        }
        actionImportPoints.triggered.connect(self.onActionImportPoints)
        actionExportPoints = QAction(QIcon(ICON_PATHS["points_export"]), "Punkt Export", self.iface.mainWindow())
        self.actions["actionExportPoints"] = {
            "QAction": actionExportPoints,
            "enabled_per_default": False,
        }
        actionExportPoints.triggered.connect(self.onActionExportPoints)
        actionProfileExportPoints = QAction(
            QIcon(ICON_PATHS["points_export_profile"]), "Profilentzerrpunkte Export", self.iface.mainWindow()
        )
        self.actions["actionProfileExportPoints"] = {
            "QAction": actionProfileExportPoints,
            "enabled_per_default": False,
        }
        actionProfileExportPoints.triggered.connect(self.onActionProfileExportPoints)
        menuPointsImport.addActions([actionImportPoints, actionExportPoints, actionProfileExportPoints])

        toolButtonPointsImport = QToolButton(self.iface.mainWindow())
        toolButtonPointsImport.setMenu(menuPointsImport)
        toolButtonPointsImport.setDefaultAction(actionImportPoints)
        toolButtonPointsImport.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolbar.addWidget(toolButtonPointsImport)

        self.resetToolbar()

    def resetToolbar(self):
        for action in self.actions.values():
            if action["QAction"].isCheckable():
                action["QAction"].setChecked(False)
            action["QAction"].setEnabled(action["enabled_per_default"])
            if not action["enabled_per_default"]:
                self.iface.removePluginMenu("&T2G Archäologie", action["QAction"])

    def activateActions(self):
        for action in [e["QAction"] for e in self.actions.values() if not e["enabled_per_default"]]:
            action.setEnabled(True)
            self.iface.addPluginToMenu("&T2G Archäologie", action)

    def onNewProjectLoaded(self):
        print("Ein neues Projekt wurde geladen!")

    def onProjectClosed(self):
        print("Projekt wurde geschlossen!")
        self.onActionStartPlugin(False)

    def onActionStartPlugin(self, checked):
        self.actions["actionStartPlugin"]["QAction"].setEnabled(False)
        QCoreApplication.processEvents()  # give Qt the chance to process signals and display other icon
        if checked:
            if not self.t2g_arch_instance:
                self.t2g_arch_instance = T2gArch(self.iface)
                self.t2g_arch_instance.initGui()
            if self.t2g_arch_instance.startAndStopPlugin(start=True):
                if is_network_path(QgsProject.instance().fileName()):
                    set_vsi_cached(True)
                self.activateActions()
            else:
                self.onActionStartPlugin(False)
        else:
            set_vsi_cached(False)
            if not self.t2g_arch_instance:
                print("PLUGIN DELETE not needed")
            else:
                self.t2g_arch_instance.startAndStopPlugin(start=False)
                self.t2g_arch_instance.unload()
                print("PLUGIN DELETE attempt ... wait for 'PLUGIN DELETE SUCCESS' message.")
                self.t2g_arch_instance = None

            gc.collect()  # make sure instances get deleted -> Qt deletes children and disconnects signals
            QApplication.processEvents()  # process signals to delete more QObjects
            self.check_for_needed_cleanup()
            self.resetToolbar()

        self.actions["actionStartPlugin"]["QAction"].setEnabled(True)

    def onActionShowHideDockwidget(self, checked):
        if self.t2g_arch_instance:
            self.t2g_arch_instance.openDockWidget(not checked)

    def onActionOpenProjectFolder(self, _):
        openProjectFolder()

    def onActionSaveProject(self, _):
        saveProject()

    def onActionImportPoints(self, _):
        if self.t2g_arch_instance:
            self.t2g_arch_instance.importPoints()

    def onActionExportPoints(self, _):
        if self.t2g_arch_instance:
            self.t2g_arch_instance.exportPoints()

    def onActionProfileExportPoints(self, _):
        if self.t2g_arch_instance:
            self.t2g_arch_instance.exportProfilePoints()

    def check_for_needed_cleanup(self):
        """
        Check for instantiated QWidgets originating from classes in our code.
        """
        def fullname(obj):
            class_object = obj.__class__
            module_object = class_object.__module__
            if module_object == "builtins":
                return class_object.__qualname__  # avoid outputs like "builtins.str"
            return module_object + "." + class_object.__qualname__

        folder_name = os_path.basename(os_path.dirname(os_path.realpath(__file__))) + "."
        for widget in QApplication.allWidgets():
            if not fullname(widget).startswith(folder_name):
                continue

            print("NEEDS CLEANUP", not sip.isdeleted(widget), fullname(widget))

            # detect if C++ object from Qt is already deleted
            # so only pyqt still holds a reference which will be deleted
            if not sip.isdeleted(widget):
                # try to solve this needed cleanup
                # if you see "NEEDS CLEANUP" and 'PLUGIN DELETE SUCCESS' in stdout
                # then this was successful, and you should add deleteLater() to your normal code
                widget.deleteLater()
