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


class BlockInst:
    """Basic block instance information."""

    def __init__(
        self,
        inst_name="",
        block="",
        address_base=0,
        hdl_path="",
        repeat=1,
        description="",
    ) -> None:
        """Initialize the group data item."""
        self.inst_name = inst_name
        self.block = block
        self.address_base = address_base
        self.hdl_path = hdl_path
        self.repeat = repeat
        self.description = description

    def __repr__(self):
        return f"BlockInst({self.inst_name}, {self.block})"

    def __hash__(self):
        "Return the ID as the hash for the instance"

        return id(self)

    def __ne__(self, other) -> bool:
        """Compare for inequality."""
        return not self.__eq__(other)

    def __eq__(self, other) -> bool:
        """Compare for equality."""
        if (
            other is None
            or self.inst_name != other.inst_name
            or self.address_base != other.address_base
            or self.hdl_path != other.hdl_path
            or self.description != other.description
            or self.repeat != other.repeat
        ):
            return False
        return True

    def json_decode(self, data) -> None:
        self.inst_name = data["inst_name"]
        self.block = data["block"]
        self.address_base = int(data["address_base"], 0)
        self.hdl_path = data["hdl_path"]
        self.description = data["description"]
        self.repeat = data["repeat"]

    def json(self):
        return {
            "inst_name": self.inst_name,
            "block": self.block,
            "address_base": f"{self.address_base}",
            "hdl_path": self.hdl_path,
            "description": self.description,
            "repeat": self.repeat,
        }