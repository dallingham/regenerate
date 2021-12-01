#
# Manage registers in a hardware design
#
# Copyright (C) 2008  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""
Provides a description of the various different bit types.

This data is used to build the register types.
"""

from typing import NamedTuple
from .enums import BitType


class BitFieldInfo(NamedTuple):
    """
    Provide the information describing the physical implementation.

    The information is used to build the RTL implementation.

    The fields are:

    * type - the bit type implementation from enums.BitType
    * id - shorthand notation for the type
    * input - indicates if the type has an input signal
    * control - indicates if the type has a control signal
    * oneshot - indicates if the type has a oneshot output
    * dataout - indicates if the type has a data out signal
    * read - indicates if the type has a read strobe control
    * readonly - indicates if the type is a readonly type
    * description - description of the type
    * simple_type - indicates the short hand notation for simple type,
                    which removes input/output information
    """

    type: BitType
    id: str
    input: bool
    control: bool
    oneshot: bool
    dataout: bool
    read: bool
    readonly: bool
    description: str
    simple_type: str


TYPES = (
    BitFieldInfo(
        type=BitType.READ_ONLY,
        id="RO",
        input=False,
        control=False,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=True,
        description="Read Only",
        simple_type="RO",
    ),
    BitFieldInfo(
        type=BitType.READ_ONLY_VALUE,
        id="ROV",
        input=True,
        control=False,
        oneshot=False,
        dataout=False,
        read=False,
        readonly=True,
        description="Read Only, value continuously assigned",
        simple_type="RO",
    ),
    BitFieldInfo(
        type=BitType.READ_ONLY_LOAD,
        id="ROLD",
        input=True,
        control=True,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=True,
        description="Read Only, value loaded on control signal",
        simple_type="RO",
    ),
    BitFieldInfo(
        type=BitType.READ_ONLY_VALUE_1S,
        id="RV1S",
        input=True,
        control=False,
        oneshot=True,
        dataout=True,
        read=True,
        readonly=True,
        description="Read Only, value continuosly assigned, one shot on read",
        simple_type="RO",
    ),
    BitFieldInfo(
        type=BitType.READ_ONLY_CLEAR_LOAD,
        id="RCLD",
        input=True,
        control=True,
        oneshot=False,
        dataout=True,
        read=True,
        readonly=True,
        description="Read Only, value loaded on control signal, cleared on read",
        simple_type="RO",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE,
        id="RW",
        input=False,
        control=False,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_1S,
        id="RW1S",
        input=False,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, one shot on any write",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_1S_1,
        id="RW1S1",
        input=False,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, one shot on write of 1",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_LOAD,
        id="RWLD",
        input=True,
        control=True,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, value loaded on control signal",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_LOAD_1S,
        id="RWLD1S",
        input=True,
        control=True,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, value loaded on control signal, one shot on any write",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_LOAD_1S_1,
        id="RWLD1S1",
        input=True,
        control=True,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, value loaded on control signal, one shot on write of 1",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_SET,
        id="RWS",
        input=True,
        control=False,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, bits set on input signal",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_SET_1S,
        id="RWS1S",
        input=True,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, bits set on input signal, one shot on any write",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_SET_1S_1,
        id="RWS1S1",
        input=True,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, bits set on input signal, one shot on write of 1",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_CLR,
        id="RWC",
        input=True,
        control=False,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, bits cleared on input signal",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_CLR_1S,
        id="RWC1S",
        input=True,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, bits cleared on input signal, one shot on any write",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_CLR_1S_1,
        id="RWC1S1",
        input=True,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, bits cleared on input signal, one shot on write of 1",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_CLEAR_SET,
        id="W1CS",
        input=True,
        control=False,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Clear, bits set on input signal",
        simple_type="W1C",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_CLEAR_SET_1S,
        id="W1CS1S",
        input=True,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Clear, bits set on input signal, one shot on any write",
        simple_type="W1C",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_CLEAR_SET_1S_1,
        id="W1CS1S1",
        input=True,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Clear, bits set on input signal, one shot on write of 1",
        simple_type="W1C",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_CLEAR_LOAD,
        id="W1CLD",
        input=True,
        control=True,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Clear, value loaded on control signal",
        simple_type="W1C",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_CLEAR_LOAD_1S,
        id="W1CLD1S",
        input=True,
        control=True,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Clear, value loaded on control signal, one shot on any write",
        simple_type="W1C",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_CLEAR_LOAD_1S_1,
        id="W1CLD1S1",
        input=True,
        control=True,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Clear, value loaded on control signal, one shot on write of 1",
        simple_type="W1C",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_SET,
        id="W1S",
        input=True,
        control=False,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Set, clear on input signal",
        simple_type="W1S",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_SET_1S,
        id="W1S1S",
        input=True,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Set, one shot on any write, clear on input signal",
        simple_type="W1S",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_SET_1S1,
        id="W1S1S1",
        input=True,
        control=False,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Set, one shot on write of 1, clear on input signal",
        simple_type="W1S",
    ),
    BitFieldInfo(
        type=BitType.WRITE_ONLY,
        id="WO",
        input=False,
        control=False,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Write Only",
        simple_type="WO",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_RESET_ON_COMP,
        id="RWRC",
        input=False,
        control=False,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write when reset, reset on complement",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_PROTECT,
        id="RWPR",
        input=False,
        control=True,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, Read only on control signal",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.READ_WRITE_PROTECT_1S,
        id="RWPR1S",
        input=False,
        control=True,
        oneshot=True,
        dataout=True,
        read=False,
        readonly=False,
        description="Read/Write, Read only on control signal, one shot on any valid write",
        simple_type="RW",
    ),
    BitFieldInfo(
        type=BitType.WRITE_1_TO_CLEAR_SET_CLR,
        id="W1CSC",
        input=True,
        control=True,
        oneshot=False,
        dataout=True,
        read=False,
        readonly=False,
        description="Write 1 to Clear, bits set on input signal, soft clear",
        simple_type="W1C",
    ),
)

TYPE_TO_ID = dict((__i.type, __i.id) for __i in TYPES)

ID_TO_TYPE = dict((__i.id, __i.type) for __i in TYPES)

TYPE_TO_SIMPLE_TYPE = dict((__i.type, __i.simple_type) for __i in TYPES)

TYPE_TO_DESCR = dict((__i.type, __i.description) for __i in TYPES)

TYPE_TO_ENABLE = dict((__i.type, (__i.input, __i.control)) for __i in TYPES)

TYPE_TO_OUTPUT = dict((__i.type, __i.dataout) for __i in TYPES)
