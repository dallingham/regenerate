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
Provides the definition of a Bit Field,
"""

import uuid


def clean_signal(name):
    "Removes white space from a string, replacing them with underscores."
    return "_".join(name.strip().split())


class BitField(object):
    """
    BitField - holds all the data related to a bit field (one or more bits
    of a register)
    """

    (TYPE_READ_ONLY,
     TYPE_READ_ONLY_VALUE,
     TYPE_READ_ONLY_LOAD,
     TYPE_READ_ONLY_CLEAR_LOAD,
     TYPE_READ_ONLY_VALUE_1S,
     TYPE_READ_WRITE,
     TYPE_READ_WRITE_1S,
     TYPE_READ_WRITE_1S_1,
     TYPE_READ_WRITE_LOAD,
     TYPE_READ_WRITE_LOAD_1S,
     TYPE_READ_WRITE_LOAD_1S_1,
     TYPE_READ_WRITE_SET,
     TYPE_READ_WRITE_SET_1S,
     TYPE_READ_WRITE_SET_1S_1,
     TYPE_READ_WRITE_CLR,
     TYPE_READ_WRITE_CLR_1S,
     TYPE_READ_WRITE_CLR_1S_1,
     TYPE_WRITE_1_TO_CLEAR_SET,
     TYPE_WRITE_1_TO_CLEAR_SET_1S,
     TYPE_WRITE_1_TO_CLEAR_SET_1S_1,
     TYPE_WRITE_1_TO_CLEAR_LOAD,
     TYPE_WRITE_1_TO_CLEAR_LOAD_1S,
     TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1,
     TYPE_WRITE_1_TO_SET,
     TYPE_WRITE_1_TO_SET_1S,
     TYPE_WRITE_1_TO_SET_1S1,
     TYPE_WRITE_ONLY,
     TYPE_READ_WRITE_RESET_ON_COMP,
     TYPE_READ_WRITE_PROTECT,
     TYPE_READ_WRITE_PROTECT_1S) = range(30)

    (FUNC_SET_BITS, FUNC_CLEAR_BITS, FUNC_PARALLEL, FUNC_ASSIGNMENT) = range(4)

    (ONE_SHOT_NONE, ONE_SHOT_ANY, ONE_SHOT_ONE,
     ONE_SHOT_ZERO, ONE_SHOT_TOGGLE) = range(5)

    (RESET_NUMERIC, RESET_INPUT, RESET_PARAMETER) = range(3)

    def __init__(self, stop=0, start=0):

        self.modified = False
        self.__output_signal = ""
        self.__input_signal = ""
        self.__id = ""
        self.lsb = start
        self.msb = stop
        self.field_name = ""
        self.use_output_enable = False
        self.field_type = BitField.TYPE_READ_ONLY
        self.volatile = False
        self.is_error_field = False
        self.reset_value = 0
        self.reset_input = ""
        self.reset_type = BitField.RESET_NUMERIC
        self.reset_parameter = ""
        self.description = ""
        self.control_signal = ""
        self.output_is_static = False
        self.output_has_side_effect = False
        self.values = []

    def __eq__(self, other):
        if self.__output_signal != other.__output_signal:
            return False
        if self.__input_signal != other.__input_signal:
            return False
        if (self.lsb, self.msb) != (other.lsb, other.msb):
            return False
        if self.field_name != other.field_name:
            return False
        if self.use_output_enable != other.use_output_enable:
            return False
        if self.field_type != other.field_type:
            return False
        if self.volatile != other.volatile:
            return False
        if self.is_error_field != other.is_error_field:
            return False
        if self.reset_value != other.reset_value:
            return False
        if self.reset_input != other.reset_input:
            return False
        if self.reset_type != other.reset_type:
            return False
        if self.reset_parameter != other.reset_parameter:
            return False
        if self.description != other.description:
            return False
        if self.control_signal != other.control_signal:
            return False
        if self.output_is_static != other.output_is_static:
            return False
        if self.output_has_side_effect != other.output_has_side_effect:
            return False
        if self.values != other.values:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_constant(self):
        """
        Indicates the the value is a constant value.
        """
        return (self.field_type == BitField.TYPE_READ_ONLY or
                self.field_type == BitField.TYPE_READ_ONLY_LOAD)

    def full_field_name(self):
        """
        Builds the name of the field, including bit positions if needed
        """
        if self.width == 1:
            return self.field_name
        else:
            return "%s[%d:%d]" % (self.field_name, self.msb, self.lsb)

    def bit_range(self):
        """
        Retruns the bit range of the field
        """
        if self.width == 1:
            return "%d" % self.lsb
        else:
            return "[%d:%d]" % (self.msb, self.lsb)

    @property
    def uuid(self):
        if not self.__id:
            self.__id = uuid.uuid4().hex
        return self.__id

    @uuid.setter
    def uuid(self, value):
        self.__id = value

    @property
    def stop_position(self):
        """Returns the most significant bit of the field."""
        return self.msb

    @stop_position.setter
    def stop_position(self, value):
        """Sets the most significant bit of the field."""
        self.msb = value

    @property
    def start_position(self):
        """Returns the least significant bit of the field."""
        return self.lsb

    @start_position.setter
    def start_position(self, value):
        """Sets the least significant bit of the field."""
        self.lsb = value

    @property
    def width(self):
        """Returns the width in bits of the bit field."""
        return self.msb - self.lsb + 1

    @property
    def output_signal(self):
        """
        Gets the output signal associated with the bit range. If the user has
        not specified the name, assume that it is the same as the name of the
        bit field.
        """
        if self.__output_signal:
            return self.__output_signal
        else:
            return clean_signal(self.field_name)

    @output_signal.setter
    def output_signal(self, output):
        """
        Sets the output signal associated with the bit range.
        """
        self.__output_signal = clean_signal(output)

    @property
    def input_signal(self):
        """
        Gets the name of the input signal, if it exists.
        """
        return self.__input_signal

    @input_signal.setter
    def input_signal(self, input_signal):
        """
        Sets the name of the input signal.
        """
        self.__input_signal = clean_signal(input_signal)
