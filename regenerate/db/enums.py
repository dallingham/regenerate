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
Enumerated types for the database.

All types are derived from IntEnum.

"""

from enum import IntEnum


class BitType(IntEnum):
    """
    The bit field type.

    Represents the different types of bit fields.
    """

    READ_ONLY = 0
    READ_ONLY_VALUE = 1
    READ_ONLY_LOAD = 2
    READ_ONLY_CLEAR_LOAD = 3
    READ_ONLY_VALUE_1S = 4
    READ_WRITE = 5
    READ_WRITE_1S = 6
    READ_WRITE_1S_1 = 7
    READ_WRITE_LOAD = 8
    READ_WRITE_LOAD_1S = 9
    READ_WRITE_LOAD_1S_1 = 10
    READ_WRITE_SET = 11
    READ_WRITE_SET_1S = 12
    READ_WRITE_SET_1S_1 = 13
    READ_WRITE_CLR = 14
    READ_WRITE_CLR_1S = 15
    READ_WRITE_CLR_1S_1 = 16
    WRITE_1_TO_CLEAR_SET = 17
    WRITE_1_TO_CLEAR_SET_1S = 18
    WRITE_1_TO_CLEAR_SET_1S_1 = 19
    WRITE_1_TO_CLEAR_LOAD = 20
    WRITE_1_TO_CLEAR_LOAD_1S = 21
    WRITE_1_TO_CLEAR_LOAD_1S_1 = 22
    WRITE_1_TO_SET = 23
    WRITE_1_TO_SET_1S = 24
    WRITE_1_TO_SET_1S1 = 25
    WRITE_ONLY = 26
    READ_WRITE_RESET_ON_COMP = 27
    READ_WRITE_PROTECT = 28
    READ_WRITE_PROTECT_1S = 29
    WRITE_1_TO_CLEAR_SET_CLR = 30
    WRITE_ONLY_WITH_DATA_1S = 31
    READ_WRITE_PROTECT_ILLEGAL_1S = 32


class OneShot(IntEnum):
    """
    One shot type.

    A bit field can have:

    * No one shot signal
    * A one shot signal asserted on a write of any value
    * A one shot signal asserted on a write of a one
    * A one shot signal asserted on a write of a zero
    * A one shot signal asserted on a change in value

    """

    NONE = 0
    ON_ANY = 1
    ON_ONE = 2
    ON_ZERO = 3
    ON_TOGGLE = 4


class ParamFunc(IntEnum):
    """
    Function modifier for parameters.

    LOG2 - log2(Parameter)
    POW2 - 2^(Parameter)
    POW2M1 - 2^(Parameter-1)
    """

    NONE = 0
    LOG2 = 1
    POW2 = 2
    POW2M1 = 3


class ResetType(IntEnum):
    """
    Reset type.

    Resets can be numerical (constants), from an input signal, or from a
    parameter.

    """

    NUMERIC = 0
    INPUT = 1
    PARAMETER = 2


class InputFunction(IntEnum):
    """
    Action taken on control signal.

    Control signals can set or clear bits, serve as a parallel load,
    or an assignment value.
    """

    SET_BITS = 0
    CLEAR_BITS = 1
    PARALLEL = 2
    ASSIGNMENT = 3


class ShareType(IntEnum):
    """
    Shared register type.

    Shared registers allow for two different registers to be a the same address
    as long as one register is read only and the other register is write only.

    """

    NONE = 0
    READ = 1
    WRITE = 2
