from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt, pyqtSignal
from .ui.tachy_joystick import Ui_Dialog as Ui_TachyJoystick
from tachyconnect.ts_control import Dispatcher
from tachyconnect.TachyRequest import (MOT_StartController,
                                       MOT_StopController,
                                       MOT_SetVelocity,
                                       AUT_Search,
                                       AUT_LockIn,
                                       AUT_PS_SearchNext,
                                       AUS_SetUserLockState,
                                       AUS_GetUserLockState,
                                       EDM_SetEglIntensity,
                                       AUT_SetATRStatus,
                                       TMC_GetHeight
)
from tachyconnect.ReplyHandler import CommandChain, ChainableCommand

import tachyconnect.gc_constants as gc

class TachyJoystick(QDialog, Ui_TachyJoystick):
    MAX_SPEED = 0.42
    STEP = 0.06

    LOCKED = "🔒"
    UNLOCKED = " "
    LOCK_STATES = {'0': UNLOCKED,
                   '1': LOCKED}
    ref_z_received = pyqtSignal(str)

    def __init__(self, dispatcher, parent=None, flags=Qt.Dialog | Qt.Tool):
        super().__init__(parent = parent, flags = flags)
        self.reject = self.accept
        self.dispatcher = dispatcher

        # THis block builds a chain of requests that are triggered after a successfull target search
        self.dispatcher.reply_handler.register_command(AUT_Search, self.searched)
        self.dispatcher.reply_handler.register_command(AUT_SetATRStatus, self.tracking)
        self.dispatcher.reply_handler.register_command(AUS_SetUserLockState, self.set_lock)

        # Other reply handling goes here
        self.dispatcher.reply_handler.register_command(AUS_GetUserLockState, self.show_lock_state)
        self.dispatcher.reply_handler.register_command(TMC_GetHeight, self.show_ref_height)
        self.dispatcher.reply_handler.register_command(AUT_PS_SearchNext, self.set_lock)
        # self.dispatcher.reply_handler.register_command(AUT_LockIn, self.get_lock_state)

        self.hzSpeed = 0
        self.vtSpeed = 0
        self.setupUi(self)
        self.connectSignalsSlots()

    ## BEGIN search reply handling
    def searched(self, *args):
        print('searched')
        self.dispatcher.send(AUT_SetATRStatus(args=[gc.ON_OFF_TYPE.ON.value]).get_geocom_command())

    def tracking(self, *args):
        self.dispatcher.send(AUS_SetUserLockState(args=[gc.ON_OFF_TYPE.ON.value]).get_geocom_command())

    def set_lock(self, *args):
        self.dispatcher.send(AUT_LockIn().get_geocom_command())
        self.get_lock_state()
    ## END search reply handling
    def get_ref_height(self):
        self.dispatcher.send(TMC_GetHeight().get_geocom_command())

    def show_ref_height(self, *args):
        z_text = f"{float(args[-1]):.3f}"
        self.refHeight.setText(z_text)
        self.ref_z_received.emit(z_text)

    def get_lock_state(self):
        self.dispatcher.send(AUS_GetUserLockState().get_geocom_command())

    def show_lock_state(self, *args):
        #print('Lock state: ' + args)
        if args[0] == '0':
            self.lockState.setText(TachyJoystick.LOCK_STATES[args[-1]])
        else:
            self.lockState.setText(TachyJoystick.LOCK_STATES[0])

    def connectSignalsSlots(self):
        self.joystickUp.clicked.connect(self.up)
        self.joystickOk.clicked.connect(self.accept)
        self.joystickDown.clicked.connect(self.down)
        self.joystickStop.clicked.connect(self.stop)
        self.joystickLeft.clicked.connect(self.left)
        self.joystickRight.clicked.connect(self.right)
        self.joystickLock.clicked.connect(self.lock)
        self.pwrSearch.clicked.connect(self.start_pwr_search)

    def lock(self):
        self.get_lock_state()
        self.dispatcher.send(AUT_Search(args=[.1, .3]).get_geocom_command())

    def lights_off(self):
        self.dispatcher.send(EDM_SetEglIntensity(args=['0']).get_geocom_command())

    def show(self):
        super().show()
        self.dispatcher.send(MOT_StartController(args=['1']).get_geocom_command())
        self.dispatcher.send(EDM_SetEglIntensity(args=['3']).get_geocom_command())
        self.get_lock_state()
        self.get_ref_height()


    def accept(self):
        self.stop()
        self.dispatcher.send(MOT_StopController().get_geocom_command())
        self.lights_off()
        super().accept()

    def set_velocity(self):
        self.dispatcher.send(MOT_SetVelocity(args=[self.hzSpeed, self.vtSpeed]).get_geocom_command())

    def up(self):
        if abs(self.vtSpeed) < TachyJoystick.MAX_SPEED:
            self.vtSpeed -= TachyJoystick.STEP
            self.set_velocity()

    def down(self):
        if abs(self.vtSpeed) < TachyJoystick.MAX_SPEED:
            self.vtSpeed += TachyJoystick.STEP
            self.set_velocity()

    def left(self):
        if abs(self.hzSpeed) < TachyJoystick.MAX_SPEED:
            self.hzSpeed += TachyJoystick.STEP
            self.set_velocity()

    def right(self):
        if abs(self.hzSpeed) < TachyJoystick.MAX_SPEED:
            self.hzSpeed -= TachyJoystick.STEP
            self.set_velocity()

    def stop(self):
        self.hzSpeed = self.vtSpeed = 0
        self.set_velocity()

    def start_pwr_search(self):
        self.dispatcher.send(AUT_PS_SearchNext(args=[d.value for d in AUT_PS_SearchNext.defaults]).get_geocom_command())