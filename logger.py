import logging

from qgis.core import Qgis, QgsMessageLog

from .settings import PLUGIN_NAME, DEBUG

_LEVEL = logging.DEBUG if DEBUG else logging.INFO
_PACKAGE_NAME = __name__.split(".")[0]

_QGIS_LEVEL_MAP = {
    logging.DEBUG: Qgis.Info,
    logging.INFO: Qgis.Info,
    logging.WARNING: Qgis.Warning,
    logging.ERROR: Qgis.Critical,
    logging.CRITICAL: Qgis.Critical,
}


class QgsLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            qgis_level = _QGIS_LEVEL_MAP.get(record.levelno, Qgis.Info)
            QgsMessageLog.logMessage(self.format(record), PLUGIN_NAME, qgis_level)
        except Exception:
            self.handleError(record)


def _build_handlers() -> list[logging.Handler]:
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    qgis_handler = QgsLogHandler()
    qgis_handler.setLevel(_LEVEL)
    qgis_handler.setFormatter(formatter)

    return [qgis_handler]


def setup_logger() -> None:
    logger = logging.getLogger(_PACKAGE_NAME)
    if not logger.handlers:
        logger.setLevel(_LEVEL)
        for handler in _build_handlers():
            logger.addHandler(handler)


def teardown_logger() -> None:
    logger = logging.getLogger(_PACKAGE_NAME)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
