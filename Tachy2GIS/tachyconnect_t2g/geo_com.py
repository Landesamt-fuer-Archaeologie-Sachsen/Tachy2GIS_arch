from . import gc_constants as gc
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QThread
from PyQt5.QtSerialPort import QSerialPort
from time import time


class GeoCOMRequest:
    PREFIX = "%R1Q"
    TERMINATOR = "\r\n"

    def __init__(self, command, *args):
        self.command = str(command)
        self.args = ','.join(map(str, args))
        self.transaction_id = 0

    def set_transaction_id(self, slot):
        self.transaction_id = slot

    def __str__(self):
        msg = ",".join((GeoCOMRequest.PREFIX, self.command))
        if self.transaction_id:
            msg = ",".join((msg, str(self.transaction_id)))
        msg = ":".join((msg, self.args))
        msg += GeoCOMRequest.TERMINATOR
        return msg

    @property
    def bytes(self):
        return str(self).encode("ascii")

    __repr__ = __str__


class GeoCOMReply:
    PREFIX = "%R1P"

    def __init__(self, bites):
        self.msg = bites.decode('ascii')
        head, tail = self.msg.split(':')
        head = head.split(',')
        tail = tail.strip().split(',')
        self.com_code = int(head[1])
        self.transaction_id = int(head[2])
        self.ret_code = int(tail.pop(0))
        self.results = tail

    def __str__(self):
        return self.msg

    __repr__ = __str__



class GeoCOMReplyHandler:
    def __init__(self, command, types, signal):
        self.command = command
        self.types = types
        self.signal = signal

    def handle(self, reply):
        # Will not work because of type mismatch between reply retcodes
        # (str) and lib constants (int) but looks nicer this way.
        if reply.com_code == gc.GRC_OK and reply.ret_code == gc.GRC_OK:
            casted = [t(value) for t, value in zip(self.types, reply.results)]
            self.signal.emit(casted)


class GeoCOMCallCenter:
    """This is the skeleton of a prototype that mainly exists to describe
    a design. Use at your own risk.
    """
    def __init__(self):
        self.handlers = {}

    def register(self, handler):
        self.handlers[str(handler.command)] = handler

    @pyqtSlot(GeoCOMRequest, GeoCOMReply)
    def handle(self, request, reply):
        handler = self.handlers.get(request.command, False)
        if handler:
            handler.handle(reply)


@pyqtSlot(str)
def connect_beep(port_name):
    serial = QSerialPort()
    serial.setPortName(port_name)
    serial.open(QSerialPort.WriteOnly)
    message = "%R1Q," + str(gc.BMM_BeepAlarm) + ":" + gc.CRLF
    serial.writeData(message.encode('ascii'))
    serial.close()
