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
Holds the information for a group. This includes the name, base address,
HDL path, the repeat count, repeat offset, and the title.
"""

from typing import List, Dict, Union
from pathlib import Path
import json

from .const import BLK_EXT
from .register_inst import RegisterInst
from .doc_pages import DocPages
from .name_base import NameBase
from .containers import Container
from .register_db import RegSetContainer


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

        self.regset_insts: List[RegisterInst] = []
        self.regsets: Dict[str, RegSetContainer] = {}
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
        ):
            return False
        return True

    def json_decode(self, data) -> None:
        """Compare for equality."""

        self.name = data["name"]
        self.uuid = data["uuid"]
        self.description = data["description"]
        self.address_size = int(data["address_size"], 0)
        self.doc_pages = DocPages()
        self.doc_pages.json_decode(data["doc_pages"])

        self.regset_insts = []
        for rset in data["regset_insts"]:
            ginst = RegisterInst()
            ginst.json_decode(rset)
            self.regset_insts.append(ginst)

        self.regsets = {}
        for key, item in data["regsets"].items():

            rs_data = RegSetContainer()
            rs_data.json_decode(item)
            self.regsets[key] = rs_data

    def json(self):
        return {
            "name": self.name,
            "uuid": self.uuid,
            "address_size": f"{self.address_size}",
            "doc_pages": self.doc_pages.json(),
            "description": self.description,
            "regset_insts": self.regset_insts,
            "regsets": self.regsets,
        }


class BlockContainer(Container):
    def __init__(self):
        super().__init__()
        self.block: Optional[Block] = None

    @property
    def filename(self) -> Path:
        return self._filename

    @filename.setter
    def filename(self, value: Union[str, Path]) -> None:
        self._filename = Path(value).with_suffix(BLK_EXT)

    def save(self):
        if self.block:
            self._save_data(self.block)

    def json(self):
        return {
            "filename": str(self.filename),
        }

    def json_decode(self, data):
        self.filename = Path(data["filename"])
        self.block = Block()
        with self.filename.open() as ifile:
            new_data = json.loads(ifile.read())
            self.block.json_decode(new_data)
        self.modified = False
