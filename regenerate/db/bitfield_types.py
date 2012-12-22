from regenerate.db import BitField
from collections import namedtuple

BitFieldInfo = namedtuple('TypeInfo',
                          'type id input control oneshot wide dataout '
                          'read readonly description')

TYPES = (
    BitFieldInfo(BitField.TYPE_READ_ONLY,
                 "RO", False, False, False, True, True, False, True,
                 "Read Only"),
    BitFieldInfo(BitField.TYPE_READ_ONLY_VALUE,
                 "ROV", True, False, False, True, False, False, True,
                 "Read Only, value continuously assigned"),
    BitFieldInfo(BitField.TYPE_READ_ONLY_LOAD,
                 "ROLD", True, True, False, True, True, False, True,
                 "Read Only, value loaded on control signal"),
    BitFieldInfo(BitField.TYPE_READ_ONLY_VALUE_1S,
                 "RV1S", True, False, True, True, True, True, True,
                 "Read Only, value continuosly assigned, one shot on read"),
    BitFieldInfo(BitField.TYPE_READ_ONLY_CLEAR_LOAD,
                 "RCLD", True, True, False, True, True, False, True,
                 "Read Only, value loaded on control signal, cleared on read"),
    BitFieldInfo(BitField.TYPE_READ_WRITE,
                 "RW", False, False, False, True, True, False, False,
                 "Read/Write"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_1S,
                 "RW1S", False, False, True, True, True, False, False,
                 "Read/Write, one shot on any write"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_1S_1,
                 "RW1S1", False, False, True, True, True, False, False,
                 "Read/Write, one shot on write of 1"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_LOAD,
                 "RWLD", True, True, False, True, True, False, False,
                 "Read/Write, value loaded on control signal"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_LOAD_1S,
                 "RWLD1S", True, True, True, True, True, False, False,
                 "Read/Write, value loaded on control signal, "
                 "one shot on any write"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_LOAD_1S_1,
                 "RWLD1S1", True, True, True, True, True, False, False,
                 "Read/Write, value loaded on control signal, "
                 "one shot on write of 1"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_SET,
                 "RWS", True, False, False, True, True, False, False,
                 "Read/Write, bits set on input signal"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_SET_1S,
                 "RWS1S", True, False, True, True, True, False, False,
                 "Read/Write, bits set on input signal, "
                 "one shot on any write"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_SET_1S_1,
                 "RWS1S1", True, False, True, True, True, False, False,
                 "Read/Write, bits set on input signal, "
                 "one shot on write of 1"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_CLR,
                 "RWC", True, False, False, True, True, False, False,
                 "Read/Write, bits cleared on input signal"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_CLR_1S,
                 "RWC1S", True, False, False, True, True, False, False,
                 "Read/Write, bits cleared on input signal, "
                 "one shot on any write"),
    BitFieldInfo(BitField.TYPE_READ_WRITE_CLR_1S_1,
                 "RWC1S1", True, False, True, True, True, False, False,
                 "Read/Write, bits cleared on input signal, "
                 "one shot on write of 1"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_SET,
                 "W1CS", True, False, False, True, True, False, False,
                 "Write 1 to Clear, bits set on input signal"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S,
                 "W1CS1S", True, False, True, True, True, False, False,
                 "Write 1 to Clear, bits set on input signal, "
                 "one shot on any write"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S_1,
                 "W1CS1S1", True, False, True, True, True, False, False,
                 "Write 1 to Clear, bits set on input signal, "
                 "one shot on write of 1"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_LOAD,
                 "W1CLD", True, True, False, True, True, False, False,
                 "Write 1 to Clear, value loaded on control signal"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S,
                 "W1CLD1S", True, True, True, True, True, False, False,
                 "Write 1 to Clear, value loaded on control signal, "
                 "one shot on any write"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1,
                 "W1CLD1S1", True, True, True, True, True, False, False,
                 "Write 1 to Clear, value loaded on control signal, "
                 "one shot on write of 1"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_SET,
                 "W1S", True, False, False, True, True, False, False,
                 "Write 1 to Set, clear on input signal"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_SET_1S,
                 "W1S1S", True, False, True, True, True, False, False,
                 "Write 1 to Set, one shot on any write, "
                 "clear on input signal"),
    BitFieldInfo(BitField.TYPE_WRITE_1_TO_SET_1S1,
                 "W1S1S1", True, False, True, True, True, False, False,
                 "Write 1 to Set, one shot on write of 1, "
                 "clear on input signal"),
    BitFieldInfo(BitField.TYPE_WRITE_ONLY,
                 "WO", False, False, True, True, False, False, False,
                 "Write Only"),
    )
