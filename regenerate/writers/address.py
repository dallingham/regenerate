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
from typing import NamedTuple, List, Dict
from jinja2 import Environment, FileSystemLoader

from regenerate.db import RegProject, Block, LOGGER
from .writer_base import ProjectWriter, ExportInfo, ProjectType


class SignalPath(NamedTuple):
    block: str
    regset: str
    name: str
    address: int
    size: int


class AddressWriter(ProjectWriter):
    "Base class that creates a flat list of register paths and addresses"

    def __init__(
        self, project: RegProject, template: str, type_map: Dict[int, str]
    ):
        super().__init__(project)
        self.type_map = type_map
        self.template = template

    def write(self, filename: Path):
        """Writes the output file"""

        template_dir = Path(__file__).parent / "templates"

        # Open the JINJA template
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template(self.template)

        try:
            with filename.open("w") as ofile:
                ofile.write(
                    template.render(
                        file_base=filename.stem,
                        path_data=build_map(self._project),
                        type_map=self.type_map,
                    )
                )
        except IOError as msg:
            LOGGER.error("Could not open %s - %s", str(filename), str(msg))


def build_map(project: RegProject) -> List[SignalPath]:

    map_list: List[SignalPath] = []

    for blk_inst in project.get_block_instances():
        block = project.get_block_from_block_inst(blk_inst)

        if blk_inst.repeat > 1:
            for blkrpt in range(0, blk_inst.repeat):
                address = (blkrpt * block.address_size) + blk_inst.address_base
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


EXPORTERS = [
    (
        ProjectType.PROJECT,
        ExportInfo(
            CDefinesWriter,
            ("C", "C Defines Writer"),
            "C header files",
            ".h",
            "headers-c",
        ),
    ),
    (
        ProjectType.PROJECT,
        ExportInfo(
            VerliogDefinesWriter,
            ("RTL", "Verilog Defines Writer"),
            "Verlog header files",
            ".vh",
            "rtl-verilog-defines",
        ),
    ),
]
