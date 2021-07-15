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

from typing import List, Dict, Union, Any
from pathlib import Path
import os
import json

from .data_reader import FileReader
from .overrides import Overrides
from .const import BLK_EXT
from .register_inst import RegisterInst
from .register_db import RegisterDb
from .doc_pages import DocPages
from .name_base import NameBase
from .logger import LOGGER
from .param_container import ParameterContainer
from .param_resolver import ParameterResolver
from .regset_finder import RegsetFinder
from .utils import save_json


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
        self.finder = RegsetFinder()
        self.address_size = address_size
        self.description = description
        self.doc_pages = DocPages()
        self.doc_pages.update_page("Overview", "", ["Confidential"])
        self.reader_class = None

        self.regset_insts: List[RegisterInst] = []
        self.regsets: Dict[str, RegisterDb] = {}
        self.modified = False
        self._filename = Path("")
        self.parameters = ParameterContainer()
        self.overrides: List[Overrides] = []

    def get_regset_insts(self) -> List[RegisterInst]:
        return self.regset_insts
        
    @property
    def filename(self) -> Path:
        "Returns the filename as a path"
        return self._filename

    @filename.setter
    def filename(self, value: Union[str, Path]) -> None:
        "Sets the filename, converting to a path, and fixing the suffix"

        self._filename = Path(value).with_suffix(BLK_EXT)

    def save(self) -> None:
        "Save the file as a JSON file"
        save_json(self.json(), self._filename)

    def __ne__(self, other) -> bool:
        """Compare for inequality."""
        return not self.__eq__(other)

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if not isinstance(other, Block):
            return NotImplemented
        if (
            self.name != other.name
            or self.uuid != other.uuid
            or self.description != other.description
            or self.address_size != other.address_size
            or self.doc_pages != other.doc_pages
        ):
            return False
        return True

    def open(self, name: Path) -> None:
        "Opens the filename and loads the object"

        self._filename = name

        LOGGER.info("Reading block file %s", str(self._filename))

        with self._filename.open() as ofile:
            data = ofile.read()
        self.json_decode(json.loads(data))

    def json_decode(self, data: Dict[str, Any]) -> None:
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
            filename = Path(self._filename.parent / item["filename"])

            regset = self.finder.find_by_file(str(filename))
            if not regset:
                regset = RegisterDb()
                if self.reader_class is None:
                    rdr = FileReader(filename)
                else:
                    rdr = self.reader_class

                json_data = json.loads(rdr.read_bytes(filename))
                regset.filename = filename
                regset.json_decode(json_data)
                self.finder.register(regset)
            self.regsets[key] = regset

        self.parameters = ParameterContainer()
        self.parameters.json_decode(data["parameters"])

        self.overrides = []
        resolver = ParameterResolver()
        try:
            for override in data["overrides"]:
                item = Overrides()
                item.json_decode(override)
                for regset_inst in self.regset_insts:
                    if item.path != regset_inst.uuid:
                        continue
                    regset = self.regsets[regset_inst.regset_id]
                    self.overrides.append(item)
                    break
        except KeyError:
            ...

        for override in self.overrides:
            resolver.add_regset_override(
                override.path, override.parameter, override.value
            )

        self.modified = False

    def json(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "uuid": self.uuid,
            "parameters": self.parameters,
            "overrides": self.overrides,
            "address_size": f"{self.address_size}",
            "doc_pages": self.doc_pages.json(),
            "description": self.description,
            "regset_insts": self.regset_insts,
        }

        data["regsets"] = {}
        for name in self.regsets:
            new_path = os.path.relpath(
                self.regsets[name].filename,
                self._filename.parent,
            )
            data["regsets"][name] = {
                "filename": new_path,
            }

        return data
