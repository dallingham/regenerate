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
Provides the definition of a Bit Field.
"""

from typing import List, Optional, Dict, Any
from .name_base import NameBase, Uuid
from .enums import BitType, ResetType
from .bit_values import BitValues
from .param_value import ParamValue
from .param_data import ParameterFinder
from .param_resolver import ParameterResolver
from .json_base import JSONEncodable


def clean_signal(name: str) -> str:
    "Remove white space from a string, replacing them with underscores."
    return "_".join(name.strip().split())


class BitFieldFlags(JSONEncodable):
    "Flags for the bit field"

    def __init__(self):
        "Initialize the flags"

        self.is_error_field: bool = False
        self.can_randomize: bool = False
        self.volatile: bool = False

    def __eq__(self, other: object) -> bool:
        "Check for equality"

        if not isinstance(other, BitFieldFlags):
            return NotImplemented
        return (
            self.is_error_field == other.is_error_field
            and self.can_randomize == other.can_randomize
            and self.volatile == other.volatile
        )


class BitField(NameBase):
    """Holds all the data of a bit field (one or more bits of a register)."""

    PARAMETERS = {}  # type: ignore

    read_only_types = (
        BitType.READ_ONLY,
        BitType.READ_ONLY_VALUE,
        BitType.READ_ONLY_LOAD,
        BitType.READ_ONLY_CLEAR_LOAD,
        BitType.READ_ONLY_VALUE_1S,
    )

    write_only_types = (BitType.WRITE_ONLY,)

    _full_compare = (
        "_input_signal",
        "_output_signal",
        "_reset_value",
        "control_signal",
        "field_type",
        "lsb",
        "msb",
        "output_has_side_effect",
        "output_is_static",
        "reset_input",
        "reset_parameter",
        "reset_type",
        "use_output_enable",
        "use_alternate_reset",
        "values",
    )

    _doc_compare = (
        "_reset_value",
        "field_type",
        "lsb",
        "msb",
        "reset_input",
        "reset_parameter",
        "reset_type",
        "values",
    )

    __slots__ = (
        "_input_signal",
        "_output_signal",
        "_reset_value",
        "control_signal",
        "field_type",
        "lsb",
        "modified",
        "_msb",
        "output_has_side_effect",
        "output_is_static",
        "reset_input",
        "reset_parameter",
        "reset_type",
        "use_alternate_reset",
        "use_output_enable",
        "values",
    )

    def __init__(self, stop: int = 0, start: int = 0):
        """Initialize the bitfield."""

        super().__init__("", Uuid(""))
        self.modified = False

        self._input_signal = ""
        self.control_signal = ""

        self.field_type = BitType.READ_ONLY

        self.flags: BitFieldFlags = BitFieldFlags()

        self.lsb = start
        self._msb = ParamValue(stop)

        self._output_signal = ""
        self.output_has_side_effect = False
        self.output_is_static = False
        self.use_output_enable = False
        self.use_alternate_reset = False

        self._reset_value = 0
        self.reset_input = ""
        self.reset_parameter = Uuid("")
        self.reset_type = ResetType.NUMERIC

        self.values: List[BitValues] = []

    def __repr__(self):
        "Returns the string representation"
        name = self.name
        msb = self.msb
        lsb = self.lsb
        ftype = str(self.field_type)
        return f"BitField(name={name}, id={self.uuid} msb={msb}, lsb={lsb}, field_type={ftype})"

    @property
    def msb(self) -> ParamValue:
        "Returns the MSB"

        return self._msb

    @msb.setter
    def msb(self, value: ParamValue) -> None:
        "Sets the MSB"

        self._msb = value

    # @staticmethod
    # def set_parameters(values) -> None:
    #     """Set the parameter value list."""
    #     print(type(values))
    #     BitField.PARAMETERS = values

    def __eq__(self, other: object) -> bool:
        """Compare for equality between two bitfieids."""

        if not isinstance(other, BitField):
            return NotImplemented
        return (
            all(
                getattr(self, i) == getattr(other, i)
                for i in self._full_compare
            )
            and self.flags == other.flags
        )

    def __ne__(self, other: object) -> bool:
        """Compare for inequality between two bitfields."""

        if not isinstance(other, BitField):
            return NotImplemented
        return not self.__eq__(other)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, BitField):
            return NotImplemented
        return self.lsb < other.lsb

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, BitField):
            return NotImplemented
        return self.lsb > other.lsb

    def is_constant(self) -> bool:
        """Indicate if the value is a constant value."""
        return self.field_type == BitType.READ_ONLY

    def is_read_only(self) -> bool:
        """Indicate if the value is a read only type."""
        return self.field_type in BitField.read_only_types

    def is_write_only(self) -> bool:
        """Indicate if the value is a write only type."""
        return self.field_type in BitField.write_only_types

    def full_field_name(self) -> str:
        """Build the name of the field, including bit positions if needed."""
        if self.width == 1:
            return self.name
        return f"{self.name}[{self.msb.resolve()}:{self.lsb}]"

    def bit_range(self) -> str:
        """Return the bit range of the field."""
        if self.width == 1:
            return str(self.lsb)
        return f"[{self.msb.resolve()}:{self.lsb}]"

    @property
    def reset_value(self) -> int:
        """
        Return the reset value. If the source is an input signal
        assume that the value is zero.
        """
        if self.reset_type == ResetType.PARAMETER:
            finder = ParameterFinder()
            resolver = ParameterResolver()
            param = finder.find(self.reset_parameter)
            if param:
                val = resolver.resolve(param)
                return val
            return 0
        if self.reset_type == ResetType.INPUT:
            return 0
        return self._reset_value

    @reset_value.setter
    def reset_value(self, value: int) -> None:
        """Set the reset value."""
        self._reset_value = value

    def reset_value_bit(self, bit: int) -> int:
        """Check for a bit to be set."""
        if self._reset_value & (1 << bit):
            return 1
        return 0

    def reset_string(self) -> Optional[str]:
        "Returns the reset value as a string"

        if self.reset_type == ResetType.PARAMETER:
            finder = ParameterFinder()
            param = finder.find(self.reset_parameter)
            if param:
                return param.name
            return ""
        if self.reset_type == ResetType.INPUT:
            return self.reset_input
        return hex(self._reset_value)

    def reset_vstr(self) -> Optional[str]:
        "Returns the reset value as a string in verilog format"

        if self.reset_type == ResetType.PARAMETER:
            finder = ParameterFinder()
            param = finder.find(self.reset_parameter)
            if param:
                return param.name
            return ""
        if self.reset_type == ResetType.INPUT:
            return self.reset_input
        if self.msb.is_parameter:
            return f"'h{self._reset_value:x}"
        return f"{self.width}'h{self._reset_value:x}"

    @property
    def stop_position(self) -> ParamValue:
        "Return the most significant bit of the field."
        return self.msb

    @stop_position.setter
    def stop_position(self, value: ParamValue) -> None:
        "Set the most significant bit of the field."
        self.msb = value

    @property
    def start_position(self) -> int:
        "Return the least significant bit of the field."
        return self.lsb

    @start_position.setter
    def start_position(self, value: int) -> None:
        "Set the least significant bit of the field."
        self.lsb = value

    @property
    def width(self) -> int:
        "Return the width in bits of the bit field."
        return self.msb.resolve() - self.lsb + 1

    def resolved_output_signal(self) -> str:
        """
        Get the output signal associated with the bit range.

        If the user has not specified the name, assume that it is the same as
        the name of the bit field.
        """
        nlist = self._output_signal.split("*")
        if len(nlist) == 1:
            return self._output_signal
        if self.msb == self.lsb:
            index = f"{self.lsb}"
        else:
            index = f"{self.msb}:{self.lsb}"
        return f"{nlist[0]}{index}{nlist[1]}"

    @property
    def output_signal(self) -> str:
        """
        Get the output signal associated with the bit range.

        If the user has not specified the name, assume that it is the same as
        the name of the bit field.
        """
        return self._output_signal

    @output_signal.setter
    def output_signal(self, output: str) -> None:
        "Set the output signal associated with the bit range."
        self._output_signal = clean_signal(output)

    @property
    def input_signal(self) -> str:
        "Get the name of the input signal, if it exists."
        return self._input_signal

    @input_signal.setter
    def input_signal(self, signal: str) -> None:
        "Set the name of the input signal."
        self._input_signal = clean_signal(signal)

    def json(self) -> Dict[str, Any]:
        "Converts the object to a JSON compatible dictionary"

        return {
            "name": self.name,
            "uuid": self.uuid,
            "description": self.description,
            "input_signal": self._input_signal,
            "output_signal": self._output_signal,
            "reset_value": f"{self._reset_value}",
            "control_signal": self.control_signal,
            "field_type": self.field_type,
            "lsb": self.lsb,
            "msb": self.msb.json(),
            "output_has_side_effect": self.output_has_side_effect,
            "output_is_static": self.output_is_static,
            "reset_input": self.reset_input,
            "reset_parameter": self.reset_parameter,
            "reset_type": self.reset_type,
            "use_output_enable": self.use_output_enable,
            "use_alternate_reset": self.use_alternate_reset,
            "values": self.values,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        "Decodes the JSON compatible dictionary into the object"

        self.name = data["name"]
        self.uuid = Uuid(data["uuid"])
        self.description = data["description"]

        self._input_signal = data["input_signal"]
        self.control_signal = data["control_signal"]

        self._output_signal = data["output_signal"]
        self.use_output_enable = data["use_output_enable"]
        self.use_alternate_reset = data.get("use_alternate_reset", False)
        self.field_type = data["field_type"]
        self.lsb = data["lsb"]
        self.msb = ParamValue()
        self.msb.json_decode(data["msb"])
        self.output_has_side_effect = data["output_has_side_effect"]
        self.output_is_static = data["output_is_static"]

        self._reset_value = int(data["reset_value"], 0)
        self.reset_input = data["reset_input"]
        rst_param = data["reset_parameter"]
        if rst_param is None:
            self.reset_parameter = Uuid("")
        else:
            self.reset_parameter = Uuid(rst_param)

        self.reset_type = data["reset_type"]

        self.values = []
        for value_json in data["values"]:
            bitval = BitValues()
            bitval.json_decode(value_json)
            self.values.append(bitval)
