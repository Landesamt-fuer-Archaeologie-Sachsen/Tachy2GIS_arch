import logging
from qgis.PyQt.QtSerialPort import QSerialPortInfo
from qgis.PyQt.QtCore import QObject, pyqtSignal, QTimer, QThread

LOGGER = logging.getLogger(__name__)


GEOCOM_RESPONSE_IDENTIFIER = "%R1P"

SERIAL_CONNECTED = "🔗"
SERIAL_AVAILABLE = "🔌"  # Emoji 'electric plug', maybe cannot be displayed
NO_SERIAL_AVAILABLE = "⚠️"


# TODO: Error when T2G is closed and opened again - No Error with class TachyReader
class AvailabilityWatchdog(QThread):
    serial_available = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pollingTimer = QTimer()
        self.pollingTimer.timeout.connect(self.poll)

    def start(self):
        self.pollingTimer.start(2131)

    def poll(self):
        # TODO: better way to find the right COM Port
        # comManList = [i.manufacturer() for i in QSerialPortInfo.availablePorts()]
        if QSerialPortInfo.availablePorts():  # TODO: Passes if any COM Port is available
            # if 'Prolific' in comManList:
            self.serial_available.emit(SERIAL_AVAILABLE)
        else:
            self.serial_available.emit(NO_SERIAL_AVAILABLE)

    def shutDown(self):
        self.pollingTimer.stop()


# Polling for ref height
class RefHeightStatus(QObject):
    ref_height_get = pyqtSignal()
    register_ref_height = pyqtSignal()

    def __init__(self):
        self.pollingTimer = QTimer()
        self.pollingTimer.timeout.connect(self.poll)
        super().__init__()

    def start(self):
        self.pollingTimer.start(2000)
        self.register_ref_height.emit()
        # self.parent.reply_handler.register_command(TMC_GetHeight, self.parent.dlg_set_ref_height)

    def stop(self):
        self.pollingTimer.stop()

    def poll(self):
        LOGGER.info("Ref height poll")
        self.ref_height_get.emit()
        # self.parent.request_ref_height()
