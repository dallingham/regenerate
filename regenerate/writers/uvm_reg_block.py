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
from typing import List, Set, Dict
from jinja2 import Environment
from ..db import TYPES
from ..extras.remap import REMAP_NAME
from .writer_base import WriterBase, ExportInfo
from ..db.reg_project import RegProject
from ..db.register_db import RegisterDb
from ..db.bitfield import BitField
from ..db.register import Register
from ..db.addrmap import AddrMapData
from ..db.group_data import GroupData

ACCESS_MAP = {}
for i in TYPES:
    ACCESS_MAP[i.type] = i.simple_type

TYPE_TO_INPUT = dict((__i.type, __i.input) for __i in TYPES)


class UVMRegBlockRegisters(WriterBase):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(self, project: RegProject, dblist: List[RegisterDb]) -> None:
        """
        Initialize the object. At the current time, only little endian is
        supported by the package
        """
        super().__init__(project, None)
        self.dblist = dblist

    def uvm_address_maps(self) -> List[AddrMapData]:
        "Return a list of all the address maps that are not excluded from UVM"

        return [d for d in self._project.get_address_maps() if not d.uvm]

    def _build_group_maps(self) -> Dict[GroupData, Set[str]]:
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

    def _used_maps(self) -> Set[str]:
        return set({addr_map.name for addr_map in self.uvm_address_maps()})

    def write(self, filename: str) -> None:
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """

        env = Environment(trim_blocks=True, lstrip_blocks=True)
        env.filters["remove_no_uvm"] = remove_no_uvm

        template_file = os.path.join(
            os.path.dirname(__file__), "templates", "uvm_reg_block.template"
        )

        with open(template_file) as ofile:
            template = env.from_string(ofile.read())

        used_dbs = self.get_used_databases()

        with open(filename, "w") as ofile:
            ofile.write(
                template.render(
                    project=self._project,
                    dblist=used_dbs,
                    individual_access=individual_access,
                    ACCESS_MAP=ACCESS_MAP,
                    TYPE_TO_INPUT=TYPE_TO_INPUT,
                    db_grp_maps=self.get_db_groups(),
                    group_maps=self._build_group_maps(),
                    fix_name=fix_name,
                    fix_reg=fix_reg_name,
                    used_maps=self._used_maps(),
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

    def get_used_databases(self) -> Set[RegisterDb]:

        grp_set = set()
        maps = self._build_group_maps()
        for key in maps:
            if maps[key]:
                grp_set.add(key.name)

        used_sets: Set[GroupData] = set()
        for group in self._project.get_grouping_list():
            if group.name in grp_set:
                for reg_sets in group.register_sets:
                    used_sets.add(reg_sets.set)
        return set({db for db in self.dblist if db.set_name in used_sets})


def is_readonly(field: BitField):
    return TYPES[field.field_type].readonly


def individual_access(field: BitField, reg: Register) -> int:
    """
    Make sure that the bits in the field are not in the same byte as any
    other field that is writable.
    """
    used_bytes = set()

    # get all the fields in the register
    flds = reg.get_bit_fields()

    # loop through all fields are are not read only and are not the original
    # field we are checking for. Calculate the bytes used, and add them to the
    # used_bytes set

    for x_field in [
        fld for fld in flds if fld != field and not is_readonly(fld)
    ]:
        for pos in range(x_field.lsb, x_field.msb + 1):
            used_bytes.add(pos / 8)

    # loop through the bytes used by the current field, and make sure they
    # do match any of the bytes used by other fields
    for pos in range(field.lsb, field.msb + 1):
        if pos / 8 in used_bytes:
            return 0
    return 1


def remove_no_uvm(slist: List[Register]) -> List[Register]:
    return [reg for reg in slist if reg.do_not_use_uvm is False]


def fix_name(field: BitField) -> str:
    """
    Creates a name from the field. If there are any spaces (which the
    UI should prevent), the are converted to underscores. We then replace
    name names that are reserved SystemVerilog words with alternatives.
    """

    name = "_".join(field.field_name.lower().split())

    if name in REMAP_NAME:
        return f"{name}_field"
    return name


def fix_reg_name(reg: Register) -> str:
    """
    Creates a name from the register. If there are any spaces (which the
    UI should prevent), the are converted to underscores. We then replace
    name names that are reserved SystemVerilog words with alternatives.
    """

    name = "_".join(reg.token.lower().split())

    if name in REMAP_NAME:
        return f"{name}_reg"
    return name


EXPORTERS = [
    (
        WriterBase.TYPE_PROJECT,
        ExportInfo(
            UVMRegBlockRegisters,
            ("Test", "UVM Registers"),
            "SystemVerilog files",
            ".sv",
            "proj-uvm",
        ),
    )
]
