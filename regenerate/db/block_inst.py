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

from .json_base import JSONEncodable


class BlockInst(JSONEncodable):
    """Basic block instance information."""

    def __init__(
        self,
        inst_name="",
        block=None,
        address_base=0,
        hdl_path="",
        repeat=1,
        description="",
    ) -> None:
        """Initialize the group data item."""
        self.inst_name = inst_name
        self.address_base = address_base
        self.hdl_path = hdl_path
        self.repeat = repeat
        self.description = description

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
            or self.name != other.name
            or self.base != other.base
            or self.hdl != other.hdl
            or self.description != other.description
            or self.repeat != other.repeat
        ):
            return False
        return True

    def json_decode(self, data) -> None:
        """Compare for equality."""
        self.inst_name = data["name"]
        self.address_base = data["base"]
        self.hdl_path = data["hdl"]
        self.description = data["description"]
        self.repeat = data["repeat"]
