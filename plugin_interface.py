import logging
from qgis.gui import QgisInterface

from .logger import setup_logger, teardown_logger
from .settings import DEBUG
from .toolbar.toolbar import T2GToolbar

LOGGER = logging.getLogger(__name__)


class PluginInterface:
    def __init__(self, iface: QgisInterface):
        setup_logger()
        LOGGER.debug("Plugin init ...")
        self.iface = iface
        self.toolbar = None

    def initGui(self):
        LOGGER.debug("Plugin loading ...")
        self.toolbar = T2GToolbar(self.iface.mainWindow())
        self.iface.addToolBar(self.toolbar)

    def unload(self):
        """
        INVARIANTE: unload() ist die exakte Umkehrung von __init__/classFactory
        und initGui(). Was dort aufgebaut/registriert/verbunden wurde, muss hier
        in umgekehrter Reihenfolge wieder abgebaut/deregistriert/getrennt werden.
        Eine unvollständige Umsetzung hat durch die Benutzung von Qt Memory-Leaks
        und alte/doppelt verbundene Signale zur Folge.
        """
        LOGGER.debug("Plugin unloading ...")
        self.iface.mainWindow().removeToolBar(self.toolbar)
        self.toolbar.deleteLater()
        self.toolbar = None

        if DEBUG:
            from .common.debug_checks import check_for_leaked_objects
            check_for_leaked_objects()

        teardown_logger()
