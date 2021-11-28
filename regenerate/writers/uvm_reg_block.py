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
UVM register generation
"""

import time
from pathlib import Path
from typing import List, Set, Dict, Any
from collections import namedtuple

from regenerate.db import (
    RegProject,
    RegisterInst,
    ParameterResolver,
    BitField,
    Register,
    BlockInst,
    AddressMap,
    TYPES,
)

from ..extras.remap import REMAP_NAME
from .writer_base import ProjectWriter, ProjectType, find_template
from .export_info import ExportInfo


GroupData = namedtuple(
    "GroupData",
    [
        "name",
        "repeat",
    ],
)


ACCESS_MAP = {}
for i in TYPES:
    ACCESS_MAP[i.type] = i.simple_type

TYPE_TO_INPUT = dict((__i.type, __i.input) for __i in TYPES)


class UVMRegBlockRegisters(ProjectWriter):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(self, project: RegProject, options: Dict[str, Any]) -> None:
        """
        Initialize the object. At the current time, only little endian is
        supported by the package
        """
        super().__init__(project, options)
        self.dblist = [dbase[1] for dbase in project.regsets.items()]

    def uvm_address_maps(self) -> List[AddressMap]:
        "Return a list of all the address maps that are not excluded from UVM"

        if (
            self.options
            and "addrmaps" in self.options
            and self.options["addrmaps"]
        ):
            uvm_maps = [
                d
                for d in self._project.get_address_maps()
                if d.uuid in self.options["addrmaps"]
            ]
        else:
            uvm_maps = list(self._project.get_address_maps())
        return uvm_maps

    def _block_inst_to_address_map(self) -> Dict[BlockInst, Set[AddressMap]]:
        "Returns the map of block instances to address maps"

        group_maps: Dict[BlockInst, Set[AddressMap]] = {}

        for map_id in self._project.address_maps:
            addr_map = self._project.address_maps[map_id]

            for blkid in addr_map.blocks:
                blkinst = self._project.get_blkinst_from_id(blkid)
                if not blkinst:
                    continue
                if blkinst not in group_maps:
                    group_maps[blkinst] = set()
                group_maps[blkinst].add(addr_map)
        return group_maps

    def _used_maps(self) -> Set[AddressMap]:
        return set(self.uvm_address_maps())

    def write(self, filename: Path) -> None:
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """

        template = find_template(
            "uvm_reg_block.template", [("remove_no_uvm", remove_no_uvm)]
        )

        used_dbs = self.get_used_databases()

        with filename.open("w") as ofile:
            ofile.write(
                template.render(
                    prj=self._project,
                    resolver=ParameterResolver(),
                    dblist=used_dbs,
                    individual_access=individual_access,
                    ACCESS_MAP=ACCESS_MAP,
                    TYPE_TO_INPUT=TYPE_TO_INPUT,
                    db_grp_maps=self.get_db_groups(),
                    group_maps=self._block_inst_to_address_map(),
                    fix_name=fix_name,
                    fix_reg=fix_reg_name,
                    used_maps=self._used_maps(),
                    current_date=time.strftime("%B %d, %Y"),
                )
            )

    def get_db_groups(self):
        "Returns the data set"

        used = set()
        data_set = []
        group_maps = self._block_inst_to_address_map()
        for blk_inst in self._project.block_insts:
            if blk_inst not in group_maps:
                continue
            for regset_inst in self._project.blocks[
                blk_inst.blkid
            ].regset_insts:
                regset = self._project.regsets[regset_inst.regset_id]

                tag = (regset.uuid, regset_inst.uuid, blk_inst.uuid)
                if tag not in used:
                    data_set.append(
                        (
                            regset,
                            regset_inst,
                            blk_inst,
                            group_maps[blk_inst],
                            tag,
                        )
                    )
                    used.add(tag)

        return data_set

    def get_used_databases(self) -> Set[RegisterInst]:
        "Gets the register sets used"

        regsets = set()
        for blk in self._project.blocks.values():
            for regset in blk.regset_insts:
                regsets.add(regset)
        return regsets


def is_readonly(field: BitField):
    "Returns True if the type is a read only type"

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
        for pos in range(x_field.lsb, x_field.msb.resolve() + 1):
            used_bytes.add(pos // 8)

    # loop through the bytes used by the current field, and make sure they
    # do match any of the bytes used by other fields
    for pos in range(field.lsb, field.msb.resolve() + 1):
        if pos // 8 in used_bytes:
            return 0
    return 1


def remove_no_uvm(slist: List[Register]) -> List[Register]:
    "Removes registers that flagged to not use UVM"

    return [reg for reg in slist if reg.flags.do_not_use_uvm is False]


def fix_name(field: BitField) -> str:
    """
    Creates a name from the field. If there are any spaces (which the
    UI should prevent), the are converted to underscores. We then replace
    name names that are reserved SystemVerilog words with alternatives.
    """

    name = "_".join(field.name.lower().split())

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
        ProjectType.PROJECT,
        ExportInfo(
            UVMRegBlockRegisters,
            "Test",
            "UVM Registers",
            "SystemVerilog files",
            "UVM register class hierarchy for verification",
            ".sv",
            "{}_reg_pkg.sv",
            {
                "addrmaps": (
                    "Select one or more Address Maps. If no maps are "
                    "selected, all maps will be used."
                ),
            },
            "proj-uvm",
        ),
    )
]
