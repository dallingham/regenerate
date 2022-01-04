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
Provides the register flags.

Maintains the register flags associated with a register.

"""

from typing import Dict, Any, Union


class RegisterFlags:
    """
    Contains the flags that control file and documentation generation.

    These flags include:
      * Do not use UVM
      * Do not generate code
      * Do not generate coverage
      * Do not test
      * Hide from documentation

    """

    __slots__ = (
        "_do_not_use_uvm",
        "_do_not_generate_code",
        "_do_not_cover",
        "_do_not_test",
        "_do_not_reset_test",
        "_hide",
    )

    def __init__(self):
        """
        Initialize the flags.

        Set all the flags to False

        """
        self._do_not_use_uvm = False
        self._do_not_generate_code = False
        self._do_not_cover = False
        self._do_not_test = False
        self._do_not_reset_test = False
        self._hide = False

    def __repr__(self) -> str:
        """
        Return the string representaton of the flags.

        Returns:
           str: String describing the object

        """
        return (
            f"RegisterFlags(uvm={self._do_not_use_uvm}, "
            f"code={self._do_not_generate_code},"
            f"cover={self._do_not_cover},"
            f"test={self._do_not_test},"
            f"reset={self._do_not_reset_test},"
            f"hide={self._hide})"
        )

    @property
    def hide(self) -> bool:
        """
        Return the value of the _hide flag.

        This cannot be accessed directly, but only via the property 'hide'

        Returns:
            bool: True if the register should be hidden from the documentation

        """
        return self._hide

    @hide.setter
    def hide(self, val: Union[int, bool]) -> None:
        """
        Set the _hide flag, indicating if documenation should not be displayed.

        This cannot be accessed directly, but only via the property 'hide'

        Parameters:
            val (Union[int,bool]): True to hide the documentation

        """
        self._hide = bool(val)

    @property
    def do_not_generate_code(self) -> bool:
        """
        Return the value of the _do_not_generate_code flag.

        Provides access to the '_do_not_generate_code' flag.

        Returns:
            bool: Indicates if the code generator should not generate code
                  for this register.

        """
        return self._do_not_generate_code

    @do_not_generate_code.setter
    def do_not_generate_code(self, val: Union[int, bool]) -> None:
        """
        Set the _do_not_generate_code flag.

        This flag cannot be accessed directly, but only via this property.
        Handles the conversion of int/bool to bool.

        Parameters:
            val (Union[int, bool]): True if code should not be generated

        """
        self._do_not_generate_code = bool(val)

    @property
    def do_not_use_uvm(self) -> bool:
        """
        Return the value of the _do_not_use_uvm flag.

        This cannot be accessed directly, but only via the property
        'do_not_use_uvm'

        Return:
            bool: Indicates if the register should have a UVM representation

        """
        return self._do_not_use_uvm

    @do_not_use_uvm.setter
    def do_not_use_uvm(self, val: Union[int, bool]) -> None:
        """
        Set the __do_not_use_uvm flag.

        This cannot be accessed directly, but only via the property
        'do_not_use_uvm'

        Parameters:
            val (Union[int, bool]): flag value to set

        """
        self._do_not_use_uvm = bool(val)

    @property
    def do_not_test(self) -> bool:
        """
        Return the value of the _do_not_test flag.

        Returns:
            bool: Indicates if the register should not be tested

        """
        return self._do_not_test

    @do_not_test.setter
    def do_not_test(self, val: Union[int, bool]) -> None:
        """
        Set the "do not test" flag.

        This cannot be accessed directly, but only via the property
        'do_not_test'

        Parameters:
            val (Union[int, bool]): flag value to set

        """
        self._do_not_test = bool(val)

    @property
    def do_not_reset_test(self) -> bool:
        """
        Return the value of the "do not reset test" flag.

        Returns:
            bool: Indicates if the register should not be tested at reset

        """
        return self._do_not_reset_test

    @do_not_reset_test.setter
    def do_not_reset_test(self, val: Union[int, bool]) -> None:
        """
        Set the "do not reset test" flag.

        Parameters:
            val (Union[int, bool]): flag value to set

        """
        self._do_not_reset_test = bool(val)

    @property
    def do_not_cover(self) -> bool:
        """
        Return the value of the "do not cover" flag.

        Returns:
            bool: Indicates if the register should not be covered

        """
        return self._do_not_cover

    @do_not_cover.setter
    def do_not_cover(self, val: Union[int, bool]) -> None:
        """
        Set the "do not cover" flag.

        Parameters:
            val (Union[int, bool]): flag value to set

        """
        self._do_not_cover = bool(val)

    def json(self) -> Dict[str, Any]:
        """
        Convert the object to a JSON compatible dictionary.

        Returns:
            Dict[str, Any]: dictionary in JSON format

        """
        return {
            "do_not_use_uvm": self._do_not_use_uvm,
            "do_not_generate_code": self._do_not_generate_code,
            "do_not_cover": self._do_not_cover,
            "do_not_test": self._do_not_test,
            "do_not_reset_test": self._do_not_reset_test,
            "hide": self._hide,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Load the object from JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data describing the object

        """
        self._do_not_use_uvm = data["do_not_use_uvm"]
        self._do_not_generate_code = data["do_not_generate_code"]
        self._do_not_cover = data["do_not_cover"]
        self._do_not_test = data["do_not_test"]
        self._do_not_reset_test = data.get(
            "do_not_reset_test", self._do_not_test
        )
        self._hide = data["hide"]
