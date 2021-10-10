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
Static timing - Writes out synthesis constraints
"""

import datetime
from pathlib import Path
from typing import NamedTuple, List, Tuple

from regenerate.db import RegProject, RegisterDb, BitField
from .writer_base import ProjectWriter, ExportInfo, ProjectType, find_template


class RegInstData(NamedTuple):
    "Holds the register instance name and list of its static paths"

    name: str
    static_list: List[str]


class BlockInstData(NamedTuple):
    "Holds the block instance name and list of its register instance's data"

    name: str
    reginst_list: List[RegInstData]


def fix_path(path: str) -> str:
    "Converts the path to the target's expected path"

    return path.replace(".", "/").replace("]/", "].")


def get_static_ports(dbase: RegisterDb) -> List[Tuple[int, BitField]]:
    "Returns the list of static ports"

    fields = []
    for reg in dbase.get_all_registers():
        for field in reg.get_bit_fields():
            if (
                field.use_output_enable
                and field.output_signal
                and field.output_is_static
            ):
                fields.append((reg.address, field))
    return fields


def build_hdl_path(hdl1, hdl2, signal, addr, index):
    "Builds the HDL path from the components"

    if hdl1 and hdl2:
        path = fix_path(f"{hdl1}/{hdl2}/r{addr:02x}_{signal}")
    elif hdl1:
        path = fix_path(f"{hdl1}/r{addr:02x}_{signal}")
    elif hdl2:
        path = fix_path(f"{hdl2}/r{addr:02x}_{signal}")
    else:
        path = ""

    if index >= 0:
        return path % index
    return path


class StaticTiming(ProjectWriter):
    "Extracts the list of static registers and writes them to the template"

    def __init__(self, project: RegProject, template: str):
        super().__init__(project)
        self.template = template
        self.dblist = set()
        self.block_list = self.build_data()

    def build_data(self) -> List[BlockInstData]:
        """Writes the output file"""

        block_list = []

        for blk_inst in self._project.block_insts:

            reglist = []
            block = self._project.blocks[blk_inst.blkid]

            block_data = BlockInstData(blk_inst.name, reglist)

            for regset_inst in block.regset_insts:
                regset = block.regsets[regset_inst.regset_id]

                static_list = []
                regset_data = RegInstData(regset.name, static_list)

                for (addr, field) in get_static_ports(regset):
                    if field.is_constant():
                        continue
                    signal_name = field.name.lower()
                    if regset_inst.repeat.resolve() > 1:
                        for i in range(0, regset_inst.repeat.resolve()):
                            hdl = build_hdl_path(
                                blk_inst.hdl_path,
                                regset_inst.hdl,
                                signal_name,
                                addr,
                                i,
                            )
                            if hdl:
                                static_list.append(hdl)
                    else:
                        hdl = build_hdl_path(
                            blk_inst.hdl_path,
                            regset_inst.hdl,
                            signal_name,
                            addr,
                            -1,
                        )
                        if hdl:
                            static_list.append(hdl)
                if static_list:
                    reglist.append(regset_data)
            if reglist:
                block_list.append(block_data)
        return block_list

    def write(self, filename: Path):
        """Writes the output file"""

        template = find_template("xdc.template")

        timeval = datetime.datetime.now()
        with filename.open("w") as ofile:
            ofile.write(
                template.render(
                    date=timeval.strftime("%H:%M on %Y-%m-%d"),
                    block_list=self.block_list,
                )
            )


class Xdc(StaticTiming):
    "Produces a file with static constraints in Xilinx XDC format"

    def __init__(self, project: RegProject):
        super().__init__(project, "xdc.template")


class Sdc(StaticTiming):
    "Produces a file with static constraints in Synopsys SDC format"

    def __init__(self, project: RegProject):
        super().__init__(project, "sdc.template")


EXPORTERS = [
    (
        ProjectType.PROJECT,
        ExportInfo(
            Xdc,
            ("Synthesis", "Vivado Constraints"),
            "XDC files",
            ".xdc",
            "xdc-constraints",
        ),
    ),
    (
        ProjectType.PROJECT,
        ExportInfo(
            Sdc,
            ("Synthesis", "SDC Constraints"),
            "SDC files",
            ".sdc",
            "syn-constraints",
        ),
    ),
]
