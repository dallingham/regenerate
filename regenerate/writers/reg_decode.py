"""
SystemVerilog RTL register decoder generator
"""

from pathlib import Path
from typing import List, NamedTuple, Dict

from regenerate.db import RegProject, RegisterDb, Block
from .writer_base import BlockWriter, ProjectType, find_template
from .export_info import ExportInfo

# Define named tuple to hold the data to pass to the template


class BlockInfo(NamedTuple):
    "Information about a block"

    inst: str
    lower: int
    upper: int
    repeat: int
    offset: int
    single_decode: bool
    db: RegisterDb


class RegDecode(BlockWriter):
    "Register decode block generator"

    def __init__(self, prj: RegProject, block: Block, options: Dict[str, str]):
        super().__init__(prj, block, options)

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

        reginst_id_list = self.options.get("reginsts")
        if not reginst_id_list:
            reginsts = block.get_regset_insts()
        else:
            reginsts = [
                inst
                for inst in block.regset_insts
                if inst.uuid in reginst_id_list
            ]

        # Build the data to send to the template
        external_list = []

        reg_addr_width = 16  # FIXME

        mask = (1 << reg_addr_width) - 1
        for reg_inst in reginsts:
            regset = proj.finder.find_by_id(reg_inst.regset_id)
            if regset is None:
                continue

            size = 1 << regset.ports.address_bus_width

            if reg_inst.repeat.resolve() > 1:  # and args.array_single_decode:
                flatten = True
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

        external_list = self.build_group_info(self._project, self._block)

        # Open the JINJA template
        template = find_template("decode_rtl.template")

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


EXPORTERS = [
    (
        ProjectType.BLOCK,
        ExportInfo(
            RegDecode,
            "RTL",
            "Register Decode Logic",
            "Register block decoder",
            "Decoder module to select the correct register module",
            ".sv",
            "{}_decode.sv",
            {
                "reginsts": "Select the register set instances used by the decoder",
            },
            "decode-sv",
        ),
    )
]
