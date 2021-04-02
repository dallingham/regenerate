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
import os.path
from typing import List, Dict, Union
import xml.sax.saxutils

from .proj_reader import ProjectReader
from .proj_writer_json import ProjectWriterJSON
from .proj_reader_json import ProjectReaderJSON
from .addrmap import AddressMap
from .textutils import clean_text
from .logger import LOGGER
from .parammap import PrjParameterData
from .export import ExportData
from .doc_pages import DocPages
from .register_db import RegisterDb
from .block import Block
from .block_inst import BlockInst
from .const import REG_EXT, PRJ_EXT, OLD_PRJ_EXT
from .containers import Container


def nested_dict(depth, dict_type):
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

    def __init__(self, path=None):

        self.short_name = "unnamed"
        self.name = "unnamed"
        self.doc_pages = DocPages()
        self.doc_pages.update_page("Overview", "")
        self.doc_pages.update_page("Implementation", "")
        self.doc_pages.update_page("Additional", "")
        self.company_name = ""
        self.access_map = nested_dict(3, int)

        self._filelist: List[Path] = []

        self._parameters: List[PrjParameterData] = []
        self.address_maps: Dict[str, AddressMap] = {}

        self.block_insts: List[BlockInst] = []
        self.blocks: Dict[str, Block] = {}

        self.regsets: Dict[str, RegisterDb] = {}

        self._group_exports = {}
        self.exports = []

        self._modified = False

        if path:
            self.path = Path(path)
            self.open(self.path)
        else:
            self.path = None

    def save(self) -> None:
        """Saves the project to the JSON file"""

        writer = ProjectWriterJSON(self)
        writer.save(self.path.with_suffix(PRJ_EXT))

        for blk_name in self.blocks:
            blk = self.blocks[blk_name]
            if blk.modified:
                LOGGER.info(
                    "Saving block %s - %s", blk_name, str(blk.filename)
                )
                blk.save()
                blk.modified = False

        for name in self.regsets:
            reg = self.regsets[name]
            if reg.modified:
                LOGGER.info(
                    "Saving register set %s - %s", name, str(reg.filename)
                )
                reg.save()
                reg.modified = False

    def open(self, name: str) -> None:
        """Opens and reads a project file. The project could be in either
        the legacy XML format or the current JSON format"""

        self.path = Path(name)

        if self.path.suffix == OLD_PRJ_EXT:
            LOGGER.info("Loading XML project file '%s'", str(self.path))
            xml_reader = ProjectReader(self)
            xml_reader.open(name)
        else:
            LOGGER.info("Loading JSON project file '%s'", str(self.path))
            json_reader = ProjectReaderJSON(self)
            json_reader.open(name)

            for _, block in self.blocks.items():
                for set_name, reg_set in block.regsets.items():
                    self.regsets[set_name] = reg_set

    def loads(self, data: str) -> None:
        """Reads XML from a string"""

        reader = ProjectReader(self)
        reader.loads(data)

    def remove_block(self, block_name):
        del self.blocks[block_name]
        self.block_insts = [
            inst for inst in self.block_insts if inst.block != block_name
        ]
        for addr_name in self.address_maps:
            addr_map = self.address_maps[addr_name]
            addr_map.blocks = [
                amap for amap in addr_map.blocks if amap != block_name
            ]

    def append_register_set_to_list(self, name: Union[str, Path]):
        """Adds a register set"""

        self._modified = True

        regset = RegisterDb()
        regset.modified = True
        regset.read_db(self.path.parent / name)
        self.regsets[regset.set_name] = regset
        new_file_path = Path(name).with_suffix(REG_EXT).resolve()
        regset.filename = new_file_path
        self._filelist.append(new_file_path)

    def add_register_set(self, path: str) -> None:
        """
        Adds a new register set to the project. Note that this only records
        the filename, and does not actually keep a reference to the RegisterDb.
        """
        self.append_register_set_to_list(path)

    def remove_register_set(self, path: str) -> None:
        """Removes the specified register set from the project."""
        self._modified = True
        try:
            path2remove = os.path.relpath(path, self.path.parent)
            self._filelist.remove(Path(path2remove).resolve())
        except ValueError as msg:
            LOGGER.error(str(msg))

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

    def get_group_exports(self, name: str):
        """Returns the export group list, returns a read-only tuple"""
        return tuple(self._group_exports.get(name, []))

    def append_to_export_list(
        self, db_path: str, exporter: str, target: str
    ) -> None:
        """
        For internal use only.

        Adds an export to the export list. The exporter will only operation
        on the specified register database (XML file).

        path - path to the the register XML file. Converted to a relative path
        exporter - the chosen exporter
        dest - destination output name
        """

        full_db_path = self.path.parent / db_path
        full_target_path = self.path.parent / target

        full_db_str = str(full_db_path.with_suffix(REG_EXT).resolve())
        full_target_str = str(full_target_path.resolve())

        self._modified = True
        exp = ExportData(exporter, full_target_str)
        if full_db_str in self.exports:
            self.exports[full_db_str].append(exp)
        else:
            self.exports[full_db_str] = [exp]

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

    def append_to_group_export_list(
        self, group: str, exporter: str, dest: str
    ) -> None:
        """
        Adds a export to the group export list. Group exporters operation
        on the entire group, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        option - the chosen export option (exporter)
        dest - destination output name
        """
        self._modified = True
        exp = ExportData(exporter, dest)
        self._group_exports[group].append(exp)

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

    def add_to_group_export_list(
        self, group: str, exporter: str, dest: str
    ) -> None:
        """
        Adds a export to the group export list. Group exporters operation
        on the entire group, not just a specific register database (XML file)

        path - path to the the register XML file. Converted to a relative path
        exporter - the chosen export exporter (exporter)
        dest - destination output name
        """
        self._modified = True
        dest = os.path.relpath(dest, self.path.parent)
        exp = ExportData(exporter, dest)
        self._group_exports[group].append(exp)

    def remove_from_export_list(
        self, path: str, exporter: str, dest: str
    ) -> None:
        """Removes the export from the export list"""
        self._modified = True
        path = os.path.relpath(path, self.path.parent)
        self.exports[str(path)] = [
            exp
            for exp in self.exports[str(path)]
            if not (exp.exporter == exporter and exp.dest == dest)
        ]

    def remove_from_project_export_list(
        self, exporter: str, dest: str
    ) -> None:
        """Removes the export from the project export list"""
        self._modified = True
        self.exports = [
            exp
            for exp in self.exports
            if not (exp.exporter == exporter and exp.dest == dest)
        ]

    def remove_from_group_export_list(
        self, group: str, exporter: str, dest: str
    ) -> None:
        """Removes the export from the group export list"""
        self._modified = True
        self._group_exports[group] = [
            exp
            for exp in self._group_exports[group]
            if not (exp.exporter == exporter and exp.dest == dest)
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

    def get_address_maps(self):
        """Returns a list of the existing address maps"""
        return self.address_maps.values()

    def get_blocks_in_address_map(self, name: str):
        """Returns the address maps associated with the specified group."""
        blocks = self.address_maps.get(name)
        if blocks:
            return [blocks]
        else:
            return self.regsets.keys()

    def get_address_maps_used_by_block(self, name: str):
        """Returns the address maps associated with the specified group."""

        used_in_uvm = set(
            {m.name for m in self.address_maps.values() if m.uvm == 0}
        )

        return [
            key
            for key in self.address_maps
            if key in used_in_uvm and name in self.address_maps[key].blocks
        ]

    def get_block_from_inst(self, name: str) -> Block:
        return self.blocks[name]

    def change_address_map_name(self, old_name: str, new_name: str) -> None:
        """Changes the name of an address map"""

        self.address_maps[new_name] = self.address_maps[old_name]
        del self.address_maps[old_name]
        self._modified = True

    def add_address_map_to_block(
        self, name: str, block_inst_name: str
    ) -> bool:
        """Adds an address map to a group if it does not already exist"""
        if block_inst_name not in self.address_maps[name].blocks:
            self.address_maps[name].blocks.append(block_inst_name)
            return True
        return False

    def get_address_base(self, name: str):
        """Returns the base address  of the address map"""
        return self.address_maps[name].base

    def get_address_fixed(self, name: str):
        """Indicates if the specified address map is at a fixed location"""
        return next(
            (d.fixed for d in self.address_maps.values() if name == d.name),
            None,
        )

    def get_address_uvm(self, name: str):
        """Indicates if the specified address map is at a fixed location"""
        return next(
            (d.uvm for d in self.address_maps.values() if name == d.name), None
        )

    def get_address_width(self, name: str):
        """Returns the width of the address group"""
        for data in self.address_maps.values():
            if name == data.name:
                return data.width
        LOGGER.error("Address map not found (%s)", name)
        return None

    def set_access(
        self, map_name: str, group_name: str, block_name: str, access
    ):
        """Sets the access mode"""
        self.access_map[map_name][group_name][block_name] = access

    def get_access_items(self, map_name, group_name):
        """Gets the access items for the map/group"""

        grp_map = self.access_map[map_name][group_name]
        return [(key, grp_map[key]) for key in grp_map]

    def get_access(self, map_name, group_name, block_name):
        """Gets the access mode"""

        try:
            return self.access_map[map_name][group_name][block_name]
        except KeyError:
            return 0

    def add_or_replace_address_map(self, addr_map):
        """Sets the specififed address map"""

        self._modified = True
        self.address_maps[addr_map.name] = addr_map

    def set_address_map(self, name, base, width, fixed, uvm):
        """Sets the specififed address map"""
        self._modified = True
        new_data = AddressMap(name, base, width, fixed, uvm)
        self.address_maps[name] = new_data

    def set_address_map_block_list(self, name: str, new_list: List[str]):
        """Sets the specififed address map"""
        self._modified = True
        self.address_maps[name].blocks = new_list

    def remove_address_map(self, name):
        """Removes the address map"""

        self._modified = True
        for i, data in enumerate(self._addr_map_list):
            if data.name == name:
                del self._addr_map_list[i]
                if data.name in self._addr_map_grps:
                    del self._addr_map_grps[data.name]

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

    def change_subsystem_name(self, old, cur):
        """
        Changes the name of a subsystem from 'old' to 'cur'.
        Searches through the access maps the group definitions
        to find the old reference, and replaces it with the new
        reference
        """

        # Search access map to find items to replace. We must
        # delete the old entry, and create a new entry. Since
        # we cannot delete in the middle of a search, we must save
        # the matches we found. After we identify them, we can
        # delete the items we found.

        to_delete = []
        for access_map in self.access_map:
            for subsys in self.access_map[access_map]:
                if subsys == old:
                    to_delete.append((access_map, old, cur))

        for (access_map, nold, ncur) in to_delete:
            self.access_map[access_map][ncur] = self.access_map[access_map][
                nold
            ]
            del self.access_map[access_map][nold]

        # Search groups for items to rename. Just change the name
        for g_data in self._groupings:
            if g_data.name == old:
                g_data.name = cur
        self._modified = True

    def change_instance_name(self, subsystem, old, cur):
        """
        Changes the register set instance name for a particular
        instance in the identified subsystem. Updates the access
        map and the groupings.
        """

        # Search access maps for items to rename. Search each
        # map, for instances of the specified subsystem, then
        # search for the instance name to be replaced in the
        # subsystem. Since the object is a tuple, and has to be
        # replaced instead of altered, we must store the items
        # to be changed, since we cannot alter the dictionary
        # as we search it.

        to_delete = []
        for access_map in self.access_map:
            for obj in self.access_map[access_map][subsystem]:
                if obj == old:
                    to_delete.append((access_map, subsystem, cur, old))

        for (access_map, subsys, ncur, nold) in to_delete:
            self.access_map[access_map][subsys][ncur] = self.access_map[
                access_map
            ][subsys][nold]
            del self.access_map[access_map][subsys][nold]

        # Search groups for items to rename
        for g_data in self._groupings:
            if g_data.name == subsystem:
                for ginst in g_data.register_sets:
                    if ginst.inst == old:
                        ginst.inst = cur
        self._modified = True

    def get_parameters(self):
        """Returns the parameter list"""
        return self._parameters

    def add_parameter(self, name, value):
        """Adds a parameter to the parameter list"""
        parameter = PrjParameterData(name, value)
        self._parameters.append(parameter)

    def remove_parameter(self, name: str):
        """Removes a parameter from the parameter list"""
        self._parameters = [
            param for param in self._parameters if param.name != name
        ]

    def set_parameters(self, parameter_list):
        """Sets the parameter list"""
        self._parameters = parameter_list

    def change_file_suffix(self, original: str, new: str):
        """Changes the suffix of the files in the file list"""

        new_list = []
        for name in self._filelist:
            new_name = Path(name)
            if new_name.suffix == original:
                new_name = new_name.with_suffix(new)
            new_list.append(new_name.resolve())
        self._filelist = new_list

    def blocks_containing_regset(self, regset_name: str):
        return [
            self.blocks[blk]
            for blk in self.blocks
            if regset_name in self.blocks[blk].regsets.keys()
        ]

    def instances_of_block(self, block: Block):
        return [
            blk_inst
            for blk_inst in self.block_insts
            if blk_inst.block == block.name
        ]

    @property
    def documentation(self) -> str:
        page_names = self.doc_pages.get_page_names()
        if page_names:
            return self.doc_pages.get_page(page_names[0])
        return ""

    def json(self):
        """Convert the data into a JSON compatible dict"""

        json_keys = (
            "short_name",
            "name",
            "doc_pages",
            "company_name",
            "access_map",
            "_parameters",
            "block_insts",
            "_group_exports",
        )

        data = {}
        for key in json_keys:
            if key[0] == "_":
                token = key[1:]
            else:
                token = key
            data[token] = self.__getattribute__(key)

        #            os.path.relpath(fname.with_suffix(REG_EXT), self.path.parent)
        data["filelist"] = [
            os.path.relpath(fname.with_suffix(REG_EXT), self.path.parent)
            for fname in self._filelist
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
                "filename": str(self.blocks[blk].filename),
            }

        return data

    def json_decode(self, data):
        """Convert the JSON data back classes"""

        Container.block_data_path = self.path.parent

        self.short_name = data["short_name"]
        self.name = data["name"]
        doc_pages = DocPages()
        doc_pages.json_decode(data["doc_pages"])
        self.doc_pages = doc_pages
        self.company_name = data["company_name"]
        self.access_map = data["access_map"]
        self.block_insts = data["block_insts"]
        self._filelist = []

        for path in data["filelist"]:
            self._filelist.append(
                Path(self.path.parent / Path(path)).resolve()
            )

        self.address_maps = {}
        for name, addr_data_json in data["address_maps"].items():
            addr_data = AddressMap()
            addr_data.json_decode(addr_data_json)
            self.address_maps[name] = addr_data

        self._parameters = []
        for param_json in data["parameters"]:
            param = PrjParameterData(param_json["name"], param_json["value"])
            self._parameters.append(param)

        self._group_exports = {}
        for key in data["group_exports"]:
            self._group_exports[key] = []
            for item in data["group_exports"][key]:
                self._group_exports[key].append(
                    ExportData(item["exporter"], item["target"])
                )

        self.exports = []
        for item in data["exports"]:
            exporter = item["exporter"]
            target = self.path / item["target"]

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
            path = data["blocks"][key]["filename"]
            blk_data = Block()
            blk_data.open(path)
            self.blocks[key] = blk_data
