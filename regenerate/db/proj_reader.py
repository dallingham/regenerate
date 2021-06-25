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

from io import BytesIO as StringIO
from pathlib import Path
from collections import defaultdict
import xml.parsers.expat

from .address_map import AddressMap
from .block import Block
from .block_inst import BlockInst
from .const import REG_EXT, BLK_EXT, OLD_REG_EXT
from .export import ExportData
from .register_inst import RegisterInst


class ProjectReader:
    """
    Reads the project information from the project file.
    """

    def __init__(self, project):
        self._prj = project
        self._current_group = None
        self._token_list = []
        self._current = ""
        self._current_map = ""
        self._current_access = 0
        self._current_map_group = None
        self.path = ""
        self.blocks = {}
        self.block_insts = []
        self.reg_exports = defaultdict(list)
        self.inst2set = {}
        self.name2blk = {}
        self.name2blkinst = {}
        self.map_groups = {}

    def open(self, name):
        """Opens and reads an XML file"""
        self.path = Path(name).resolve()

        with self.path.open("rb") as ofile:
            parser = xml.parsers.expat.ParserCreate()
            parser.StartElementHandler = self.startElement
            parser.EndElementHandler = self.endElement
            parser.CharacterDataHandler = self.characters
            parser.ParseFile(ofile)
        self._prj.modified = True

    def loads(self, data, path):
        """Loads the data from a text string"""
        self.path = Path(path)
        try:
            ofile = StringIO(data)
        except Exception as msg:
            print("ERR", str(msg))

        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.startElement
        parser.EndElementHandler = self.endElement
        parser.CharacterDataHandler = self.characters
        parser.ParseFile(ofile)
        self._prj.modified = True

    def startElement(self, tag, attrs):
        """
        Called every time an XML element begins
        """
        self._token_list = []
        mname = "start_" + tag
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(attrs)

    def endElement(self, tag):
        """
        Called every time an XML element end
        """
        text = "".join(self._token_list)
        mname = "end_" + tag
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(text)

    def characters(self, data):
        """
        Called with segments of the character data. This is not predictable
        in how it is called, so we must collect the information for assembly
        later.
        """
        self._token_list.append(data)

    def start_project(self, attrs):
        """Called when a project tag is found"""
        self._prj.name = attrs["name"]
        self._prj.short_name = attrs.get("short_name", "")
        self._prj.company_name = attrs.get("company_name", "")

    def start_registerset(self, attrs):
        """Called when a registerset tag is found"""
        self._current = attrs["name"]
        reg_path = self.path.parent / self._current
        reg_path_str = str(reg_path.resolve())
        reg_path_xml = str(reg_path.with_suffix(OLD_REG_EXT).resolve())
        self._prj.append_register_set_to_list(reg_path_xml)
        
    def start_export(self, attrs):
        """Called when an export tag is found"""

        if str(self.path) != "<string>":
            db_path = self.path.parent / Path(self._current).with_suffix(REG_EXT)
            db_path_str = str(db_path.resolve())
            target = Path(self.path.parent) / attrs["path"]
            self.reg_exports[db_path_str].append(
                ExportData(attrs["option"], str(target.resolve()))
            )

    def start_group_export(self, attrs):
        """Called when an group_export tag is found"""
        return
        dest = attrs["dest"]
        option = attrs["option"]
        self._prj.append_to_group_export_list(
            self._current_group.name, dest, option
        )

    def start_project_export(self, attrs):
        """Called when a project_export tag is found"""

        if str(self.path) != "<string>":
            target = Path(self.path.parent) / attrs["path"]
            self._prj.append_to_project_export_list(
                attrs["option"], str(target.resolve())
            )
            
    def start_grouping(self, attrs):
        """Called when a grouping tag is found"""

        if attrs["name"] not in self.name2blk:
            self.new_block = Block(
                attrs["name"],
                int(attrs.get("repeat_offset", 0x10000)),
                attrs.get("title", ""),
            )
            self.blocks[self.new_block.uuid] = self.new_block
            self.name2blk[self.new_block.name] = self.new_block.uuid
        else:
            self.new_block = self.blocks[self.new_block.uuid]

        self._current_blk_inst = BlockInst(attrs["name"])
        self.name2blkinst[attrs["name"]] = self._current_blk_inst.uuid
        self._prj.block_insts.append(self._current_blk_inst)

        self._current_blk_inst.blkid = self.new_block.uuid
        self._current_blk_inst.address_base = int(attrs["start"], 16)
        self._current_blk_inst.repeat = int(attrs.get("repeat", "1"))
        self._current_blk_inst.hdl_path = attrs.get("hdl", "")

    def start_map(self, attrs):

        """Called when a map tag is found"""
        sname = attrs["set"]
        self.inst2set[attrs["inst"]] = sname

        data = RegisterInst(
            sname,
            attrs.get("inst", sname),
            int(attrs["offset"], 16),
            int(attrs["repeat"]),
            int(attrs["repeat_offset"]),
            attrs.get("hdl", ""),
            int(attrs.get("no_uvm", "0")),
            int(attrs.get("no_decode", "0")),
            int(attrs.get("array", "0")),
            int(attrs.get("single_decode", "0")),
        )
        self.new_block.regset_insts.append(data)

    def start_address_map(self, attrs):
        """Called when an address tag is found"""
        address_map = AddressMap(
            attrs["name"],
            int(attrs.get("base", 0), 16),
            int(attrs.get("width", 4)),
            bool(int(attrs.get("fixed", 1))),
            bool(int(attrs.get("no_uvm", 0))),
        )

        self._prj.set_address_map(address_map)
        self._current_map = address_map.uuid
        self._current_map_group = None

    def end_documentation(self, text):
        """
        Called when the documentation XML tag is encountered. Assigns the
        current text string to the documentation variable
        """
        self._prj.doc_pages.update_page("Overview", text)

    def end_overview(self, text):
        """
        Called when the overview XML tag is encountered. Assigns the
        current text string to the current group's docs variable
        """
        if self._current_group:
            self._current_group.docs = text
        self.new_block.doc_pages.update_page("Overview", text)

    def start_map_group(self, attrs):
        """
        Called when the map_group XML tag is encountered. Assigns the
        current text string to the current group's docs variable
        """

        name = attrs.get("name")

        if name == "None":
            return

        if self._current_map in self.map_groups:
            self.map_groups[self._current_map].append(name)
        else:
            self.map_groups[self._current_map] = [name]

    #        self._prj.add_address_map_to_block(
    #            self._current_map, self._current_map_group
    #        )

    def end_map_group(self, text):
        """
        Called when the map_group XML tag ended
        """
        return
        if self._current_map_group is None:
            self._prj.add_address_map_to_block(self._current_map, text)

    def start_access(self, attrs):
        "Starts the access type"

        self._current_access = int(attrs.get("type", "0"))

    def end_access(self, text):
        "Ends the access type"

        self._prj.set_access(
            self._current_map,
            self._current_map_group,
            text,
            self._current_access,
        )

    def start_parameter(self, attrs):
        "Starts a parameter"

        self._prj.add_parameter(attrs["name"], int(attrs["value"]))

    def end_parameters(self, _attrs):
        "Ends a parameter"
        ...

    def end_project(self, _text):
        from collections import Counter

        self.reg_id = {}
        for x in self._prj.regsets:
            rset = self._prj.regsets[x]
            self.reg_id[rset.name] = rset.uuid

        for blkid in self.blocks:

            counter = Counter()
            for rset in self.blocks[blkid].regset_insts:
                try:
                    counter[Path(self.reg_id[rset.regset_id]).parent] += 1
                except KeyError:
                    print(rset.uuid, "not found")

            blk = self.blocks[blkid]
            blk.modified = True

            if str(self.path) != "<string>":
                filename = (
                    Path(counter.most_common(1)[0][0]) / f"{blk.name}{BLK_EXT}"
                )
                block_dir = Path(self.path.parent).resolve()
                filename = block_dir / filename
                
                blk.filename = Path(filename).resolve()
                
            self._prj.blocks[blkid] = blk

            for reg_inst in blk.regset_insts:
                name = self.inst2set[reg_inst.name]
                uuid = self.reg_id[name]  # self._prj.regsets[name].uuid
                blk.regsets[uuid] = self._prj.regsets[uuid]
                path = blk.regsets[uuid].filename
                reg_inst.regset_id = uuid
                blk.regsets[uuid].exports = self.reg_exports[str(path)]

        for map_id in self.map_groups:
            blkinst_list = self.map_groups[map_id]
            for blkinst_name in blkinst_list:
                blkinst_id = self.name2blkinst[blkinst_name]
                if blkinst_id != "":
                    self._prj.add_address_map_to_block(map_id, blkinst_id)
