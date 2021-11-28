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
Holds the infomration for a group. This includes the name, base address,
HDL path, the repeat count, repeat offset, and the title.
"""

from typing import Dict, Any
from .name_base import NameBase, Uuid


class BlockInst(NameBase):
    """Basic block instance information."""

    def __init__(self, name: str = "", blkid: Uuid = Uuid("")) -> None:
        """Initialize the group data item."""
        super().__init__(name, Uuid(""))
        self.blkid = blkid
        self.address_base = 0
        self.hdl_path = ""
        self.repeat = 1
        self.description = ""

    def __repr__(self) -> str:
        return f"BlockInst({self.name}, {self.blkid})"

    def json_decode(self, data: Dict[str, Any]) -> None:
        self.name = data["name"]
        self.uuid = Uuid(data["id"])
        self.blkid = data["blkid"]
        self.address_base = int(data["address_base"], 0)
        self.hdl_path = data["hdl_path"]
        self.description = data["description"]
        self.repeat = data["repeat"]

    def json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "id": self.uuid,
            "blkid": self.blkid,
            "address_base": f"{self.address_base}",
            "hdl_path": self.hdl_path,
            "description": self.description,
            "repeat": self.repeat,
        }
