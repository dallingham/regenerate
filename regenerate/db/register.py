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

from value import Value


class Register(object):
    """
    Defines a hardware register.
    """

    def __init__(self, address=0, width=32, name=""):
        self.__address = Value(address)
        self.__token = Value("")
        self.__name = Value(name)
        self.__description = Value("")
        self.__width = Value(width)
        self.__nocode = Value(False)
        self.__dont_test = Value(False)
        self.__hide = Value(False)
        self.__bit_fields = {}

    def find_first_unused_bit(self):
        """
        Finds the first unused bit in a the register.
        """
        bit = [0] * self.width
        for field in self.__bit_fields.values():
            for val in range(field.start_position, field.stop_position + 1):
                bit[val] = 1
        for pos in range(0, self.width):
            if bit[pos] == 0:
                return pos
        bit = set([])
        for field in self.__bit_fields.values():
            for val in range(field.start_position, field.stop_position + 1):
                bit.add(val)
        all_bits = set(range(0, self.width))
        l = sorted(list(bit.difference(all_bits)))
        if l:
            return l[0]
        else:
            return 0

    def find_next_unused_bit(self):
        """
        Finds the first unused bit in a the register.
        """
        bit = set([])
        for field in self.__bit_fields.values():
            for val in range(field.start_position, field.stop_position + 1):
                bit.add(val)
        lbits = sorted(list(bit))
        if lbits:
            if lbits[-1] == self.width - 1:
                return self.find_first_unused_bit()
            else:
                return lbits[-1] + 1
        else:
            return 0

    def __set_dont_test(self, val):
        """
        Sets the __dont_test flag. This cannot be accessed directly, but only
        via the propery 'do_not_test'.
        """
        self.__dont_test.set(val)

    def __get_dont_test(self):
        """
        Returns the value of the __dont_test flag. This cannot be accessed
        directly, but only via the property 'do_not_test'
        """
        return self.__dont_test.get()

    def get_dont_test_obj(self):
        """
        Returns the actual lower level __dont_test object. This is needed to
        set the modified flag and the last modified time stamp.
        """
        return self.__dont_test

    do_not_test = property(__get_dont_test, __set_dont_test, None,
                         "Indicates if the register should not be tested "
                         "by automatic tests")

    def __set_hide(self, val):
        """
        Sets the __hide flag . This cannot be accessed directly, but only
        via the propery 'hide'.
        """
        self.__hide.set(val)

    def __get_hide(self):
        """
        Returns the value of the __hide flag. This cannot be accessed
        directly, but only via the property 'hide'
        """
        return self.__hide.get()

    def get_hide_obj(self):
        """
        Returns the actual lower level __hide object. This is needed to
        set the modified flag and the last modified time stamp.
        """
        return self.__dont_test

    hide = property(__get_hide, __set_hide, None,
                    "Indicates if the register should be hidden "
                    "from documentation")

    def __set_no_code(self, val):
        """
        Sets the __nocode flag. This cannot be accessed directly, but only
        via the propery 'do_not_generate_code'
        """
        self.__nocode.set(bool(val))

    def __get_no_code(self):
        """
        Returns the value of the __nocode flag. This cannot be accessed
        directly, but only via the property 'do_not_generate_code'
        """
        return self.__nocode.get()

    def get_no_code_obj(self):
        """
        Returns the actual lower level __nocode object. This is needed to
        set the modified flag and the last modified time stamp.
        """
        return self.__nocode

    do_not_generate_code = property(__get_no_code, __set_no_code, None,
                                 "Indicates if code generation should be "
                                 "suppressed")

    def __set_token(self, val):
        """
        Sets the __token flag. This cannot be accessed directly, but only
        via the propery 'token'
        """
        self.__token.set(val.strip().upper())

    def __get_token(self):
        """
        Returns the value of the __token flag. This cannot be accessed
        directly, but only via the property 'token'
        """
        return self.__token.get()

    def get_token_obj(self):
        """
        Returns the actual lower level __token object. This is needed to
        set the modified flag and the last modified time stamp.
        """
        return self.__token

    token = property(__get_token, __set_token, None,
                     "token name of the register")

    def __set_name(self, name):
        """
        Sets the __name flag. This cannot be accessed directly, but only
        via the propery 'register_name'
        """
        self.__name.set(name.strip())

    def __get_name(self):
        """
        Returns the value of the __name flag. This cannot be accessed
        directly, but only via the property 'register_name'
        """
        return self.__name.get()

    def get_name_obj(self):
        """
        Returns the actual lower level __name object. This is needed to
        set the modified flag and the last modified time stamp.
        """
        return self.__name

    register_name = property(__get_name, __set_name, None,
                             "Name of the register")

    def __set_address(self, addr):
        """
        Sets the __address flag. This cannot be accessed directly, but only
        via the propery 'address'
        """
        self.__address.set(addr)

    def __get_address(self):
        """
        Returns the value of the __address flag. This cannot be accessed
        directly, but only via the property 'address'
        """
        return self.__address.get()

    def get_address_obj(self):
        """
        Returns the actual lower level __address object. This is needed to
        set the modified flag and the last modified time stamp.
        """
        return self.__address

    address = property(__get_address, __set_address, None,
                       "Address of the register")

    def __set_description(self, description):
        """
        Sets the __description flag. This cannot be accessed directly, but
        only via the propery 'Description'
        """
        self.__description.set(description)

    def __get_description(self):
        """
        Returns the value of the __description flag. This cannot be accessed
        directly, but only via the property 'description'
        """
        return self.__description.get()

    def get_description_obj(self):
        """
        Returns the actual lower level __description object. This is needed to
        set the modified flag and the last modified time stamp.
        """
        return self.__description

    description = property(__get_description, __set_description, None,
                           "description of the register")

    def __set_width(self, width):
        """
        Sets the __width flag. This cannot be accessed directly, but
        only via the propery 'width'
        """
        self.__width.set(width)

    def __get_width(self):
        """
        Returns the value of the __width flag. This cannot be accessed
        directly, but only via the property 'width'
        """
        return self.__width.get()

    def get_width_obj(self):
        """
        Returns the actual lower level __width object. This is needed to
        set the modified flag and the last modified time stamp.
        """
        return self.__width

    width = property(__get_width, __set_width, None, "Width of the register")

    def get_bit_fields(self):
        """
        Returns a dictionary of bit fields. The key is stop_position of the
        bit field.
        """
        return self.__bit_fields

    def get_bit_field(self, key):
        """
        Returns the bit field associated with the specified key.
        """
        return self.__bit_fields.get(key)

    def get_bit_field_keys(self):
        """
        Returns the list of keys associated with the bit fields
        """
        return sorted(self.__bit_fields.keys())

    def add_bit_field(self, field):
        """
        Adds a bit field to the set of bit fields.
        """
        self.__bit_fields[field.stop_position] = field

    def delete_bit_field(self, field):
        """
        Removes the specified bit field from the dictionary. We cannot
        use the stop_position, since it may have changed.
        """
        for key in self.__bit_fields.keys():
            if self.__bit_fields[key] == field:
                del self.__bit_fields[key]
