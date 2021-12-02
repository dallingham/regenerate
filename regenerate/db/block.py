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

from typing import List, Dict, Any, Optional
from pathlib import Path
import os
import json

from .name_base import Uuid
from .data_reader import FileReader
from .overrides import Overrides
from .register_inst import RegisterInst
from .register_db import RegisterDb
from .doc_pages import DocPages
from .base_file import BaseFile
from .logger import LOGGER
from .param_container import ParameterContainer
from .param_resolver import ParameterResolver
from .regset_finder import RegsetFinder
from .export import ExportData
from .exceptions import (
    CorruptBlockFile,
    IoErrorBlockFile,
    CorruptRegsetFile,
    IoErrorRegsetFile,
)


class Block(BaseFile):
    """Basic group information."""

    def __init__(
        self,
        name: str = "",
        address_size: int = 0x10000,
        description: str = "",
    ) -> None:
        """Initialize the block item."""

        super().__init__(name, Uuid(""))
        self.finder = RegsetFinder()
        self.address_size = address_size
        self.description = description
        self.doc_pages = DocPages()
        self.doc_pages.update_page("Overview", "", ["Confidential"])
        self.reader_class = None

        self.regset_insts: List[RegisterInst] = []
        self.regsets: Dict[str, RegisterDb] = {}
        self.parameters = ParameterContainer()
        self.overrides: List[Overrides] = []
        self.exports: List[ExportData] = []

    def get_reginst_from_id(self, uuid: Uuid) -> Optional[RegisterInst]:
        "Returns the register instance based on the uuid"

        results = [inst for inst in self.regset_insts if inst.uuid == uuid]
        if results:
            return results[0]
        return None

    def get_regset_insts(self) -> List[RegisterInst]:
        "Returns a list of register instances"
        return self.regset_insts

    def get_regsets_dict(self) -> Dict[str, RegisterDb]:
        "Returns a dict of register sets"
        return self.regsets

    def get_regset_from_reg_inst(self, reg_inst: RegisterInst) -> RegisterDb:
        "Returns the register set connected to the register instance"
        return self.regsets[reg_inst.regset_id]

    def remove_register_set(self, uuid: Uuid) -> None:
        "Removes the register set using the UUID"
        if uuid in self.regsets:
            del self.regsets[uuid]
        self.regset_insts = [
            inst for inst in self.regset_insts if inst.regset_id != uuid
        ]

    def save(self) -> None:
        "Save the file as a JSON file"
        self.save_json(self.json(), self._filename)

    def __ne__(self, other: object) -> bool:
        """Compare for inequality."""
        if not isinstance(other, Block):
            return NotImplemented
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

        try:
            with self._filename.open() as ofile:
                data = ofile.read()
                self.json_decode(json.loads(data))
        except json.decoder.JSONDecodeError as msg:
            raise CorruptBlockFile(self._filename.resolve(), str(msg))
        except OSError as msg:
            raise IoErrorBlockFile(self._filename.resolve(), msg)

    def get_address_size(self) -> int:
        "Returns the size of the address space"
        base = 0
        for reginst in self.regset_insts:
            regset = self.regsets[reginst.regset_id]
            base = max(
                base, reginst.offset + (1 << regset.ports.address_bus_width)
            )
        return base

    def _json_decode_regsets(
        self, data: Dict[str, Any]
    ) -> Dict[str, RegisterDb]:
        "Decode the register sets section of the JSON data"

        regsets = {}
        for key, item in data.items():
            filename = Path(self._filename.parent / item["filename"]).resolve()

            regset = self.finder.find_by_file(str(filename))
            if not regset:
                regset = RegisterDb()
                if self.reader_class is None:
                    rdr = FileReader(filename)
                else:
                    rdr = self.reader_class

                try:
                    json_data = json.loads(rdr.read_bytes(filename))
                except json.decoder.JSONDecodeError as msg:
                    raise CorruptRegsetFile(filename.resolve(), str(msg))
                except OSError as msg:
                    raise IoErrorRegsetFile(filename.resolve(), msg)

                regset.filename = filename
                regset.json_decode(json_data)
                self.finder.register(regset)
            regsets[key] = regset
        return regsets

    def _json_decode_exports(
        self, data: Optional[List[Dict[str, Any]]]
    ) -> List[ExportData]:
        "Decode the exports section of the JSON data"

        exports = []
        if data:
            for exp_json in data:
                exp = ExportData()
                target = exp_json["target"]
                exp.target = str((self.filename.parent / target).resolve())
                exp.options = exp_json["options"]
                exp.exporter = exp_json["exporter"]

                exports.append(exp)
        return exports

    def json_decode(self, data: Dict[str, Any]) -> None:
        "Compare for equality."

        self.name = data["name"]
        self.uuid = Uuid(data["uuid"])
        self.description = data["description"]
        self.address_size = int(data["address_size"], 0)
        self.doc_pages = DocPages()
        self.doc_pages.json_decode(data["doc_pages"])

        self.regset_insts = _json_decode_reginsts(data["regset_insts"])

        self.regsets = self._json_decode_regsets(data["regsets"])

        self.parameters = ParameterContainer()
        self.parameters.json_decode(data["parameters"])

        self.exports = self._json_decode_exports(data.get("exports"))

        self.overrides = []
        resolver = ParameterResolver()
        try:
            for override in data["overrides"]:
                item = Overrides()
                item.json_decode(override)
                for regset_inst in self.regset_insts:
                    if item.path != regset_inst.uuid:
                        continue
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
        data: Dict[str, Any] = {
            "name": self.name,
            "uuid": Uuid(self.uuid),
            "parameters": self.parameters,
            "overrides": self.overrides,
            "address_size": f"{self.address_size}",
            "doc_pages": self.doc_pages.json(),
            "description": self.description,
            "regset_insts": self.regset_insts,
            "exports": [],
            "regsets": {},
        }

        for exp in self.exports:
            info = {
                "exporter": exp.exporter,
                "target": os.path.relpath(exp.target, self.filename.parent),
                "options": exp.options,
            }
            data["exports"].append(info)

        for name in self.regsets:
            new_path = os.path.relpath(
                self.regsets[name].filename,
                self._filename.parent,
            )
            data["regsets"][name] = {
                "filename": new_path,
            }

        return data


def _json_decode_reginsts(data: List[Any]) -> List[RegisterInst]:
    "Decode the register instance section of the JSON data"

    reginst_list = []
    for rset in data:
        ginst = RegisterInst()
        ginst.json_decode(rset)
        reginst_list.append(ginst)
    return reginst_list
