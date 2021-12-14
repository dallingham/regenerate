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
RegProject is the container object for a regenerate project
"""

from collections import defaultdict
from pathlib import Path
import json
import os.path
from typing import (
    List,
    Dict,
    ValuesView,
    Any,
    Optional,
    Union,
    Tuple,
)
import xml.sax.saxutils

from .name_base import Uuid
from .data_reader import FileReader
from .address_map import AddressMap
from .block import Block
from .block_inst import BlockInst
from .register_inst import RegisterInst
from .const import REG_EXT, PRJ_EXT, OLD_PRJ_EXT, OLD_REG_EXT
from .param_resolver import ParameterResolver
from .exceptions import CorruptProjectFile, IoErrorProjectFile
from .doc_pages import DocPages
from .export import ExportData
from .logger import LOGGER
from .overrides import Overrides
from .param_container import ParameterContainer
from .proj_reader import ProjectReader
from .register_db import RegisterDb
from .textutils import clean_text
from .regset_finder import RegsetFinder
from .base_file import BaseFile


def nested_dict(depth: int) -> Dict[Uuid, Any]:
    """Builds a nested dictionary"""
    if depth == 1:
        return defaultdict(int)
    return defaultdict(lambda: nested_dict(depth - 1))


def cleanup(data: str) -> str:
    "Convert some unicode characters to standard ASCII"
    return xml.sax.saxutils.escape(clean_text(data))


class RegProject(BaseFile):
    """
    RegProject is the container object for a regenerate project.

    The project consists of several different types. General project
    information (name, company_name, etc.), the list of register sets,
    groupings of instances, and exports (register set and entire
    project exports), and address maps.
    """

    def __init__(self, path: Optional[Path] = None):

        super().__init__("unnamed", Uuid(""))
        self.short_name = "unnamed"
        self.doc_pages = DocPages()
        self.doc_pages.update_page("Overview", "", ["Confidential"])
        self.company_name = ""
        self.access_map = nested_dict(3)
        self.finder = RegsetFinder()
        self._filelist: List[Path] = []
        self.reader_class = None
        self.block_data_path = ""

        self.parameters = ParameterContainer()
        self.overrides: List[Overrides] = []
        self.address_maps: Dict[Uuid, AddressMap] = {}

        self.block_insts: List[BlockInst] = []
        self.blocks: Dict[Uuid, Block] = {}
        self.regsets: Dict[Uuid, RegisterDb] = {}

        self.exports: List[ExportData] = []

        if path:
            self._filename = Path(path)
            self.open(self._filename)
        else:
            self._filename = Path(".")

    def save(self) -> None:
        """Saves the project to the JSON file"""

        new_path = Path(self._filename).with_suffix(PRJ_EXT)
        self.block_data_path = str(new_path.parent)

        self.save_json(self.json(), new_path)

        for blkid in self.blocks:
            blk = self.blocks[blkid]
            if blk.modified:
                LOGGER.info(
                    "Saving block %s - %s", blk.name, str(blk.filename)
                )
                blk.save()
                blk.modified = False

        for regid in self.regsets:
            reg = self.regsets[regid]
            if reg.modified:
                LOGGER.info(
                    "Saving register set %s - %s", reg.name, str(reg.filename)
                )
                reg.save()
                reg.modified = False

    def open(self, name: Union[str, Path]) -> None:
        """Opens and reads a project file. The project could be in either
        the legacy XML format or the current JSON format"""

        self._filename = Path(name)

        if self._filename.suffix == OLD_PRJ_EXT:
            LOGGER.info("Loading XML project file '%s'", str(self._filename))

            with self._filename.open("rb") as xfile:
                self.loads(xfile.read(), str(self._filename))
        else:
            LOGGER.info("Loading JSON project file '%s'", str(self._filename))

            try:
                with open(str(self._filename)) as jfile:
                    self.json_loads(jfile.read())
            except json.decoder.JSONDecodeError as msg:
                raise CorruptProjectFile(self._filename.name, str(msg))
            except OSError as msg:
                raise IoErrorProjectFile(self._filename.name, msg)

    def xml_loads(self, data: bytes, name: str) -> None:
        """
        Load the XML data from the passed string.

        Parameters:
           data (bytes): data stream from the json file

           name (str): name of the file

        """
        self.loads(data, name)

    def json_loads(self, data: str) -> None:
        """
        Loads the JSON data from the passed string.

        Parameters:
           data (bytes): data stream from the json file

        """
        json_data = json.loads(data)
        self.json_decode(json_data)

        for _, block in self.blocks.items():
            for _, reg_set in block.regsets.items():
                self.regsets[reg_set.uuid] = reg_set

    def loads(self, data: bytes, name: str) -> None:
        """
        Read XML from a string.

        Parameters:
           data (bytes): data stream from the json file

           name (str): name of the file

        """
        reader = ProjectReader(self)
        reader.loads(data, name)
        self._filename = Path(name)

        for block in self.blocks.values():
            for reg_set in block.regsets.values():
                self.regsets[reg_set.uuid] = reg_set

    def get_blkinst_from_id(self, uuid: Uuid) -> Optional[BlockInst]:
        """
        Return the block instance from the uuid.

        Parameters:
            uuid (Uuid): block instance's uuid

        Returns:
            Optional[BlockInst]: BlockInst if it exists, else None

        """
        results = [inst for inst in self.block_insts if inst.uuid == uuid]
        if results:
            return results[0]
        return None

    def remove_block(self, blk_id: Uuid) -> None:
        """
        Remove a block from the database.

        Parameters:
            blk_id (Uuid): uuid of the block to remove

        """
        del self.blocks[blk_id]
        self.block_insts = [
            inst for inst in self.block_insts if inst.blkid != blk_id
        ]
        for addr_id, addr_map in self.address_maps.items():
            addr_map.block_insts = [
                map_id for map_id in addr_map.block_insts if addr_id != blk_id
            ]

    def append_register_set_to_list(self, name: Path) -> None:
        """
        Add a register set to the project.

        The register path is added to the project, and the file is loaded. Both
        old style (.rprj XML) and new style (.regp JSON) files are supported
        and loaded based on their extension.

        The FileReader class is the default reader to use if the reader_class
        variable has not been set. This exists so that other methods can be
        used to load data (e.g. GitLab REST API).

        Parameters:
            name (Path): path to the register set to add

        """
        self.modified = True

        if self.reader_class is None:
            rdr = FileReader(self._filename)
        else:
            rdr = self.reader_class

        filename, new_file_path = rdr.resolve_path(name)

        regset = self.finder.find_by_file(str(filename))
        if not regset:
            regset = RegisterDb()
            data = rdr.read_bytes(filename)
            if Path(filename).suffix == OLD_REG_EXT:
                regset.loads(data, filename)
            else:
                regset.json_decode(json.loads(data))
            self.finder.register(regset)
            self.new_register_set(regset, new_file_path)

    def new_register_set(self, regset: RegisterDb, path: Path) -> None:
        "Stores the register set and its path"

        self.regsets[regset.uuid] = regset
        self._filelist.append(path)

    def add_register_set(self, path: Path) -> None:
        """
        Adds a new register set to the project.

        Alias for append_register_set_to_list

        Parameters:
            path (Path): path to the register set to add
        """
        self.append_register_set_to_list(path)

    def remove_register_set(self, uuid: Uuid) -> None:
        """Removes the specified register set from the project."""

        self.modified = True
        regset = self.regsets[uuid]
        del self.regsets[uuid]

        try:
            self._filelist.remove(regset.filename)
        except ValueError:
            LOGGER.debug("Failed removing %s from filelist", regset.filename)

    def get_exports(self, path: str) -> Tuple[ExportData, ...]:
        """
        Converts the exports to be relative to the passed path. Returns a
        read-only tuple
        """
        for regset in self.regsets.values():
            if str(regset.filename) == path:
                return tuple(regset.exports)
        return tuple([])

    def get_project_exports(self) -> Tuple[ExportData, ...]:
        """Returns the export project list, returns a read-only tuple"""
        return tuple(self.exports)

    def append_to_project_export_list(self, exporter: str, dest: str) -> None:
        """
        Adds a export to the project export list. Project exporters operation
        on the entire project, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self.modified = True
        exp = ExportData(exporter, dest)
        self.exports.append(exp)

    def add_to_project_export_list(
        self, exporter: str, dest: str, options: Dict[str, str]
    ) -> None:
        """
        Adds a export to the project export list. Project exporters operation
        on the entire project, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        exporter - the chosen export exporter (exporter)
        dest - destination output name
        """
        self.modified = True
        self.exports.append(ExportData(exporter, dest, options))

    def remove_from_project_export_list(
        self, exporter: str, dest: str
    ) -> None:
        """Removes the export from the project export list"""
        self.modified = True
        self.exports = [
            exp
            for exp in self.exports
            if exp.expo.rter != exporter or exp.target != dest
        ]

    def get_block_instances(self):
        "Return the block instances"
        return self.block_insts

    def get_block_from_block_inst(self, blk_inst: BlockInst) -> Block:
        "Find the block associated with a particular block instance"
        return self.blocks[blk_inst.blkid]

    def get_regset_from_regset_inst(
        self, regset_inst: RegisterInst
    ) -> RegisterDb:
        "Find the regset associated with a particular regset instance"
        return self.regsets[regset_inst.regset_id]

    def get_register_set(self) -> List[Path]:
        """
        Returns the register databases (XML files) referenced by the project
        file.
        """
        if self._filename is None:
            return self._filelist
        base = self._filename.parent
        return [Path(base / i).resolve() for i in self._filelist]

    def get_address_maps(self) -> ValuesView[AddressMap]:
        """Returns a list of the existing address maps"""
        return self.address_maps.values()

    def get_blocks_in_address_map(self, map_id: Uuid) -> List[BlockInst]:
        """Returns the address maps associated with the specified group."""
        addr_map = self.address_maps.get(map_id)
        if addr_map:
            blocks = addr_map.block_insts
            if blocks:
                return [
                    blk_inst
                    for blk_inst in self.block_insts
                    if blk_inst.name in set(blocks)
                ]
        return self.block_insts

    def get_address_maps_used_by_block(self, blk_id: Uuid) -> List[Uuid]:
        """Returns the address maps associated with the specified group."""

        map_list: List[Uuid] = []
        for key in self.address_maps:
            if blk_id in self.address_maps[key].block_insts:
                map_list.append(key)
        return map_list

    def change_address_map_name(self, map_id: Uuid, new_name: str) -> None:
        """Changes the name of an address map"""

        self.address_maps[map_id].name = new_name
        self.modified = True

    def add_address_map_to_block(self, map_id: Uuid, blk_id: Uuid) -> bool:
        """Adds an address map to a group if it does not already exist"""
        if blk_id not in self.address_maps[map_id].block_insts:
            self.address_maps[map_id].block_insts.append(blk_id)
            return True
        return False

    def get_address_base(self, map_id: Uuid) -> int:
        """Returns the base address  of the address map"""
        return self.address_maps[map_id].base

    def get_address_width(self, map_id: Uuid) -> int:
        """Returns the width of the address group"""
        try:
            return self.address_maps[map_id].width
        except KeyError:
            LOGGER.error(
                "Address map not found (%s) - valid %s",
                map_id,
                list(self.address_maps.keys()),
            )
        return 16

    def set_access(
        self,
        map_id: Uuid,
        blkinst_uuid: Uuid,
        reginst_uuid: Uuid,
        access: int,
    ) -> None:
        """Sets the access mode"""
        self.access_map[map_id][blkinst_uuid][reginst_uuid] = access

    def get_access(
        self, map_id: Uuid, blkinst_uuid: Uuid, reginst_uuid: Uuid
    ) -> int:
        """Gets the access mode"""

        try:
            return self.access_map[map_id][blkinst_uuid][reginst_uuid]
        except (KeyError, TypeError):
            return 0

    def add_or_replace_address_map(self, addr_map: AddressMap) -> None:
        """Sets the specififed address map"""

        self.modified = True
        self.address_maps[addr_map.uuid] = addr_map

    def set_address_map(self, address_map: AddressMap) -> None:
        """Sets the specififed address map"""
        self.modified = True
        self.address_maps[address_map.uuid] = address_map

    def set_address_map_block_list(
        self, map_id: Uuid, new_list: List[Uuid]
    ) -> None:
        """Sets the specififed address map"""
        self.modified = True
        self.address_maps[map_id].block_insts = new_list

    def remove_address_map(self, map_id: Uuid) -> None:
        """Removes the address map"""
        if map_id in self.address_maps:
            del self.address_maps[map_id]

    @property
    def files(self) -> Tuple[Path, ...]:
        """Returns the file list"""
        return tuple(self._filelist)

    def change_file_suffix(self, original: str, new: str) -> None:
        """Changes the suffix of the files in the file list"""

        new_list = []
        for name in self._filelist:
            new_name = Path(name)
            if new_name.suffix == original:
                new_name = new_name.with_suffix(new)
            new_list.append(new_name.resolve())
        self._filelist = new_list

    def blocks_containing_regset(self, regset_id: Uuid) -> List[Block]:
        "Find all the blocks that contain the register set id"
        return [
            self.blocks[blk]
            for blk in self.blocks
            if regset_id in self.blocks[blk].regsets
        ]

    def instances_of_block(self, block: Block) -> List[BlockInst]:
        "Return all the instances of a block"
        return [
            blk_inst
            for blk_inst in self.block_insts
            if blk_inst.blkid == block.uuid
        ]

    @property
    def documentation(self) -> str:
        "Backward compatible method torn the first doc string"

        page_names = self.doc_pages.get_page_names()
        if page_names:
            page = self.doc_pages.get_page(page_names[0])
            if page:
                return page[0]
        return ""

    def json(self) -> Dict[str, Any]:
        """Convert the data into a JSON compatible dict"""

        json_keys = (
            "short_name",
            "name",
            "doc_pages",
            "company_name",
            "access_map",
            "parameters",
            "overrides",
            "block_insts",
        )
        data = {}
        for key in json_keys:
            token = key[1:] if key[0] == "_" else key
            data[token] = self.__getattribute__(key)

        data["filelist"] = [
            os.path.relpath(
                Path(fname).with_suffix(REG_EXT), self._filename.parent
            )
            for fname in set(self._filelist)
        ]
        data["address_maps"] = self.address_maps

        data["exports"] = []
        for exp in self.exports:
            info = {
                "options": exp.options,
                "target": os.path.relpath(exp.target, self._filename.parent),
                "exporter": exp.exporter,
            }
            data["exports"].append(info)

        data["blocks"] = {}
        for blk in self.blocks:
            data["blocks"][blk] = {
                "filename": os.path.relpath(
                    str(self.blocks[blk].filename), self._filename.parent
                ),
            }

        return data

    def json_decode(self, data: Dict[str, Any]) -> None:
        """Convert the JSON data back classes"""

        self.block_data_path = str(self._filename.parent)
        skip = False

        self.short_name = data["short_name"]
        self.name = data["name"]
        self.doc_pages = DocPages()
        self.doc_pages.json_decode(data["doc_pages"])
        self.company_name = data["company_name"]
        if "access_map" in data and data["access_map"] is not None:
            self.access_map = data["access_map"]
        else:
            self.access_map = nested_dict(3)

        self.block_insts = data["block_insts"]
        self._filelist = []

        if not skip:
            for path in data["filelist"]:
                full_path = Path(self._filename.parent / path).resolve()
                self._filelist.append(
                    Path(os.path.relpath(full_path, self._filename.parent))
                )

        self._load_address_maps_from_json_data(data["address_maps"])

        if not skip:
            self._load_exports_from_json_data(data["exports"])

        self._load_block_insts_from_json_data(data["block_insts"])
        self._load_blocks_from_json_data(data["blocks"])

        self.parameters = ParameterContainer()
        self.parameters.json_decode(data["parameters"])

        self._load_overrides_from_json_data(data["overrides"])
        self._load_missing_register_sets()

    def _load_address_maps_from_json_data(self, data: Dict[str, Any]) -> None:
        "Loads the address map information from JSON data"

        if data:
            for uuid, addr_data_json in data.items():
                addr_data = AddressMap()
                addr_data.json_decode(addr_data_json)
                self.address_maps[Uuid(uuid)] = addr_data

    def _load_exports_from_json_data(self, data: List[Dict[str, Any]]) -> None:
        "Loads the export information from JSON data"

        self.exports = []
        for item in data:
            exporter = item["exporter"]
            target = self._filename.parent / item["target"]

            exp_data = ExportData(
                exporter,
                str(target.resolve()),
            )
            exp_data.options = item["options"]

            self.exports.append(exp_data)

    def _load_block_insts_from_json_data(
        self, data: List[Dict[str, Any]]
    ) -> None:
        "Loads the block instances from JSON data"

        self.block_insts = []
        for blk_inst_data_json in data:
            blk_inst_data = BlockInst()
            blk_inst_data.json_decode(blk_inst_data_json)
            self.block_insts.append(blk_inst_data)

    def _load_blocks_from_json_data(self, data: Dict[str, Any]) -> None:
        "Loads the blocks from JSON data"

        self.blocks = {}
        if data:
            for key in data:
                blk_data = Block()
                base_path = data[key]["filename"]

                if self.reader_class:
                    rdr = self.reader_class
                    text = rdr.read_bytes(base_path)

                    json_data = json.loads(text)
                    blk_data.filename, _ = self.reader_class.resolve_path(
                        base_path
                    )
                    blk_data.reader_class = self.reader_class.__class__(
                        base_path,
                        self.reader_class.repo,
                        self.reader_class.rtl_id,
                    )
                    blk_data.json_decode(json_data)
                else:
                    path = self._filename.parent / base_path
                    blk_data.open(path)

                self.blocks[Uuid(key)] = blk_data

    def _load_overrides_from_json_data(
        self, data: List[Dict[str, Any]]
    ) -> None:
        "Loads the overrides from the JSON data"

        self.overrides = []
        try:
            for override in data:
                item = Overrides()
                item.json_decode(override)
                self.overrides.append(item)
        except KeyError:
            ...

        resolver = ParameterResolver()
        for override_val in self.overrides:
            resolver.add_blockinst_override(
                override_val.path, override_val.parameter, override_val.value
            )

    def _load_missing_register_sets(self):
        """
        Loads any registers sets not loaded by the blocks, but listed in
        the filelist
        """

        for filename in self._filelist:
            full_path = (self._filename.parent / filename).resolve()
            regset = self.finder.find_by_file(str(full_path))
            if not regset and full_path.exists():
                regset = RegisterDb()
                if self.reader_class is None:
                    rdr = FileReader(full_path)
                else:
                    rdr = self.reader_class

                json_data = json.loads(rdr.read_bytes(full_path))
                regset.filename = full_path
                regset.json_decode(json_data)
                self.finder.register(regset)
                self.regsets[regset.uuid] = regset
