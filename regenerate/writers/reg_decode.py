"""
SystemVerilog RTL register decoder generator
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple, Dict, NamedTuple

from jinja2 import Environment, FileSystemLoader
from regenerate.db import RegProject, RegisterDb, Block
from .writer_base import BlockWriter, ExportInfo, ProjectType

# Define named tuple to hold the data to pass to the template


class BlockInfo(NamedTuple):
    inst: str
    lower: int
    upper: int
    repeat: int
    offset: int
    single_decode: bool
    db: RegisterDb


class RegDecode(BlockWriter):
    def __init__(self, prj: RegProject, blkid: str):
        super().__init__(prj, blkid)

    def find_group_data(self, prj: RegProject, name: str) -> Block:
        """Finds the group structure based on the name provided"""
        for grp in prj.blocks.values():
            if grp.name == name:
                group = grp
                break
            else:
                sys.stderr.write('Group "%s" not found\n' % name)
                return None

        return group

    def build_group_info(
        self, proj: RegProject, block: Block
    ) -> List[BlockInfo]:
        """
        For each register instance in the block, return:

        * block instance name
        * base address of the block (dropping lower 3 bits to align
        to 64-bit boundary)
        * size of the address range (dropping lower 3 bits to align
        to 64-bit boundary)
        * number of times the instance is repeated (if any)
        * space between repeated block instances (again, aligned to
        64-bit boundary)
        """

        reginsts = block.get_regset_insts()

        # Build the data to send to the template
        external_list = []

        reg_addr_width = 16  # FIXME

        mask = (1 << reg_addr_width) - 1
        for reg_inst in reginsts:

            regset = proj.finder.find_by_id(reg_inst.regset_id)
            size = 1 << regset.ports.address_bus_width

            if reg_inst.repeat.resolve() > 1:  # and args.array_single_decode:
                flatten = 1
                repeat_val = 1
                size = reg_inst.repeat.resolve() >> 3
            else:
                flatten = reg_inst.single_decode
                repeat_val = reg_inst.repeat.resolve()
                offset = reg_inst.repeat_offset >> 3

            lower = reg_inst.offset & mask
            upper = lower + size

            new_set = BlockInfo(
                reg_inst.name,
                lower // 8,
                upper // 8,
                repeat_val,
                offset,
                flatten,
                regset,
            )

            external_list.append(new_set)

        return external_list

    def write(self, filename: Path):
        """Main program"""

        proj = self._project

        external_list = self.build_group_info(self._project, self._block)

        # Open the JINJA template
        env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), "templates")
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template("decode_rtl.template")

        try:
            with filename.open("w") as ofile:
                ofile.write(
                    template.render(
                        REG_ADDR_WIDTH=16,  # args.reg_addr_width,
                        ADDR_WIDTH=16,  # FIXME args.addr_width,
                        flatten=False,  # FIXME args.flatten,
                        DATA_WIDTH=64,  # FIXME args.width,
                        ID_WIDTH=4,  # args.id_size,
                        GROUP=self._block.name,
                        ext_insts=external_list,
                    )
                )
        except IOError as msg:
            sys.stderr.write(
                "Could not open %s - %s\n" % (args.output, str(msg))
            )


EXPORTERS = [
    (
        ProjectType.BLOCK,
        ExportInfo(
            RegDecode,
            ("RTL", "Register Decode Logic"),
            "Register block decoder",
            ".sv",
            "decode-sv",
        ),
    )
]
