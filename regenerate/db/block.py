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
Holds the information for a block.

This includes the name, base address, HDL path, the repeat count,
repeat offset, and the title.

"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import os
import json

from .name_base import Uuid
from .data_reader import FileReader
from .register_inst import RegisterInst
from .register_set import RegisterSet
from .doc_pages import DocPages
from .base_file import BaseFile
from .logger import LOGGER

# from .param_container import ParameterContainer
# from .overrides import ParameterOverrides
# from .param_resolver import ParameterResolver

from .parameters import (
    ParameterResolver,
    ParameterContainer,
    ParameterOverrides,
)
from .regset_finder import RegsetFinder
from .export import ExportData
from .exceptions import (
    CorruptBlockFile,
    IoErrorBlockFile,
    CorruptRegsetFile,
    IoErrorRegsetFile,
)


class Block(BaseFile):
    """
    Defines a Block.

    A block is a collection of register instances and their address
    offsets within the block.

    """

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

        self._regset_insts: List[RegisterInst] = []
        self._regsets: Dict[Uuid, RegisterSet] = {}
        self.parameters = ParameterContainer()
        self.overrides: List[ParameterOverrides] = []
        self.exports: List[ExportData] = []

    def __repr__(self) -> str:
        """
        Return a string representation of the block.

        Returns:
            str: string representation

        """
        return f'Block(name="{self.name}", uuid="{self.uuid}")'

    def add_register_set(self, regset: RegisterSet) -> None:
        """
        Add a register set to the block.

        Parameters:
            regiset (RegisterSet): register set to add

        """
        self._regsets[regset.uuid] = regset

    def add_regset_inst(self, reginst: RegisterInst) -> None:
        """
        Add a register set instance to the block.

        Parameters:
            regset_inst (RegisterInst): register set instance to add

        """
        self._regset_insts.append(reginst)

    def get_reginst_from_id(self, uuid: Uuid) -> Optional[RegisterInst]:
        """
        Return the register instance based on the uuid.

        Parameters:
            uuid: UUID of the register inst

        Returns:
            Optional[Registerinst]: The register instance if it exists.

        """
        results = [inst for inst in self._regset_insts if inst.uuid == uuid]
        if results:
            return results[0]
        return None

    def get_regset_insts(self) -> List[RegisterInst]:
        """
        Return a list of register instances.

        Returns:
            List[RegisterInst]: All register instances in the block

        """
        return self._regset_insts

    def get_regset_from_id(self, uuid: Uuid) -> Optional[RegisterSet]:
        """
        Return a list of register instances.

        Parameters:
            uuid: UUID of the desired register set_access

        Returns:
            Optional[RegisterSet]: The register set, if it exists

        """
        return self._regsets.get(uuid)

    def get_regsets_dict(self) -> Dict[Uuid, RegisterSet]:
        """
        Return a dict of register sets.

        Returns:
            Dict[Uuid, RegisterSet]: dictionary mapping the uuid to register
                sets

        """
        return self._regsets

    def get_regset_from_reg_inst(self, reg_inst: RegisterInst) -> RegisterSet:
        """
        Return the register set connected to the register instance.

        Parameter:
            reg_inst (RegisterInst): register instance

        Returns:
            RegisterSet: register set associated with the register instance

        """
        return self._regsets[reg_inst.regset_id]

    def remove_register_set(self, uuid: Uuid) -> None:
        """
        Remove the register set using the UUID.

        Parameter:
            uuid: Register set to remove

        """
        if uuid in self._regsets:
            del self._regsets[uuid]
        self._regset_insts = [
            inst for inst in self._regset_insts if inst.regset_id != uuid
        ]

    def save(self) -> None:
        """
        Save the data as a JSON file.

        Saves the data to the associated filename.

        """
        self.save_json(self.json(), self._filename)

    def __ne__(self, other: object) -> bool:
        """
        Compare for inequality.

        Parameters:
            other (object): Object to compare against

        Returns:
            bool: True if not equal

        """
        if not isinstance(other, Block):
            return NotImplemented
        return not self.__eq__(other)

    def __eq__(self, other: object) -> bool:
        """
        Compare for equality.

        Parameters:
            other (object): Object to compare against

        Returns:
            bool: True if equal

        """
        if not isinstance(other, Block):
            return NotImplemented
        return (
            self.name == other.name
            and self.uuid == other.uuid
            and self.description == other.description
            and self.address_size == other.address_size
            and self.doc_pages == other.doc_pages
        )

    def open(self, name: Path) -> None:
        """
        Open the filename and loads the data into the object.

        Parameters:
            name (Path): name of the file to save

        """
        self._filename = name

        LOGGER.info("Reading block file %s", str(self._filename))

        try:
            with self._filename.open() as ofile:
                data = ofile.read()
                self.json_decode(json.loads(data))
        except json.decoder.JSONDecodeError as msg:
            raise CorruptBlockFile(str(self._filename.resolve()), str(msg))
        except OSError as msg:
            raise IoErrorBlockFile(str(self._filename.resolve()), msg)

    def get_address_size(self) -> int:
        """
        Return the size of the address space.

        Returns:
            int: address size in bytes

        """
        base = 0
        for reginst in self._regset_insts:
            regset = self._regsets[reginst.regset_id]
            base = max(
                base, reginst.offset + (1 << regset.ports.address_bus_width)
            )
        return base

    def _json_decode_regsets(
        self, data: Dict[Uuid, Any]
    ) -> Dict[Uuid, RegisterSet]:
        """
        Decode the register set section of the JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data to decode

        """
        regsets: Dict[Uuid, RegisterSet] = {}
        for key, item in data.items():
            filename = Path(self._filename.parent / item["filename"]).resolve()

            regset = self.finder.find_by_file(str(filename))
            if not regset:
                regset = RegisterSet()
                rdr = (
                    FileReader(filename)
                    if self.reader_class is None
                    else self.reader_class
                )
                try:
                    json_data = json.loads(rdr.read_bytes(filename))
                except json.decoder.JSONDecodeError as msg:
                    raise CorruptRegsetFile(str(filename.resolve()), str(msg))
                except OSError as msg:
                    raise IoErrorRegsetFile(str(filename.resolve()), msg)

                regset.filename = filename
                regset.json_decode(json_data)
                self.finder.register(regset)
            regsets[regset.uuid] = regset
        return regsets

    def _json_decode_exports(
        self, data: Optional[List[Dict[str, Any]]]
    ) -> List[ExportData]:
        """
        Decode the exports section of the JSON data.

        Parameters:
            data (Optional[List[Dict[str, Any]]): JSON data to decode

        """
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
        """
        Decode the JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data to decode

        """
        self.name = data["name"]
        self.uuid = Uuid(data["uuid"])
        self.description = data["description"]
        self.address_size = int(data["address_size"], 0)
        self.doc_pages = DocPages()
        self.doc_pages.json_decode(data["doc_pages"])

        self._regset_insts = _json_decode_reginsts(data["regset_insts"])
        self._regsets = self._json_decode_regsets(data["regsets"])

        self.parameters = ParameterContainer()
        self.parameters.json_decode(data["parameters"])

        self.exports = self._json_decode_exports(data.get("exports"))

        self.overrides = []
        resolver = ParameterResolver()
        try:
            for override in data["overrides"]:
                item = ParameterOverrides()
                item.json_decode(override)
                for regset_inst in self._regset_insts:
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
        """
        Encode the object to a JSON dictionary.

        Returns:
            Dict[str, Any]: JSON-ish dictionary

        """
        data: Dict[str, Any] = {
            "name": self.name,
            "uuid": Uuid(self.uuid),
            "parameters": self.parameters,
            "overrides": self.overrides,
            "address_size": f"{self.address_size}",
            "doc_pages": self.doc_pages.json(),
            "description": self.description,
            "regset_insts": self._regset_insts,
            "exports": [],
            "regsets": {},
        }

        self._dump_exports(self.exports, data["exports"])

        for name in self._regsets:
            new_path = os.path.relpath(
                self._regsets[name].filename,
                self._filename.parent,
            )
            data["regsets"][name] = {
                "filename": new_path,
            }

        return data


def _json_decode_reginsts(data: List[Any]) -> List[RegisterInst]:
    """
    Decode the register instance section of the JSON data.

    Parameters:
        data (List[Any]): JSON data

    Returns:
        List[RegisterInst]: list of register instances

    """
    reginst_list = []
    for rset in data:
        ginst = RegisterInst()
        ginst.json_decode(rset)
        reginst_list.append(ginst)
    return reginst_list
