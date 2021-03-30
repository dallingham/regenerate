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

import os
import json
import re
from operator import methodcaller
from io import BytesIO as StringIO
from pathlib import Path
from typing import Union, Optional

from .register import Register
from .reg_parser import RegParser
from .reg_parser_json import RegParserJSON
from .reg_writer import RegWriter
from .signals import Signals
from .const import OLD_REG_EXT, REG_EXT
from .containers import Container
from .export import ExportData


class RegisterDb:
    """
    Container database for a set of registers.
    """

    def __init__(self, filename=None):

        self._module = "unnamed_regs"
        self._title = ""
        self._registers = {}
        self._parameters = []
        self.exports: List[ExportData] = []

        self.ports = Signals()

        self.array_is_reg = False
        self.internal_only = False
        self.owner = ""
        self.organization = ""
        self.use_interface = False
        self.overview_text = ""
        self.coverage = True
        self.set_name = ""
        self._filename = None
        self.modified = False

        if filename is not None:
            self.read_db(filename)
            self.filename = Path(filename)
            
    @property
    def filename(self) -> Path:
        return self._filename

    @filename.setter
    def filename(self, value: Union[str, Path]) -> None:
        self._filename = Path(value).with_suffix(REG_EXT)
            
    def total_bits(self):
        """Returns bits in register"""
        bits = 0
        for key in self._registers:
            reg = self._registers[key]
            for field in reg.get_bit_fields():
                bits += field.width
        return bits

    def get_keys(self):
        """Returns the register keys, which is the address of the register"""
        return [
            a.uuid
            for a in sorted(self._registers.values(), key=lambda a: a.address)
        ]

    def get_all_registers(self):
        """Returns the register keys, which is the address of the register"""
        return iter(sorted(self._registers.values(), key=lambda a: a.address))

    def get_register(self, key):
        """
        Returns the register from the specified key, which should be the
        address.
        """
        return self._registers.get(key)

    def add_register(self, reg):
        """Adds the register to the database."""
        self._registers[reg.uuid] = reg
        reg.set_parameters(self._parameters)

    def delete_register(self, reg):
        """Removes the register to the database."""
        del self._registers[reg.uuid]

    def read_db(self, filename: Path):

        if filename.suffix == OLD_REG_EXT:
            self.read_xml(filename)
        else:
            self.read_json(filename)

    def read_xml(self, filename: Path):
        """Reads the XML file, loading the databsae."""

        with filename.open("rb") as ifile:
            self.set_name = filename.stem
            parser = RegParser(self)
            parser.parse(ifile)
        return self

    def read_json(self, filename: Path):
        """Reads the XML file, loading the databsae."""

        self.filename = filename.resolve()

        with self.filename.open("r") as ifile:
            self.set_name = filename.stem
            parser = RegParserJSON(self)
            parser.parse(ifile)
        return self

    def save_xml(self, filename):
        """Saves the database to the specified XML file"""
        self.filename = Path(filename)
        writer = RegWriter(self)
        writer.save(filename)

    def loads(self, data, filename):
        """Reads the XML file, loading the databsae."""

        filename = Path(filename)

        self.set_name = filename.stem
        ifile = StringIO(data)
        parser = RegParser(self)
        parser.parse(ifile)
        return self

    def save(self):
        try:
            data = self.json()
            with self.filename.open("w") as ofile:
                ofile.write(
                    json.dumps(data, default=methodcaller("json"), indent=4)
                )
        except FileNotFoundError as msg:
            LOGGER.error(str(msg))

    @property
    def module_name(self):
        """
        Gets _module, which is accessed via the module_name property
        """
        return self._module

    @module_name.setter
    def module_name(self, name):
        """
        Sets _module, which is accessed via the module_name property
        """
        self._module = name.replace(" ", "_")

    @property
    def descriptive_title(self):
        """
        Gets _title, which is accessed via the descriptive_title property
        """
        return self._title

    @descriptive_title.setter
    def descriptive_title(self, name):
        """
        Sets _title, which is accessed via the descriptive_title property
        """
        self._title = name.strip()

    def find_register_by_name(self, name):
        """Finds a register with the given name, or None if not found"""
        for i in self._registers:
            if self._registers[i].name == name:
                return self._registers[i]
        return None

    def find_register_by_token(self, name):
        """Finds a register with the given token name, or None if not found"""
        for i in self._registers:
            if self._registers[i].token == name:
                return self._registers[i]
        return None

    def find_registers_by_name_regexp(self, name):
        """Finds a register with the given name, or None if not found"""
        regexp = re.compile(name)
        return [
            self._registers[i]
            for i in self._registers
            if regexp.match(self._registers[i].name)
        ]

    def find_registers_by_token_regexp(self, name):
        """Finds a register with the given name, or None if not found"""
        regexp = re.compile(name)
        return [
            self._registers[i]
            for i in self._registers
            if regexp.match(self._registers[i].token)
        ]

    def get_parameters(self):
        """Returns the parameter list"""
        return self._parameters

    def add_parameter(self, parameter):
        """Adds a parameter to the list"""

        self._parameters.append(parameter)

    def remove_parameter(self, name):
        """Removes a parameter from the list if it exists"""
        self._parameters = [p for p in self._parameters if p.name != name]

    def set_parameters(self, parameter_list):
        """Sets the parameter list"""
        self._parameters = parameter_list

    def json(self):
        data = {
            "module": self._module,
            "parameters": self._parameters,
            "title": self._title,
            "ports": self.ports,
            "set_name": self.set_name,
            "array_is_reg": self.array_is_reg,
            "coverage": self.coverage,
            "internal_only": self.internal_only,
            "organization": self.organization,
            "overview_text": self.overview_text,
            "owner": self.owner,
            "use_interface": self.use_interface,
            "register_inst": [reg for index, reg in self._registers.items()],
        }
        data["exports"] = []

        for exp in self.exports:
            info = {
                "exporter": exp.exporter,
                "target": os.path.relpath(exp.target, self.filename.parent),
                "options": exp.options,
            }
            data["exports"].append(info)
            
        return data

    def json_decode(self, data):
        self._module = data["module"]
        self._parameters = data["parameters"]
        self._title = data["title"]

        ports = Signals()
        ports.json_decode(data["ports"])
        self.ports = ports

        self.set_name = data["set_name"]
        self.array_is_reg = data["array_is_reg"]
        self.coverage = data["coverage"]
        self.internal_only = data["internal_only"]
        self.organization = data["organization"]
        self.overview_text = data["overview_text"]
        self.owner = data["owner"]
        self.use_interface = data["use_interface"]
        self.modified = False

        for reg_json in data["register_inst"]:
            reg = Register()
            reg.json_decode(reg_json)
            self._registers[reg.uuid] = reg

        self.exports = []
        for exp_json in data["exports"]:
            exp = ExportData()
            exp.target = Path(
                self.filename.parent / exp_json["target"]
            ).resolve()
            exp.options = exp_json["options"]
            exp.exporter = exp_json["exporter"]

            self.exports.append(exp)

