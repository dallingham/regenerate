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

"""Provides the definition of a Bit Field."""

import uuid
from regenerate.db.enums import BitType, ResetType


def clean_signal(name):
    """Remove white space from a string, replacing them with underscores."""
    return "_".join(name.strip().split())


class BitField:
    """Holds all the data of a bit field (one or more bits of a register)."""

    PARAMETERS = {}

    read_only_types = (
        BitType.READ_ONLY,
        BitType.READ_ONLY_VALUE,
        BitType.READ_ONLY_LOAD,
        BitType.READ_ONLY_CLEAR_LOAD,
        BitType.READ_ONLY_VALUE_1S,
    )

    write_only_types = (BitType.WRITE_ONLY,)

    full_compare = (
        "_field_name",
        "_id",
        "_input_signal",
        "_output_signal",
        "_reset_value",
        "control_signal",
        "description",
        "field_type",
        "is_error_field",
        "lsb",
        "msb",
        "output_has_side_effect",
        "output_is_static",
        "reset_input",
        "reset_parameter",
        "reset_type",
        "use_output_enable",
        "values",
        "volatile",
    )

    doc_compare = (
        "_field_name",
        "_id",
        "_reset_value",
        "description",
        "field_type",
        "is_error_field",
        "lsb",
        "msb",
        "reset_input",
        "reset_parameter",
        "reset_type",
        "values",
    )

    __slots__ = (
        "_field_name",
        "_id",
        "_input_signal",
        "_output_signal",
        "_reset_value",
        "can_randomize",
        "control_signal",
        "description",
        "field_type",
        "is_error_field",
        "lsb",
        "modified",
        "msb",
        "output_has_side_effect",
        "output_is_static",
        "reset_input",
        "reset_parameter",
        "reset_type",
        "use_output_enable",
        "values",
        "volatile",
    )

    def __init__(self, stop=0, start=0):
        """Initialize the bitfield."""
        self.modified = False
        self._output_signal = ""
        self._input_signal = ""
        self._id = ""
        self.lsb = start
        self.msb = stop
        self._field_name = ""
        self.use_output_enable = False
        self.field_type = BitType.READ_ONLY
        self.volatile = False
        self.is_error_field = False
        self._reset_value = 0
        self.reset_input = ""
        self.reset_type = ResetType.NUMERIC
        self.reset_parameter = ""
        self.description = ""
        self.can_randomize = False
        self.control_signal = ""
        self.output_is_static = False
        self.output_has_side_effect = False
        self.values = []

    @staticmethod
    def set_parameters(values):
        """Set the parameter value list."""
        BitField.PARAMETERS = values

    def __eq__(self, other):
        """Compare for equality between two bitfieids."""
        return all(
            self.__dict__[i] == other.__dict__[i] for i in self.full_compare
        )

    def __ne__(self, other):
        """Compare for inequality between two bitfields."""
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.lsb < other.lsb

    def __gt__(self, other):
        return self.lsb > other.lsb

    def is_constant(self):
        """Indicate if the value is a constant value."""
        return self.field_type == BitType.READ_ONLY

    def is_read_only(self):
        """Indicate if the value is a read only type."""
        return self.field_type in BitField.read_only_types

    def is_write_only(self):
        """Indicate if the value is a write only type."""
        return self.field_type in BitField.write_only_types

    def full_field_name(self):
        """Build the name of the field, including bit positions if needed."""
        if self.width == 1:
            return self._field_name
        return "%s[%d:%d]" % (self._field_name, self.msb, self.lsb)

    def bit_range(self):
        """Return the bit range of the field."""
        if self.width == 1:
            return str(self.lsb)
        return "[%d:%d]" % (self.msb, self.lsb)

    @property
    def reset_value(self):
        """Return the reset value."""
        if self.reset_type == ResetType.PARAMETER:
            return BitField.PARAMETERS.get(self.reset_parameter, 0)
        return self._reset_value

    @reset_value.setter
    def reset_value(self, value):
        """Set the reset value."""
        self._reset_value = value

    def reset_value_bit(self, bit):
        """Check for a bit to be set."""
        if self._reset_value & (1 << bit):
            return 1
        return 0

    @property
    def uuid(self):
        """Return the UUID for the bitfield."""
        if not self._id:
            self._id = uuid.uuid4().hex
        return self._id

    @uuid.setter
    def uuid(self, value):
        """Set the UUID for the bitfield."""
        self._id = value

    @property
    def stop_position(self):
        """Return the most significant bit of the field."""
        return self.msb

    @stop_position.setter
    def stop_position(self, value):
        """Set the most significant bit of the field."""
        self.msb = value

    @property
    def start_position(self):
        """Return the least significant bit of the field."""
        return self.lsb

    @start_position.setter
    def start_position(self, value):
        """Set the least significant bit of the field."""
        self.lsb = value

    @property
    def width(self):
        """Return the width in bits of the bit field."""
        return self.msb - self.lsb + 1

    @property
    def field_name(self):
        """Return the name of the fieid."""
        return self._field_name

    @field_name.setter
    def field_name(self, value):
        """Set the name of the fieid."""
        self._field_name = value.strip()

    @property
    def output_signal(self):
        """
        Get the output signal associated with the bit range.

        If the user has not specified the name, assume that it is the same as
        the name of the bit field.
        """
        return self._output_signal

    def resolved_output_signal(self):
        """
        Get the output signal associated with the bit range.

        If the user has not specified the name, assume that it is the same as
        the name of the bit field.
        """
        nlist = self._output_signal.split("*")
        if len(nlist) == 1:
            return self._output_signal
        if self.msb == self.lsb:
            index = "%d" % self.lsb
        else:
            index = "%d:%d" % (self.msb, self.lsb)
        return "%s%s%s" % (nlist[0], index, nlist[1])

    @output_signal.setter
    def output_signal(self, output):
        """Set the output signal associated with the bit range."""
        self._output_signal = clean_signal(output)

    @property
    def input_signal(self):
        """Get the name of the input signal, if it exists."""
        return self._input_signal

    @input_signal.setter
    def input_signal(self, input_signal):
        """Set the name of the input signal."""
        self._input_signal = clean_signal(input_signal)
