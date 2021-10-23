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
Actual program. Parses the arguments, and initiates the main window
"""

import time
import os
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment

from regenerate.db import RegProject, BitField, Register
from regenerate.extras.remap import REMAP_NAME
from .writer_base import ProjectWriter, ProjectType
from .export_info import ExportInfo


class CStruct(ProjectWriter):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(self, project: RegProject, options: Dict[str, Any]):
        """
        Initialize the object. At the current time, only little endian is
        supported by the package
        """
        super().__init__(self, project, options)

    def fix_name(self, field: BitField):
        """
        Creates a name from the field. If there are any spaces (which the
        UI should prevent), the are converted to underscores. We then replace
        name names that are reserved SystemVerilog words with alternatives.
        """
        name = "_".join(field.name.lower().split())

        if name in REMAP_NAME:
            return f"{name}_field"
        return name

    def fix_reg_name(self, reg: Register):
        """
        Creates a name from the register. If there are any spaces (which the
        UI should prevent), the are converted to underscores. We then replace
        name names that are reserved SystemVerilog words with alternatives.
        """
        name = "_".join(reg.token.lower().split())

        if name in REMAP_NAME:
            return f"{name}_reg"
        return name

    def uvm_address_maps(self):
        return [d for d in self._project.get_address_maps() if not d.uvm]

    def build_map_name_to_groups(self):
        map2grp = {}
        all_groups = [grp.name for grp in self._project.get_grouping_list()]

        for data in self.uvm_address_maps():
            name = data.name
            map2grp[name] = self._project.get_address_map_groups(name)
            if not map2grp[name]:
                map2grp[name] = all_groups
        return map2grp

    def _build_group_maps(self):
        group_maps = {}
        for group in self._project.get_grouping_list():
            in_maps = set()
            for addr_map in self.uvm_address_maps():
                map_list = self._project.get_address_map_groups(addr_map.name)
                if not map_list or group.name in map_list:
                    in_maps.add(addr_map.name)
            if in_maps:
                group_maps[group] = in_maps
        return group_maps

    def _used_maps(self):
        return set({addr_map.name for addr_map in self.uvm_address_maps()})

    def write(self, filename: Path):
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """

        dirpath = os.path.dirname(__file__)

        env = Environment(trim_blocks=True, lstrip_blocks=True)

        template_file = os.path.join(dirpath, "templates", "cstruct.template")

        with open(template_file) as ifile:
            template = env.from_string(ifile.read())

        used_dbs = self.get_used_databases()

        with filename.open("w") as ofile:
            ofile.write(
                template.render(
                    project=self._project,
                    dblist=used_dbs,
                    db_grp_maps=self.get_db_groups(),
                    group_maps=self._build_group_maps(),
                    fix_name=self.fix_name,
                    fix_reg=self.fix_reg_name,
                    use_new=False,
                    used_maps=self._used_maps(),
                    map2grp=self.build_map_name_to_groups(),
                    current_date=time.strftime("%B %d, %Y"),
                )
            )

    def get_db_groups(self):
        data_set = []
        group_maps = self._build_group_maps()
        for dbase in self.get_used_databases():
            for group in self._project.get_grouping_list():
                used = set()
                for grp in group.register_sets:
                    if grp.set == dbase.set_name and grp.set not in used:
                        used.add(grp.set)
                        if group in group_maps:
                            data_set.append((dbase, group, group_maps[group]))
        return data_set

    def get_used_databases(self):

        grp_set = set()
        maps = self._build_group_maps()
        for key in maps:
            if maps[key]:
                grp_set.add(key.name)

        used_sets = set([])
        for group in self._project.get_grouping_list():
            if group.name in grp_set:
                for reg_sets in group.register_sets:
                    used_sets.add(reg_sets.set)
        return set({db for db in self.dblist if db.set_name in used_sets})


# EXPORTERS = [
#     (
#         ProjectType.REGSET,
#         ExportInfo(
#             CStruct,
#             ("Header files", "C Structures"),
#             "Structures for C Headers",
#             "C structure representing the address map",
#             ".h",
#             "structs-c",
#         ),
#     )
# ]
