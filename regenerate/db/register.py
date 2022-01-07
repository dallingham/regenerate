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
Provides the register description.

Contains the general information about the register, including the
list of bit fields.
"""

from typing import List, Dict, Optional, Any
from .name_base import NameBase, Uuid
from .enums import ResetType, ShareType
from .bitfield import BitField
from .parameters import ParameterValue, ParameterContainer

# from .param_container import ParameterContainer
from .register_flags import RegisterFlags


class Register(NameBase):
    """Defines a hardware register."""

    _full_compare = (
        "address",
        "ram_size",
        "width",
        "_token",
        "flags",
        "dimension",
    )

    _array_compare = (
        "ram_size",
        "width",
        "share",
    )

    _doc_compare = (
        "address",
        "ram_size",
        "width",
        "_token",
        "dimension",
    )

    def __init__(self, address: int = 0, width: int = 32, name: str = ""):
        """
        Initialize the register.

        Parameters:
            address (int): address of the register
            width (int): width of the register in bits
            name (str): name of the register

        """
        super().__init__(name, Uuid(""))

        self.dimension = ParameterValue(1)
        self._token = ""
        self._bit_fields: Dict[int, BitField] = {}
        self._parameter_list: ParameterContainer = ParameterContainer()

        self.flags = RegisterFlags()
        self.address = address
        self.ram_size = 0
        self.width = width
        self.regset_name: Optional[str] = None
        self.share = ShareType.NONE

    def __repr__(self) -> str:
        """
        Return the string representation of the object.

        Returns:
            str: string representing the object

        """
        name = self.name
        address = self.address
        width = self.width
        dim = self.dimension
        return f'Register(name="{name}", address=0x{address:x}, width={width}, dimension={dim})'

    def __hash__(self) -> int:
        """
        Provide the hash function so that the object can be hashed.

        Returns:
            int: Returns the hash value of the UUID.

        """
        return hash(self.uuid)

    def __ne__(self, other: object) -> bool:
        """
        Compare for inequality.

        Parameters:
            other (object): Object to compare against

        Returns:
            bool: True if not equal

        """
        if not isinstance(other, Register):
            return NotImplemented
        return not self.__eq__(other)

    def __eq__(self, other: object) -> bool:
        """
        Compare for equality.

        Parameters:
            other (object): Object to compare against

        Returns:
            bool: True if equal

        """
        if not isinstance(other, Register):
            return NotImplemented
        if not all(
            getattr(self, i) == getattr(other, i) for i in self._full_compare
        ):
            return False
        return self.get_bit_fields() == other.get_bit_fields()

    def array_cmp(self, other: object) -> bool:
        """
        Array compare.

        Parameters:
            other (object): Object to compare against

        Returns:
            bool: True if equal

        """
        if not isinstance(other, Register):
            return NotImplemented

        if other is None:
            return False
        if not all(
            getattr(self, i) == getattr(other, i) for i in self._array_compare
        ):
            return False
        if other.address + (other.width // 8) != self.address:
            return False
        return self.get_bit_fields() == other.get_bit_fields()

    def group_cmp(self, other: object) -> bool:
        """
        Group compare.

        Parameters:
            other (object): Object to compare against

        Returns:
            bool: True if equal

        """
        if not isinstance(other, Register):
            return NotImplemented
        if not all(
            getattr(self, i) == getattr(other, i) for i in self._array_compare
        ):
            return False
        return self.get_bit_fields() == other.get_bit_fields()

    def find_first_unused_bit(self) -> int:
        """
        Find the first unused bit in the register.

        Returns:
            int: index of the first unused bit, -1 if no bit unused

        """
        bit_list = [0] * self.width
        for field in self._bit_fields.values():
            for val in range(field.lsb, field.msb.resolve() + 1):
                bit_list[val] = 1
        for pos in range(0, self.width):
            if bit_list[pos] == 0:
                return pos

        bit_set = set()
        for field in self._bit_fields.values():
            for val in range(field.lsb, field.msb.resolve() + 1):
                bit_set.add(val)
        all_bits = set(range(0, self.width))
        sorted_bits = sorted(list(bit_set.difference(all_bits)))
        if sorted_bits:
            return sorted_bits[0]
        return -1

    def find_next_unused_bit(self) -> int:
        """
        Find the first unused bit at the end of the register.

        Returns:
            int: index of the first unused bit, -1 if no bit unused

        """
        bit = set()
        for field in self._bit_fields.values():
            for val in range(field.lsb, field.msb.resolve() + 1):
                bit.add(val)
        lbits = sorted(list(bit))

        if lbits:
            if lbits[-1] == self.width - 1:
                return self.find_first_unused_bit()
            return lbits[-1] + 1
        return 0

    @property
    def token(self) -> str:
        """
        Return the value of the token value.

        Returns:
            str: token value of the register

        """
        return self._token

    @token.setter
    def token(self, val: str) -> None:
        """
        Set the token value.

        Strips off any ending spaces and converts the value to all caps.

        """
        self._token = val.strip().upper()

    def get_bit_fields_with_values(self) -> List[BitField]:
        """
        Returns a dictionary of bit fields. The key is msb of the
        bit field.
        """
        return sorted(
            [s for s in self._bit_fields.values() if s.values],
            key=lambda x: x.lsb,
        )

    def get_bit_fields(self) -> List[BitField]:
        """
        Return the bit fields.

        Returns:
           List[BitFields]: list of the associated bit fields sorted by LSB

        """
        return sorted(self._bit_fields.values(), key=lambda x: x.lsb)

    # def get_bit_fields_with_values(self) -> List[BitField]:
    #     """
    #     Returns a dictionary of bit fields. The key is msb of the
    #     bit field.
    #     """
    #     return sorted(
    #         [s for s in self._bit_fields.values() if s.values],
    #         key=lambda x: x.lsb,
    #     )

    def get_bit_field(self, key: int) -> Optional[BitField]:
        """
        Return the bit field associated with the specified key.

        The key is the MSB of the bit field.

        Returns:
            Optional[BitField]: bit field associated with the LSB, or None

        """
        return self._bit_fields.get(key)

    def get_bit_field_keys(self) -> List[int]:
        """
        Return the list of keys associated with the bit fields.

        Returns:
            List[int]: sorted list of bit field keys (LSBs)

        """
        return sorted(self._bit_fields.keys())

    def add_bit_field(self, field: BitField) -> None:
        """
        Add a bit field to the set of bit fields.

        Adds the bit field using the field's LSB as the key.

        Parameters:
            field (BitField): bit field to add

        """
        self._bit_fields[field.lsb] = field

    def change_bit_field(self, field: BitField) -> None:
        """
        Move the bit field to a different index.

        Parameters:
            field (BitField): bit field to change

        """
        remove_val = None
        for current_field in self._bit_fields:
            if field == self._bit_fields[current_field]:
                remove_val = current_field

        if remove_val is not None:
            del self._bit_fields[remove_val]
        self._bit_fields[field.lsb] = field

    def delete_bit_field(self, field: BitField) -> None:
        """
        Remove the specified bit field from the register.

        Parameters:
            field (BitField): bit field to remove

        """
        delete_keys = [
            key for key in self._bit_fields if self._bit_fields[key] == field
        ]
        for key in delete_keys:
            del self._bit_fields[key]

    def is_completely_read_only(self) -> bool:
        """
        Indicate if all bits in the register are read only.

        Returns:
            bool: True if all bitfields are read only

        """
        for key in self._bit_fields:
            if not self._bit_fields[key].is_read_only():
                return False
        return True

    def is_completely_write_only(self) -> bool:
        """
        Indicate if all bits in the register are write only.

        Returns:
            bool: True if all bitfields are write only

        """
        for key in self._bit_fields:
            if not self._bit_fields[key].is_write_only():
                return False
        return True

    def no_reset_test(self) -> bool:
        """
        Indicate if no reset test should be done on the register.

        Returns:
            bool: True if the register should not be tested

        """
        if self.flags.do_not_reset_test:
            return True
        for key in self._bit_fields:
            if self._bit_fields[key].reset_type != ResetType.NUMERIC:
                return True
        return False

    def strict_volatile(self) -> bool:
        """
        Indicate if the register may have a different value between reads.

        Returns:
            bool: True if a field is marked as volatile or if there is an
                  input signal specified

        """
        for key in self._bit_fields:
            field = self._bit_fields[key]
            if field.flags.volatile or field.input_signal != "":
                return True
        return False

    def loose_volatile(self) -> bool:
        """
        Indicate if the register may have a different value between reads.

        Returns:
            bool: True if a field is marked as volatile

        """
        for key in self._bit_fields:
            if self._bit_fields[key].flags.volatile:
                return True
        return False

    def reset_value(self) -> int:
        """
        Return the reset value for the register.

        Builds the reset values from the bit fields.

        Returns:
            int: reset value of the register

        """
        val = 0
        for key in self._bit_fields:
            field = self._bit_fields[key]
            val |= field.reset_value << field.lsb
        return val

    def reset_mask(self) -> int:
        """
        Return a mask of the active fields (not reserved fields).

        Returns:
            int: reset mask

        """
        val = 0
        for key in self._bit_fields:
            field = self._bit_fields[key]
            for i in range(field.lsb, field.msb.resolve() + 1):
                val |= 1 << i
        return val

    def set_parameters(self, parameter_list: ParameterContainer) -> None:
        """
        Set the parameter list.

        Parameters:
            parameter_list (ParameterContainer): Parameters associated with
                the register

        """
        self._parameter_list = parameter_list

    def json(self) -> Dict[str, Any]:
        """
        Convert the object to a JSON compatible dictionary.

        Returns:
            Dict[str, Any]: dictionary in JSON format

        """
        val = {
            "name": self.name,
            "uuid": self.uuid,
            "description": self.description,
            "token": self._token,
            "address": f"{self.address}",
            "flags": self.flags.json(),
            "ram_size": self.ram_size,
            "share": self.share,
            "width": self.width,
            "bitfields": [
                field.json() for index, field in self._bit_fields.items()
            ],
        }
        val["dimension"] = self.dimension.json()
        return val

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Load the object from JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data describing the object

        """
        self.name = data["name"]
        self.uuid = Uuid(data["uuid"])
        self.description = data["description"]
        self.dimension = ParameterValue()
        self.dimension.json_decode(data["dimension"])

        self._token = data["token"]
        self.address = int(data["address"], 0)

        self.flags = RegisterFlags()
        self.flags.json_decode(data["flags"])

        self.ram_size = data["ram_size"]
        self.share = ShareType(data["share"])
        self.width = data["width"]

        self._bit_fields = {}
        for field_json in data["bitfields"]:
            field = BitField()
            field.json_decode(field_json)
            self._bit_fields[field.lsb] = field
