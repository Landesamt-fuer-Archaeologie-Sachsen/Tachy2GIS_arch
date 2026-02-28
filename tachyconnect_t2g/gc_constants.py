from enum import Enum


GRC_OK = 0                               # Function successfully completed.
GRC_UNDEFINED = 1                        # Unknown error, result unspecified.
GRC_IVPARAM = 2                          # Invalid parameter detected. Result unspecified.
GRC_IVRESULT = 3                         # Invalid result.
GRC_FATAL = 4                            # Fatal error.
GRC_NOT_IMPL = 5                         # Not implemented yet.
GRC_TIME_OUT = 6                         # Function execution timed out. Result unspecified.
GRC_SET_INCOMPL = 7                      # Parameter setup for subsystem is incomplete.
GRC_ABORT = 8                            # Function execution has been aborted.
GRC_NOMEMORY = 9                         # Fatal error - not enough memory.
GRC_NOTINIT = 10                         # Fatal error - subsystem not initialized.
GRC_SHUT_DOWN = 12                       # Subsystem is down.
GRC_SYSBUSY = 13                         # System busy/already in use of another process. Cannot execute function.
GRC_HWFAILURE = 14                       # Fatal error - hardware failure.
GRC_ABORT_APPL = 15                      # Execution of application has been aborted (SHIFT-ESC).
GRC_LOW_POWER = 16                       # Operation aborted - insufficient power supply level.
GRC_IVVERSION = 17                       # Invalid version of file, ...
GRC_BATT_EMPTY = 18                      # Battery empty
GRC_NO_EVENT = 20                        # no event pending.
GRC_OUT_OF_TEMP = 21                     # out of temperature range
GRC_INSTRUMENT_TILT = 22                 # instrument tilting out of range
GRC_COM_SETTING = 23                     # communication error
GRC_NO_ACTION = 24                       # GRC_TYPE Input 'do no action'
GRC_SLEEP_MODE = 25                      # Instr. run into the sleep mode
GRC_NOTOK = 26                           # Function not successfully completed.
GRC_NA = 27                              # Not available
GRC_OVERFLOW = 28                        # Overflow error
GRC_STOPPED = 29                         # System or subsystem has been stopped
GRC_ANG_ERROR = 257                      # Angles and Inclinations not valid
GRC_ANG_INCL_ERROR = 258                 # inclinations not valid
GRC_ANG_BAD_ACC = 259                    # value accuracies not reached
GRC_ANG_BAD_ANGLE_ACC = 260              # angle-accuracies not reached
GRC_ANG_BAD_INCLIN_ACC = 261             # inclination accuracies not reached
GRC_ANG_WRITE_PROTECTED = 266            # no write access allowed
GRC_ANG_OUT_OF_RANGE = 267               # value out of range
GRC_ANG_IR_OCCURED = 268                 # function aborted due to interrupt
GRC_ANG_HZ_MOVED = 269                   # hz moved during incline measurement
GRC_ANG_OS_ERROR = 270                   # troubles with operation system
GRC_ANG_DATA_ERROR = 271                 # overflow at parameter values
GRC_ANG_PEAK_CNT_UFL = 272               # too less peaks
GRC_ANG_TIME_OUT = 273                   # reading timeout
GRC_ANG_TOO_MANY_EXPOS = 274             # too many exposures wanted
GRC_ANG_PIX_CTRL_ERR = 275               # picture height out of range
GRC_ANG_MAX_POS_SKIP = 276               # positive exposure dynamic overflow
GRC_ANG_MAX_NEG_SKIP = 277               # negative exposure dynamic overflow
GRC_ANG_EXP_LIMIT = 278                  # exposure time overflow
GRC_ANG_UNDER_EXPOSURE = 279             # picture underexposured
GRC_ANG_OVER_EXPOSURE = 280              # picture overexposured
GRC_ANG_TMANY_PEAKS = 300                # too many peaks detected
GRC_ANG_TLESS_PEAKS = 301                # too less peaks detected
GRC_ANG_PEAK_TOO_SLIM = 302              # peak too slim
GRC_ANG_PEAK_TOO_WIDE = 303              # peak to wide
GRC_ANG_BAD_PEAKDIFF = 304               # bad peak difference
GRC_ANG_UNDER_EXP_PICT = 305             # too less peak amplitude
GRC_ANG_PEAKS_INHOMOGEN = 306            # inhomogeneous peak amplitudes
GRC_ANG_NO_DECOD_POSS = 307              # no peak decoding possible
GRC_ANG_UNSTABLE_DECOD = 308             # peak decoding not stable
GRC_ANG_TLESS_FPEAKS = 309               # too less valid finepeaks
GRC_ATA_NOT_READY = 512                  # ATR-System is not ready.
GRC_ATA_NO_RESULT = 513                  # Result isn't available yet.
GRC_ATA_SEVERAL_TARGETS = 514            # Several Targets detected.
GRC_ATA_BIG_SPOT = 515                   # Spot is too big for analyse.
GRC_ATA_BACKGROUND = 516                 # Background is too bright.
GRC_ATA_NO_TARGETS = 517                 # No targets detected.
GRC_ATA_NOT_ACCURAT = 518                # Accuracy worse than asked for.
GRC_ATA_SPOT_ON_EDGE = 519               # Spot is on the edge of the sensing area.
GRC_ATA_BLOOMING = 522                   # Blooming or spot on edge detected.
GRC_ATA_NOT_BUSY = 523                   # ATR isn't in a continuous mode.
GRC_ATA_STRANGE_LIGHT = 524              # Not the spot of the own target illuminator.
GRC_ATA_V24_FAIL = 525                   # Communication error to sensor (ATR).
GRC_ATA_DECODE_ERROR = 526               # Received Arguments cannot be decoded
GRC_ATA_HZ_FAIL = 527                    # No Spot detected in Hz-direction.
GRC_ATA_V_FAIL = 528                     # No Spot detected in V-direction.
GRC_ATA_HZ_STRANGE_L = 529               # Strange light in Hz-direction.
GRC_ATA_V_STRANGE_L = 530                # Strange light in V-direction.
GRC_ATA_SLDR_TRANSFER_PENDING = 531      # On multiple ATA_SLDR_OpenTransfer.
GRC_ATA_SLDR_TRANSFER_ILLEGAL = 532      # No ATA_SLDR_OpenTransfer happened.
GRC_ATA_SLDR_DATA_ERROR = 533            # Unexpected data format received.
GRC_ATA_SLDR_CHK_SUM_ERROR = 534         # Checksum error in transmitted data.
GRC_ATA_SLDR_ADDRESS_ERROR = 535         # Address out of valid range.
GRC_ATA_SLDR_INV_LOADFILE = 536          # Firmware file has invalid format.
GRC_ATA_SLDR_UNSUPPORTED = 537           # Current (loaded) firmware doesn't support upload.
GRC_ATA_PS_NOT_READY = 538               # PS-System is not ready.
GRC_ATA_ATR_SYSTEM_ERR = 539             # ATR system error
GRC_EDM_SYSTEM_ERR = 769                 # Fatal EDM sensor error. See for the exact reason the original EDM sensor error number. In the most cases a service problem.
GRC_EDM_INVALID_COMMAND = 770            # Invalid command or unknown command, see command syntax.
GRC_EDM_BOOM_ERR = 771                   # Boomerang error.
GRC_EDM_SIGN_LOW_ERR = 772               # Received signal to low, prism to far away, or natural barrier, bad environment, etc.
GRC_EDM_DIL_ERR = 773                    # obsolete
GRC_EDM_SIGN_HIGH_ERR = 774              # Received signal to strong, prism to near, stranger light effect.
GRC_EDM_TIMEOUT = 775                    # Timeout, measuring time exceeded (signal too weak, beam interrupted,..)
GRC_EDM_FLUKT_ERR = 776                  # to much turbulences or distractions
GRC_EDM_FMOT_ERR = 777                   # filter motor defective
GRC_EDM_DEV_NOT_INSTALLED = 778          # Device like EGL, DL is not installed.
GRC_EDM_NOT_FOUND = 779                  # Search result invalid. For the exact explanation, see in the description of the called function.
GRC_EDM_ERROR_RECEIVED = 780             # Communication ok, but an error reported from the EDM sensor.
GRC_EDM_MISSING_SRVPWD = 781             # No service password is set.
GRC_EDM_INVALID_ANSWER = 782             # Communication ok, but an unexpected answer received.
GRC_EDM_SEND_ERR = 783                   # Data send error, sending buffer is full.
GRC_EDM_RECEIVE_ERR = 784                # Data receive error, like parity buffer overflow.
GRC_EDM_INTERNAL_ERR = 785               # Internal EDM subsystem error.
GRC_EDM_BUSY = 786                       # Sensor is working already, abort current measuring first.
GRC_EDM_NO_MEASACTIVITY = 787            # No measurement activity started.
GRC_EDM_CHKSUM_ERR = 788                 # Calculated checksum, resp. received data wrong (only in binary communication mode possible).
GRC_EDM_INIT_OR_STOP_ERR = 789           # During start up or shut down phase an error occured. It is saved in the DEL buffer.
GRC_EDM_SRL_NOT_AVAILABLE = 790          # Red laser not available on this sensor HW.
GRC_EDM_MEAS_ABORTED = 791               # Measurement will be aborted (will be used for the laser security)
GRC_EDM_SLDR_TRANSFER_PENDING = 798      # Multiple OpenTransfer calls.
GRC_EDM_SLDR_TRANSFER_ILLEGAL = 799      # No open transfer happened.
GRC_EDM_SLDR_DATA_ERROR = 800            # Unexpected data format received.
GRC_EDM_SLDR_CHK_SUM_ERROR = 801         # Checksum error in transmitted data.
GRC_EDM_SLDR_ADDR_ERROR = 802            # Address out of valid range.
GRC_EDM_SLDR_INV_LOADFILE = 803          # Firmware file has invalid format.
GRC_EDM_SLDR_UNSUPPORTED = 804           # Current (loaded) firmware doesn't support upload.
GRC_EDM_UNKNOW_ERR = 808                 # Undocumented error from the EDM sensor, should not occur.
GRC_EDM_DISTRANGE_ERR = 818              # Out of distance range (dist too small or large)
GRC_EDM_SIGNTONOISE_ERR = 819            # Signal to noise ratio too small
GRC_EDM_NOISEHIGH_ERR = 820              # Noise to high
GRC_EDM_PWD_NOTSET = 821                 # Password is not set
GRC_EDM_ACTION_NO_MORE_VALID = 822       # Elapsed time between prepare und start fast measurement for ATR to long
GRC_EDM_MULTRG_ERR = 823                 # Possibly more than one target (also a sensor error)
GRC_TMC_NO_FULL_CORRECTION = 1283        # Warning: measurement without full correction
GRC_TMC_ACCURACY_GUARANTEE = 1284        # Info: accuracy can not be guarantee
GRC_TMC_ANGLE_OK = 1285                  # Warning: only angle measurement valid
GRC_TMC_ANGLE_NOT_FULL_CORR = 1288       # Warning: only angle measurement valid but without full correction
GRC_TMC_ANGLE_NO_ACC_GUARANTY = 1289     # Info: only angle measurement valid but accuracy can not be guarantee
GRC_TMC_ANGLE_ERROR = 1290               # Error: no angle measurement
GRC_TMC_DIST_PPM = 1291                  # Error: wrong setting of PPM or MM on EDM
GRC_TMC_DIST_ERROR = 1292                # Error: distance measurement not done (no aim, etc.)
GRC_TMC_BUSY = 1293                      # Error: system is busy (no measurement done)
GRC_TMC_SIGNAL_ERROR = 1294              # Error: no signal on EDM (only in signal mode)
MOT_RC_UNREADY = 1792                    # Motorization not ready
MOT_RC_BUSY = 1793                       # Motorization is handling another task
MOT_RC_NOT_OCONST = 1794                 # Not in velocity mode
MOT_RC_NOT_CONFIG = 1795                 # Motorization is in the wrong mode or busy
MOT_RC_NOT_POSIT = 1796                  # Not in posit mode
MOT_RC_NOT_SERVICE = 1797                # Not in service mode
MOT_RC_NOT_BUSY = 1798                   # Motorization is handling no task
MOT_RC_NOT_LOCK = 1799                   # Not in tracking mode
GRC_BMM_XFER_PENDING = 2305              # Loading process already opened
GRC_BMM_NO_XFER_OPEN = 2306              # Transfer not opened
GRC_BMM_UNKNOWN_CHARSET = 2307           # Unknown character set
GRC_BMM_NOT_INSTALLED = 2308             # Display module not present
GRC_BMM_ALREADY_EXIST = 2309             # Character set already exists
GRC_BMM_CANT_DELETE = 2310               # Character set cannot be deleted
GRC_BMM_MEM_ERROR = 2311                 # Memory cannot be allocated
GRC_BMM_CHARSET_USED = 2312              # Character set still used
GRC_BMM_CHARSET_SAVED = 2313             # Charset cannot be deleted or is protected
GRC_BMM_INVALID_ADR = 2314               # Attempt to copy a character block outside the allocated memory
GRC_BMM_CANCELANDADR_ERROR = 2315        # Error during release of allocated memory
GRC_BMM_INVALID_SIZE = 2316              # Number of bytes specified in header does not match the bytes read
GRC_BMM_CANCELANDINVSIZE_ERROR = 2317    # Allocated memory could not be released
GRC_BMM_ALL_GROUP_OCC = 2318             # Max. number of character sets already loaded
GRC_BMM_CANT_DEL_LAYERS = 2319           # Layer cannot be deleted
GRC_BMM_UNKNOWN_LAYER = 2320             # Required layer does not exist
GRC_BMM_INVALID_LAYERLEN = 2321          # Layer length exceeds maximum
GRC_COM_ERO = 3072                       # Initiate Extended Runtime Operation (ERO).
GRC_COM_CANT_ENCODE = 3073               # Cannot encode arguments in client.
GRC_COM_CANT_DECODE = 3074               # Cannot decode results in client.
GRC_COM_CANT_SEND = 3075                 # Hardware error while sending.
GRC_COM_CANT_RECV = 3076                 # Hardware error while receiving.
GRC_COM_TIMEDOUT = 3077                  # Request timed out.
GRC_COM_WRONG_FORMAT = 3078              # Packet format error.
GRC_COM_VER_MISMATCH = 3079              # Version mismatch between client and server.
GRC_COM_CANT_DECODE_REQ = 3080           # Cannot decode arguments in server.
GRC_COM_PROC_UNAVAIL = 3081              # Unknown RPC, procedure ID invalid.
GRC_COM_CANT_ENCODE_REP = 3082           # Cannot encode results in server.
GRC_COM_SYSTEM_ERR = 3083                # Unspecified generic system error.
GRC_COM_FAILED = 3085                    # Unspecified error.
GRC_COM_NO_BINARY = 3086                 # Binary protocol not available.
GRC_COM_INTR = 3087                      # Call interrupted.
GRC_COM_REQUIRES_8DBITS = 3090           # Protocol needs 8bit encoded characters.
GRC_COM_TR_ID_MISMATCH = 3093            # TRANSACTIONS ID mismatch error.
GRC_COM_NOT_GEOCOM = 3094                # Protocol not recognizable.
GRC_COM_UNKNOWN_PORT = 3095              # (WIN) Invalid port address.
GRC_COM_ERO_END = 3099                   # ERO is terminating.
GRC_COM_OVERRUN = 3100                   # Internal error: data buffer overflow.
GRC_COM_SRVR_RX_CHECKSUM_ERRR = 3101     # Invalid checksum on server side received.
GRC_COM_CLNT_RX_CHECKSUM_ERRR = 3102     # Invalid checksum on client side received.
GRC_COM_PORT_NOT_AVAILABLE = 3103        # (WIN) Port not available.
GRC_COM_PORT_NOT_OPEN = 3104             # (WIN) Port not opened.
GRC_COM_NO_PARTNER = 3105                # (WIN) Unable to find TPS.
GRC_COM_ERO_NOT_STARTED = 3106           # Extended Runtime Operation could not be started.
GRC_COM_CONS_REQ = 3107                  # Att to send cons reqs
GRC_COM_SRVR_IS_SLEEPING = 3108          # TPS has gone to sleep. Wait and try again.
GRC_COM_SRVR_IS_OFF = 3109               # TPS has shut down. Wait and try again.
WIR_PTNR_OVERFLOW = 5121                 # point number overflow
WIR_NUM_ASCII_CARRY = 5122               # carry from number to ASCII conversion
WIR_PTNR_NO_INC = 5123                   # can't increment point number
WIR_STEP_SIZE = 5124                     # wrong step size
WIR_BUSY = 5125                          # resource occupied
WIR_CONFIG_FNC = 5127                    # user function selected
WIR_CANT_OPEN_FILE = 5128                # can't open file
WIR_FILE_WRITE_ERROR = 5129              # can't write into file
WIR_MEDIUM_NOMEM = 5130                  # no anymore memory on PC-Card
WIR_NO_MEDIUM = 5131                     # no PC-Card
WIR_EMPTY_FILE = 5132                    # empty GSI file
WIR_INVALID_DATA = 5133                  # invalid data in GSI file
WIR_F2_BUTTON = 5134                     # F2 button pressed
WIR_F3_BUTTON = 5135                     # F3 button pressed
WIR_F4_BUTTON = 5136                     # F4 button pressed
WIR_SHF2_BUTTON = 5137                   # SHIFT F2 button pressed
GRC_AUT_TIMEOUT = 8704                   # Position not reached
GRC_AUT_DETENT_ERROR = 8705              # Positioning not possible due to mounted EDM
GRC_AUT_ANGLE_ERROR = 8706               # Angle measurement error
GRC_AUT_MOTOR_ERROR = 8707               # Motorisation error
GRC_AUT_INCACC = 8708                    # Position not exactly reached
GRC_AUT_DEV_ERROR = 8709                 # Deviation measurement error
GRC_AUT_NO_TARGET = 8710                 # No target detected
GRC_AUT_MULTIPLE_TARGETS = 8711          # Multiple target detected
GRC_AUT_BAD_ENVIRONMENT = 8712           # Bad environment conditions
GRC_AUT_DETECTOR_ERROR = 8713            # Error in target acquisition
GRC_AUT_NOT_ENABLED = 8714               # Target acquisition not enabled
GRC_AUT_CALACC = 8715                    # ATR-Calibration failed
GRC_AUT_ACCURACY = 8716                  # Target position not exactly reached
GRC_AUT_DIST_STARTED = 8717              # Info: dist. measurement has been started
GRC_AUT_SUPPLY_TOO_HIGH = 8718           # external Supply voltage is too high
GRC_AUT_SUPPLY_TOO_LOW = 8719            # int. or ext. Supply voltage is too low
GRC_AUT_NO_WORKING_AREA = 8720           # working area not set
GRC_AUT_ARRAY_FULL = 8721                # power search data array is filled
GRC_AUT_NO_DATA = 8722                   # no data available
BAP_CHANGE_ALL_TO_DIST = 9217            # Command changed from ALL to DIST
GRC_KDM_NOT_AVAILABLE = 12544            # KDM device is not available.
GRC_FTR_FILEACCESS = 13056               # File access error
GRC_FTR_WRONGFILEBLOCKNUMBER = 13057     # block number was not the expected one
GRC_FTR_NOTENOUGHSPACE = 13058           # not enough space on device to proceed uploading
GRC_FTR_INVALIDINPUT = 13059             # Rename of file failed.
GRC_FTR_MISSINGSETUP = 13060             # invalid parameter as input


MESSAGES = {0: "Function successfully completed.",
            1: "Unknown error, result unspecified.",
            2: "Invalid parameter detected. Result unspecified.",
            3: "Invalid result.",
            4: "Fatal error.",
            5: "Not implemented yet.",
            6: "Function execution timed out. Result unspecified.",
            7: "Parameter setup for subsystem is incomplete.",
            8: "Function execution has been aborted.",
            9: "Fatal error - not enough memory.",
            10: "Fatal error - subsystem not initialized.",
            12: "Subsystem is down.",
            13: "System busy/already in use of another process. Cannot execute function.",
            14: "Fatal error - hardware failure.",
            15: "Execution of application has been aborted (SHIFT-ESC).",
            16: "Operation aborted - insufficient power supply level.",
            17: "Invalid version of file, ...",
            18: "Battery empty",
            20: "no event pending.",
            21: "out of temperature range",
            22: "instrument tilting out of range",
            23: "communication error",
            24: "GRC_TYPE Input 'do no action'",
            25: "Instr. run into the sleep mode",
            26: "Function not successfully completed.",
            27: "Not available",
            28: "Overflow error",
            29: "System or subsystem has been stopped",
            257: "Angles and Inclinations not valid",
            258: "inclinations not valid",
            259: "value accuracies not reached",
            260: "angle-accuracies not reached",
            261: "inclination accuracies not reached",
            266: "no write access allowed",
            267: "value out of range",
            268: "function aborted due to interrupt",
            269: "hz moved during incline measurement",
            270: "troubles with operation system",
            271: "overflow at parameter values",
            272: "too less peaks",
            273: "reading timeout",
            274: "too many exposures wanted",
            275: "picture height out of range",
            276: "positive exposure dynamic overflow",
            277: "negative exposure dynamic overflow",
            278: "exposure time overflow",
            279: "picture underexposured",
            280: "picture overexposured",
            300: "too many peaks detected",
            301: "too less peaks detected",
            302: "peak too slim",
            303: "peak to wide",
            304: "bad peak difference",
            305: "too less peak amplitude",
            306: "inhomogeneous peak amplitudes",
            307: "no peak decoding possible",
            308: "peak decoding not stable",
            309: "too less valid finepeaks",
            512: "ATR-System is not ready.",
            513: "Result isn't available yet.",
            514: "Several Targets detected.",
            515: "Spot is too big for analyse.",
            516: "Background is too bright.",
            517: "No targets detected.",
            518: "Accuracy worse than asked for.",
            519: "Spot is on the edge of the sensing area.",
            522: "Blooming or spot on edge detected.",
            523: "ATR isn't in a continuous mode.",
            524: "Not the spot of the own target illuminator.",
            525: "Communication error to sensor (ATR).",
            526: "Received Arguments cannot be decoded",
            527: "No Spot detected in Hz-direction.",
            528: "No Spot detected in V-direction.",
            529: "Strange light in Hz-direction.",
            530: "Strange light in V-direction.",
            531: "On multiple ATA_SLDR_OpenTransfer.",
            532: "No ATA_SLDR_OpenTransfer happened.",
            533: "Unexpected data format received.",
            534: "Checksum error in transmitted data.",
            535: "Address out of valid range.",
            536: "Firmware file has invalid format.",
            537: "Current (loaded) firmware doesn't support upload.",
            538: "PS-System is not ready.",
            539: "ATR system error",
            769: "Fatal EDM sensor error. See for the exact reason the original EDM sensor error number. In the most cases a service problem.",
            770: "Invalid command or unknown command, see command syntax.",
            771: "Boomerang error.",
            772: "Received signal to low, prism to far away, or natural barrier, bad environment, etc.",
            773: "obsolete",
            774: "Received signal to strong, prism to near, stranger light effect.",
            775: "Timeout, measuring time exceeded (signal too weak, beam interrupted,..)",
            776: "to much turbulences or distractions",
            777: "filter motor defective",
            778: "Device like EGL, DL is not installed.",
            779: "Search result invalid. For the exact explanation, see in the description of the called function.",
            780: "Communication ok, but an error reported from the EDM sensor.",
            781: "No service password is set.",
            782: "Communication ok, but an unexpected answer received.",
            783: "Data send error, sending buffer is full.",
            784: "Data receive error, like parity buffer overflow.",
            785: "Internal EDM subsystem error.",
            786: "Sensor is working already, abort current measuring first.",
            787: "No measurement activity started.",
            788: "Calculated checksum, resp. received data wrong (only in binary communication mode possible).",
            789: "During start up or shut down phase an error occured. It is saved in the DEL buffer.",
            790: "Red laser not available on this sensor HW.",
            791: "Measurement will be aborted (will be used for the laser security)",
            798: "Multiple OpenTransfer calls.",
            799: "No open transfer happened.",
            800: "Unexpected data format received.",
            801: "Checksum error in transmitted data.",
            802: "Address out of valid range.",
            803: "Firmware file has invalid format.",
            804: "Current (loaded) firmware doesn't support upload.",
            808: "Undocumented error from the EDM sensor, should not occur.",
            818: "Out of distance range (dist too small or large)",
            819: "Signal to noise ratio too small",
            820: "Noise to high",
            821: "Password is not set",
            822: "Elapsed time between prepare und start fast measurement for ATR to long",
            823: "Possibly more than one target (also a sensor error)",
            1283: "Warning: measurement without full correction",
            1284: "Info: accuracy can not be guarantee",
            1285: "Warning: only angle measurement valid",
            1288: "Warning: only angle measurement valid but without full correction",
            1289: "Info: only angle measurement valid but accuracy can not be guarantee",
            1290: "Error: no angle measurement",
            1291: "Error: wrong setting of PPM or MM on EDM",
            1292: "Error: distance measurement not done (no aim, etc.)",
            1293: "Error: system is busy (no measurement done)",
            1294: "Error: no signal on EDM (only in signal mode)",
            1792: "Motorization not ready",
            1793: "Motorization is handling another task",
            1794: "Not in velocity mode",
            1795: "Motorization is in the wrong mode or busy",
            1796: "Not in posit mode",
            1797: "Not in service mode",
            1798: "Motorization is handling no task",
            1799: "Not in tracking mode",
            2305: "Loading process already opened",
            2306: "Transfer not opened",
            2307: "Unknown character set",
            2308: "Display module not present",
            2309: "Character set already exists",
            2310: "Character set cannot be deleted",
            2311: "Memory cannot be allocated",
            2312: "Character set still used",
            2313: "Charset cannot be deleted or is protected",
            2314: "Attempt to copy a character block outside the allocated memory",
            2315: "Error during release of allocated memory",
            2316: "Number of bytes specified in header does not match the bytes read",
            2317: "Allocated memory could not be released",
            2318: "Max. number of character sets already loaded",
            2319: "Layer cannot be deleted",
            2320: "Required layer does not exist",
            2321: "Layer length exceeds maximum",
            3072: "Initiate Extended Runtime Operation (ERO).",
            3073: "Cannot encode arguments in client.",
            3074: "Cannot decode results in client.",
            3075: "Hardware error while sending.",
            3076: "Hardware error while receiving.",
            3077: "Request timed out.",
            3078: "Packet format error.",
            3079: "Version mismatch between client and server.",
            3080: "Cannot decode arguments in server.",
            3081: "Unknown RPC, procedure ID invalid.",
            3082: "Cannot encode results in server.",
            3083: "Unspecified generic system error.",
            3085: "Unspecified error.",
            3086: "Binary protocol not available.",
            3087: "Call interrupted.",
            3090: "Protocol needs 8bit encoded characters.",
            3093: "TRANSACTIONS ID mismatch error.",
            3094: "Protocol not recognizable.",
            3095: "(WIN) Invalid port address.",
            3099: "ERO is terminating.",
            3100: "Internal error: data buffer overflow.",
            3101: "Invalid checksum on server side received.",
            3102: "Invalid checksum on client side received.",
            3103: "(WIN) Port not available.",
            3104: "(WIN) Port not opened.",
            3105: "(WIN) Unable to find TPS.",
            3106: "Extended Runtime Operation could not be started.",
            3107: "Att to send cons reqs",
            3108: "TPS has gone to sleep. Wait and try again.",
            3109: "TPS has shut down. Wait and try again.",
            5121: "point number overflow",
            5122: "carry from number to ASCII conversion",
            5123: "can't increment point number",
            5124: "wrong step size",
            5125: "resource occupied",
            5127: "user function selected",
            5128: "can't open file",
            5129: "can't write into file",
            5130: "no anymore memory on PC-Card",
            5131: "no PC-Card",
            5132: "empty GSI file",
            5133: "invalid data in GSI file",
            5134: "F2 button pressed",
            5135: "F3 button pressed",
            5136: "F4 button pressed",
            5137: "SHIFT F2 button pressed",
            8704: "Position not reached",
            8705: "Positioning not possible due to mounted EDM",
            8706: "Angle measurement error",
            8707: "Motorisation error",
            8708: "Position not exactly reached",
            8709: "Deviation measurement error",
            8710: "No target detected",
            8711: "Multiple target detected",
            8712: "Bad environment conditions",
            8713: "Error in target acquisition",
            8714: "Target acquisition not enabled",
            8715: "ATR-Calibration failed",
            8716: "Target position not exactly reached",
            8717: "Info: dist. measurement has been started",
            8718: "external Supply voltage is too high",
            8719: "int. or ext. Supply voltage is too low",
            8720: "working area not set",
            8721: "power search data array is filled",
            8722: "no data available",
            9217: "Command changed from ALL to DIST",
            12544: "KDM device is not available.",
            13056: "File access error",
            13057: "block number was not the expected one",
            13058: "not enough space on device to proceed uploading",
            13059: "Rename of file failed.",
            13060: "invalid parameter as input",
            }


CODES = {0: "GRC_OK",
         1: "GRC_UNDEFINED",
         2: "GRC_IVPARAM",
         3: "GRC_IVRESULT",
         4: "GRC_FATAL",
         5: "GRC_NOT_IMPL",
         6: "GRC_TIME_OUT",
         7: "GRC_SET_INCOMPL",
         8: "GRC_ABORT",
         9: "GRC_NOMEMORY",
         10: "GRC_NOTINIT",
         12: "GRC_SHUT_DOWN",
         13: "GRC_SYSBUSY",
         14: "GRC_HWFAILURE",
         15: "GRC_ABORT_APPL",
         16: "GRC_LOW_POWER",
         17: "GRC_IVVERSION",
         18: "GRC_BATT_EMPTY",
         20: "GRC_NO_EVENT",
         21: "GRC_OUT_OF_TEMP",
         22: "GRC_INSTRUMENT_TILT",
         23: "GRC_COM_SETTING",
         24: "GRC_NO_ACTION",
         25: "GRC_SLEEP_MODE",
         26: "GRC_NOTOK",
         27: "GRC_NA",
         28: "GRC_OVERFLOW",
         29: "GRC_STOPPED",
         257: "GRC_ANG_ERROR",
         258: "GRC_ANG_INCL_ERROR",
         259: "GRC_ANG_BAD_ACC",
         260: "GRC_ANG_BAD_ANGLE_ACC",
         261: "GRC_ANG_BAD_INCLIN_ACC",
         266: "GRC_ANG_WRITE_PROTECTED",
         267: "GRC_ANG_OUT_OF_RANGE",
         268: "GRC_ANG_IR_OCCURED",
         269: "GRC_ANG_HZ_MOVED",
         270: "GRC_ANG_OS_ERROR",
         271: "GRC_ANG_DATA_ERROR",
         272: "GRC_ANG_PEAK_CNT_UFL",
         273: "GRC_ANG_TIME_OUT",
         274: "GRC_ANG_TOO_MANY_EXPOS",
         275: "GRC_ANG_PIX_CTRL_ERR",
         276: "GRC_ANG_MAX_POS_SKIP",
         277: "GRC_ANG_MAX_NEG_SKIP",
         278: "GRC_ANG_EXP_LIMIT",
         279: "GRC_ANG_UNDER_EXPOSURE",
         280: "GRC_ANG_OVER_EXPOSURE",
         300: "GRC_ANG_TMANY_PEAKS",
         301: "GRC_ANG_TLESS_PEAKS",
         302: "GRC_ANG_PEAK_TOO_SLIM",
         303: "GRC_ANG_PEAK_TOO_WIDE",
         304: "GRC_ANG_BAD_PEAKDIFF",
         305: "GRC_ANG_UNDER_EXP_PICT",
         306: "GRC_ANG_PEAKS_INHOMOGEN",
         307: "GRC_ANG_NO_DECOD_POSS",
         308: "GRC_ANG_UNSTABLE_DECOD",
         309: "GRC_ANG_TLESS_FPEAKS",
         512: "GRC_ATA_NOT_READY",
         513: "GRC_ATA_NO_RESULT",
         514: "GRC_ATA_SEVERAL_TARGETS",
         515: "GRC_ATA_BIG_SPOT",
         516: "GRC_ATA_BACKGROUND",
         517: "GRC_ATA_NO_TARGETS",
         518: "GRC_ATA_NOT_ACCURAT",
         519: "GRC_ATA_SPOT_ON_EDGE",
         522: "GRC_ATA_BLOOMING",
         523: "GRC_ATA_NOT_BUSY",
         524: "GRC_ATA_STRANGE_LIGHT",
         525: "GRC_ATA_V24_FAIL",
         526: "GRC_ATA_DECODE_ERROR",
         527: "GRC_ATA_HZ_FAIL",
         528: "GRC_ATA_V_FAIL",
         529: "GRC_ATA_HZ_STRANGE_L",
         530: "GRC_ATA_V_STRANGE_L",
         531: "GRC_ATA_SLDR_TRANSFER_PENDING",
         532: "GRC_ATA_SLDR_TRANSFER_ILLEGAL",
         533: "GRC_ATA_SLDR_DATA_ERROR",
         534: "GRC_ATA_SLDR_CHK_SUM_ERROR",
         535: "GRC_ATA_SLDR_ADDRESS_ERROR",
         536: "GRC_ATA_SLDR_INV_LOADFILE",
         537: "GRC_ATA_SLDR_UNSUPPORTED",
         538: "GRC_ATA_PS_NOT_READY",
         539: "GRC_ATA_ATR_SYSTEM_ERR",
         769: "GRC_EDM_SYSTEM_ERR",
         770: "GRC_EDM_INVALID_COMMAND",
         771: "GRC_EDM_BOOM_ERR",
         772: "GRC_EDM_SIGN_LOW_ERR",
         773: "GRC_EDM_DIL_ERR",
         774: "GRC_EDM_SIGN_HIGH_ERR",
         775: "GRC_EDM_TIMEOUT",
         776: "GRC_EDM_FLUKT_ERR",
         777: "GRC_EDM_FMOT_ERR",
         778: "GRC_EDM_DEV_NOT_INSTALLED",
         779: "GRC_EDM_NOT_FOUND",
         780: "GRC_EDM_ERROR_RECEIVED",
         781: "GRC_EDM_MISSING_SRVPWD",
         782: "GRC_EDM_INVALID_ANSWER",
         783: "GRC_EDM_SEND_ERR",
         784: "GRC_EDM_RECEIVE_ERR",
         785: "GRC_EDM_INTERNAL_ERR",
         786: "GRC_EDM_BUSY",
         787: "GRC_EDM_NO_MEASACTIVITY",
         788: "GRC_EDM_CHKSUM_ERR",
         789: "GRC_EDM_INIT_OR_STOP_ERR",
         790: "GRC_EDM_SRL_NOT_AVAILABLE",
         791: "GRC_EDM_MEAS_ABORTED",
         798: "GRC_EDM_SLDR_TRANSFER_PENDING",
         799: "GRC_EDM_SLDR_TRANSFER_ILLEGAL",
         800: "GRC_EDM_SLDR_DATA_ERROR",
         801: "GRC_EDM_SLDR_CHK_SUM_ERROR",
         802: "GRC_EDM_SLDR_ADDR_ERROR",
         803: "GRC_EDM_SLDR_INV_LOADFILE",
         804: "GRC_EDM_SLDR_UNSUPPORTED",
         808: "GRC_EDM_UNKNOW_ERR",
         818: "GRC_EDM_DISTRANGE_ERR",
         819: "GRC_EDM_SIGNTONOISE_ERR",
         820: "GRC_EDM_NOISEHIGH_ERR",
         821: "GRC_EDM_PWD_NOTSET",
         822: "GRC_EDM_ACTION_NO_MORE_VALID",
         823: "GRC_EDM_MULTRG_ERR",
         1283: "GRC_TMC_NO_FULL_CORRECTION",
         1284: "GRC_TMC_ACCURACY_GUARANTEE",
         1285: "GRC_TMC_ANGLE_OK",
         1288: "GRC_TMC_ANGLE_NOT_FULL_CORR",
         1289: "GRC_TMC_ANGLE_NO_ACC_GUARANTY",
         1290: "GRC_TMC_ANGLE_ERROR",
         1291: "GRC_TMC_DIST_PPM",
         1292: "GRC_TMC_DIST_ERROR",
         1293: "GRC_TMC_BUSY",
         1294: "GRC_TMC_SIGNAL_ERROR",
         1792: "MOT_RC_UNREADY",
         1793: "MOT_RC_BUSY",
         1794: "MOT_RC_NOT_OCONST",
         1795: "MOT_RC_NOT_CONFIG",
         1796: "MOT_RC_NOT_POSIT",
         1797: "MOT_RC_NOT_SERVICE",
         1798: "MOT_RC_NOT_BUSY",
         1799: "MOT_RC_NOT_LOCK",
         2305: "GRC_BMM_XFER_PENDING",
         2306: "GRC_BMM_NO_XFER_OPEN",
         2307: "GRC_BMM_UNKNOWN_CHARSET",
         2308: "GRC_BMM_NOT_INSTALLED",
         2309: "GRC_BMM_ALREADY_EXIST",
         2310: "GRC_BMM_CANT_DELETE",
         2311: "GRC_BMM_MEM_ERROR",
         2312: "GRC_BMM_CHARSET_USED",
         2313: "GRC_BMM_CHARSET_SAVED",
         2314: "GRC_BMM_INVALID_ADR",
         2315: "GRC_BMM_CANCELANDADR_ERROR",
         2316: "GRC_BMM_INVALID_SIZE",
         2317: "GRC_BMM_CANCELANDINVSIZE_ERROR",
         2318: "GRC_BMM_ALL_GROUP_OCC",
         2319: "GRC_BMM_CANT_DEL_LAYERS",
         2320: "GRC_BMM_UNKNOWN_LAYER",
         2321: "GRC_BMM_INVALID_LAYERLEN",
         3072: "GRC_COM_ERO",
         3073: "GRC_COM_CANT_ENCODE",
         3074: "GRC_COM_CANT_DECODE",
         3075: "GRC_COM_CANT_SEND",
         3076: "GRC_COM_CANT_RECV",
         3077: "GRC_COM_TIMEDOUT",
         3078: "GRC_COM_WRONG_FORMAT",
         3079: "GRC_COM_VER_MISMATCH",
         3080: "GRC_COM_CANT_DECODE_REQ",
         3081: "GRC_COM_PROC_UNAVAIL",
         3082: "GRC_COM_CANT_ENCODE_REP",
         3083: "GRC_COM_SYSTEM_ERR",
         3085: "GRC_COM_FAILED",
         3086: "GRC_COM_NO_BINARY",
         3087: "GRC_COM_INTR",
         3090: "GRC_COM_REQUIRES_8DBITS",
         3093: "GRC_COM_TR_ID_MISMATCH",
         3094: "GRC_COM_NOT_GEOCOM",
         3095: "GRC_COM_UNKNOWN_PORT",
         3099: "GRC_COM_ERO_END",
         3100: "GRC_COM_OVERRUN",
         3101: "GRC_COM_SRVR_RX_CHECKSUM_ERRR",
         3102: "GRC_COM_CLNT_RX_CHECKSUM_ERRR",
         3103: "GRC_COM_PORT_NOT_AVAILABLE",
         3104: "GRC_COM_PORT_NOT_OPEN",
         3105: "GRC_COM_NO_PARTNER",
         3106: "GRC_COM_ERO_NOT_STARTED",
         3107: "GRC_COM_CONS_REQ",
         3108: "GRC_COM_SRVR_IS_SLEEPING",
         3109: "GRC_COM_SRVR_IS_OFF",
         5121: "WIR_PTNR_OVERFLOW",
         5122: "WIR_NUM_ASCII_CARRY",
         5123: "WIR_PTNR_NO_INC",
         5124: "WIR_STEP_SIZE",
         5125: "WIR_BUSY",
         5127: "WIR_CONFIG_FNC",
         5128: "WIR_CANT_OPEN_FILE",
         5129: "WIR_FILE_WRITE_ERROR",
         5130: "WIR_MEDIUM_NOMEM",
         5131: "WIR_NO_MEDIUM",
         5132: "WIR_EMPTY_FILE",
         5133: "WIR_INVALID_DATA",
         5134: "WIR_F2_BUTTON",
         5135: "WIR_F3_BUTTON",
         5136: "WIR_F4_BUTTON",
         5137: "WIR_SHF2_BUTTON",
         8704: "GRC_AUT_TIMEOUT",
         8705: "GRC_AUT_DETENT_ERROR",
         8706: "GRC_AUT_ANGLE_ERROR",
         8707: "GRC_AUT_MOTOR_ERROR",
         8708: "GRC_AUT_INCACC",
         8709: "GRC_AUT_DEV_ERROR",
         8710: "GRC_AUT_NO_TARGET",
         8711: "GRC_AUT_MULTIPLE_TARGETS",
         8712: "GRC_AUT_BAD_ENVIRONMENT",
         8713: "GRC_AUT_DETECTOR_ERROR",
         8714: "GRC_AUT_NOT_ENABLED",
         8715: "GRC_AUT_CALACC",
         8716: "GRC_AUT_ACCURACY",
         8717: "GRC_AUT_DIST_STARTED",
         8718: "GRC_AUT_SUPPLY_TOO_HIGH",
         8719: "GRC_AUT_SUPPLY_TOO_LOW",
         8720: "GRC_AUT_NO_WORKING_AREA",
         8721: "GRC_AUT_ARRAY_FULL",
         8722: "GRC_AUT_NO_DATA",
         9217: "BAP_CHANGE_ALL_TO_DIST",
         12544: "GRC_KDM_NOT_AVAILABLE",
         13056: "GRC_FTR_FILEACCESS",
         13057: "GRC_FTR_WRONGFILEBLOCKNUMBER",
         13058: "GRC_FTR_NOTENOUGHSPACE",
         13059: "GRC_FTR_INVALIDINPUT",
         13060: "GRC_FTR_MISSINGSETUP",
         }

AUS_GetRcsSearchSwitch = 18010
AUS_GetUserAtrState = 18006
AUS_GetUserLockState = 18008
AUS_SetUserAtrState = 18005
AUS_SetUserLockState = 18007
AUS_SwitchRcsSearch = 18009
AUT_ChangeFace = 9028
AUT_ChangeFace4 = 9028
AUT_FineAdjust = 9037
AUT_FineAdjust3 = 9037
AUT_GetATRStatus = 9019
AUT_GetFineAdjustMode = 9030
AUT_GetLockStatus = 9021
AUT_GetSearchArea = 9042
AUT_GetUserSpiral = 9040
AUT_LockIn = 9013
AUT_MakePositioning = 9027
AUT_MakePositioning4 = 9027
AUT_PS_EnableRange = 9048
AUT_PS_SearchNext = 9051
AUT_PS_SearchWindow = 9052
AUT_PS_SetRange = 9047
AUT_ReadTimeout = 9012
AUT_ReadTol = 9008
AUT_Search = 9029
AUT_Search2 = 9029
AUT_SetATRStatus = 9018
AUT_SetFineAdjustMode = 9031
AUT_SetLockStatus = 9020
AUT_SetSearchArea = 9043
AUT_SetTimeout = 9011
AUT_SetTol = 9007
AUT_SetUserSpiral = 9041
BAP_GetLastDisplayedError = 17003
BAP_GetMeasPrg = 17018
BAP_GetPrismDef = 17023
BAP_GetPrismType = 17009
BAP_GetTargetType = 17022
BAP_MeasDistanceAngle = 17017
BAP_SearchTarget = 17020
BAP_SetMeasPrg = 17019
BAP_SetPrismDef = 17024
BAP_SetPrismType = 17008
BAP_SetTargetType = 17021
BMM_BeepAlarm = 11004
BMM_BeepNormal = 11003
BMM_BeepOff = 11002
BMM_BeepOn = 11001
COM_EnableSignOff = 115
COM_GetBinaryAvailable = 113
COM_GetDoublePrecision = 108
COM_GetSWVersion = 110
COM_Local = 1
COM_NullProc = 0
COM_SetBinaryAvailable = 114
COM_SetDoublePrecision = 107
COM_SetSendDelay = 109
COM_SwitchOffTPS = 112
COM_SwitchOnTPS = 111
CSV_GetDateTime = 5008
CSV_GetDeviceConfig = 5035
CSV_GetInstrumentName = 5004
CSV_GetInstrumentNo = 5003
CSV_GetIntTemp = 5011
CSV_GetSWVersion = 5034
CSV_GetSWVersion2 = 5034
CSV_GetUserInstrumentName = 5006
CSV_GetVBat = 5009
CSV_GetVMem = 5010
CSV_SetDateTime = 5007
CSV_SetUserInstrumentName = 5005
CTL_GetUpCounter = 12003
EDM_GetBumerang = 1044
EDM_GetEglIntensity = 1058
EDM_GetTrkLightBrightness = 1041
EDM_GetTrkLightSwitch = 1040
EDM_Laserpointer = 1004
EDM_On = 1010
EDM_SetBumerang = 1007
EDM_SetEglIntensity = 1059
EDM_SetTrkLightBrightness = 1032
EDM_SetTrkLightSwitch = 1031
IOS_BeepOff = 20000
IOS_BeepOn = 20001
MOT_ReadLockStatus = 6021
MOT_SetVelocity = 6004
MOT_StartController = 6001
MOT_StopController = 6002
SUP_GetConfig = 14001
SUP_SetConfig = 14002
SUP_SwitchLowTempControl = 14003
TMC_DoMeasure = 2008
TMC_GetAngSwitch = 2014
TMC_GetAngle1 = 2003
TMC_GetAngle5 = 2107
TMC_GetAtmCorr = 2029
TMC_GetCoordinate = 2082
TMC_GetCoordinate1 = 2082
TMC_GetEdmMode = 2021
TMC_GetFace = 2026
TMC_GetHeight = 2011
TMC_GetInclineSwitch = 2007
TMC_GetPrismCorr = 2023
TMC_GetRefractiveCorr = 2031
TMC_GetRefractiveMethod = 2091
TMC_GetSignal = 2022
TMC_GetSimpleCoord = 2116
TMC_GetSimpleMea = 2108
TMC_GetSlopeDistCorr = 2126
TMC_GetStation = 2009
TMC_IfDataAzeCorrError = 2114
TMC_IfDataIncCorrError = 2115
TMC_QuickDist = 2117
TMC_SetAngSwitch = 2016
TMC_SetAtmCorr = 2028
TMC_SetEdmMode = 2020
TMC_SetHandDist = 2019
TMC_SetHeight = 2012
TMC_SetInclineSwitch = 2006
TMC_SetOrientation = 2113
TMC_SetPrismCorr = 2024
TMC_SetRefractiveCorr = 2030
TMC_SetRefractiveMethod = 2090
TMC_SetStation = 2010
WIR_GetRecFormat = 8011
WIR_SetRecFormat = 8012
CRLF = "\r\n"


COMMAND_CODES = {'AUS_GetRcsSearchSwitch': 18010,
                 'AUS_GetUserAtrState': 18006,
                 'AUS_GetUserLockState': 18008,
                 'AUS_SetUserAtrState': 18005,
                 'AUS_SetUserLockState': 18007,
                 'AUS_SwitchRcsSearch': 18009,
                 'AUT_ChangeFace': 9028,
                 'AUT_ChangeFace4': 9028,
                 'AUT_FineAdjust': 9037,
                 'AUT_FineAdjust3': 9037,
                 'AUT_GetATRStatus': 9019,
                 'AUT_GetFineAdjustMode': 9030,
                 'AUT_GetLockStatus': 9021,
                 'AUT_GetSearchArea': 9042,
                 'AUT_GetUserSpiral': 9040,
                 'AUT_LockIn': 9013,
                 'AUT_MakePositioning': 9027,
                 'AUT_MakePositioning4': 9027,
                 'AUT_PS_EnableRange': 9048,
                 'AUT_PS_SearchNext': 9051,
                 'AUT_PS_SearchWindow': 9052,
                 'AUT_PS_SetRange': 9047,
                 'AUT_ReadTimeout': 9012,
                 'AUT_ReadTol': 9008,
                 'AUT_Search': 9029,
                 'AUT_Search2': 9029,
                 'AUT_SetATRStatus': 9018,
                 'AUT_SetFineAdjustMode': 9031,
                 'AUT_SetLockStatus': 9020,
                 'AUT_SetSearchArea': 9043,
                 'AUT_SetTimeout': 9011,
                 'AUT_SetTol': 9007,
                 'AUT_SetUserSpiral': 9041,
                 'BAP_GetLastDisplayedError': 17003,
                 'BAP_GetMeasPrg': 17018,
                 'BAP_GetPrismDef': 17023,
                 'BAP_GetPrismType': 17009,
                 'BAP_GetTargetType': 17022,
                 'BAP_MeasDistanceAngle': 17017,
                 'BAP_SearchTarget': 17020,
                 'BAP_SetMeasPrg': 17019,
                 'BAP_SetPrismDef': 17024,
                 'BAP_SetPrismType': 17008,
                 'BAP_SetTargetType': 17021,
                 'BMM_BeepAlarm': 11004,
                 'BMM_BeepNormal': 11003,
                 'BMM_BeepOff': 11002,
                 'BMM_BeepOn': 11001,
                 'COM_EnableSignOff': 115,
                 'COM_GetBinaryAvailable': 113,
                 'COM_GetDoublePrecision': 108,
                 'COM_GetSWVersion': 110,
                 'COM_Local': 1,
                 'COM_NullProc': 0,
                 'COM_SetBinaryAvailable': 114,
                 'COM_SetDoublePrecision': 107,
                 'COM_SetSendDelay': 109,
                 'COM_SwitchOffTPS': 112,
                 'COM_SwitchOnTPS': 111,
                 'CSV_GetDateTime': 5008,
                 'CSV_GetDeviceConfig': 5035,
                 'CSV_GetInstrumentName': 5004,
                 'CSV_GetInstrumentNo': 5003,
                 'CSV_GetIntTemp': 5011,
                 'CSV_GetSWVersion': 5034,
                 'CSV_GetSWVersion2': 5034,
                 'CSV_GetUserInstrumentName': 5006,
                 'CSV_GetVBat': 5009,
                 'CSV_GetVMem': 5010,
                 'CSV_SetDateTime': 5007,
                 'CSV_SetUserInstrumentName': 5005,
                 'CTL_GetUpCounter': 12003,
                 'EDM_GetBumerang': 1044,
                 'EDM_GetEglIntensity': 1058,
                 'EDM_GetTrkLightBrightness': 1041,
                 'EDM_GetTrkLightSwitch': 1040,
                 'EDM_Laserpointer': 1004,
                 'EDM_On': 1010,
                 'EDM_SetBumerang': 1007,
                 'EDM_SetEglIntensity': 1059,
                 'EDM_SetTrkLightBrightness': 1032,
                 'EDM_SetTrkLightSwitch': 1031,
                 'IOS_BeepOff': 20000,
                 'IOS_BeepOn': 20001,
                 'MOT_ReadLockStatus': 6021,
                 'MOT_SetVelocity': 6004,
                 'MOT_StartController': 6001,
                 'MOT_StopController': 6002,
                 'SUP_GetConfig': 14001,
                 'SUP_SetConfig': 14002,
                 'SUP_SwitchLowTempControl': 14003,
                 'TMC_DoMeasure': 2008,
                 'TMC_GetAngSwitch': 2014,
                 'TMC_GetAngle1': 2003,
                 'TMC_GetAngle5': 2107,
                 'TMC_GetAtmCorr': 2029,
                 'TMC_GetCoordinate': 2082,
                 'TMC_GetCoordinate1': 2082,
                 'TMC_GetEdmMode': 2021,
                 'TMC_GetFace': 2026,
                 'TMC_GetHeight': 2011,
                 'TMC_GetInclineSwitch': 2007,
                 'TMC_GetPrismCorr': 2023,
                 'TMC_GetRefractiveCorr': 2031,
                 'TMC_GetRefractiveMethod': 2091,
                 'TMC_GetSignal': 2022,
                 'TMC_GetSimpleCoord': 2116,
                 'TMC_GetSimpleMea': 2108,
                 'TMC_GetSlopeDistCorr': 2126,
                 'TMC_GetStation': 2009,
                 'TMC_IfDataAzeCorrError': 2114,
                 'TMC_IfDataIncCorrError': 2115,
                 'TMC_QuickDist': 2117,
                 'TMC_SetAngSwitch': 2016,
                 'TMC_SetAtmCorr': 2028,
                 'TMC_SetEdmMode': 2020,
                 'TMC_SetHandDist': 2019,
                 'TMC_SetHeight': 2012,
                 'TMC_SetInclineSwitch': 2006,
                 'TMC_SetOrientation': 2113,
                 'TMC_SetPrismCorr': 2024,
                 'TMC_SetRefractiveCorr': 2030,
                 'TMC_SetRefractiveMethod': 2090,
                 'TMC_SetStation': 2010,
                 'WIR_GetRecFormat': 8011,
                 'WIR_SetRecFormat': 8012,
                 }

# enums

# KInd of universal
class BOOLEAN_TYPE(Enum):
    FALSE = 0
    TRUE = 1

class ON_OFF_TYPE(Enum):  # on/off switch type
    OFF = 0  # Switch is off
    ON = 1  # Switch is on

# AUT
class AUT_DIRECTION(Enum):
    AUT_CLOCKWISE = 1, # direction clockwise.
    AUT_ANTICLOCKWISE = -1 # direction counter clockwise.

# Position Precision
class AUT_POSMODE(Enum):
    AUT_NORMAL = 0  # fast positioning mode
    AUT_PRECISE = 1  # exact positioning mode
    # note: can distinctly claim more time for the positioning

# Fine-adjust Position Mode
class AUT_ADJMODE(Enum):
# Possible settings of the positioning
# tolerance relating the angle- or the
# point- accuracy at the fine adjust.
    AUT_NORM_MODE = 0  # Angle tolerance
    AUT_POINT_MODE = 1  # Point tolerance
    AUT_DEFINE_MODE = 2  # System independent positioning tolerance. Set with AUT_SetTol

# Automatic Target Recognition Mode
class AUT_ATRMODE(Enum):  # Possible modes of the target recognition
    AUT_POSITION = 0  # Positioning to the hz- and v-angle
    AUT_TARGET = 1  # Positioning to a target in the environment of the hz- and v-angle.

# BAP - Measurement Modes
class BAP_MEASURE_PRG(Enum):
    BAP_NO_MEAS = 0  # no measurements, take last one
    BAP_NO_DIST = 1  # no dist. measurement, angles only
    BAP_DEF_DIST = 2  # default distance measurements, pre-defined using BAP_SetMeasPrg
    BAP_CLEAR_DIST = 5  # clear distances
    BAP_STOP_TRK = 6  # stop tracking laser

# BAP - Distance measurement programs
class BAP_USER_MEASPRG(Enum):
    BAP_SINGLE_REF_STANDARD = 0  # standard single IR distance with reflector
    BAP_SINGLE_REF_FAST = 1  # fast single IR distance with reflector
    BAP_SINGLE_REF_VISIBLE = 2  # long range distance with reflector (red laser)
    BAP_SINGLE_RLESS_VISIBLE = 3  # single RL distance, reflector free (red laser)
    BAP_CONT_REF_STANDARD = 4  # tracking IR distance with reflector
    BAP_CONT_REF_FAST = 5  # fast tracking IR distance with reflector
    BAP_CONT_RLESS_VISIBLE = 6  # fast tracking RL distance, reflector free (red)
    BAP_AVG_REF_STANDARD = 7  # Average IR distance with reflector
    BAP_AVG_REF_VISIBLE = 8  # Average long range dist. with reflector (red)
    BAP_AVG_RLESS_VISIBLE = 9  # Average RL distance, reflector free (red laser)

# BAP - Prism type definition
class BAP_PRISMTYPE(Enum):
    BAP_PRISM_ROUND = 0  # prism type: round
    BAP_PRISM_MINI = 1  # prism type: mini
    BAP_PRISM_TAPE = 2  # prism type: tape
    BAP_PRISM_360 = 3  # prism type: 360
    BAP_PRISM_USER1 = 4  # prism type: user1
    BAP_PRISM_USER2 = 5  # prism type: user2
    BAP_PRISM_USER3 = 6  # prism type: user3

# BAP - Reflector type definition
class BAP_REFLTYPE(Enum):
    BAP_REFL_UNDEF = 0  # reflector not defined
    BAP_REFL_PRISM = 1  # reflector prism
    BAP_REFL_TAPE = 2  # reflector tape

# BAP - Target type definition
class BAP_TARGET_TYPE(Enum):
    BAP_REFL_USE = 0  # with reflector
    BAP_REFL_LESS = 1  # without reflector

# COM
class COM_FORMAT(Enum):
    COM_ASCII = 0 # Force ASCII comm.
    COM_BINARY = 1 # Enable binary comm.

class COM_BAUD_RATE(Enum):
    COM_BAUD_38400 = 0
    COM_BAUD_19200 = 1  # default baud rate
    COM_BAUD_9600 = 2
    COM_BAUD_4800 = 3
    COM_BAUD_2400 = 4

class COM_TPS_STATUS(Enum):
    COM_TPS_OFF = 0  # switched off
    COM_TPS_SLEEPING = 1  # sleep mode
    COM_TPS_ONLINE = 2  # online mode
    COM_TPS_LOCAL = 3  # local mode
    COM_TPS_UNKNOWN = 4  # unknown or not initialised

# COM - Start Mode, used in COM_SwitchOnTPS(COM_TPS_STARTUP_MODE eOnMode)
class COM_TPS_STARTUP_MODE(Enum):
    COM_TPS_STARTUP_LOCAL = 0  # RPC’s enabled, local mode
    COM_TPS_STARTUP_REMOTE= 1  # RPC’s enabled, online mode

# COM - Stop Mode, used in COM_SwitchOffTPS(COM_TPS_STOP_MODE eOffMode)
class COM_TPS_STOP_MODE(Enum):
    COM_TPS_STOP_SHUT_DOWN = 0  # power down instrument
    COM_TPS_STOP_SLEEP = 1  # puts instrument into sleep state

# //? TODO: unused?
# TPS Device Precision Class
class TPS_DEVICE_CLASS(Enum):
    TPS_CLASS_1100 = 0  # TPS1000 family member, 1 mgon, 3"
    TPS_CLASS_1700 = 1  # TPS1000 family member, 0.5 mgon, 1.5"
    TPS_CLASS_1800 = 2  # TPS1000 family member, 0.3 mgon, 1"
    TPS_CLASS_5000 = 3  # TPS2000 family member
    TPS_CLASS_6000 = 4  # TPS2000 family member
    TPS_CLASS_1500 = 5  # TPS1000 family member
    TPS_CLASS_2003 = 6  # TPS2000 family member
    TPS_CLASS_5005 = 7  # TPS5000 family member
    TPS_CLASS_5100 = 8  # TPS5000 family member
    TPS_CLASS_1102 = 100  # TPS1100 family member, 2"
    TPS_CLASS_1103 = 101  # TPS1100 family member, 3"
    TPS_CLASS_1105 = 102  # TPS1100 family member, 5"
    TPS_CLASS_1101 = 103  # TPS1100 family member, 1"

# //? TODO: unused?
# TPS Device Configuration Type
class TPS_DEVICE_TYPE(Enum):
    TPS_DEVICE_T = 0x00000  # theodolite without built-in EDM
    TPS_DEVICE_TC1 = 0x00001  # tachymeter built-in
    TPS_DEVICE_TC2 = 0x00002  # tachymeter with red red laser built-in
    TPS_DEVICE_MOT = 0x00004  # motorized device
    TPS_DEVICE_ATR = 0x00008  # automatic target recognition
    TPS_DEVICE_EGL = 0x00010  # electronic guide light
    TPS_DEVICE_DB = 0x00020  # reserved
    TPS_DEVICE_DL = 0x00040  # diode laser
    TPS_DEVICE_LP = 0x00080  # laser plummet
    TPS_DEVICE_ATC = 0x00100  # autocollimination lamp
    TPS_DEVICE_LPNT= 0x00200  # Laserpointer
    TPS_DEVICE_RL_EXT = 0x00400  # Red laser with extended range
    TPS_DEVICE_SIM = 0x04000  # runs on simulation, not on hardware

# EDM - Intensity of Electronic Guidelight
class EDM_EGLINTENSITY_TYPE(Enum):
    EDM_EGLINTEN_OFF = 0,
    EDM_EGLINTEN_LOW = 1,
    EDM_EGLINTEN_MID = 2,
    EDM_EGLINTEN_HIGH = 3

# MOT - Lock Conditions
class MOT_LOCK_STATUS(Enum):
    MOT_LOCKED_OUT = 0  # locked out
    MOT_LOCKED_IN = 1  # locked in
    MOT_PREDICTION = 2  # prediction mode

# MOT - Controller Stop Mode
class MOT_STOPMODE(Enum):
    MOT_NORMAL = 0  # slow down with current acceleration
    MOT_SHUTDOWN = 1  # slow down by switch off power supply

# MOT - Controller Configuration
class MOT_MODE(Enum):
    MOT_POSIT = 0  # configured for relative postioning
    MOT_OCONST = 1  # configured for constant speed
    MOT_MANUPOS = 2  # configured for manual positioning default setting
    MOT_LOCK = 3  # configured as "Lock-In"-controller
    MOT_BREAK = 4 # configured as "Brake"-controller do not use 5 and 6
    MOT_TERM = 7  # terminates the controller task

# SUP - Automatic Shutdown Mechanism for the System
class SUP_AUTO_POWER(Enum):
    AUTO_POWER_DISABLED = 0  # deactivate the mechanism
    AUTO_POWER_SLEEP = 1  # activate sleep mechanism
    AUTO_POWER_OFF = 2  # activate shut down mechanism

# TMC - Inclination Sensor Measurement Program
class TMC_INCLINE_PRG(Enum):
    TMC_MEA_INC = 0  # Use sensor (apriori sigma)
    TMC_AUTO_INC = 1  # Automatic mode (sensor/plane)
    TMC_PLANE_INC = 2  # Use plane (apriori sigma)

# TMC - Measurement Mode
class TMC_MEASURE_PRG(Enum):
    TMC_STOP = 0  # Stop measurement program
    TMC_DEF_DIST = 1  # Default DIST-measurement program
    TMC_TRK_DIST = 2  # Distance-TRK measurement program
    TMC_CLEAR = 3  # TMC_STOP and clear data
    TMC_SIGNAL = 4  # Signal measurement (test function)
    TMC_DO_MEASURE = 6  # (Re)start measurement task
    TMC_RTRK_DIST = 8  # Distance-TRK measurement program
    TMC_RED_TRK_DIST = 10  # Red laser tracking
    TMC_FREQUENCY = 11  # Frequency measurement (test)

# EDM - Measurement Mode
class EDM_MODE(Enum):
    EDM_MODE_NOT_USED = 0  # Init value
    EDM_SINGLE_TAPE = 1  # Single measurement with tape
    EDM_SINGLE_STANDARD = 2  # Standard single measurement
    EDM_SINGLE_FAST = 3  # Fast single measurement
    EDM_SINGLE_LRANGE = 4  # Long range single measurement
    EDM_SINGLE_SRANGE = 5  # Short range single measurement
    EDM_CONT_STANDARD = 6  # Standard repeated measurement
    EDM_CONT_DYNAMIC = 7  # Dynamic repeated measurement
    EDM_CONT_REFLESS = 8  # Reflectorless repeated measurement
    EDM_CONT_FAST = 9  # Fast repeated measurement
    EDM_AVERAGE_IR = 10  # Standard average measurement
    EDM_AVERAGE_SR = 11  # Short range average measurement
    EDM_AVERAGE_LR = 12  # Long range average measurent

# Used before TPS1100 to set tracking light brightness
class EDM_TRKLIGHT_BRIGHTNESS(Enum):
    EDM_LOW_BRIGHTNESS = 0
    EDM_MEDIUM_BRIGHTNESS = 1
    EDM_HIGH_BRIGHTNESS = 2


class EDM_EGLINTENSITY_TYPE(Enum):
    EDM_EGLINTEN_OFF = 0
    EDM_EGLINTEN_LOW = 1
    EDM_EGLINTEN_MID = 2
    EDM_EGLINTEN_HIGH = 3

class WIR_RECFORMAT(Enum):
    WIR_RECFORMAT_GSI = 0 # defines recording format is GSI (standard)
    WIR_RECFORMAT_GSI16 = 1 # defines recording format is the new GSI-16