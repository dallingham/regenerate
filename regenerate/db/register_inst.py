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
Manages the instance of a register within a group.
"""
from typing import Union, Dict, Any

from .parameters import ParameterValue
from .name_base import NameBase, Uuid


class RegisterInst(NameBase):
    """Instance information when contained in a group"""

    def __init__(
        self,
        rset: Uuid = Uuid(""),
        inst: str = "",
        offset: int = 0,
        repeat: int = 1,
        repeat_offset: int = 0,
        hdl: str = "",
        no_uvm: bool = False,
        no_decode: bool = False,
        array: bool = False,
        single_decode: bool = False,
    ) -> None:
        super().__init__(inst, Uuid(""))
        self.regset_id = rset
        self.offset = offset
        self.repeat = ParameterValue(repeat)
        self.repeat_offset = repeat_offset
        self.hdl = hdl
        self._no_uvm = no_uvm
        self._no_decode = no_decode
        self._array = array
        self._single_decode = single_decode

    def __repr__(self) -> str:
        return f'RegisterInst(name="{self.name}", uuid="{self.uuid}")'

    @property
    def single_decode(self) -> bool:
        "Returns the single decode flag"
        return self._single_decode

    @single_decode.setter
    def single_decode(self, val: Union[bool, int]) -> None:
        "Sets the single decode flag, converting to boolean"
        self._single_decode = bool(val)

    @property
    def no_uvm(self) -> bool:
        "Returns the no_uvm flag"
        return self._no_uvm

    @no_uvm.setter
    def no_uvm(self, val: Union[bool, int]) -> None:
        "Sets the no_uvm flag, converting to a boolen"

        self._no_uvm = bool(val)

    @property
    def no_decode(self) -> bool:
        "Returns the no_decode flag"

        return self._no_decode

    @no_decode.setter
    def no_decode(self, val: Union[bool, int]) -> None:
        "Sets the no_decode flag, converting to a boolen"

        self._no_decode = bool(val)

    @property
    def array(self) -> bool:
        "Returns the array flag"

        return self._array

    @array.setter
    def array(self, val: Union[int, bool]) -> None:
        "Sets the array flag, converting to a boolen"

        self._array = bool(val)

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Load the object from JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data describing the object

        """
        self.regset_id = Uuid(data["regset_id"])
        self.uuid = Uuid(data["uuid"])
        self.name = data["name"]
        self.offset = data["offset"]
        self.repeat = ParameterValue()
        self.repeat.json_decode(data["repeat"])
        self.hdl = data["hdl"]
        self.no_uvm = data["no_uvm"]
        self.no_decode = data["no_decode"]
        self.array = data["array"]
        self.single_decode = data["single_decode"]

    def json(self) -> Dict[str, Any]:
        """
        Convert the object to a JSON compatible dictionary.

        Returns:
            Dict[str, Any]: dictionary in JSON format

        """
        return {
            "regset_id": self.regset_id,
            "name": self.name,
            "uuid": self.uuid,
            "offset": self.offset,
            "repeat": self.repeat,
            "hdl": self.hdl,
            "no_uvm": self.no_uvm,
            "no_decode": self.no_decode,
            "array": self.array,
            "single_decode": self.single_decode,
        }
