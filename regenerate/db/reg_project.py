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
from operator import methodcaller
from pathlib import Path
import json
import os.path
from typing import List, Dict, ValuesView, Any, Optional, Union
import xml.sax.saxutils

from .data_reader import FileReader
from .address_map import AddressMap
from .block import Block
from .block_inst import BlockInst
from .const import REG_EXT, PRJ_EXT, OLD_PRJ_EXT, OLD_REG_EXT
from .containers import Container
from .doc_pages import DocPages
from .export import ExportData
from .logger import LOGGER
from .overrides import Overrides
from .param_container import ParameterContainer
from .proj_reader import ProjectReader
from .register_db import RegisterDb
from .textutils import clean_text
from .regset_finder import RegsetFinder


def nested_dict(depth: int, dict_type):
    """Builds a nested dictionary"""
    if depth == 1:
        return defaultdict(dict_type)
    return defaultdict(lambda: nested_dict(depth - 1, dict_type))


def cleanup(data: str) -> str:
    "Convert some unicode characters to standard ASCII"
    return xml.sax.saxutils.escape(clean_text(data))


class RegProject:
    """
    RegProject is the container object for a regenerate project. The project
    consists of several different types. General project information (name,
    company_name, etc.), the list of register sets, groupings of instances,
    and exports (register set and entire project exports), and address maps.
    """

    def __init__(self, path: Optional[Path] = None):

        self.short_name = "unnamed"
        self.name = "unnamed"
        self.doc_pages = DocPages()
        self.doc_pages.update_page("Overview", "")
        self.company_name = ""
        self.access_map = nested_dict(3, int)
        self.finder = RegsetFinder()
        self._filelist: List[Path] = []
        self.reader_class = None

        self.parameters = ParameterContainer()
        self.overrides: List[Overrides] = []
        self.address_maps: Dict[str, AddressMap] = {}

        self.block_insts: List[BlockInst] = []
        self.blocks: Dict[str, Block] = {}
        self.regsets: Dict[str, RegisterDb] = {}

        self.exports: List[ExportData] = []

        self._modified = False

        if path:
            self.path = Path(path)
            self.open(self.path)
        else:
            self.path = Path(".")

    def save(self) -> None:
        """Saves the project to the JSON file"""

        new_path = Path(self.path).with_suffix(PRJ_EXT)
        Container.block_data_path = str(new_path.parent)

        with new_path.open("w") as ofile:
            ofile.write(
                json.dumps(self, default=methodcaller("json"), indent=4)
            )
        self.modified = False

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

        self.path = Path(name)

        if self.path.suffix == OLD_PRJ_EXT:
            LOGGER.info("Loading XML project file '%s'", str(self.path))

            with self.path.open("rb") as xfile:
                self.loads(xfile.read(), str(self.path))
        else:
            LOGGER.info("Loading JSON project file '%s'", str(self.path))

            with open(str(self.path)) as jfile:
                self.json_loads(jfile.read())

    def xml_loads(self, data: bytes, name: str) -> None:
        "Load the XML data from the passed string"

        self.loads(data, name)

    def json_loads(self, data: str) -> None:
        "Loads the JSON data from the passed string"

        json_data = json.loads(data)
        self.json_decode(json_data)

        for _, block in self.blocks.items():
            for _, reg_set in block.regsets.items():
                self.regsets[reg_set.uuid] = reg_set

    def loads(self, data: bytes, name: str) -> None:
        """Reads XML from a string"""

        reader = ProjectReader(self)
        reader.loads(data, name)
        self.path = Path(name)

        for _, block in self.blocks.items():
            for _, reg_set in block.regsets.items():
                self.regsets[reg_set.uuid] = reg_set

    def remove_block(self, blk_id: str) -> None:
        "Removes a block from the database"

        del self.blocks[blk_id]
        self.block_insts = [
            inst for inst in self.block_insts if inst.blkid != blk_id
        ]
        for addr_id in self.address_maps:
            addr_map = self.address_maps[addr_id]
            addr_map.blocks = [
                map_id for map_id in addr_map.blocks if addr_id != blk_id
            ]

    def append_register_set_to_list(self, name: Path) -> None:
        "Adds a register set"

        self._modified = True

        if self.reader_class is None:
            rdr = FileReader(self.path)
        else:
            rdr = self.reader_class

        filename, new_file_path = rdr.resolve_path(name)

        regset = self.finder.find_by_file(str(filename))
        if not regset:
            regset = RegisterDb()
            if Path(filename).suffix == OLD_REG_EXT:
                data = rdr.read_bytes(filename)
                regset.loads(data, filename)
            else:
                data = rdr.read_bytes(filename)
                regset.json_decode(json.loads(data))
            self.finder.register(regset)
            self.new_register_set(regset, new_file_path)

    def new_register_set(self, regset: RegisterDb, path: Path) -> None:
        "Stores the register set and its path"

        self.regsets[regset.uuid] = regset
        self._filelist.append(path)
        print(self.regsets, self._filelist)

    def add_register_set(self, path: Path) -> None:
        """
        Adds a new register set to the project. Note that this only records
        the filename, and does not actually keep a reference to the RegisterDb.
        """
        self.append_register_set_to_list(path)

    def remove_register_set(self, uuid: str) -> None:
        """Removes the specified register set from the project."""

        self._modified = True
        regset = self.regsets[uuid]
        del self.regsets[uuid]

        try:
            self._filelist.remove(regset.filename)
        except ValueError:
            LOGGER.debug("Failed removing %s from filelist", regset.filename)

    def get_exports(self, path: str):
        """
        Converts the exports to be relative to the passed path. Returns a
        read-only tuple
        """
        for regset in self.regsets.values():
            if str(regset.filename) == path:
                return tuple(regset.exports)
        return tuple([])

    def get_project_exports(self):
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
        self._modified = True
        exp = ExportData(exporter, dest)
        self.exports.append(exp)

    def add_to_project_export_list(self, exporter: str, dest: str) -> None:
        """
        Adds a export to the project export list. Project exporters operation
        on the entire project, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        exporter - the chosen export exporter (exporter)
        dest - destination output name
        """
        self._modified = True
        dest = os.path.relpath(dest, self.path.parent)
        self.exports.append(ExportData(exporter, dest))

    def remove_from_project_export_list(
        self, exporter: str, dest: str
    ) -> None:
        """Removes the export from the project export list"""
        self._modified = True
        self.exports = [
            exp
            for exp in self.exports
            if not (exp.exporter == exporter and exp.target == dest)
        ]

    def get_register_set(self) -> List[Path]:
        """
        Returns the register databases (XML files) referenced by the project
        file.
        """
        if self.path is None:
            return self._filelist
        base = self.path.parent
        return [Path(base / i).resolve() for i in self._filelist]

    def get_address_maps(self) -> ValuesView[AddressMap]:
        """Returns a list of the existing address maps"""
        return self.address_maps.values()

    def get_blocks_in_address_map(self, map_id: str) -> List[BlockInst]:
        """Returns the address maps associated with the specified group."""
        addr_map = self.address_maps.get(map_id)
        if addr_map:
            blocks = addr_map.blocks
            if blocks:
                return [
                    blk_inst
                    for blk_inst in self.block_insts
                    if blk_inst.name in set(blocks)
                ]
        return self.block_insts

    def get_address_maps_used_by_block(self, blk_id: str) -> List[str]:
        """Returns the address maps associated with the specified group."""

        used_in_uvm = set(
            {m.uuid for m in self.address_maps.values() if m.uvm == 0}
        )
        map_list = []
        for key in self.address_maps:
            if key in used_in_uvm and blk_id in self.address_maps[key].blocks:
                map_list.append(key)
        return map_list

    def change_address_map_name(self, map_id: str, new_name: str) -> None:
        """Changes the name of an address map"""

        self.address_maps[map_id].name = new_name
        self._modified = True

    def add_address_map_to_block(self, map_id: str, blk_id: str) -> bool:
        """Adds an address map to a group if it does not already exist"""
        if blk_id not in self.address_maps[map_id].blocks:
            self.address_maps[map_id].blocks.append(blk_id)
            return True
        return False

    def get_address_base(self, map_id: str):
        """Returns the base address  of the address map"""
        return self.address_maps[map_id].base

    def get_address_fixed(self, map_id: str):
        """Indicates if the specified address map is at a fixed location"""
        return next(
            (d.fixed for d in self.address_maps.values() if map_id == d.uuid),
            None,
        )

    def get_address_uvm(self, map_id: str):
        """Indicates if the specified address map is at a fixed location"""
        return next(
            (d.uvm for d in self.address_maps.values() if map_id == d.uuid),
            None,
        )

    def get_address_width(self, map_id: str):
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
        self, map_id: str, group_name: str, block_name: str, access
    ):
        """Sets the access mode"""
        self.access_map[map_id][group_name][block_name] = access

    def get_access_items(self, map_id, group_name):
        """Gets the access items for the map/group"""

        grp_map = self.access_map[map_id][group_name]
        return [(key, grp_map[key]) for key in grp_map]

    def get_access(self, map_id, group_name, block_name):
        """Gets the access mode"""

        try:
            return self.access_map[map_id][group_name][block_name]
        except KeyError:
            return 0

    def add_or_replace_address_map(self, addr_map):
        """Sets the specififed address map"""

        self._modified = True
        self.address_maps[addr_map.uuid] = addr_map

    def set_address_map(self, address_map):
        """Sets the specififed address map"""
        self._modified = True
        self.address_maps[address_map.uuid] = address_map

    def set_address_map_block_list(self, map_id: str, new_list: List[str]):
        """Sets the specififed address map"""
        self._modified = True
        self.address_maps[map_id].blocks = new_list

    def remove_address_map(self, map_id):
        """Removes the address map"""
        del self.address_maps[map_id]

    @property
    def files(self):
        """Returns the file list"""
        return tuple(self._filelist)

    @property
    def modified(self):
        """Sets the modified flag"""
        return self._modified

    @modified.setter
    def modified(self, value: bool):
        """Clears the modified flag"""
        self._modified = bool(value)

    def change_file_suffix(self, original: str, new: str):
        """Changes the suffix of the files in the file list"""

        new_list = []
        for name in self._filelist:
            new_name = Path(name)
            if new_name.suffix == original:
                new_name = new_name.with_suffix(new)
            new_list.append(new_name.resolve())
        self._filelist = new_list

    def blocks_containing_regset(self, regset_id: str) -> List[Block]:
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
                return page
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
            if key[0] == "_":
                token = key[1:]
            else:
                token = key
            data[token] = self.__getattribute__(key)

        data["filelist"] = [
            os.path.relpath(Path(fname).with_suffix(REG_EXT), self.path.parent)
            for fname in set(self._filelist)
        ]
        data["address_maps"] = self.address_maps

        data["exports"] = []
        for exp in self.exports:
            info = {
                "options": exp.options,
                "target": os.path.relpath(exp.target, self.path.parent),
                "exporter": exp.exporter,
            }
            data["exports"].append(info)

        data["blocks"] = {}
        for blk in self.blocks:
            data["blocks"][blk] = {
                "filename": os.path.relpath(
                    str(self.blocks[blk].filename), self.path.parent
                ),
            }

        return data

    def json_decode(self, data: Dict[str, Any]) -> None:
        """Convert the JSON data back classes"""

        try:
            Container.block_data_path = str(self.path.parent)
            skip = False
        except:
            Container.block_data_path = ""
            skip = True

        self.short_name = data["short_name"]
        self.name = data["name"]
        self.doc_pages = DocPages()
        self.doc_pages.json_decode(data["doc_pages"])
        self.company_name = data["company_name"]
        self.access_map = data["access_map"]
        self.block_insts = data["block_insts"]
        self._filelist = []

        if not skip:
            for path in data["filelist"]:
                full_path = Path(self.path.parent / Path(path)).resolve()
                self._filelist.append(
                    Path(os.path.relpath(full_path, self.path.parent))
                )

        self.address_maps = {}
        for name, addr_data_json in data["address_maps"].items():
            addr_data = AddressMap()
            addr_data.json_decode(addr_data_json)
            self.address_maps[name] = addr_data

        if not skip:
            self.exports = []
            for item in data["exports"]:
                exporter = item["exporter"]
                target = self.path.parent / item["target"]

                exp_data = ExportData(
                    exporter,
                    str(target.resolve()),
                )
                exp_data.options = item["options"]

                self.exports.append(exp_data)

        self.block_insts = []
        for blk_inst_data_json in data["block_insts"]:
            blk_inst_data = BlockInst()
            blk_inst_data.json_decode(blk_inst_data_json)
            self.block_insts.append(blk_inst_data)

        self.blocks = {}
        for key in data["blocks"]:
            blk_data = Block()
            base_path = data["blocks"][key]["filename"]

            if self.reader_class:
                rdr = self.reader_class
                text = rdr.read_bytes(base_path)
                json_data = json.loads(text)
                blk_data.filename, _ = self.reader_class.resolve_path(
                    base_path
                )
                blk_data.reader_class = self.reader_class.__class__(
                    base_path, self.reader_class.repo, self.reader_class.rtl_id
                )
                blk_data.json_decode(json_data)
            else:
                path = self.path.parent / base_path
                blk_data.open(path)

            self.blocks[key] = blk_data

        self.parameters = ParameterContainer()
        self.parameters.json_decode(data["parameters"])

        self.overrides = []
        try:
            for override in data["overrides"]:
                item = Overrides()
                item.json_decode(override)
                self.overrides.append(item)
        except KeyError:
            ...
