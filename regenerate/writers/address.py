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
DefsWriter - Writes out Verilog defines representing the register addresses
"""

from pathlib import Path
from typing import NamedTuple, List, Dict, Optional

from regenerate.db import RegProject, Block, LOGGER, AddressMap
from .writer_base import ProjectWriter, ExportInfo, ProjectType, find_template


class SignalPath(NamedTuple):
    block: str
    regset: str
    name: str
    address: int
    size: int


class AddressWriter(ProjectWriter):
    "Base class that creates a flat list of register paths and addresses"

    def __init__(
        self,
        project: RegProject,
        template: str,
        type_map: Dict[int, str],
        addr_map: Optional[AddressMap] = None,
    ):
        super().__init__(project)
        self.type_map = type_map
        self.template = template
        self.addr_map = addr_map
        if addr_map:
            self.addr_width = addr_map.width
            if addr_map.fixed:
                self.map_base = addr_map.base
            else:
                self.map_base = 0
        else:
            self.addr_width = 64
            self.map_base = 0

    def write(self, filename: Path):
        """Writes the output file"""

        template = find_template(self.template)

        try:
            with filename.open("w") as ofile:
                ofile.write(
                    template.render(
                        file_base=filename.stem,
                        path_data=build_map(self._project, self.map_base),
                        type_map=self.type_map,
                        addr_width=self.addr_width,
                    )
                )
        except IOError as msg:
            LOGGER.error("Could not open %s - %s", str(filename), str(msg))


def build_map(project: RegProject, map_base: int) -> List[SignalPath]:

    map_list: List[SignalPath] = []

    for blk_inst in project.get_block_instances():
        block = project.get_block_from_block_inst(blk_inst)

        if blk_inst.repeat > 1:
            for blkrpt in range(0, blk_inst.repeat):
                address = (
                    (blkrpt * block.address_size)
                    + blk_inst.address_base
                    + map_base
                )
                blk_name = f"{blk_inst.name}_{blkrpt}"
                dump_blkinst(blk_name, block, address, map_list)
        else:
            dump_blkinst(blk_inst.name, block, blk_inst.address_base, map_list)
    return map_list


def dump_blkinst(
    blk_name: str,
    block: Block,
    address: int,
    map_list: List[SignalPath],
) -> None:

    for reg_inst in block.get_regset_insts():
        regset = block.get_regset_from_reg_inst(reg_inst)

        repeat = reg_inst.repeat.resolve()
        if repeat > 1:
            for i in range(0, repeat):
                for reg in regset.get_all_registers():
                    base = reg.address + reg_inst.offset + address
                    addr = base + (i * (1 << reg.ports.address_bus_width))
                    path = SignalPath(
                        blk_name,
                        f"{reg_inst.name}_{i}",
                        reg.token.lower(),
                        addr,
                        reg.width,
                    )
                    map_list.append(path)
        else:
            for reg in regset.get_all_registers():
                addr = reg.address + reg_inst.offset + address
                path = SignalPath(
                    blk_name,
                    reg_inst.name,
                    reg.token.lower(),
                    addr,
                    reg.width,
                )
                map_list.append(path)


class CDefinesWriter(AddressWriter):
    """
    Writes out Verilog defines representing the register addresses
    """

    def __init__(self, project: RegProject):
        type_map = {
            8: "unsigned char",
            16: "unsigned short",
            32: "unsigned long",
            64: "unsigned long long",
        }
        super().__init__(project, "c_defines.writer", type_map)


class VerliogDefinesWriter(AddressWriter):
    """
    Writes out Verilog defines representing the register addresses
    """

    def __init__(self, project: RegProject):
        type_map = {}
        super().__init__(project, "verilog_defines.writer", type_map)


class VerliogParametersWriter(AddressWriter):
    """
    Writes out Verilog defines representing the register addresses
    """

    def __init__(self, project: RegProject):
        type_map = {}
        super().__init__(project, "verilog_parameters.writer", type_map)


class VerliogConstPkgWriter(AddressWriter):
    """
    Writes out Verilog defines representing the register addresses
    """

    def __init__(self, project: RegProject):
        type_map = {}
        super().__init__(project, "verilog_const_pkg.template", type_map)


EXPORTERS = [
    (
        ProjectType.PROJECT,
        ExportInfo(
            CDefinesWriter,
            ("C", "C Defines"),
            "C header files",
            ".h",
            "headers-c",
        ),
    ),
    (
        ProjectType.PROJECT,
        ExportInfo(
            VerliogDefinesWriter,
            ("RTL", "Verilog Defines"),
            "Verilog header files",
            ".vh",
            "rtl-verilog-defines",
        ),
    ),
    (
        ProjectType.PROJECT,
        ExportInfo(
            VerliogParametersWriter,
            ("RTL", "Verilog Parameters"),
            "Verilog header files",
            ".vh",
            "rtl-verilog-parameters",
        ),
    ),
    (
        ProjectType.PROJECT,
        ExportInfo(
            VerliogConstPkgWriter,
            ("RTL", "SystemVerilog Constants"),
            "Verilog package",
            ".sv",
            "headers-system-verilog",
        ),
    ),
]
