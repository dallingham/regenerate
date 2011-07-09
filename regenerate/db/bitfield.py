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

This class makes extensive use of the 'property' feature in python. This
feature allows us to use a named property like a class variable. When accessed,
it calls the set/get function to handle any processing needed.
"""

from data_item import DataItem


def clean_signal(name):
    """
    Removes white space from a string, replacing them with underscores.
    """
    return "_".join(name.strip().split())


class BitField(DataItem):
    """
    BitField - holds all the data related to a bit field (one or more bits
    of a register)
    """

    (READ_ONLY, READ_WRITE, WRITE_1_TO_CLEAR,
     WRITE_1_TO_SET, WRITE_ONLY) = range(5)

    (ONE_SHOT_NONE, ONE_SHOT_ANY, ONE_SHOT_ONE,
     ONE_SHOT_ZERO, ONE_SHOT_TOGGLE) = range(5)

    (FUNC_SET_BITS, FUNC_CLEAR_BITS, FUNC_PARALLEL,
     FUNC_ASSIGNMENT) = range(4)

    (RESET_NUMERIC, RESET_INPUT, RESET_PARAMETER) = range(3)

    __slots__ = ('start_position', 'stop_position', 'field_name',
                 'use_output_enable', '__output_signal', '__input_signal',
                 'field_type', 'reset_value', 'reset_input', 'reset_type',
                 'reset_parameter', 'one_shot_type', 'input_function',
                 'description', 'control_signal', 'output_is_static',
                 'output_has_side_effect', 'values' )

    def __init__(self, stop=0, start=0, name="",
                 sig_type=READ_ONLY, descr="", reset=0):

        DataItem.__init__(self)

        self.__output_signal = ""
        self.__input_signal = ""

        self.start_position = start
        self.stop_position = stop
        self.field_name = name
        self.use_output_enable = False
        self.field_type = sig_type
        self.reset_value = reset
        self.reset_input = ""
        self.reset_type = BitField.RESET_NUMERIC
        self.reset_parameter = ""
        self.one_shot_type = BitField.ONE_SHOT_NONE
        self.input_function = BitField.FUNC_ASSIGNMENT
        self.description = descr
        self.control_signal = ""
        self.output_is_static = False
        self.output_has_side_effect = False
        self.values = []

    def is_constant(self):
        """
        Indicates the the value is a constant value.
        """
        return (self.field_type == BitField.READ_ONLY and
                self.input_function != BitField.FUNC_PARALLEL)

    def __get_width(self):
        """
        Returns the width in bits of the bit field.
        """
        return self.stop_position - self.start_position + 1

    width = property(__get_width, None, None, "Width of the data field")

    def __set_output_signal(self, output):
        """
        Sets the output signal associated with the bit range.
        """
        self.__output_signal = clean_signal(output)

    def __get_output_signal(self):
        """
        Gets the output signal associated with the bit range. If the user has
        not specified the name, assume that it is the same as the name of the
        bit field.
        """
        if self.__output_signal:
            return self.__output_signal
        else:
            return clean_signal(self.field_name)

    output_signal = property(__get_output_signal, __set_output_signal,
                            None, "Name of the output signal")

    def __set_input_signal(self, input_signal):
        """
        Sets the name of the input signal.
        """
        self.__input_signal = clean_signal(input_signal)

    def __get_input_signal(self):
        """
        Gets the name of the input signal, if it exists.
        """
        return self.__input_signal

    input_signal = property(__get_input_signal, __set_input_signal,
                           None, "Name of the input signal")
