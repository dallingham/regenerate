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
Manages the reading of the project file (.rprj)
"""

from io import BytesIO
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Union
import xml.parsers.expat

from .xml_base import XmlBase
from .address_map import AddressMap
from .block import Block
from .block_inst import BlockInst
from .const import REG_EXT, BLK_EXT, OLD_REG_EXT
from .export import ExportData
from .register_inst import RegisterInst
from .logger import LOGGER


class ProjectReader(XmlBase):
    """
    Reads the project information from the project file.
    """

    def __init__(self, project):
        super().__init__()

        self.prj = project
        self.current_group = None
        self.current = ""
        self.current_map = ""
        self.current_access = 0
        self.current_map_group = None
        self.path = Path(".")
        self.id_to_block: Dict[str, Block] = {}
        self.block_insts: List[BlockInst] = []
        self.reg_exports: Dict[str, List[ExportData]] = defaultdict(list)
        self.name_to_blk_id: Dict[str, str] = {}
        self.name_to_blkinst_id: Dict[str, str] = {}
        self.map_id_to_name: Dict[str, List[str]] = {}
        self.new_block = Block()
        self.current_blk_inst = BlockInst()

    def open(self, name: Union[str, Path]) -> None:
        """Opens and reads an XML file"""

        self.path = Path(name).resolve()

        with self.path.open("rb") as ofile:
            parser = xml.parsers.expat.ParserCreate()
            parser.StartElementHandler = self.start_element
            parser.EndElementHandler = self.end_element
            parser.CharacterDataHandler = self.characters
            parser.ParseFile(ofile)
        self.prj.modified = True

    def loads(self, data: bytes, path: Union[str, Path]) -> None:
        """Loads the data from a text string"""
        self.path = Path(path)
        ofile = BytesIO(data)

        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.characters
        parser.ParseFile(ofile)
        self.prj.modified = True

    def start_project(self, attrs: Dict[str, str]) -> None:
        """Called when a project tag is found"""
        self.prj.name = attrs["name"]
        self.prj.short_name = attrs.get("short_name", "")
        self.prj.company_name = attrs.get("company_name", "")

    def start_registerset(self, attrs: Dict[str, str]) -> None:
        """Called when a registerset tag is found"""
        self.current = attrs["name"]
        reg_path = self.path.parent / self.current
        reg_path_xml = reg_path.with_suffix(OLD_REG_EXT).resolve()
        self.prj.append_register_set_to_list(reg_path_xml)

    def start_export(self, attrs: Dict[str, str]) -> None:
        """Called when an export tag is found"""

        db_path = self.path.parent / Path(self.current).with_suffix(REG_EXT)
        db_path_str = str(db_path.resolve())
        target = Path(self.path.parent) / attrs["path"]
        self.reg_exports[db_path_str].append(
            ExportData(attrs["option"], str(target.resolve()))
        )

    def start_project_export(self, attrs: Dict[str, str]) -> None:
        """Called when a project_export tag is found"""

        target = Path(self.path.parent) / attrs["path"]
        self.prj.append_to_project_export_list(
            attrs["option"], str(target.resolve())
        )

    def start_grouping(self, attrs: Dict[str, str]) -> None:
        """Called when a grouping tag is found"""

        if attrs["name"] not in self.name_to_blk_id:
            self.new_block = Block(
                attrs["name"],
                int(attrs.get("repeat_offset", 0x10000)),
                attrs.get("title", ""),
            )
            self.id_to_block[self.new_block.uuid] = self.new_block
            self.name_to_blk_id[self.new_block.name] = self.new_block.uuid
        else:
            self.new_block = self.id_to_block[self.new_block.uuid]

        self.current_blk_inst = BlockInst(attrs["name"])
        self.name_to_blkinst_id[attrs["name"]] = self.current_blk_inst.uuid
        self.prj.block_insts.append(self.current_blk_inst)

        self.current_blk_inst.blkid = self.new_block.uuid
        self.current_blk_inst.address_base = int(attrs["start"], 16)
        self.current_blk_inst.repeat = int(attrs.get("repeat", "1"))
        self.current_blk_inst.hdl_path = attrs.get("hdl", "")

    def start_map(self, attrs: Dict[str, str]) -> None:
        """Called when a map tag is found"""

        sname = attrs["set"]

        data = RegisterInst(
            sname,
            attrs.get("inst", sname),
            int(attrs["offset"], 16),
            int(attrs["repeat"]),
            int(attrs["repeat_offset"]),
            attrs.get("hdl", ""),
            bool(attrs.get("no_uvm", "0")),
            bool(attrs.get("no_decode", "0")),
            bool(attrs.get("array", "0")),
            bool(attrs.get("single_decode", "0")),
        )
        self.new_block.regset_insts.append(data)

    def start_address_map(self, attrs: Dict[str, str]) -> None:
        """Called when an address tag is found"""
        address_map = AddressMap(
            attrs["name"],
            int(attrs.get("base", "0"), 16),
            int(attrs.get("width", "4")),
            bool(int(attrs.get("fixed", 1))),
            bool(int(attrs.get("no_uvm", 0))),
        )

        self.prj.set_address_map(address_map)
        self.current_map = address_map.uuid
        self.current_map_group = None

    def end_documentation(self, text: str) -> None:
        """
        Called when the documentation XML tag is encountered. Assigns the
        current text string to the documentation variable
        """
        self.prj.doc_pages.update_page("Overview", text, ["Confidential"])

    def end_overview(self, text: str) -> None:
        """
        Called when the overview XML tag is encountered. Assigns the
        current text string to the current group's docs variable
        """
        if self.current_group:
            self.current_group.docs = text
        self.new_block.doc_pages.update_page(
            "Overview", text, ["Confidential"]
        )

    def start_map_group(self, attrs: Dict[str, str]) -> None:
        """
        Called when the map_group XML tag is encountered. Assigns the
        current text string to the current group's docs variable
        """

        name = attrs.get("name")

        if name == "None" or name is None:
            return

        if self.current_map in self.map_id_to_name:
            self.map_id_to_name[self.current_map].append(name)
        else:
            self.map_id_to_name[self.current_map] = [name]

    def start_access(self, attrs: Dict[str, str]) -> None:
        "Starts the access type"

        self.current_access = int(attrs.get("type", "0"))

    def end_access(self, text: str) -> None:
        "Ends the access type"

        self.prj.set_access(
            self.current_map,
            self.current_map_group,
            text,
            self.current_access,
        )

    def start_parameter(self, attrs: Dict[str, str]) -> None:
        "Starts a parameter"

        self.prj.add_parameter(attrs["name"], int(attrs["value"]))

    def end_project(self, _text: str) -> None:
        """
        Called when the project file has been loaded. At this point, we need
        to do some cleanup. This includes:

         * Fixing the register instance reference IDs
         * Creating a file path for the block files, since there was no
           original file.
         * Cleaning up the address maps
        """

        self.fix_reginst_ids()

        for blkid in self.id_to_block:

            blk = self.id_to_block[blkid]
            blk.modified = True
            blk.filename = self.guess_block_path(blk)

            self.prj.blocks[blkid] = blk

            for reg_inst in blk.regset_insts:
                uuid = reg_inst.regset_id
                blk.regsets[uuid] = self.prj.regsets[uuid]
                path = blk.regsets[uuid].filename
                blk.regsets[uuid].exports = self.reg_exports[str(path)]

        self.connect_address_maps()

    def guess_block_path(self, blk: Block) -> Path:
        """
        Make the best guess at a path for the block file.
        """
        counter = self.build_path_counter(blk.uuid)
        most_common = counter.most_common(1)[0][0]
        filename = Path(most_common) / f"{blk.name}{BLK_EXT}"
        block_dir = Path(self.path.parent).resolve()
        filename = block_dir / filename

        return filename.resolve()

    def connect_address_maps(self) -> None:
        """
        Connect the block instances to the address maps. The map to
        block instance names were found during parsing. Now they just
        need to be converted to references.
        """
        for map_id, blkinst_list in self.map_id_to_name.items():
            for blkinst_name in blkinst_list:
                blkinst_id = self.name_to_blkinst_id[blkinst_name]
                self.prj.add_address_map_to_block(map_id, blkinst_id)

    def build_path_counter(self, blkid: str) -> Counter:
        """
        When importing from RPRJ files, we do not have block files, so
        we need to figure out where the block file should go. So we look
        at the path names of the register files that in are the block and
        pick the directory where we have the most register files associated
        with that block.
        """

        counter: Counter = Counter()
        for rset_inst in self.id_to_block[blkid].regset_insts:
            try:
                regset = self.prj.regsets[rset_inst.regset_id]
                regset_dir = regset.filename.parent
                counter[regset_dir] += 1
            except KeyError:
                LOGGER.error(
                    "Register set with id %s referenced in instance %s in block %s not found",
                    rset_inst.regset_id,
                    rset_inst.name,
                    self.id_to_block[blkid],
                )

        return counter

    def fix_reginst_ids(self) -> None:
        """
        Regsets are referenced in the XML project file before they are
        defined, so we don't have the UUIDs for these to build a cross
        reference. Instead, the block name is temporarily stored in the
        uuid file while parsing. When we are done with the parsing, we
        have to go back and convert those names to the real UUIDs.
        """

        name2id = {
            regset.name: regset.uuid for regset in self.prj.regsets.values()
        }
        for rset in self.prj.regsets.values():
            name2id[rset.filename.stem] = rset.uuid

        for blk in self.id_to_block.values():
            for reg_inst in blk.regset_insts:
                if reg_inst.name in name2id:
                    reg_inst.regset_id = name2id[reg_inst.name]
                elif reg_inst.regset_id in name2id:
                    reg_inst.regset_id = name2id[reg_inst.regset_id]
                else:
                    LOGGER.error(
                        "Could not find mapping for %s", reg_inst.regset_id
                    )
