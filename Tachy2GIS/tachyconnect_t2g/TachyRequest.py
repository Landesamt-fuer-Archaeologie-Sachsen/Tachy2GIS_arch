from datetime import datetime as dt
from . import gc_constants as gc
from .ts_control import GeoCOMCommand, GSICommand, CommunicationConstants
from PyQt5.QtCore import QObject

class TachyRequest(QObject):
    gsi_command = ""
    gc_command = ""
    unpacking_keys = {}
    defaults = []
    description = ""

    def __init__(self, args = []):
        super().__init__()
        self.gc_command = str(gc.COMMAND_CODES.get(self.get_class_name()))
        self.args = args

    def get_class_name(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.get_class_name()}: {', '.join(self.args) if len(self.args) else 'No args'}."

    def get_gsi_command(self):
        if self.gsi_command == "":
            raise NotImplementedError(f'No GSI command for {self.get_class_name()}')
        return GSICommand(self.gsi_command, self.get_class_name(), *self.args)

    def get_geocom_command(self):
        return GeoCOMCommand(self.gc_command, self.get_class_name(), *self.args)

    @classmethod
    def get_defaults(cls):
        return cls.defaults

    @classmethod
    def get_helptext(cls, i):
        if i < len(cls.helptexts):
            return cls.helptexts[i]
        else:
            return ''


class COM_NullProc(TachyRequest):
    description = """Check Communication
This function does not provide any functionality except of checking if the
communication is up and running."""


class COM_Local(TachyRequest):
    description = """Switch TPS1100 into Local Mode
Leaves on-line mode and switches TPS1100 into local mode. If in local
mode, no communication will take place. Any attempt of sending data will
be ignored. Changing local into online mode can be done manually only."""


class COM_SetDoublePrecision(TachyRequest):
    description = """Set Double Precision Setting
This function sets the precision - number of digits to the right of the
decimal - when double floating-point values are transmitted. The TPS’
system software always calculates with highest possible precision. The
default precision is fifteen digits. However, if this precision is not needed
then transmission of double data (ASCII transmission) can be speeded up
by choosing a lower precision. Especially when many double values are
transmitted this may enhance the operational speed. The usage of this
function is only meaningful if the communication is set to ASCII
transmission mode. In the case of an ASCII request, the precision of the
server side will be set. Notice that trailing Zeros will not be sent by the
server and values may be rounded. E.g. if precision is set to 3 and the exact
value is 1.99975 the resulting value will be 2.0
Note: With this function one can decrease the accuracy of the delivered
values."""
    defaults = ["15"]
    helptexts = ["Number of digits right to the comma"]


class COM_GetDoublePrecision(TachyRequest):
    description = """Get Double Precision Setting
This function returns the precision - number of digits to the right of the
decimal point - when double floating-point values are transmitted. The
usage of this function is only meaningful if the communication is set to
ASCII transmission mode. Precision is equal in both transmission
directions. In the case of an ASCII request, the precision of the server side
will be returned."""


class COM_SetSendDelay(TachyRequest):
    description = """Set Reply Delay
The GeoCOM implementation of the server has been optimised for speed.
If the server reacts to fast, then it may happen, that the client is not able to
receive the reply (complete and) correctly. This RPC inserts a delay before
the server responds to a request. This might be of interest especially for
radio data links. Reset to no delay can be done with nSendDelay = 0."""
    defaults = ["0"]
    helptexts = ["Time of transmission delay in milliseconds"]


class COM_GetBinaryAvailable(TachyRequest):
    description = """Get Binary Attribute of Server
This function gets the ability information about the server to handle binary
communication. Since TPS1100 Release 2.00 the client may make requests in
binary format which speeds up the communication by about 40-50%."""


class COM_SetBinaryAvailable(TachyRequest):
    description = """Set Binary Attribute of Server
This function sets the ability of the server to handle binary communication.
With this function, one can force to communicate in ASCII only. During
initialisation, the client checks if binary communication is enabled /
possible or not which depends on this flag. Binary data format is not
supported yet in GeoCOM Versions below 2.0."""
    defaults = [gc.BOOLEAN_TYPE.TRUE]
    helptexts = ["""TRUE: enable binary operation.
FALSE: enable ASCII operation only."""]


class COM_GetSWVersion(TachyRequest):
    gsi_command = "GET/I/WI593;"
    description = """Retrieve Server Release Information
This function retrieves the current GeoCOM release (release, version and
subversion) of the server."""


class COM_SwitchOnTPS(TachyRequest):
    gsi_command = "a"
    description = """Switch on TPS instrument
This function switches on the TPS1100 instrument and put it into remote
mode. It can also be used to switch from sleep into remote mode."""
    defaults = [gc.COM_TPS_STARTUP_MODE.COM_TPS_STARTUP_REMOTE]
    helptexts = """Run mode - use COM_TPS_STARTUP_REMOTE only!
COM_TPS_STARTUP_LOCAL will yield to erroneous behaviour."""


class COM_SwitchOffTPS(TachyRequest):
    gsi_command = "b"
    description = """Switch off TPS1100 or Set Sleep Mode
This function switches off the TPS1100 instrument or put it into sleep
mode."""
    defaults = [gc.COM_TPS_STOP_MODE.COM_TPS_STOP_SLEEP]
    helptexts = ["Stop mode"]


class COM_EnableSignOff(TachyRequest):
    description = """Enable Remote Mode Logging
This function enables logging if the Remote mode changes. See also
section 3.5 TPS1100 Instrument Modes of Operation for further
explanations."""
    defaults = [gc.BOOLEAN_TYPE.FALSE]
    helptexts = ["TRUE: enable mode logging"]


class EDM_Laserpointer(TachyRequest):
    description = """Switch on/off laserpointer
Laserpointer is only available in theodolites which supports distance
measurement without reflector."""
    defaults = [gc.ON_OFF_TYPE.ON]
    helptexts = ["""
ON - switch Laserpointer on
OFF - switch Laserpointer off"""]


class EDM_SetBumerang(TachyRequest):
    description = """Switch boomerang filter on/off
The boomerang filter is not available for some add-on EDM’s.
Deleted in TPS1100"""
    defaults = [gc.ON_OFF_TYPE.OFF]
    helptexts = ["""ON - switch boomerang filter on
OFF - switch boomerang filter off"""]


class EDM_On(TachyRequest):
    description = """Switch on/off EDM
Normal distance measurement switches on or off the EDM automatically. If
there is no supply voltage for the EDM, EDM_On also connects it. Normally
the supply voltage is switched off together with the EDM, unless the
Tracklight or the diode laser is switched on too, or the permanent power-on-
mode is set. These functions overlie the functionality of EDM_On and EDM
cannot be switched off before the Tracklight or the diode laser stops
working. However, after 10 min the EDM will be switched off.
Deleted in TPS1100"""
    defaults = [gc.ON_OFF_TYPE.ON]
    helptexts = ["""ON - switch EDM on
OFF - switch EDM off"""]


class EDM_SetTrkLightSwitch(TachyRequest):
    description = """Switch on/off tracklight
The Tracklight must be available for EDM.
Replaced by: EDM_SetEGLIntensity in TPS1100"""
    defaults = [gc.ON_OFF_TYPE.ON]
    helptexts = ["""ON - switch on Tracklight
OFF - switch off Tracklight"""]


class EDM_SetTrkLightBrightness(TachyRequest):
    description = """Change intensity of tracklight
The Tracklight must be available for EDM.
Replaced by: EDM_SetEGLIntensity in TPS1100"""
    defaults = [gc.EDM_TRKLIGHT_BRIGHTNESS.EDM_HIGH_BRIGHTNESS]
    helptexts = [""""""]


class EDM_GetTrkLightSwitch(TachyRequest):
    description = """Get status of tracklight switch
The Tracklight must be available for EDM.
Replaced by: EDM_GetEGLIntensity in TPS1100"""


class EDM_GetTrkLightBrightness(TachyRequest):
    description = """Get value of intensity of tracklight
The Tracklight must be available for EDM.
Replaced by: EDM_GetEGLIntensity"""


class EDM_GetBumerang(TachyRequest):
    description = """Get status of boomerang filter
Call this function to retrieve the status of the "boomerang filter" (i.e. ON,
OFF). If the distance is within 60-100 meters and the boomerang filter is
turned off, wrong measurement results are possible. With the boomerang
filter turned on, the measurement accuracy can be increased until up to max.
2.5 cm.
The boomerang filter is not available for some add-on EDM’s.
Deleted in TPS1100"""


class EDM_GetEglIntensity(TachyRequest):
    description = """Get value of intensity of guide light
The Electronic Guide Light must be implemented in the theodolite."""


class EDM_SetEglIntensity(TachyRequest):
    description = """Change intensity of guide light
The Electronic Guide Light must be implemented in the theodolite.
New since TPS1100"""
    defaults=[gc.EDM_EGLINTENSITY_TYPE.EDM_EGLINTEN_HIGH]
    helptexts=[""""""]


class TMC_GetAngle1(TachyRequest):
    description = """Returns complete angle measurement
This function carries out an angle measurement and, in dependence of
configuration, inclination measurement and returns the results. As shown
the result is very comprehensive. For simple angle measurements use
TMC_GetAngle5 or TMC_GetSimpleMea instead."""
    defaults = [gc.TMC_INCLINE_PRG.TMC_AUTO_INC]
    helptexts = ["Inclination sensor measurement mode."]


class TMC_SetInclineSwitch(TachyRequest):
    description = """Switch dual axis compensator on or off
This function switches the dual axis compensator on or off."""
    defaults = [gc.ON_OFF_TYPE.ON]
    helptexts = ["Dual axis compensator's state."]


class TMC_GetInclineSwitch(TachyRequest):
    description = """Get the dual axis compensator's state
This function returns the current dual axis compensator's state."""


class TMC_DoMeasure(TachyRequest):
    description = """Carries out a distance measurement
This function carries out a distance measurement in a variety of TMC
measurement modes like single distance, rapid tracking,... . Please note that
this command does not output any values (distances). In order to get the
values you have to use other measurement functions such as
TMC_GetCoordinate, TMC_GetSimpleMea or TMC_GetAngle.
The value of the distance measured is kept in the instrument up to the next
TMC_DoMeasure command where a new distance is requested or the
distance is clear by the measurement program TMC_CLEAR.
Note: If you perform a distance measurement with the measure program
TMC_DEF_DIST, the distance sensor will be work with the set EDM
mode, see TMC_SetEdmMode."""
    defaults = [gc.TMC_MEASURE_PRG.TMC_DEF_DIST, gc.TMC_INCLINE_PRG.TMC_AUTO_INC]
    helptexts = ["TMC measurement mode.", "Inclination sensor measurement mode."]


class TMC_GetStation(TachyRequest):
    description = """Get the coordinates of the instrument station
This function is used to get the co-ordinates of the instrument station."""


class TMC_SetStation(TachyRequest):
    description = """Set the coordinates of the instrument station
This function is used to set the co-ordinates of the instrument station."""
    defaults = ["0", "0", "0", "0"]
    helptexts = ["E0[double] - Station easting coordinate",
               "N0[double] - Station northing coordinate",
               "H0[double] - Station height coordinate",
               "Hi[double] - Instrument height"]


class TMC_GetHeight(TachyRequest):
    gsi_command = "GET/I/WI88"
    description = """Returns the current reflector height
This function returns the current reflector height."""



class TMC_SetHeight(TachyRequest):
    description = """Sets new reflector height
This function sets a new reflector height."""
    defaults = ["0"]
    helptexts = ["New reflector height"]


class TMC_GetAngSwitch(TachyRequest):
    description = """Get angular correction's states
This function returns the angular correction's state."""


# ASCII Request takes no parameters
class TMC_SetAngSwitch(TachyRequest):
    description = """Enable/disable angle corrections
With this function you can enable/disable follow angle measurement correction.
incline: The incline will be considered in the angle
measurement if enabled.
stand axis: The stand axis will be considered in the angle
measurement if enabled.
collimation: The collimation will be considered in the angle
measurement if enabled
tilt axis: The tilt axis will be considered in the angle
measurement if enabled.
Note: You can set the various corrections only, if no distance is existing! (Use the
function TMC_DoMeasure(TMC_CLEAR,..) in order to clear the distance)"""


class TMC_SetHandDist(TachyRequest):
    description = """Input slope distance and height offset
This function is used to input manually measured slope distance and height
offset for a following measurement. Additionally an inclination
measurement and an angle measurement are carried out to determine the
co-ordinates of target. The V-angle is corrected to π/2 or 3⋅π/2 in
dependence of the instrument’s face because of the manual input.
After the function call the previous measured distance is cleared."""
    defaults = ["10", "1", gc.TMC_INCLINE_PRG.TMC_AUTO_INC]
    helptexts = ["Slope distance", "Height offset" , "Inclination sensor measurement mode."]


class TMC_SetEdmMode(TachyRequest):
    description = """Set EDM measurement modes
This function set the current measurement modes new. The measure
function TMC_DoMeasure(TMC_DEF_DIST) will work with this
configuration."""
    defaults = [gc.EDM_MODE.EDM_SINGLE_STANDARD]
    helptexts = ["EDM measurement mode."]


class TMC_GetEdmMode(TachyRequest):
    description = """Get the EDM measurement mode
This function returns the EDM measurement mode."""


class TMC_GetSignal(TachyRequest):
    description = """Get information about EDM’s signal amplitude
This function returns information about the amplitude of the EDM signal.
The function only can perform measuring if the signal measurement
program is activated. Start the signal measurement program with
TMC_DoMeasure where Command = TMC_SIGNAL. After the
measurement the EDM must be switch off (use TMC_DoMeasure where
Command = TMC_CLEAR"""


class TMC_GetPrismCorr(TachyRequest):
    description = """Get the prism constant
This function is used to get the prism constant."""


class TMC_SetPrismCorr(TachyRequest):
    description = """Set the prism constant
This function is used to set the prism constant.
The high-level function BAP_SetPrismType overwrites this setting."""
    defaults = ["0.1"]
    helptexts = ["Prism constant [mm]"]


class TMC_GetFace(TachyRequest):
    description = """Get face information of current telescope position
This function returns the face information of the current telescope position.
The face information is only valid, if the instrument is in an active
measurement state (that means a measurement function was called before
the TMC_GetFace call, see example). Note that the instrument
automatically turns into an inactive measurement state after a predefined
timeout."""

# todo: Try GetAtmCorr for default values
class TMC_SetAtmCorr(TachyRequest):
    description = """Set atmospheric correction parameters
This function is used to set the parameters for the atmospheric correction."""
    defaults = ["", "", "", ""]
    helptexts = ["Wave length of the EDM transmitter",
                "Atmospheric pressure",
                "Dry temperature",
                "Wet temperature"]


class TMC_GetAtmCorr(TachyRequest):
    description = """Get atmospheric correction parameters
This function is used to get the parameters for the atmospheric correction."""


# todo: Try GetRefractiveCorr for default values
class TMC_SetRefractiveCorr(TachyRequest):
    description = """Set the refraction factor
This function is used to set the refraction distortion factor for correction of
measured height difference."""
    defaults = [gc.ON_OFF_TYPE.ON, "", ""]
    helptexts = ["Refraction correction On/Off", "Radius of the earth", "Refractive coefficient"]


class TMC_GetRefractiveCorr(TachyRequest):
    gsi_command = "GET/I/WI538"
    description = """Get the refraction factor
This function is used to get the refraction distortion factor for correction of
measured height difference."""


class TMC_GetCoordinate(TachyRequest):
    description = """Gets the coordinates of a measured point
This function issues an angle measurement and, in dependence of the
selected Mode, an inclination measurement and calculates the co-ordinates
of the measured point with an already measured distance. The WaitTime is
a delay to wait for the distance measurement to finish. Single and tracking
measurements are supported. Information about a missing distance
measurement and other information about the quality of the result is
returned in the return-code."""
    defaults=["1000", gc.TMC_INCLINE_PRG.TMC_AUTO_INC]
    helptexts=["""The delay to wait for the distance
measurement to finish [ms].""",
"Inclination sensor measurement mode"]


class TMC_GetCoordinate1(TMC_GetCoordinate):
    pass


class TMC_SetRefractiveMethod(TachyRequest):
    description = """Set the refraction model
This function is used to set the refraction model."""
    defaults=["2"]
    helptexts=["""Refraction data:
Method = 1 means method 1 (for
Australia)
Method = 2 means method 2 (for the rest
of the world)"""]


class TMC_GetRefractiveMethod(TachyRequest):
    description = """Get the refraction model
This function is used to get the current refraction model."""


class TMC_GetAngle5(TachyRequest):
    description = """Returns simple angle measurement
This function carries out an angle measurement and returns the results. In
contrast to the function TMC_GetAngle1 this function returns only the
values of the angle. For simple angle measurements use or
TMC_GetSimpleMea instead.
Information about measurement is returned in the return code."""


class TMC_GetSimpleMea(TachyRequest):
    description = """Returns angle and distance measurement
This function returns the angles and distance measurement data. The
distance measurement will be set invalid afterwards. It is important to note
that this command does not issue a new distance measurement.
If a distance measurement is valid the function ignores WaitTime and
returns the results.
If no valid distance measurement is available and the distance measurement
unit is not activated (by TMC_DoMeasure before the TMC_GetSimpleMea
call) the WaitTime is also ignored and the angle measurement result is
returned. So this function can be used instead of TMC_GetAngle5.
Information about distance measurement is returned in the return- code."""
    defaults=["3000", gc.TMC_INCLINE_PRG.TMC_AUTO_INC]
    helptexts=["""The delay to wait for the distance
measurement to finish [ms].""", """Inclination sensor measurement mode."""]


class TMC_SetOrientation(TachyRequest):
    description = """Orients the theodolite in Hz direction
This function is used to orientates the instrument in Hz direction. It is a
combination of an angle measurement to get the Hz offset and afterwards
setting the angle Hz offset in order to orientates onto a target. Before the
new orientation can be set an existing distance must be cleared (use
TMC_DoMeasure with the command = TMC_CLEAR)."""
    defaults=["0.0"]
    helptexts=["Hz Orientation [rad]"]


class TMC_IfDataAzeCorrError(TachyRequest):
    description = """If ATR error occur
If you get back the return code
TMC_ANGLE_NO_FULL_CORRECTION or TMC_
NO_FULL_CORRECTION from a measurement function, so you can find
out with this function, whether the returned data record from the
measurement function a missing deviation correction of the ATR included
or not."""


class TMC_IfDataIncCorrError(TachyRequest):
    description = """If incline error occur
If you get back the return code
TMC_ANGLE_NO_FULL_CORRECTION or TMC_
NO_FULL_CORRECTION from a measurement function, so you can find
out with this function, whether the returned data record from the
measurement function a missing inclination correction of the incline sensor
included or not. A error information can only occur if the incline sensor is
active."""


class TMC_GetSimpleCoord(TachyRequest):
    description = """Get cartesian coordinates
This function get the cartesian co-ordinates if a valid distance existing. The
parameter WaitTime defined the max wait time in order to get a valid
distance. If after the wait time not a valid distance existing, the function
initialise the parameter for the co-ordinates (E,N,H) with 0 and returns a
error. For the co-ordinate calculate will require incline results. With the
parameter eProg you have the possibility the incline results either to
calculate or to measure it anew explicitly. We recommend to use the third
variant, let the system determined (see parameters)."""
    defaults=["1000", gc.TMC_INCLINE_PRG.TMC_AUTO_INC]
    helptexts=["Max. wait time to get a valid distance [ms]", """Incline measuring program
Note: The best performance regarding measure
rate and accuracy you get with the automatically
program, the instrument checks the conditions
around the station. We recommend to take this
mode any time."""]


class TMC_QuickDist(TachyRequest):
    description = """Returns slope-distance and hz-,v-angle
The function waits until a new distance is measured and then it returns the angle
and the slope-distance, but no co-ordinates. Is no distance available, then it returns
the angle values (hz, v) and the corresponding return-code.
At the call of this function, a distance measurement will be started with the rapid-
tracking measuring program. If the EDM is already active with the standard
tracking measuring program, the measuring program will not changed to rapid
tracking. Generally if the EDM is not active, then the rapid tracking measuring
program will be started, otherwise the used measuring program will not be
changed.
In order to abort the current measuring program use the function
TMC_DoMeasure.
This function is very good suitable for target tracking, where high data transfers
are required.
Note: Due to performance reasons the used inclination will be calculated (only if
incline is activated), so the basic data for the incline calculation is exact, at
least two forced incline measurements should be performed in between.
The forced incline measurement is only necessary if the incline of the
instrument because of measuring assembly has been changed.
Use the function TMC_GetAngle(TMC_MEA_INC, Angle) for the forced
incline measurement. (For the forced incline measurement, the instrument
must be in stable state for more than 3sec.)."""


class TMC_GetSlopeDistCorr(TachyRequest):
    description = """Get slope distance correction factors
This function retrieves the correction factors that are used for slope
distance measurement corrections."""


class CSV_GetInstrumentNo(TachyRequest):
    description = """Get factory defined instrument number
Returns the serial number."""


class CSV_GetInstrumentName(TachyRequest):
    gsi_command = "GET/I/WI13"
    description = """Get Leica specific instrument name
Returns the instrument name"""


class CSV_SetUserInstrumentName(TachyRequest):
    description = """Set user defined instrument name
Deleted in TPS1100+"""
    defaults=[""""""]
    helptexts=["""The user defined instrument name."""]


class CSV_GetUserInstrumentName(TachyRequest):
    description = """Get user defined instrument name
This name can be set by the user (see CSV_SetUserInstrumentName) If
no user instrument name is set the return code is RC_UNDEFINED and the
Leica specific instrument name is returned.
Deleted in TPS1100+"""


class CSV_SetDateTime(TachyRequest):
    description = """Set date and time
It is not possible to set invalid date or time. See data type description of
DATIME for valid date and time."""
    helptexts = ["Year", "Month", "Day", "Hour", "Minute", "Second"]

    @classmethod
    def get_defaults(cls):
        return dt.now().strftime("%Y,%m,%d,%H,%M,%S").split(",")

class CSV_GetDateTime(TachyRequest):
    description = """Get date and time.
The ASCII response is formatted corresponding to the data type DATIME.
A possible response can look like this: %R1P,0,0:0,1996,'07',
'19','10','13','2f' (see chapter ASCII data type declaration for
further information)"""


class CSV_GetVBat(TachyRequest):
    description = """Get the value of the voltage supply
The value of Vbat gives information about the state of charge of the battery.
New function TPS1100+: CSV_CheckPower"""


class CSV_GetVMem(TachyRequest):
    description = """Get value of the memory backup voltage supply
This routine returns the capacity of the current power source and its source
(internal or external)."""


class CSV_GetIntTemp(TachyRequest):
    description = """Get the temperature
Get the internal temperature of the instrument, measured on the Mainboard
side. Values are reported in degrees Celsius."""


class CSV_GetSWVersion(TachyRequest):
    description = """Retrieve Server Release Information
This function retrieves the current GeoCOM release (release, version and
subversion) of the server."""


class CSV_GetSWVersion2(TachyRequest):
    description = """Get Software Version
Returns the system software version."""


class CSV_GetDeviceConfig(TachyRequest):
    description = """Get instrument configuration
This function returns information about the class and the configuration type
of the instrument."""


class MOT_StartController(TachyRequest):
    description = """Start motor controller
This command is used to enable remote or user interaction to the motor
controller."""
    defaults = [gc.MOT_MODE.MOT_MANUPOS]
    helptexts = ["""Controller mode. If used together with
MOT_SetVelocity the control mode has
to be MOT_OCONST"""]


class MOT_StopController(TachyRequest):
    description = """Stop motor controller
This command is used to stop movement and to stop the motor controller
operation."""
    defaults=[gc.MOT_STOPMODE.MOT_NORMAL]
    helptexts=["Stop mode"]


class MOT_SetVelocity(TachyRequest):
    description = """Drive Instrument with visual control
This command is used to set up the velocity of motorization. This function
is valid only if MOT_StartController(MOT_OCONST) has been called
previously. RefOmega[0] denotes the horizontal and RefOmega[1]
denotes the vertical velocity setting.

RefOmega in
The speed in horizontal and vertical
direction in rad/s. The maximum speed
is +/- 0.79 rad/s each."""
    defaults = ["0.0", "0.0"]
    helptexts = ["Horizontal Speed", "Vertical Speed"]


class MOT_ReadLockStatus(TachyRequest):
    description = """Return condition of LockIn control
This function returns the current condition of the LockIn control (see
subsystem AUT for further information). This command is valid for TCA
instruments only."""


class WIR_GetRecFormat(TachyRequest):
    description = """Get Record Format
This function retrieves which recording format is in use.
0 defines recording format is GSI (standard)
1 defines recording format is the new GSI-16"""


class WIR_SetRecFormat(TachyRequest):
    description = """Set Record Format
This function sets which recording format should be used."""
    defaults=[gc.WIR_RECFORMAT.WIR_RECFORMAT_GSI16]
    helptexts=["GSI or GSI16"]


class AUT_SetTol(TachyRequest):
    description = """Set the positioning tolerances
This command stops every movement and sets new values for the
positioning tolerances of the Hz- and V- instrument axes. This command is
valid for TCM and TCA instruments only.
The tolerances must be in the range of 1[cc] ( =1.57079 E-06[rad] ) to
100[cc] ( =1.57079 E-04[rad] ).
Note: The max. Resolution of the angle measurement system depends on the
instrument accuracy class. If smaller positioning tolerances are required,
the positioning time can increase drastically."""
    defaults=["0.000028274333882", "0.000028274333882"] # default after ReadTol
    helptexts=["""The values for the positioning tolerances
in Hz and V direction [rad].""", """The values for the positioning tolerances
in Hz and V direction [rad]."""]


class AUT_ReadTol(TachyRequest):
    description = """Read current setting for the positioning tolerances
This command reads the current setting for the positioning tolerances of the
Hz- and V- instrument axis.
This command is valid for TCM and TCA instruments only."""


class AUT_SetTimeout(TachyRequest):
    description = """Set timeout for positioning
This command set the positioning timeout (set maximum time to perform a
positioning). The timeout is reset on 10[sec] after each power on"""
    defaults=["10", "10"]
    helptexts=["""The values for the positioning timeout in
Hz and V direction [s]. Valid values are
between 1 [sec] and 60 [sec].""",
"""The values for the positioning timeout in
Hz and V direction [s]. Valid values are
between 1 [sec] and 60 [sec]."""]


class AUT_ReadTimeout(TachyRequest):
    description = """Read current timeout setting for positioning
This command reads the current setting for the positioning time out
(maximum time to perform positioning)."""


class AUT_LockIn(TachyRequest):
    description = """Starts the target tracking
Function starts the target tracking. Is at this time another ATR-
configuration active, this configuration will be aborted before. The function
can be called several times. If the target is already locked, the command
will be ignored. The LOCK mode must be enabled for this functionality,
see AUS_SetUserLockState and AUS_GetUserLockState. The ATR
can only lock the target, if it is in the field of view (FoV)."""


class AUT_SetATRStatus(TachyRequest):
    description = """Set the status of the ATR mode
Activate respectively deactivate the ATR mode.
Activate ATR mode:
The ATR mode is activated and the LOCK mode keep unchanged.
Deactivate ATR mode:
The ATR mode is deactivated and the LOCK mode (if sets) will be reset
automatically also.
This command is valid for TCA instruments only.
New function TPS1100+: AUS_SetUserAtrState"""
    defaults = [gc.ON_OFF_TYPE.ON]
    helptexts = ['Status of the ATR mode']


class AUT_GetATRStatus(TachyRequest):
    description = """Get the status of the ATR mode
Get the current status of the ATR mode on TCA instruments. This
command does not indicate whether the ATR has currently acquired a
prism.
New function TPS1100+: AUS_GetUserAtrState"""


class AUT_SetLockStatus(TachyRequest):
    description = """Set of the ATR lock switch
Set the lock status.
Status ON:
The target tracking functionality is available but not activated. In order to
activate target tracking, see the function AUT_LockIn. The ATR mode will
be set automatically.
Status OFF:
A running target tracking will be aborted and the manual driving wheel is
activated. The ATR mode will be not reset automatically respectively keep
unchanged.
This command is valid for TCA instruments only.
New Function TPS1100+: AUT_SetUserLockState"""
    defaults = [gc.ON_OFF_TYPE.ON]
    helptexts = ["Status of the ATR lock switch"]


class AUT_GetLockStatus(TachyRequest):
    description = """Get the status of the lock switch
This command gets the current LOCK switch. This command is valid for
TCA instruments only and does not indicate whether the ATR has a prism
in lock or not.
With the function MOT_ReadLockStatus you can find out whether a target
is locked or not.
New function TPS1100+: AUS_GetUserLockState"""


class AUT_MakePositioning(TachyRequest):
    description = """Turns telescope to specified position
This procedure turns the telescope absolute to the in Hz and V specified
position, taking tolerance settings for positioning (see AUT_POSTOL) into
account. Any active control function is terminated by this function call.
If the position mode is set to normal (PosMode = AUT_NORMAL) it is
assumed that the current value of the compensator measurement is valid.
Positioning precise (PosMode = AUT_PRECISE) forces a new
compensator measurement at the specified position and includes this
information for positioning.
If ATR is possible and activated and the ATR mode is set to AUT_TARGET,
the instrument tries to position onto a target in the destination area. In
addition, the target is locked after positioning if the LockIn status is set. If
the Lock status not set, the manual driving wheel is activated after the
positioning."""
    defaults = ["0.0", "0.0", gc.AUT_POSMODE.AUT_NORMAL, gc.AUT_ATRMODE.AUT_POSITION, gc.BOOLEAN_TYPE.FALSE]
    helptexts = ["Horizontal (telescope) position [rad].",
                 "Vertical (instrument) position [rad].",
                 """Position mode:
AUT_NORMAL: (default) uses the current
value of the compensator (no
compensator measurement while
positioning). For values >25GON
positioning might tend to inaccuracy.
AUT_PRECISE: tries to measure exact
inclination of target. Tend to longer
position time (check AUT_TIMEOUT
and/or COM-time out if necessary).""",
                 """Mode of ATR:
AUT_POSITION: (default) conventional
position using values Hz and V.
AUT_TARGET: tries to position onto a
target in the destination area. This mode is
only possible if ATR exists and is
activated.""",
                 """It’s reserved for future use, set bDummy
always to FALSE"""]


class AUT_MakePositioning4(AUT_MakePositioning):
    pass


class AUT_ChangeFace(TachyRequest):
    description = """Turns telescope to other face
This procedure turns the telescope to the other face.
Is in the moment of the function calling an other control function active it
will be terminated before.
The start angle is automatically measured before the position starts.
If the position mode is set to normal (PosMode = AUT_NORMAL) it is
allowed that the current value of the compensator measurement is inexact.
Positioning precise (PosMode = AUT_PRECISE) forces a new
compensator measurement. If this measurement is not possible, the position
does not take place.
If ATR is possible and activated and the ATR mode is set to
AUT_TARGET the instrument tries to position onto a target in the destination
area. In addition, the target is locked after positioning if the LockIn status
is set."""
    defaults = [gc.AUT_POSMODE.AUT_NORMAL,
                gc.AUT_ATRMODE.AUT_TARGET,
                gc.BOOLEAN_TYPE.FALSE]
    helptexts = ["""
Position mode:
AUT_NORMAL: uses the current value of the compensator.
For values >25GON positioning might tend to inexact.
AUT_PRECISE: tries to measure exact inclination of target.
Tends to long position time
(check AUT_TIMEOUT and/or COM-time out if necessary).""",
"""Mode of ATR:
AUT_POSITION: conventional position to other face.
AUT_TARGET: tries to position onto a target in the destination area.
This set is only possible if ATR exists and is activated.""",
"""It’s reserved for future use, set bDummy always to FALSE"""]


class AUT_ChangeFace4(AUT_ChangeFace):
    pass


class AUT_Search(TachyRequest):
    description = """Performs an automatically target search
This procedure performs an automatically target search within a given area.
The search area has an elliptical shape where the input parameters
determine the axis in horizontal and vertical direction. If the search was
successful, the telescope will position to the target in a exactness of the
field of vision (±1.25[GON]), otherwise the instrument turns back to the
initial start position. With the ESC key a running search process will be
aborted. The ATR mode must be enabled for this functionality, see
AUS_SetUserAtrState() and AUS_GetUserAtrState. For a exact
positioning use fine adjust (see AUT_FineAdjust) afterwards.
Note: If you expand the search range of the function AUT_FineAdjust, then you
have a target search and a fine positioning in one function."""
    defaults = ["0.1", "0.3", gc.BOOLEAN_TYPE.FALSE]
    helptexts = ["Horizontal search region [rad].",
                 "Vertical search region [rad].",
                 "It’s reserved for future use, set bDummy always to FALSE"]


class AUT_Search2(AUT_Search):
    pass


class AUT_GetFineAdjustMode(TachyRequest):
    description = """Get fine adjust positioning mode
This function returns the current activated fine adjust positioning mode.
This command is valid for all instruments, but has only effects for TCA
instruments."""


class AUT_SetFineAdjustMode(TachyRequest):
    description = """Set the fine adjustment mode
This function sets the positioning tolerances (default values for both
modes) relating the angle accuracy or the point accuracy for the fine adjust.
This command is valid for all instruments, but has only effects for TCA
instruments. If a target is very near or held by hand, it’s recommended to
set the adjust-mode to AUT_POINT_MODE."""
    defaults = [gc.AUT_ADJMODE.AUT_POINT_MODE]
    helptexts = ["""AUT_NORM_MODE: Fine positioning with
angle tolerance
AUT_POINT_MODE: Fine positioning with
point tolerance"""]


class AUT_FineAdjust(TachyRequest):
    description = """Automatic target positioning
This procedure performs a positioning of the Theodolite axis onto a
destination target. If the target is not within the sensor measure region a
target search will be executed. The target search range is limited by the
parameter dSrchV in V- direction and by parameter dSrchHz in Hz -
direction. If no target found the instrument turns back to the initial start
position. The ATR mode must be enabled for this functionality, see
AUS_SetUserAtrState and AUS_GetUserAtrState.
Any actual target lock is terminated by this procedure call. After position,
the target is not locked again.
The timeout of this operation is set to 5s, regardless of the general position
timeout settings. The positioning tolerance is depends on the previously set
up the fine adjust mode (see AUT_SetFineAdjustMoed and
AUT_GetFineAdjustMode).
Tolerance settings (with AUT_SetTol and AUT_ReadTol) have no
influence to this operation. The tolerance settings as well as the ATR
measure precision depends on the instrument’s class and the used EDM
measure mode (The EDM measure modes are handled by the subsystem
TMC)."""
    defaults = ["0.1", "0.3", gc.BOOLEAN_TYPE.FALSE]
    helptexts = ["Search range Hz-axis",
                 "Search range V-axis",
                 "It’s reserved for future use, set bDummy always to FALSE"]


class AUT_FineAdjust3(AUT_FineAdjust):
    pass


class AUT_GetUserSpiral(TachyRequest):
    description = """Get user searching spiral
This function returns the current dimension of the searching spiral. This
command is valid for all instruments, but has only effects for TCA
instruments."""


class AUT_SetUserSpiral(TachyRequest):
    description = """Set user searching spiral
This function sets the dimension of the searching spiral. This command is
valid for all instruments, but has only effects for TCA instruments."""
    defaults = ["0.4", "0.2"]
    helptexts = ["Width of spiral [rad]", "Maximal height of spiral [rad]"]


class AUT_GetSearchArea(TachyRequest):
    description = """Get user searching area
This function returns the current user searching area. This command is
valid for all instruments, but has only effects for TCA instruments."""


class AUT_SetSearchArea(TachyRequest):
    description = """Set user searching area
This function defines the user definable searching area. This command is
valid for all instruments, but has only effects for TCA instruments."""
    defaults = ["0.5", "1.5708", "0.4", "0.2", gc.BOOLEAN_TYPE.TRUE]
    helptexts = ["Hz angle of spiral - center",
                 "V angle of spiral - center",
                 "Width of spiral [rad]",
                 "Maximal height of spiral [rad]",
                 "TRUE: user defined spiral is active"]


class AUT_PS_SetRange(TachyRequest):
    description = """Setting the PowerSearch range
This command defines the PowerSearch distance range limits.
These additional limits (additional to the PowerSearch window) will be used once the range checking is enabled
(AUT_PS_EnableRange).
TPS1200+"""
    defaults=["0.1", "0.3"]
    helptexts=["Minimal distance to prism (≥ 0m)",
               """Maximal distance to prism, where
lMaxDist ≤ 400m
lMaxdist ≥ lMinDist + 10"""]


class AUT_PS_EnableRange(TachyRequest):
    description = """Enabling the PowerSearch window and PowerSearch range
This command enables / disables the predefined PowerSearch window including the predefined PowerSearch
range limits, set by AUT_PS_SetRange"""
    defaults=[gc.BOOLEAN_TYPE.TRUE]
    helptexts=["""TRUE: Enables the user distance limits for PowerSearch
FALSE: Default range 0..400m"""]


class AUT_PS_SearchNext(TachyRequest):
    description = """Searching for the next target
This command executes the 360º default PowerSearch and searches for the next target. A previously defined
PowerSearch window (AUT_SetSearchArea) is not taken into account. Use AUT_PS_SearchWindow to do so.
TPS1200+"""
    defaults = [gc.AUT_DIRECTION.AUT_ANTICLOCKWISE, gc.BOOLEAN_TYPE.TRUE]
    helptexts = ["Defines the searching direction (CLKW=1 or ACLKW=-1)", """TRUE: Searching starts -10 gon to the given direction
lDirection. This setting finds targets left of the telescope
direction faster"""]


class AUT_PS_SearchWindow(TachyRequest):
    description = """Starting PowerSearch
This command starts PowerSearch inside the given PowerSearch window, defined by AUT_SetSearchArea
and optional by AUT_PS_SetRange"""


class BMM_BeepOn(TachyRequest):
    description = """Start a beep-signal
This function switches on the beep-signal with the intensity nIntens and
the frequency nFreq. If a continuous signal is active, it will be stopped
first. Turn off the beeping device with BMM_BeepOff.
TPS1000
New function TPS1100+: IOS_BeepOn"""
    defaults = ["100", "3900"]
    helptexts = ["""Intensity of the beep-signal (volume)
expressed as a percentage.
Default value is 100 %""",
"""Frequency of the beep-signal.
Default value is 3900 Hz.
Range: 500 Hz ... 5000 Hz"""]


class BMM_BeepOff(TachyRequest):
    description = """Stop active beep-signal
TPS1000
New function TPS1100+: IOS_BeepOff"""


class BMM_BeepNormal(TachyRequest):
    description = """A single beep-signal
This function produces a single beep with the configured intensity and
frequency, which cannot be changed. If a continuous signal is active, it will
be stopped first."""


class BMM_BeepAlarm(TachyRequest):
    description = """Output of an alarm-signal
This function produces a triple beep with the configured intensity and
frequency, which cannot be changed. If there is a continuous signal active,
it will be stopped before."""


class CTL_GetUpCounter(TachyRequest):
    description = """Get Up Counter
This function retrieves how often, since the last call of this function, the
TPS1100 instrument has been switched on and how often it has been
awakened from sleep mode. Both counters are unique and will be reset to
Zero once the function has been called."""


class SUP_GetConfig(TachyRequest):
    description = """Get power management configuration status
The returned settings are power off configuration and timing."""


class SUP_SetConfig(TachyRequest):
    description = """Set power management configuration
Set the configuration for the low temperature control (ON|OFF), the auto
power off automatic (AUTO_POWER_DISABLED|..._SLEEP|..._OFF)
and the corresponding timeout for the auto power off automatic."""
    defaults = [gc.ON_OFF_TYPE.ON, gc.SUP_AUTO_POWER.AUTO_POWER_SLEEP, "900000"]
    helptexts = ["""Switch for the low temperature control.
Per default the device automatically turns
off when internal temperature fall short of
-24 °C (LowTempOnOff = On).""",
"""Defines the behaviour of the power off automatic
(default: AutoPower = AUTO_POWER_SLEEP).""",
"""The timeout in ms. After this time the
device switches in the mode defined by the
value of AutoPower when no user activity
(press a key, turn the device or
communication via GeoCOM) occurs.
The default value for Timeout is 900000ms = 15 Min."""]


class SUP_SwitchLowTempControl(TachyRequest):
    description = """Set low temperature control
Activate (ON) respectively deactivate (OFF) the low temperature control."""
    defaults = [gc.ON_OFF_TYPE.ON]
    helptexts = ["""Switch for the low temperature control.
Per defaults the device automatically turns
off when internal temperature fall short of
-24 °C."""]


class BAP_GetLastDisplayedError(TachyRequest):
    description = """Get last TPS system error number
This function returns the last displayed error and clears it in the TPS
system. So a second GetLastDisplayedError call will result in
RC_IVRESULT."""


class BAP_SetPrismType(TachyRequest):
    description = """Sets the prism type
Sets the prism type for measurements with a reflector. It overwrites the
prism constant, set by TMC_SetPrismCorr."""
    defaults=[gc.BAP_PRISMTYPE.BAP_PRISM_360]
    helptexts=["Prism type"]


class BAP_GetPrismType(TachyRequest):
    description = """Get actual prism type
Gets the current prism type."""


class BAP_MeasDistanceAngle(TachyRequest):
    description = """Measure distance and angles
This function measures distances and angles depending on the mode
DistMode and updates the internal data pool after correct measurements. It
controls the special beep (sector or lost lock), maintains measurement icons
and disables the "FNC"-key during tracking."""
    defaults = [gc.BAP_MEASURE_PRG.BAP_DEF_DIST]
    helptexts = ["BAP_DEF_DIST, pre-defined using BAP_SetMeasPrg"]


class BAP_GetMeasPrg(TachyRequest):
    description = """Get actual distance measurement program"""


class BAP_SetMeasPrg(TachyRequest):
    description = """Set the distance measurement program
Defines the distance measurement program i.e. for
BAP_MeasDistanceAngle
Reflector-free measurement programs are not available on all instrument
types.
Changing the measurement programs may change the target type too (with
reflector / reflector-free)"""
    defaults = [gc.BAP_USER_MEASPRG.BAP_SINGLE_REF_STANDARD]
    helptexts = ["Measurement program"]


class BAP_SearchTarget(TachyRequest):
    description = """Search the target
Function searches a target. The used searching range is dependent of the set
searching area and whether the additional user area is enabled or not. The
functionality is only available by ATR instruments."""
    defaults = [gc.BOOLEAN_TYPE.FALSE]
    helptexts = ["""It’s reserved for future use, set bDummy
always to FALSE"""]


class BAP_SetTargetType(TachyRequest):
    description = """Sets the target type
Defines the target type, with reflector or reflector-free
If the actual distance measurement not valid for the set target type, then the
measurement program will be changed to the last used one for this type.
BAP_SetMeasPrg can also change the target type.
Reflector-free measurement programs are not available on all instrument
types."""
    defaults = [gc.BAP_TARGET_TYPE.BAP_REFL_USE]
    helptexts = ["""Target type"""]


class BAP_GetTargetType(TachyRequest):
    description = """Get actual target type
Gets the current target type for distance measurements (with reflector or
without reflector)."""


class BAP_GetPrismDef(TachyRequest):
    description = """Get a prism definition
Get the definition of a prism."""
    defaults = [gc.BAP_PRISMTYPE.BAP_PRISM_360]
    helptexts = ["Actual prism type"]


class BAP_SetPrismDef(TachyRequest):
    description = """Sets a user prism definition
Defines an user prism."""
    defaults = [gc.BAP_PRISMTYPE.BAP_PRISM_USER1, "name", "0.0", gc.BAP_REFLTYPE.BAP_REFL_PRISM]
    helptexts = ["""Prism type. Valid:
BAP_PRISM_USER1.. BAP_PRISM_USER3""",
                "Prism name string",
                "Prism correction",
                "Reflector type"]


class AUS_GetUserAtrState(TachyRequest):
    description = """Get the status of the ATR mode
Get the current status of the ATR mode on TCA instruments. This
command does not indicate whether the ATR has currently acquired a
prism. It replaces the function AUT_GetAtrStatus."""


class AUS_SetUserAtrState(TachyRequest):
    description = """Set the status of the ATR mode
Activate respectively deactivate the ATR mode.
Activate ATR mode:
The ATR mode is activated and the LOCK mode (if sets) will be reset
automatically also."""
    defaults = [gc.ON_OFF_TYPE.OFF]
    helptexts = ["State of the ATR mode"]


class AUS_GetUserLockState(TachyRequest):
    description = """Get the status of the lock switch
This command gets the current LOCK switch. This command is valid for
TCA instruments only and does not indicate whether the ATR has a prism
in lock or not.
With the function MOT_ReadLockStatus you can find out whether a
target is locked or not.
This command is valid for TCA instruments only. It replaces the function
AUT_GetLockStatu"""


class AUS_SetUserLockState(TachyRequest):
    description = """Set the lock status.
Status ON:
The target tracking functionality is available but not activated. In order to
activate target tracking, see the function AUT_LockIn. The ATR mode will
be set automatically.
Status OFF:
A running target tracking will be aborted and the manual driving wheel is
activated. The ATR mode will be not reset automatically respectively keep
unchanged.
This command is valid for TCA instruments only. It replaces the function
AUT_SetLockStatus."""
    defaults = [gc.ON_OFF_TYPE.OFF]
    helptexts = ["State of the ATR lock switch"]


class AUS_SwitchRcsSearch(TachyRequest):
    description = """Set the RCS searching mode switch.
If the RCS style searching is enabled, then the extended for
BAP_SearchTarget or after a loss of lock is activated.
This command is valid for TCA instruments only."""
    defaults = [gc.ON_OFF_TYPE.OFF]
    helptexts = ["Get RCS-Searching mode switch"]


class AUS_GetRcsSearchSwitch(TachyRequest):
    description = """Get RCS-Searching mode switch
This command gets the current RCS-Searching mode switch.
If RCS style searching is enabled, then the extended searching for
BAP_SearchTarget or after a loss of lock is activated.
This command is valid for TCA instruments only."""


class IOS_BeepOn(TachyRequest):
    description = """Start a beep-signal
This function switches on the beep-signal with the intensity nIntens. If a
continuous signal is active, it will be stopped first. Turn off the beeping
device with IOS_BeepOff"""
    defaults = ["100"]
    helptexts = ["""Intensity of the beep-signal (volume)
expressed as a percentage.
Default value is 100 %"""]


class IOS_BeepOff(TachyRequest):
    description = """Stop active beep-signal
This function switches off the beep-signal."""


ALL_COMMANDS = [
    AUS_GetRcsSearchSwitch,
    AUS_GetUserAtrState,
    AUS_GetUserLockState,
    AUS_SetUserAtrState,
    AUS_SetUserLockState,
    AUS_SwitchRcsSearch,
    AUT_ChangeFace,
    AUT_ChangeFace4,
    AUT_FineAdjust,
    AUT_FineAdjust3,
    AUT_GetATRStatus,
    AUT_GetFineAdjustMode,
    AUT_GetLockStatus,
    AUT_GetSearchArea,
    AUT_GetUserSpiral,
    AUT_LockIn,
    AUT_MakePositioning,
    AUT_MakePositioning4,
    AUT_PS_EnableRange,
    AUT_PS_SearchNext,
    AUT_PS_SearchWindow,
    AUT_PS_SetRange,
    AUT_ReadTimeout,
    AUT_ReadTol,
    AUT_Search,
    AUT_Search2,
    AUT_SetATRStatus,
    AUT_SetFineAdjustMode,
    AUT_SetLockStatus,
    AUT_SetSearchArea,
    AUT_SetTimeout,
    AUT_SetTol,
    AUT_SetUserSpiral,
    BAP_GetLastDisplayedError,
    BAP_GetMeasPrg,
    BAP_GetPrismDef,
    BAP_GetPrismType,
    BAP_GetTargetType,
    BAP_MeasDistanceAngle,
    BAP_SearchTarget,
    BAP_SetMeasPrg,
    BAP_SetPrismDef,
    BAP_SetPrismType,
    BAP_SetTargetType,
    BMM_BeepAlarm,
    BMM_BeepNormal,
    BMM_BeepOff,
    BMM_BeepOn,
    COM_EnableSignOff,
    COM_GetBinaryAvailable,
    COM_GetDoublePrecision,
    COM_GetSWVersion,
    COM_Local,
    COM_NullProc,
    COM_SetBinaryAvailable,
    COM_SetDoublePrecision,
    COM_SetSendDelay,
    COM_SwitchOffTPS,
    COM_SwitchOnTPS,
    CSV_GetDateTime,
    CSV_GetDeviceConfig,
    CSV_GetInstrumentName,
    CSV_GetInstrumentNo,
    CSV_GetIntTemp,
    CSV_GetSWVersion,
    CSV_GetSWVersion2,
    CSV_GetUserInstrumentName,
    CSV_GetVBat,
    CSV_GetVMem,
    CSV_SetDateTime,
    CSV_SetUserInstrumentName,
    CTL_GetUpCounter,
    EDM_GetBumerang,
    EDM_GetEglIntensity,
    EDM_GetTrkLightBrightness,
    EDM_GetTrkLightSwitch,
    EDM_Laserpointer,
    EDM_On,
    EDM_SetBumerang,
    EDM_SetEglIntensity,
    EDM_SetTrkLightBrightness,
    EDM_SetTrkLightSwitch,
    IOS_BeepOff,
    IOS_BeepOn,
    MOT_ReadLockStatus,
    MOT_SetVelocity,
    MOT_StartController,
    MOT_StopController,
    SUP_GetConfig,
    SUP_SetConfig,
    SUP_SwitchLowTempControl,
    TMC_DoMeasure,
    TMC_GetAngle1,
    TMC_GetAngle5,
    TMC_GetAngSwitch,
    TMC_GetAtmCorr,
    TMC_GetCoordinate,
    TMC_GetCoordinate1,
    TMC_GetEdmMode,
    TMC_GetFace,
    TMC_GetHeight,
    TMC_GetInclineSwitch,
    TMC_GetPrismCorr,
    TMC_GetRefractiveCorr,
    TMC_GetRefractiveMethod,
    TMC_GetSignal,
    TMC_GetSimpleCoord,
    TMC_GetSimpleMea,
    TMC_GetSlopeDistCorr,
    TMC_GetStation,
    TMC_IfDataAzeCorrError,
    TMC_IfDataIncCorrError,
    TMC_QuickDist,
    TMC_SetAngSwitch,
    TMC_SetAtmCorr,
    TMC_SetEdmMode,
    TMC_SetHandDist,
    TMC_SetHeight,
    TMC_SetInclineSwitch,
    TMC_SetOrientation,
    TMC_SetPrismCorr,
    TMC_SetRefractiveCorr,
    TMC_SetRefractiveMethod,
    TMC_SetStation,
    WIR_GetRecFormat,
    WIR_SetRecFormat
    ]

if __name__=="__main__":
    set_station = TMC_SetStation()
    print(f"Code for set station: {set_station.gc_command}")

