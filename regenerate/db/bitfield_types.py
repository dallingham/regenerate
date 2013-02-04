from regenerate.db import BitField
from collections import namedtuple

BitFieldInfo = namedtuple('TypeInfo',
                          'type id input control oneshot wide dataout '
                          'read readonly description simple_type')

TYPES = (
    BitFieldInfo(BitField.TYPE_READ_ONLY,
                 "RO", False, False, False, True, True, False, True,
                 "Read Only", "RO"),
    BitFieldInfo(BitField.TYPE_READ_ONLY_VALUE,
                 "ROV", True, False, False, True, False, False, True,
                 "Read Only, value continuously assigned", "RO"),
    BitFieldInfo(BitField.TYPE_READ_ONLY_LOAD,
                 "ROLD", True, True, False, True, True, False, True,
                 "Read Only, value loaded on control signal", "RO"),
    BitFieldInfo(BitField.TYPE_READ_ONLY_VALUE_1S,
                 "RV1S", True, False, True, True, True, True, True,
                 "Read Only, value continuosly assigned, one shot on read",
                 "RO"),
    BitFieldInfo(BitField.TYPE_READ_ONLY_CLEAR_LOAD,
                 "RCLD", True, True, False, True, True, False, True,
                 "Read Only, value loaded on control signal, cleared on read",
                 "RO"),
    BitFieldInfo(BitField.TYPE_READ_WRITE,
                 "RW", False, False, False, True, True, False, False,
                 "Read/Write", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_1S,
                 "RW1S", False, False, True, True, True, False, False,
                 "Read/Write, one shot on any write", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_1S_1,
                 "RW1S1", False, False, True, True, True, False, False,
                 "Read/Write, one shot on write of 1", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_LOAD,
                 "RWLD", True, True, False, True, True, False, False,
                 "Read/Write, value loaded on control signal", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_LOAD_1S,
                 "RWLD1S", True, True, True, True, True, False, False,
                 "Read/Write, value loaded on control signal, "
                 "one shot on any write", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_LOAD_1S_1,
                 "RWLD1S1", True, True, True, True, True, False, False,
                 "Read/Write, value loaded on control signal, "
                 "one shot on write of 1", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_SET,
                 "RWS", True, False, False, True, True, False, False,
                 "Read/Write, bits set on input signal", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_SET_1S,
                 "RWS1S", True, False, True, True, True, False, False,
                 "Read/Write, bits set on input signal, "
                 "one shot on any write", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_SET_1S_1,
                 "RWS1S1", True, False, True, True, True, False, False,
                 "Read/Write, bits set on input signal, "
                 "one shot on write of 1", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_CLR,
                 "RWC", True, False, False, True, True, False, False,
                 "Read/Write, bits cleared on input signal", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_CLR_1S,
                 "RWC1S", True, False, False, True, True, False, False,
                 "Read/Write, bits cleared on input signal, "
                 "one shot on any write", "RW"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_CLR_1S_1,
                 "RWC1S1", True, False, True, True, True, False, False,
                 "Read/Write, bits cleared on input signal, "
                 "one shot on write of 1", "RW"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_SET,
                 "W1CS", True, False, False, True, True, False, False,
                 "Write 1 to Clear, bits set on input signal", "W1C"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S,
                 "W1CS1S", True, False, True, True, True, False, False,
                 "Write 1 to Clear, bits set on input signal, "
                 "one shot on any write", "W1C"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S_1,
                 "W1CS1S1", True, False, True, True, True, False, False,
                 "Write 1 to Clear, bits set on input signal, "
                 "one shot on write of 1", "W1C"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_LOAD,
                 "W1CLD", True, True, False, True, True, False, False,
                 "Write 1 to Clear, value loaded on control signal", "W1C"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S,
                 "W1CLD1S", True, True, True, True, True, False, False,
                 "Write 1 to Clear, value loaded on control signal, "
                 "one shot on any write", "W1C"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1,
                 "W1CLD1S1", True, True, True, True, True, False, False,
                 "Write 1 to Clear, value loaded on control signal, "
                 "one shot on write of 1", "W1C"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_SET,
                 "W1S", True, False, False, True, True, False, False,
                 "Write 1 to Set, clear on input signal", "W1S"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_SET_1S,
                 "W1S1S", True, False, True, True, True, False, False,
                 "Write 1 to Set, one shot on any write, "
                 "clear on input signal", "W1S"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_SET_1S1,
                 "W1S1S1", True, False, True, True, True, False, False,
                 "Write 1 to Set, one shot on write of 1, "
                 "clear on input signal", "W1S"),
    BitFieldInfo(BitField.TYPE_WRITE_ONLY,
                 "WO", False, False, True, True, False, False, False,
                 "Write Only", "WO"),
    )

TYPE_TO_ID = {}
for __i in TYPES:
    TYPE_TO_ID[__i.type] = __i.id

ID_TO_TYPE = {}
for __i in TYPES:
    ID_TO_TYPE[__i.id] = __i.type

TYPE_TO_SIMPLE_TYPE = {}
for __i in TYPES:
    TYPE_TO_SIMPLE_TYPE[__i.type] = __i.simple_type

TYPE_TO_DESCR = {}
for __i in TYPES:
    TYPE_TO_DESCR[__i.type] = __i.description

TYPE_TO_ENABLE = {}
for i in TYPES:
    TYPE_TO_ENABLE[i.type] = (i.input, i.control)
