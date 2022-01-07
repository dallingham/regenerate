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
Provides the container database for a set of registers.
"""

import re
import json
from io import BytesIO as StringIO
from pathlib import Path
from typing import List, Optional, Dict, Iterator, Any

from .register import Register
from .reg_parser import RegParser
from .signals import Signals
from .const import OLD_REG_EXT, REG_EXT
from .export import ExportData
from .logger import LOGGER
from .base_file import BaseFile
from .doc_pages import DocPages
from .parameters import ParameterDefinition, ParameterContainer

# from .param_container import ParameterContainer
from .exceptions import CorruptRegsetFile, IoErrorRegsetFile
from .name_base import Uuid


class RegisterSet(BaseFile):
    """
    Container database for a set of registers.
    """

    def __init__(self, filename=None):
        super().__init__("", Uuid(""))
        self.descriptive_title = ""
        self._registers: Dict[Uuid, Register] = {}
        self.parameters = ParameterContainer()
        self.exports: List[ExportData] = []

        self.ports = Signals()

        self.memory = False
        self.array_is_reg = False
        self.internal_only = False
        self.owner = ""
        self.organization = ""
        self.use_interface = False
        self.coverage = True
        self.doc_pages = DocPages()
        self.doc_pages.update_page("Overview", "", ["Confidential"])

        if filename is not None:
            self.read_db(filename)
            self.filename = Path(filename)

    def __repr__(self) -> str:
        return f'RegisterSet(name="{self.name}", uuid="{self.uuid}")'

    def total_bits(self) -> int:
        """Returns bits in register"""
        bits = 0
        for key in self._registers:
            reg = self._registers[key]
            for field in reg.get_bit_fields():
                bits += field.width
        return bits

    def get_keys(self) -> List[Uuid]:
        """Returns the register keys, which is the address of the register"""
        return [
            a.uuid
            for a in sorted(self._registers.values(), key=lambda a: a.address)
        ]

    def get_all_registers(self) -> Iterator[Register]:
        """Returns the register keys, which is the address of the register"""
        return iter(sorted(self._registers.values(), key=lambda a: a.address))

    def get_register(self, key: Uuid) -> Optional[Register]:
        """
        Returns the register from the specified key, which should be the
        address.
        """
        return self._registers.get(key)

    def add_register(self, reg: Register) -> None:
        """Adds the register to the database."""
        self._registers[reg.uuid] = reg
        reg.regset_name = self.name
        reg.set_parameters(self.parameters)

    def delete_register(self, reg: Register) -> None:
        """Removes the register to the database."""
        del self._registers[reg.uuid]

    def read_db(self, filename: Path) -> None:
        "Loads either from XML or JSON depending on the extension"
        if filename.suffix == OLD_REG_EXT:
            self.read_xml(filename)
        else:
            self.read_json(filename)

    def read_xml(self, filename: Path) -> "RegisterSet":
        """Reads the XML file, loading the databsae."""

        LOGGER.info("Reading XML register file %s", str(filename))
        with filename.open("rb") as ifile:
            self.name = filename.stem
            name = filename.parents[1].stem + filename.stem
            parser = RegParser(self, name)
            parser.parse(ifile)
        return self

    def read_json(self, filename: Path) -> "RegisterSet":
        """Reads the JSON file, loading the databsae."""

        self.filename = filename.resolve()

        LOGGER.info("Reading JSON register file %s", str(self.filename))
        try:
            with self.filename.open("r") as ifile:
                self.name = filename.stem
                self.json_decode(json.loads(ifile.read()))
        except json.decoder.JSONDecodeError as msg:
            raise CorruptRegsetFile(self.filename.name, str(msg))
        except OSError as msg:
            raise IoErrorRegsetFile(self._filename.name, msg)
        return self

    def loads(self, data, filename):
        """Reads the XML file, loading the databsae."""

        filename = Path(filename)

        self.filename = filename
        self.name = filename.stem
        ifile = StringIO(data)
        name = filename.parent.stem + filename.stem
        parser = RegParser(self, name)
        parser.parse(ifile)
        return self

    def save(self) -> None:
        "Save the data to the specified file as a JSON file"
        self.save_json(self.json(), self.filename.with_suffix(REG_EXT))

    @property
    def overview_text(self) -> str:
        "Backward compatible method to get first document page"

        pnames = self.doc_pages.get_page_names()
        if pnames:
            data = self.doc_pages.get_page(pnames[0])
            if data:
                return data.page
        return ""

    def add_parameter(self, new_param: ParameterDefinition) -> None:
        "Adds a parameter to the register set"

        self.parameters.add(new_param)

    def find_register_by_name(self, name: str) -> Optional[Register]:
        """Finds a register with the given name, or None if not found"""
        for i in self._registers:
            if self._registers[i].name == name:
                return self._registers[i]
        return None

    def find_register_by_token(self, name: str) -> Optional[Register]:
        """Finds a register with the given token name, or None if not found"""
        for i in self._registers:
            if self._registers[i].token == name:
                return self._registers[i]
        return None

    def find_registers_by_name_regexp(self, name: str) -> List[Register]:
        """Finds a register with the given name, or None if not found"""
        regexp = re.compile(name)
        return [
            self._registers[i]
            for i in self._registers
            if regexp.match(self._registers[i].name)
        ]

    def find_registers_by_token_regexp(self, name: str) -> List[Register]:
        """Finds a register with the given name, or None if not found"""
        regexp = re.compile(name)
        return [
            self._registers[i]
            for i in self._registers
            if regexp.match(self._registers[i].token)
        ]

    def json(self) -> Dict[str, Any]:
        data = {
            "name": self.name,
            "uuid": self.uuid,
            "parameters": self.parameters,
            "title": self.descriptive_title,
            "ports": self.ports,
            "memory": self.memory,
            "array_is_reg": self.array_is_reg,
            "coverage": self.coverage,
            "internal_only": self.internal_only,
            "organization": self.organization,
            "doc_pages": self.doc_pages.json(),
            "owner": self.owner,
            "exports": [],
            "use_interface": self.use_interface,
            "register_inst": [reg for index, reg in self._registers.items()],
        }

        self._dump_exports(self.exports, data["exports"])
        return data

    def json_decode(self, data: Dict[str, Any]) -> None:
        self.parameters = ParameterContainer()
        self.parameters.json_decode(data["parameters"])
        self.descriptive_title = data["title"]

        ports = Signals()
        ports.json_decode(data["ports"])
        self.ports = ports

        self.name = data["name"]
        self.uuid = Uuid(data["uuid"])
        self.array_is_reg = data["array_is_reg"]
        self.memory = data.get("memory", False)
        self.coverage = data["coverage"]
        self.internal_only = data["internal_only"]
        self.organization = data["organization"]

        self.doc_pages = DocPages()
        if "overview_text" in data:
            self.doc_pages.update_page(
                "Overview", data["overview_text"], ["Confidential"]
            )
        else:
            self.doc_pages.json_decode(data["doc_pages"])

        self.owner = data["owner"]
        self.use_interface = data["use_interface"]
        self.modified = False

        for reg_json in data["register_inst"]:
            reg = Register()
            reg.json_decode(reg_json)
            reg.regset_name = self.name
            self._registers[reg.uuid] = reg

        self.exports = []
        for exp_json in data["exports"]:
            exp = ExportData()
            exp.target = str(
                Path(self.filename.parent / exp_json["target"]).resolve()
            )
            exp.options = exp_json["options"]
            exp.exporter = exp_json["exporter"]

            self.exports.append(exp)