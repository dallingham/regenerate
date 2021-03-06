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

from typing import List
from .register_db import RegisterDb
from .group_inst_data import GroupInstData
from .json_base import JSONEncodable


class GroupData(JSONEncodable):
    """Basic group information."""

    def __init__(
        self,
        name="",
        base=0,
        hdl="",
        repeat=1,
        repeat_offset=0x10000,
        title="",
    ) -> None:
        """Initialize the group data item."""
        self.name = name
        self.base = base
        self.hdl = hdl
        self.repeat = repeat
        self.repeat_offset = repeat_offset
        self.register_sets: List[GroupInstData] = []
        self.title = title
        self.docs = ""

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
            or self.title != other.title
            or self.repeat != other.repeat
            or self.repeat_offset != other.repeat_offset
            or self.docs != other.docs
            or self.register_sets != other.register_sets
        ):
            return False
        return True

    def json_decode(self, data) -> None:
        """Compare for equality."""
        self.name = data["name"]
        self.base = data["base"]
        self.hdl = data["hdl"]
        self.title = data["title"]
        self.repeat = data["repeat"]
        self.repeat_offset = data["repeat_offset"]
        self.docs = data["docs"]

        self.register_sets = []
        for rset in data["register_sets"]:
            ginst = GroupInstData()
            ginst.json_decode(rset)
            self.register_sets.append(ginst)
