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

    (TYPE_READ_ONLY, TYPE_READ_ONLY_VALUE, TYPE_READ_ONLY_LOAD,
     TYPE_READ_ONLY_CLEAR_LOAD, TYPE_READ_ONLY_VALUE_1S, TYPE_READ_WRITE,
     TYPE_READ_WRITE_1S, TYPE_READ_WRITE_1S_1, TYPE_READ_WRITE_LOAD,
     TYPE_READ_WRITE_LOAD_1S, TYPE_READ_WRITE_LOAD_1S_1, TYPE_READ_WRITE_SET,
     TYPE_READ_WRITE_SET_1S, TYPE_READ_WRITE_SET_1S_1, TYPE_READ_WRITE_CLR,
     TYPE_READ_WRITE_CLR_1S, TYPE_READ_WRITE_CLR_1S_1,
     TYPE_WRITE_1_TO_CLEAR_SET, TYPE_WRITE_1_TO_CLEAR_SET_1S,
     TYPE_WRITE_1_TO_CLEAR_SET_1S_1, TYPE_WRITE_1_TO_CLEAR_LOAD,
     TYPE_WRITE_1_TO_CLEAR_LOAD_1S, TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1,
     TYPE_WRITE_1_TO_SET, TYPE_WRITE_1_TO_SET_1S, TYPE_WRITE_1_TO_SET_1S1,
     TYPE_WRITE_ONLY, TYPE_READ_WRITE_RESET_ON_COMP, TYPE_READ_WRITE_PROTECT,
     TYPE_READ_WRITE_PROTECT_1S, TYPE_WRITE_1_TO_CLEAR_SET_CLR) = range(31)

    (FUNC_SET_BITS, FUNC_CLEAR_BITS, FUNC_PARALLEL, FUNC_ASSIGNMENT) = range(4)

    (ONE_SHOT_NONE, ONE_SHOT_ANY, ONE_SHOT_ONE, ONE_SHOT_ZERO,
     ONE_SHOT_TOGGLE) = range(5)

    (RESET_NUMERIC, RESET_INPUT, RESET_PARAMETER) = range(3)

    full_compare = ("_output_signal", "_input_signal", "_id", "lsb", "msb",
                    "_field_name", "use_output_enable", "field_type",
                    "volatile", "is_error_field", "reset_value", "reset_input",
                    "reset_type", "reset_parameter", "description",
                    "control_signal", "output_is_static",
                    "output_has_side_effect", "values")

    doc_compare = ("_id", "lsb", "msb", "_field_name", "field_type",
                   "is_error_field", "reset_value", "reset_input",
                   "reset_type", "reset_parameter", "description", "values")

    def __init__(self, stop=0, start=0):

        self.modified = False
        self._output_signal = ""
        self._input_signal = ""
        self._id = ""
        self.lsb = start
        self.msb = stop
        self._field_name = ""
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
        return all(self.__dict__[i] == other.__dict__[i]
                   for i in self.full_compare)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        return cmp(self.msb, other.msb)

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
            return self._field_name
        else:
            return "%s[%d:%d]" % (self._field_name, self.msb, self.lsb)

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
        if not self._id:
            self._id = uuid.uuid4().hex
        return self._id

    @uuid.setter
    def uuid(self, value):
        self._id = value

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
    def field_name(self):
        return self._field_name

    @field_name.setter
    def field_name(self, value):
        self._field_name = value.strip()

    @property
    def output_signal(self):
        """
        Gets the output signal associated with the bit range. If the user has
        not specified the name, assume that it is the same as the name of the
        bit field.
        """
        if self._output_signal:
            return self._output_signal
        else:
            return clean_signal(self._field_name)

    @output_signal.setter
    def output_signal(self, output):
        """
        Sets the output signal associated with the bit range.
        """
        self._output_signal = clean_signal(output)

    @property
    def input_signal(self):
        """
        Gets the name of the input signal, if it exists.
        """
        return self._input_signal

    @input_signal.setter
    def input_signal(self, input_signal):
        """
        Sets the name of the input signal.
        """
        self._input_signal = clean_signal(input_signal)
