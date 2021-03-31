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
Provides the register description. Contains the general information about the
register, including the list of bit fields.
"""

from typing import List, Dict, Tuple, Optional
from .name_base import NameBase
from .enums import ResetType, ShareType
from .bitfield import BitField


class RegisterFlags:
    """
    Contains the flags that control file and documentation generation
    """

    __slots__ = (
        "_do_not_use_uvm",
        "_do_not_generate_code",
        "_do_not_cover",
        "_do_not_test",
        "_hide",
    )

    def __init__(self):
        self._do_not_use_uvm = False
        self._do_not_generate_code = False
        self._do_not_cover = False
        self._do_not_test = False
        self._hide = False

    @property
    def hide(self) -> bool:
        """
        Returns the value of the _hide flag. This cannot be accessed
        directly, but only via the property 'hide'
        """
        return self._hide

    @hide.setter
    def hide(self, val: bool) -> None:
        """
        Sets the __hide flag. This cannot be accessed directly, but only
        via the property 'hide'
        """
        self._hide = bool(val)

    @property
    def do_not_generate_code(self) -> bool:
        """
        Returns the value of the _do_not_generate_code flag. This cannot
        be accessed directly, but only via the property 'do_not_generate_code'
        """
        return self._do_not_generate_code

    @do_not_generate_code.setter
    def do_not_generate_code(self, val: bool) -> None:
        """
        Sets the __do_not_generate_code flag. This cannot be accessed
        directly, but only via the property 'do_not_generate_code'
        """
        self._do_not_generate_code = bool(val)

    @property
    def do_not_use_uvm(self) -> bool:
        """
        Returns the value of the _do_not_use_uvm flag. This cannot
        be accessed directly, but only via the property 'do_not_use_uvm'
        """
        return self._do_not_use_uvm

    @do_not_use_uvm.setter
    def do_not_use_uvm(self, val: bool) -> None:
        """
        Sets the __do_not_use_uvm flag. This cannot be accessed
        directly, but only via the property 'do_not_use_uvm'
        """
        self._do_not_use_uvm = bool(val)

    @property
    def do_not_test(self) -> bool:
        """
        Returns the value of the _do_not_test flag. This
        cannot be accessed directly, but only via the property 'do_not_test'
        """
        return self._do_not_test

    @do_not_test.setter
    def do_not_test(self, val: bool) -> None:
        """
        Sets the __do_not_test flag. This cannot be accessed
        directly, but only via the property 'do_not_test'
        """
        self._do_not_test = bool(val)

    @property
    def do_not_cover(self) -> bool:
        """
        Returns the value of the _do_not_cover flag. This
        cannot be accessed directly, but only via the property 'do_not_cover'
        """
        return self._do_not_cover

    @do_not_cover.setter
    def do_not_cover(self, val: bool) -> None:
        """
        Sets the __do_not_cover flag. This cannot be accessed
        directly, but only via the property 'do_not_cover'
        """
        self._do_not_cover = bool(val)


class Register(NameBase):
    """Defines a hardware register."""

    __slots__ = (
        "_bit_fields",
        "_dimension",
        "_plist",
        "_token",
        "address",
        "flags",
        "ram_size",
        "share",
        "width",
    )

    _full_compare = (
        "address",
        "ram_size",
        "width",
        "_token",
        "flags",
        "_dimension",
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
        "_dimension",
    )

    def __init__(self, address: int = 0, width: int = 32, name: str = ""):

        super().__init__(name, "")

        self._dimension = "1"
        self._token = ""
        self._bit_fields = {}  # type: Dict[int, BitField]
        self._plist = []  # type: List[Tuple[str, int, int, int]]

        self.flags = RegisterFlags()
        self.address = address
        self.ram_size = 0
        self.width = width

        self.share = ShareType.NONE

    def __hash__(self):
        """Provides the hash function so that the object can be hashed"""

        return hash(self.uuid)

    def __ne__(self, other) -> bool:
        """Provides the not equal function"""

        return not self.__eq__(other)

    def __eq__(self, other) -> bool:
        """Provides the equal function"""

        if not all(
            getattr(self, i) == getattr(other, i) for i in self._full_compare
        ):
            return False
        return self.get_bit_fields() == other.get_bit_fields()

    def array_cmp(self, other) -> bool:
        """Array compare"""

        if other is None:
            return False
        if not all(
            getattr(self, i) == getattr(other, i) for i in self._array_compare
        ):
            return False
        if other.address + (other.width // 8) != self.address:
            return False
        return self.get_bit_fields() == other.get_bit_fields()

    def group_cmp(self, other) -> bool:
        "Group compare"

        if not all(
            getattr(self, i) == getattr(other, i) for i in self._array_compare
        ):
            return False
        return self.get_bit_fields() == other.get_bit_fields()

    def find_first_unused_bit(self) -> int:
        """Finds the first unused bit in a the register."""

        bit_list = [0] * self.width
        for field in self._bit_fields.values():
            for val in range(field.lsb, field.msb + 1):
                bit_list[val] = 1
        for pos in range(0, self.width):
            if bit_list[pos] == 0:
                return pos

        bit_set = set()
        for field in self._bit_fields.values():
            for val in range(field.lsb, field.msb + 1):
                bit_set.add(val)
        all_bits = set(range(0, self.width))
        sorted_bits = sorted(list(bit_set.difference(all_bits)))
        if sorted_bits:
            return sorted_bits[0]
        return -1

    def find_next_unused_bit(self) -> int:
        """Finds the first unused bit in a the register."""

        bit = set()
        for field in self._bit_fields.values():
            for val in range(field.lsb, field.msb + 1):
                bit.add(val)
        lbits = sorted(list(bit))

        if lbits:
            if lbits[-1] == self.width - 1:
                return self.find_first_unused_bit()
            return lbits[-1] + 1
        return 0

    def dimension_is_param(self) -> bool:
        """Determines if the dimension is an int or parameter"""

        try:
            _ = int(self._dimension, 0)
            return False
        except ValueError:
            return True

    @property
    def dimension(self) -> int:
        """
        Returns the dimension as an integer, resolving the parameter
        value if it exists.
        """

        try:
            return int(self._dimension)
        except ValueError:
            if self._plist:
                for (name, value, _, _) in self._plist:
                    if name == self._dimension:
                        return value
            return 1

    @dimension.setter
    def dimension(self, value) -> None:
        """Sets the dimension as a string"""
        self._dimension = str(value)

    @property
    def dimension_str(self) -> str:
        """Returns the dimension as a string, not resolving parameters"""
        return self._dimension

    @property
    def token(self) -> str:
        """
        Returns the value of the _token flag. This cannot be accessed
        directly, but only via the property 'token'
        """
        return self._token

    @token.setter
    def token(self, val: str) -> None:
        """
        Sets the __token flag. This cannot be accessed directly, but only
        via the property 'token'
        """
        self._token = val.strip().upper()

    def get_bit_fields(self) -> List[BitField]:
        """
        Returns a dictionary of bit fields. The key is msb of the
        bit field.
        """
        return sorted(self._bit_fields.values(), key=lambda x: x.lsb)

    def get_bit_fields_with_values(self) -> List[BitField]:
        """
        Returns a dictionary of bit fields. The key is msb of the
        bit field.
        """
        return sorted(
            [s for s in self._bit_fields.values() if s.values],
            key=lambda x: x.lsb,
        )

    def get_bit_field(self, key: int) -> Optional[BitField]:
        """Returns the bit field associated with the specified key."""
        return self._bit_fields.get(key)

    def get_bit_field_keys(self) -> List[int]:
        """Returns the list of keys associated with the bit fields"""
        return sorted(self._bit_fields.keys())

    def add_bit_field(self, field: BitField) -> None:
        """Adds a bit field to the set of bit fields."""
        self._bit_fields[field.lsb] = field

    def change_bit_field(self, field: BitField) -> None:
        """Adds a bit field to the set of bit fields."""
        remove_val = None
        for current_field in self._bit_fields:
            if field == self._bit_fields[current_field]:
                remove_val = current_field

        if remove_val is not None:
            del self._bit_fields[remove_val]
        self._bit_fields[field.lsb] = field

    def delete_bit_field(self, field: BitField) -> None:
        """
        Removes the specified bit field from the dictionary. We cannot
        use the msb, since it may have changed.
        """
        delete_keys = [
            key for key in self._bit_fields if self._bit_fields[key] == field
        ]
        for key in delete_keys:
            del self._bit_fields[key]

    def is_completely_read_only(self) -> bool:
        """Returns True if all bitfields are read only"""

        for key in self._bit_fields:
            if not self._bit_fields[key].is_read_only():
                return False
        return True

    def is_completely_write_only(self) -> bool:
        """Returns True if all bitfields are write only"""

        for key in self._bit_fields:
            if not self._bit_fields[key].is_write_only():
                return False
        return True

    def no_reset_test(self) -> bool:
        """
        Indicates if no reset test should be done on the register.
        If any field is a don't test, then we won't test the register
        """
        if self.flags.do_not_test:
            return True
        for key in self._bit_fields:
            if self._bit_fields[key].reset_type != ResetType.NUMERIC:
                return True
        return False

    def strict_volatile(self) -> bool:
        """
        Returns True if a field is marked as volatile or if there
        is an input signal specified
        """

        for key in self._bit_fields:
            field = self._bit_fields[key]
            if field.flags.volatile or field.input_signal != "":
                return True
        return False

    def loose_volatile(self) -> bool:
        """
        Returns True if a field is marked volatile, and disregards
        if there is an input signal
        """

        for key in self._bit_fields:
            if self._bit_fields[key].flags.volatile:
                return True
        return False

    def reset_value(self) -> int:
        """
        Returns the reset value for the register from the reset values
        in the bit fields.
        """
        val = 0
        for key in self._bit_fields:
            field = self._bit_fields[key]
            val |= field.reset_value << field.lsb
        return val

    def reset_mask(self) -> int:
        """Returns a mask of the active fields (not reserved fields)"""
        val = 0
        for key in self._bit_fields:
            field = self._bit_fields[key]
            for i in range(field.lsb, field.msb + 1):
                val |= 1 << i
        return val

    def set_parameters(self, plist: List[Tuple[str, int, int, int]]) -> None:
        """Sets the parameter list"""
        self._plist = plist
