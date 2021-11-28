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

from typing import List, Union, Dict, Any
from .name_base import NameBase, Uuid


class AddressMap(NameBase):
    """Address map data"""

    def __init__(self, name: str = "", base: int = 0, width: int = 0):
        super().__init__(name, Uuid(""))
        self.base = base
        self.width = width
        self._fixed = False
        self.blocks: List[str] = []

    @property
    def fixed(self) -> bool:
        "Return the fixed flag"

        return self._fixed

    @fixed.setter
    def fixed(self, val: Union[bool, int]) -> None:
        "Set the fixed flag, converting to boolean type"

        self._fixed = bool(val)

    def json_decode(self, data: Dict[str, Any]) -> None:
        "Convert the incoming JSON data to the class variables"

        self.name = data["name"]
        self.uuid = Uuid(data["uuid"])
        self.base = int(data["base"], 0)
        self.width = data["width"]
        self.fixed = data["fixed"]
        self.blocks = data["block_insts"]

    def json(self) -> Dict[str, Any]:
        "Encode the class variables into a dictionary for JSON encoding"

        return {
            "name": self.name,
            "uuid": self.uuid,
            "base": f"{self.base}",
            "width": self.width,
            "fixed": self.fixed,
            "block_insts": self.blocks,
        }
