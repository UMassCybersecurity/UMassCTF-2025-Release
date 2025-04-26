from enum import Enum

class Commands(Enum):
    UNKNOWN = 0x0
    COMM_INIT = 0x3
    SET_CHIP_FREQ = 0x5
    ID_AUTHENTICATION = 0x34 
    READ = 0x69
    
class Responses(Enum):
    ACK = 0x50
    INVALID_COMMAND = 0x80
    FLOW_ERROR = 0x81
    UNAUTHORIZED = 0x82
    INVALID_FREQUENCY = 0x83
    INVALID_ID_LEN = 0x84
    INVALID_ADDRESS = 0x87
    INVALID_ADDRESS_ALIGNMENT = 0x88