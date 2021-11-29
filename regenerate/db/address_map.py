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
Contains the data in the address map.

Address maps store the base address, width, and block instances that
belong to a particular map.
"""

from typing import List, Union, Dict, Any
from .name_base import NameBase, Uuid


class AddressMap(NameBase):
    """
    Address map data.

    Contains the following items.

    name - name of the map
    uuid - unique ID
    base - base address
    fixed - indicator if the map is fixed or relocatable
    block_insts - list of uuids for the block instances that it contains
    """

    def __init__(self, name: str = "", base: int = 0, width: int = 0):
        """
        Initialize the class with optional fields.

        Parameters:
           name (str): Name of the address map
           base (int): Address base of the address map
           width (int): bit width of the address map

        """
        super().__init__(name, Uuid(""))
        self.base = base
        self.width = width
        self._fixed = False
        self.block_insts: List[Uuid] = []

    @property
    def fixed(self) -> bool:
        """
        Return the fixed flag.

        Returns:
           fixed (bool): True indicates a fixed address map, False is
                         relocatable

        """
        return self._fixed

    @fixed.setter
    def fixed(self, value: Union[bool, int]) -> None:
        """
        Set the fixed flag, converting to boolean type if needed.

        Parameters:
           value (Union[bool, int]): New value for the fixed flag

        """
        self._fixed = bool(value)

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Convert the incoming JSON data to the class variables.

        Parameters:
           data (Dict[str, Any]) - JSON data

        """
        self.name = data["name"]
        self.uuid = Uuid(data["uuid"])
        self.base = int(data["base"], 0)
        self.width = data["width"]
        self.fixed = data["fixed"]
        self.block_insts = data["block_insts"]

    def json(self) -> Dict[str, Any]:
        """
        Encode the class variables into a dictionary for JSON encoding.

        Returns:
           JSON data (Dict[str, Any]): Dictionary of data in JSON
           format

        """
        return {
            "name": self.name,
            "uuid": self.uuid,
            "base": f"{self.base}",
            "width": self.width,
            "fixed": self.fixed,
            "block_insts": self.block_insts,
        }
