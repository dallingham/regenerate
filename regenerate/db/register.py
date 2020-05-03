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

import uuid
from .enums import ResetType, ShareType


class Register(object):
    """Defines a hardware register."""

    full_compare = (
        "address",
        "ram_size",
        "description",
        "width",
        "_id",
        "_token",
        "_do_not_test",
        "_name",
        "_hide",
        "dimension",
        "_do_not_generate_code",
        "_do_not_cover",
        "_do_not_use_uvm",
    )

    array_compare = (
        "ram_size",
        "width",
        "_do_not_test",
        "_hide",
        "_do_not_generate_code",
        "_do_not_cover",
        "_do_not_use_uvm",
        "share",
    )

    doc_compare = (
        "address",
        "ram_size",
        "description",
        "width",
        "_id",
        "_token",
        "_name",
        "_hide",
        "dimension",
    )

    def __init__(self, address=0, width=32, name=""):
        self.address = address
        self.dimension = 1
        self.ram_size = 0
        self.description = ""
        self.width = width
        self._id = ""

        self._token = ""
        self._do_not_test = False
        self._do_not_cover = False
        self._do_not_use_uvm = False
        self._do_not_generate_code = False
        self._name = name
        self._hide = False
        self.__bit_fields = {}
        self.share = ShareType.NONE

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if not all(
            self.__dict__[i] == other.__dict__[i] for i in self.full_compare
        ):
            return False
        return self.get_bit_fields() == other.get_bit_fields()

    def __cmp__(self, other):
        return cmp(self.address, other.address)

    def __hash__(self):
        return id(self)

    def array_cmp(self, other):
        if other is None:
            return False
        if not all(
            self.__dict__[i] == other.__dict__[i] for i in self.array_compare
        ):
            return False
        if other.address + (other.width / 8) != self.address:
            return False
        return self.get_bit_fields() == other.get_bit_fields()

    def group_cmp(self, other):
        if not all(
            self.__dict__[i] == other.__dict__[i] for i in self.array_compare
        ):
            return False
        return self.get_bit_fields() == other.get_bit_fields()

    def find_first_unused_bit(self):
        """
        Finds the first unused bit in a the register.
        """
        bit = [0] * self.width
        for field in self.__bit_fields.values():
            for val in range(field.lsb, field.msb + 1):
                bit[val] = 1
        for pos in range(0, self.width):
            if bit[pos] == 0:
                return pos
        bit = set([])
        for field in self.__bit_fields.values():
            for val in range(field.lsb, field.msb + 1):
                bit.add(val)
        all_bits = set(range(0, self.width))
        sorted_bits = sorted(list(bit.difference(all_bits)))
        if sorted_bits:
            return sorted_bits[0]
        return -1

    def find_next_unused_bit(self):
        """Finds the first unused bit in a the register."""
        bit = set([])
        for field in self.__bit_fields.values():
            for val in range(field.lsb, field.msb + 1):
                bit.add(val)
        lbits = sorted(list(bit))

        if lbits:
            if lbits[-1] == self.width - 1:
                return self.find_first_unused_bit()
            return lbits[-1] + 1
        return 0

    @property
    def uuid(self):
        if not self._id:
            self._id = uuid.uuid4().hex
        return self._id

    @uuid.setter
    def uuid(self, value):
        self._id = value

    @property
    def do_not_generate_code(self):
        """
        Returns the value of the _do_not_generate_code flag. This cannot
        be accessed directly, but only via the property 'do_not_generate_code'
        """
        return self._do_not_generate_code

    @do_not_generate_code.setter
    def do_not_generate_code(self, val):
        """
        Sets the __do_not_generate_code flag. This cannot be accessed
        directly, but only via the property 'do_not_generate_code'
        """
        self._do_not_generate_code = bool(val)

    @property
    def do_not_use_uvm(self):
        """
        Returns the value of the _do_not_use_uvm flag. This cannot
        be accessed directly, but only via the property 'do_not_use_uvm'
        """
        return self._do_not_use_uvm

    @do_not_use_uvm.setter
    def do_not_use_uvm(self, val):
        """
        Sets the __do_not_use_uvm flag. This cannot be accessed
        directly, but only via the property 'do_not_use_uvm'
        """
        self._do_not_use_uvm = bool(val)

    @property
    def do_not_test(self):
        """
        Returns the value of the _do_not_generate_code flag. This
        cannot be accessed directly, but only via the property 'do_not_test'
        """
        return self._do_not_test

    @do_not_test.setter
    def do_not_test(self, val):
        """
        Sets the __do_not_generate_code flag. This cannot be accessed
        directly, but only via the property 'do_not_test'
        """
        self._do_not_test = bool(val)

    @property
    def do_not_cover(self):
        """
        Returns the value of the _do_not_cover flag. This
        cannot be accessed directly, but only via the property 'do_not_cover'
        """
        return self._do_not_cover

    @do_not_cover.setter
    def do_not_cover(self, val):
        """
        Sets the __do_not_cover flag. This cannot be accessed
        directly, but only via the property 'do_not_cover'
        """
        self._do_not_cover = bool(val)

    @property
    def hide(self):
        """
        Returns the value of the _hide flag. This cannot be accessed
        directly, but only via the property 'hide'
        """
        return self._hide

    @hide.setter
    def hide(self, val):
        """
        Sets the __hide flag. This cannot be accessed directly, but only
        via the property 'hide'
        """
        self._hide = bool(val)

    @property
    def token(self):
        """
        Returns the value of the _token flag. This cannot be accessed
        directly, but only via the property 'token'
        """
        return self._token

    @token.setter
    def token(self, val):
        """
        Sets the __token flag. This cannot be accessed directly, but only
        via the property 'token'
        """
        self._token = val.strip().upper()

    @property
    def register_name(self):
        """
        Returns the value of the _name flag. This cannot be accessed
        directly, but only via the property 'register_name'
        """
        return self._name

    @register_name.setter
    def register_name(self, name):
        """
        Sets the __name flag. This cannot be accessed directly, but only
        via the property 'register_name'
        """
        self._name = name.strip()

    def get_bit_fields(self):
        """
        Returns a dictionary of bit fields. The key is msb of the
        bit field.
        """
        return sorted(self.__bit_fields.values(), key=lambda x: x.lsb)

    def get_bit_fields_with_values(self):
        """
        Returns a dictionary of bit fields. The key is msb of the
        bit field.
        """
        return sorted(
            [s for s in self.__bit_fields.values() if s.values],
            key=lambda x: x.lsb,
        )

    def get_bit_field(self, key):
        """Returns the bit field associated with the specified key."""
        return self.__bit_fields.get(key)

    def get_bit_field_keys(self):
        """Returns the list of keys associated with the bit fields"""
        return sorted(self.__bit_fields.keys())

    def add_bit_field(self, field):
        """Adds a bit field to the set of bit fields."""
        self.__bit_fields[field.lsb] = field

    def change_bit_field(self, field):
        """Adds a bit field to the set of bit fields."""
        remove_val = None
        for current_field in self.__bit_fields:
            if field == self.__bit_fields[current_field]:
                remove_val = current_field

        if remove_val is not None:
            del self.__bit_fields[remove_val]
        self.__bit_fields[field.lsb] = field

    def delete_bit_field(self, field):
        """
        Removes the specified bit field from the dictionary. We cannot
        use the msb, since it may have changed.
        """
        delete_keys = [
            key for key in self.__bit_fields if self.__bit_fields[key] == field
        ]
        for key in delete_keys:
            del self.__bit_fields[key]

    def is_completely_read_only(self):
        for key in self.__bit_fields:
            if not self.__bit_fields[key].is_read_only():
                return False
        return True

    def is_completely_write_only(self):
        for key in self.__bit_fields:
            if not self.__bit_fields[key].is_write_only():
                return False
        return True

    def no_reset_test(self):
        if self._do_not_test:
            return True
        for key in self.__bit_fields:
            if self.__bit_fields[key].reset_type != ResetType.NUMERIC:
                return True
        return False

    def strict_volatile(self):
        for key in self.__bit_fields:
            field = self.__bit_fields[key]
            if field.volatile or field.input_signal != "":
                return True
        return False

    def loose_volatile(self):
        for key in self.__bit_fields:
            if self.__bit_fields[key].volatile:
                return True
        return False

    def reset_value(self):
        val = 0
        for key in self.__bit_fields:
            field = self.__bit_fields[key]
            val |= field.reset_value << field.lsb
        return val

    def reset_mask(self):
        val = 0
        for key in self.__bit_fields:
            field = self.__bit_fields[key]
            for i in range(field.lsb, field.msb + 1):
                val |= 1 << i
        return val
