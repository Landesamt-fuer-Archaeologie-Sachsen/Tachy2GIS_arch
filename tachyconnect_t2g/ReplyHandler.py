import logging
from PyQt5.QtCore import pyqtSignal, QObject, QEventLoop

from .ts_control import TachyReply

LOGGER = logging.getLogger(__name__)


class ReplyHandler(QObject):
    caught_reply = pyqtSignal(TachyReply)
    fall_back_signal = pyqtSignal(tuple)
    has_fall_back = False

    def __init__(self, fall_back=None):
        super().__init__()
        # per instance, NOT a class attribute: a class-level dict lives as long
        # as the class object itself and keeps every registered bound method -
        # and therefore its receiver (e.g. the whole VtkViewer) - alive far
        # beyond the instance's lifetime
        self.slots = {}
        if fall_back:
            self.fall_back_signal.connect(fall_back)
            self.has_fall_back = True

    def register_command(self, command_class, slot):
        self.slots[command_class.__name__] = slot

    def unregister_command(self, command_class):
        self.slots.pop(command_class.__name__, None)

    def handle(self, request, reply):
        LOGGER.debug(request)
        LOGGER.debug(reply)
        self.caught_reply.emit(reply)
        command = request["message"]
        slot = self.slots.get(command)
        if slot:
            slot(*reply.get_result())
            return True
        elif self.has_fall_back:
            self.fall_back_signal.emit((request, reply))
            return True
        return False


class CommandChain:
    def __init__(self, dispatcher, *commands):
        self.dispatcher = dispatcher
        self.reply_handler = self.dispatcher.reply_handler
        self.index = 0
        self.loop = QEventLoop()
        self.commands = commands

    def set_commands(self, *args):
        LOGGER.debug(f"setting commands: {args}")
        self.commands = args

    def run_chain(self, *results):
        command = self.commands[self.index]
        if results:
            self.reply_handler.unregister_command(self.commands.command)
            self.index += 1
        if self.index < len(self.commands):
            command = self.commands[self.index]
            self.reply_handler.register_command(command.command, self.run_chain)
            self.dispatcher.send(command.command(args=command.args).get_geocom_command())

    def reset(self):
        self.index = 0


class ChainableCommand:
    def __init__(self, command, *args):
        self.command = command
        self.args = args
        LOGGER.debug(self.command)
        LOGGER.debug(self.args)
        LOGGER.debug("ChainableCommand ctored.")
