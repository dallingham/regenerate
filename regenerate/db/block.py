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

from typing import List, Dict
from .register_inst import RegisterInst
from .doc_pages import DocPages
from .name_base import NameBase


class Block(NameBase):
    """Basic group information."""

    def __init__(
        self,
        name="",
        address_size=0x10000,
        description="",
    ) -> None:
        """Initialize the group data item."""

        super().__init__(name)
        self.address_size = address_size
        self.register_sets: List[RegisterInst] = []
        self.description = description
        self.doc_pages = DocPages()
        self.doc_pages.update_page("Overview", "")
        self.doc_pages.update_page("Architecture", "")
        self.doc_pages.update_page("Programming Model", "")
        self.doc_pages.update_page("Additional", "")
        self.regname2path: Dict[str, str] = {}
        self.modified = False

    def __hash__(self):
        "Return the ID as the hash for the instance"
        return id(self.uuid)

    def __ne__(self, other) -> bool:
        """Compare for inequality."""
        return not self.__eq__(other)

    def __eq__(self, other) -> bool:
        """Compare for equality."""
        if (
            other is None
            or self.name != other.name
            or self.uuid != other.uuid
            or self.description != other.description
            or self.address_size != other.address_size
            or self.doc_pages != other.doc_pages
            or self.register_sets != other.register_sets
        ):
            return False
        return True

    def json_decode(self, data) -> None:
        """Compare for equality."""

        self.name = data["name"]
        self.uuid = data["uuid"]
        self.description = data["description"]
        self.address_size = data["address_size"]
        self.doc_pages = DocPages()
        self.doc_pages.json_decode(data["doc_pages"])

        self.register_sets = []
        for rset in data["register_sets"]:
            ginst = RegisterInst()
            ginst.json_decode(rset)
            self.register_sets.append(ginst)

        self.regname2path = data["regname2path"]

    def json(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "address_size": self.address_size,
            "doc_pages": self.doc_pages.json(),
            "description": self.description,
            "register_sets": self.register_sets,
            "regname2path": self.regname2path,
        }
