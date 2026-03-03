from enum import Enum

from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QEventLoop, QObject, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QInputDialog

from . import gc_constants, GSI_Parser


class CommunicationConstants:
    GSI = "GSI"
    GEOCOM = "geoCOM"

    GSI_MESSAGE_PREFIX = "?"
    GEOCOM_MESSAGE_PREFIX = "%R1Q"

    GEOCOM_REPLY_PREFIX = "%R1P"

    GSI_REPLY_PREFIXES = ["?", "*"]

    class ImplementationStates(Enum):
        NOT_YET_DETECTED = 0
        NOT_IMPLEMENTED = 1
        GSI = 2
        GEOCOM = 3

    COMMANDS = [""]


class TachyCommand(QObject):
    MESSAGE_PREFIX = ""
    REPLY_PREFIX = ""
    protocol = None

    def __init__(self, command: str, label=None, args=[]):
        super().__init__()
        self.command = command
        self.args = args
        self.transaction_id = 0
        self.label = command if label is None else label

    def parse_reply(self, reply_bytes: bytes):
        return reply_bytes.decode("ascii")

    def set_transaction_id(self, id: int):
        self.transaction_id = id

    def get_transaction_id(self) -> int:
        return self.transaction_id

    def get_protocol(self):
        return self.protocol

    def __str__(self):
        try:
            return f"{self.protocol}: {self.command}, {str(self.args)}"
        except ValueError:
            return "Unitialized command object"


class GSICommand(TachyCommand):
    def __init__(self, command: str, label=None, args=[]):
        super().__init__(command, label, args=args)
        self.protocol = CommunicationConstants.GSI

    def get_transaction_id(self) -> int:
        return 1

    @property
    def bytes(self):
        params = ""
        if len(self.args):
            for arg in self.args:
                params += str(arg) + " "

        message = f"{self.command}{params}{gc_constants.CRLF}"
        return message.encode("ascii")


class GeoCOMCommand(TachyCommand):
    MESSAGE_PREFIX = CommunicationConstants.GEOCOM_MESSAGE_PREFIX

    def __init__(self, command: str, label=None, *args):
        super().__init__(command, label, args=args)
        self.protocol = CommunicationConstants.GEOCOM

    @property
    def bytes(self):
        message = f"{self.MESSAGE_PREFIX},{str(self.command)},{self.transaction_id}:{','.join(map(str, self.args))}{gc_constants.CRLF}"
        return message.encode("ascii")


class TachyReply:
    def __init__(self, bites: bytes):
        self.bites = bites
        self.ascii = bites.data().decode("latin-1")

    def __str__(self):
        return self.ascii

    def get_transaction_id(self):
        raise ValueError("This base type is not supposed to have an id.")

    def get_protocol(self):
        if self.ascii[0] in CommunicationConstants.GSI_REPLY_PREFIXES:
            return CommunicationConstants.GSI
        if self.ascii.startswith(CommunicationConstants.GEOCOM_REPLY_PREFIX) or self.ascii[:4] == "@W127":
            return CommunicationConstants.GEOCOM
        raise ValueError(f"Tachymeter reply uses unknown protocoll: {self.ascii}")

    def get_result(self):
        raise NotImplemented("Has to be implemented for each subclass.")

    def success(self):
        return False


class GSIReply(TachyReply):
    @property
    def PREFIX(self):
        self.ascii[0]

    def get_transaction_id(self):
        return 1

    def success(self):
        return self.ascii.startswith(GSI_Parser.REPLY_ACK)

    def get_result(self):
        return GSI_Parser.parse(self.ascii)


class GeoCOMReply(TachyReply):
    PREFIX = CommunicationConstants.GEOCOM_REPLY_PREFIX

    def get_transaction_id(self):
        header = self.ascii.split(":")[0]
        segments = header.split(",")
        return int(segments[2])

    def success(self):
        return self.ascii.startswith(GeoCOMReply.PREFIX)

    def get_result(self):
        payload = self.ascii.split(":")[1].strip()
        return payload.split(",")


class MessageQueue(QObject):
    non_requested_data = pyqtSignal(str)

    def __init__(self, n_slots=7):
        super().__init__()
        self.indices = list(range(1, n_slots + 1))
        self.slots = {}
        self.serial = QSerialPort

    def set_serial(self, serial):
        self.serial = serial

    def append(self, msg: TachyCommand):
        def first_free_slot():
            for i in self.indices:
                if i not in self.slots.keys():
                    return i
            return False

        if self.serial is None:
            return False
        slot = first_free_slot()
        if slot and self.serial:
            self.slots[slot] = {"message": msg.label}
            msg.set_transaction_id(slot)
            self.serial.write(msg.bytes)
        return slot

    def register_reply(self, reply: TachyReply):
        message_id = reply.get_transaction_id()
        try:
            request = self.slots.pop(message_id)
            return request, reply
        except KeyError:
            self.non_requested_data.emit(reply.ascii)

    def close(self):
        self.serial.close()

    def __str__(self):
        n_slots = self.indices[-1]
        return f"Message queue with {n_slots} slot{'s' if n_slots > 1 else ''}"


class Dispatcher(QThread):
    pollingInterval = 1000
    serial_disconnected = pyqtSignal(str, str)
    serial_connected = pyqtSignal(str, str)
    log = pyqtSignal(str)
    non_requested_data = pyqtSignal(str)
    SERIAL_CONNECTED = "🔗"
    NO_SERIAL_AVAILABLE = "⚠️"

    def __init__(self, gsi_queue: MessageQueue, geocom_queue: MessageQueue, reply_handler, parent=None):
        super(self.__class__, self).__init__(parent)
        self.pollingTimer = QTimer(self)
        self.pollingTimer.timeout.connect(self.poll)
        self.serial = QSerialPort()
        self.loop = QEventLoop()
        self.queues = {CommunicationConstants.GSI: gsi_queue, CommunicationConstants.GEOCOM: geocom_queue}
        self.reply_types = {CommunicationConstants.GSI: GSIReply, CommunicationConstants.GEOCOM: GeoCOMReply}
        self.reply_handler = reply_handler
        for queue in self.queues.values():
            queue.non_requested_data.connect(self.emit_non_requested_data)

    def emit_non_requested_data(self, data):
        self.non_requested_data.emit(data)

    def hook_up(self):
        # close port if connection is established
        self.log.emit("Connection attempt")
        if self.serial.isOpen():
            port_name = self.serial.portName()
            self.serial.close()
            self.serial_disconnected.emit(self.NO_SERIAL_AVAILABLE, port_name)
            self.loop.quit()
            return
        port_names = [port.portName() for port in QSerialPortInfo.availablePorts()]
        port_names.reverse()

        def moin():
            if port_names:
                ping = Ping(port_names.pop(), 500)
                ping.timed_out.connect(moin)
                ping.found_tachy.connect(self.set_serial_port)
                ping.fire()

        moin()

    def manual_hook_up(self):
        """Let the user manually select a COM port from available ports."""
        self.log.emit("Manual connection attempt")
        if self.serial.isOpen():
            port_name = self.serial.portName()
            self.serial.close()
            self.serial_disconnected.emit(self.NO_SERIAL_AVAILABLE, port_name)
            self.loop.quit()
            return
        all_port_names = [port.portName() for port in QSerialPortInfo.availablePorts()]
        if not all_port_names:
            self.log.emit("No COM ports available.")
            return
        selected_port, ok = QInputDialog.getItem(None, "Verbinden...", "COM-Port auswählen:", all_port_names, 0, False)
        if ok and selected_port:
            self._send_beep_alarm(selected_port)
            self.set_serial_port(selected_port)

    def _send_beep_alarm(self, port_name):
        """Open port briefly to send BMM_BeepAlarm, then close again so set_serial_port can re-open it cleanly."""
        beep_serial = QSerialPort()
        beep_serial.setPortName(port_name)
        if beep_serial.open(QSerialPort.ReadWrite):
            message = f"{GeoCOMCommand.MESSAGE_PREFIX},{str(gc_constants.BMM_BeepNormal)},1:{gc_constants.CRLF}"
            beep_serial.writeData(message.encode("ascii"))
            beep_serial.flush()
            beep_serial.close()

    def start(self):
        self.pollingTimer.start(self.pollingInterval)
        self.serial_connected.emit(self.SERIAL_CONNECTED, self.serial.portName())
        self.log.emit("Started listening.")
        self.loop = QEventLoop()
        self.loop.exec_()

    def stop(self):
        self.pollingTimer.stop()

    def send_log(self, *args):
        self.log.emit(str(args))

    def set_serial_port(self, port_name):
        if self.serial.isOpen():
            self.serial.close()
        self.serial.setPortName(port_name)
        self.serial.open(QSerialPort.ReadWrite)
        for queue in self.queues.values():
            self.log.emit(f"Connecting {str(queue)} to {self.serial.portName()}")
            queue.set_serial(self.serial)
        self.start()

    def poll(self):
        if self.serial.error() == QSerialPort.ResourceError:  # device is unexpectedly removed from the system
            self.serial.close()
            self.serial_disconnected.emit(f"Connection {self.serial.portName} failed", self.serial.portName())
        while self.serial.canReadLine():
            reply = TachyReply(self.serial.readLine())
            self.register_reply(reply)
        else:
            pass

    def send(self, message: TachyCommand):
        queue = self.queues[message.protocol]
        success = queue.append(message)
        return bool(success)

    def register_reply(self, reply: TachyReply):
        protocol = reply.get_protocol()
        reply_type = self.reply_types[protocol]
        queue = self.queues[protocol]
        try:
            self.reply_handler.handle(*queue.register_reply(reply_type(reply.bites)))
        except TypeError:
            """TypeErrors usually stem from incoming data that can not be
            associated with any request. These are handled by the 'non_requested_data'
            signal."""
            pass


class Ping(QThread):
    found_tachy = pyqtSignal(str)
    found_something = pyqtSignal(str)
    timed_out = pyqtSignal(str)
    pinging = pyqtSignal(str)

    def __init__(self, port_name, timeout=1200):
        super().__init__()
        self.timeout = timeout
        self.serial = QSerialPort()
        self.serial.setPortName(port_name)
        self.is_open = self.serial.open(QSerialPort.ReadWrite)
        if not self.is_open:
            return
        message = f"{GeoCOMCommand.MESSAGE_PREFIX},{str(gc_constants.BMM_BeepNormal)},1:{gc_constants.CRLF}"
        self.serial.writeData(message.encode("ascii"))
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.read)

    def fire(self):
        if self.is_open:
            self.timer.start(self.timeout)
            self.ping_loop = QEventLoop()
            self.ping_loop.exec_()

    def read(self):
        self.pinging.emit(f"Pinging {self.serial.portName()}")
        if self.serial.canReadLine():
            reply = bytes(self.serial.readLine()).decode("latin-1")
            self.serial.close()
            if reply.startswith(GeoCOMReply.PREFIX):
                self.found_tachy.emit(self.serial.portName())
            else:
                self.found_something.emit(self.serial.portName())
        else:
            self.timed_out.emit(f"Ping timed out: {self.serial.portName()}")

        self.serial.close()
        self.ping_loop.quit()
        self.quit()
