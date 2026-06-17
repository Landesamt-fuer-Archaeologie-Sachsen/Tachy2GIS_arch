import logging
import os

from qgis.gui import QgisInterface
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt import sip

from .toolbar.toolbar import T2GToolbar
from .logger import setup_logger, teardown_logger

LOGGER = logging.getLogger(__name__)


class PluginInterface:
    def __init__(self, iface: QgisInterface):
        setup_logger()
        LOGGER.debug("Plugin initiated")
        self.iface = iface
        self.toolbar = None

    def initGui(self):
        LOGGER.debug("Plugin loaded")
        self.toolbar = T2GToolbar(self.iface.mainWindow())
        self.iface.addToolBar(self.toolbar)

    def unload(self):
        LOGGER.debug("Plugin unloaded")
        self.iface.mainWindow().removeToolBar(self.toolbar)
        self.toolbar.deleteLater()
        self.toolbar = None

        self.check_and_cleanup()
        teardown_logger()

    def check_and_cleanup(self):
        """Check for instantiated QWidgets originating from classes in our code."""

        def fullname(obj):
            class_object = obj.__class__
            module_object = class_object.__module__
            if module_object == "builtins":
                return class_object.__qualname__  # avoid outputs like "builtins.str"
            return module_object + "." + class_object.__qualname__

        folder_name = os.path.basename(os.path.dirname(os.path.realpath(__file__))) + "."
        for widget in QApplication.allWidgets():
            if not fullname(widget).startswith(folder_name):
                continue

            LOGGER.debug(f"NEEDS CLEANUP {not sip.isdeleted(widget)} {fullname(widget)}")

            # detect if C++ object from Qt is already deleted
            # so only pyqt still holds a reference which will be deleted
            if not sip.isdeleted(widget):
                # try to solve this needed cleanup
                # if you see "NEEDS CLEANUP" and 'PLUGIN DELETE SUCCESS' in stdout
                # then this was successful, and you should add deleteLater() to your normal code
                widget.deleteLater()
