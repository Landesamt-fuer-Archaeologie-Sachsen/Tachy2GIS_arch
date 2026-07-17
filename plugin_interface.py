import logging

from qgis.gui import QgisInterface

from .logger import setup_logger, teardown_logger
from .settings import DEBUG
from .toolbar.toolbar import T2GToolbar

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

        if DEBUG:
            from .common.debug_checks import check_for_leaked_objects
            check_for_leaked_objects()

        teardown_logger()
