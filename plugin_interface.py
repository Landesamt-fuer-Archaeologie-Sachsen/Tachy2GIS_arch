import logging

from qgis.gui import QgisInterface

from .logger import setup_logger, teardown_logger
from .settings import DEBUG
from .toolbar.toolbar import T2GToolbar

LOGGER = logging.getLogger(__name__)


class PluginInterface:
    def __init__(self, iface: QgisInterface):
        if DEBUG:
            # first statement in the plugin's lifetime, so everything created
            # afterwards is recorded. Safe to run before setup_logger():
            # debug_checks deliberately reports via print(), not via LOGGER.
            from .common.debug_checks import install_origin_tracker
            install_origin_tracker()

        setup_logger()
        LOGGER.debug("Plugin initiated")
        self.iface = iface
        self.toolbar = None

    def initGui(self):
        LOGGER.debug("Plugin loaded")
        self.toolbar = T2GToolbar(self.iface.mainWindow())
        self.iface.addToolBar(self.toolbar)

    def unload(self):
        """
        INVARIANT: unload() is the exact reverse of __init__/classFactory
        and initGui(). Whatever was built/registered/connected there must
        be torn down/deregistered/disconnected here in reverse order. An
        incomplete implementation causes Qt memory leaks and stale/double
        connected signals through use.
        """
        LOGGER.debug("Plugin unloaded")
        self.iface.mainWindow().removeToolBar(self.toolbar)
        self.toolbar.deleteLater()
        self.toolbar = None

        # process the deleteLater() cascade NOW: a reload creates the new
        # widgets in the same event-processing burst, and tools like the
        # Plugin Reloader flag the still-pending old ones as duplicates
        # (with DEBUG=True, check_for_leaked_objects happened to do this)
        from qgis.PyQt.QtCore import QEvent
        from qgis.PyQt.QtWidgets import QApplication
        QApplication.sendPostedEvents(None, QEvent.DeferredDelete)

        if DEBUG:
            from .common.debug_checks import check_for_leaked_objects
            check_for_leaked_objects()

        teardown_logger()
