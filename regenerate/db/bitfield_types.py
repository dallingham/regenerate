from regenerate.db import BitField

BFT_TYPE = 0
BFT_ID   = 1
BFT_INP  = 2
BFT_CTRL = 3
BFT_1S   = 4
BFT_DESC = 5

TYPES =  (
    (BitField.TYPE_READ_ONLY,                 "RO",      False, False, False, "Read Only"),
    (BitField.TYPE_READ_ONLY_LOAD,            "ROL",     True,  True,  False, "Read Only, value loaded on control signal" ),
    (BitField.TYPE_READ_WRITE,                "RW",      False, False, False, "Read/Write"),
    (BitField.TYPE_READ_WRITE_1S,             "RW1S",    False, False, True,  "Read/Write, one shot on any write"),
    (BitField.TYPE_READ_WRITE_1S_1,           "RW1S1",   False, False, True,  "Read/Write, one shot on write of 1"),
    (BitField.TYPE_READ_WRITE_LOAD,           "RWLD",    True,  True,  False, "Read/Write, value loaded on control signal"),
    (BitField.TYPE_READ_WRITE_LOAD_1S,        "RWLD1S",  True,  True,  True,  "Read/Write, value loaded on control signal, one shot on any write"),
    (BitField.TYPE_READ_WRITE_LOAD_1S_1,      "RWLD1S1", True,  True,  True,  "Read/Write, value loaded on control signal, one shot on write of 1"),
    (BitField.TYPE_READ_WRITE_SET,            "RWS",     True,  False, False, "Read/Write, bits set on input signal"),
    (BitField.TYPE_READ_WRITE_SET_1S,         "RWS1S",   True,  False, True,  "Read/Write, bits set on input signal, one shot on any write"),
    (BitField.TYPE_READ_WRITE_SET_1S_1,       "RWS1S1",  True,  False, False, "Read/Write, bits set on input signal, one shot on write of 1"),
    (BitField.TYPE_WRITE_1_TO_CLEAR_SET,      "W1CS",    True,  False, False, "Write 1 to Clear, bits set on input signal"),
    (BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S,   "W1CS1S",  True,  False, True,  "Write 1 to Clear, bits set on input signal, one shot on any write"),
    (BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S_1, "W1CS1S1", True,  False, True,  "Write 1 to Clear, bits set on input signal, one shot on write of 1"),
    (BitField.TYPE_WRITE_1_TO_CLEAR_LOAD,     "W1CLD",   True,  True,  False, "Write 1 to Clear, value loaded on control signal"),
    (BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S,  "W1CLD1S", True,  True,  True,  "Write 1 to Clear, value loaded on control signal, one shot on any write"),
    (BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1,"W1CLD1S1",True,  True,  True,  "Write 1 to Clear, value loaded on control signal, one shot on write of 1"),
    (BitField.TYPE_WRITE_1_TO_SET,            "W1S",     False, False, False, "Write 1 to Set"),
    (BitField.TYPE_WRITE_ONLY,                "WO",      False, False, False, "Write Only"),
    )
