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
Contains the data in the address map
"""

from typing import List, Union
from .name_base import NameBase


class AddressMap(NameBase):
    """Address map data"""

    def __init__(
        self,
        name: str = "",
        base: int = 0,
        width: int = 0,
        fixed: bool = False,
        uvm: bool = False,
    ):
        super().__init__(name, "")
        self.base: int = base
        self.width: int = width
        self._fixed: bool = fixed
        self._uvm: bool = uvm
        self.blocks: List[str] = []

    @property
    def fixed(self) -> bool:
        return self._fixed

    @fixed.setter
    def fixed(self, val: Union[bool, int]) -> None:
        self._fixed = bool(val)

    @property
    def uvm(self) -> bool:
        return self._uvm

    @uvm.setter
    def uvm(self, val: Union[int, bool]):
        self._uvm = bool(val)

    def __hash__(self):
        return hash(self.uuid)

    def json_decode(self, data):
        self.name = data["name"]
        self.uuid = data["uuid"]
        self.base = int(data["base"], 0)
        self.width = data["width"]
        self.fixed = data["fixed"]
        self.uvm = data["uvm"]
        self.blocks = data["block_insts"]

    def json(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "base": f"{self.base}",
            "width": self.width,
            "fixed": self.fixed,
            "uvm": self.uvm,
            "block_insts": self.blocks,
        }
