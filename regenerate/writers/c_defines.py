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
CWriter - Writes out C defines representing the register addresses
"""

from typing import Optional, TextIO
from pathlib import Path

from regenerate.db import RegProject, RegisterDb, Register
from .writer_base import RegsetWriter, ExportInfo, ProjectType


HEADER = [
    "/*------------------------------------------------------------------\n",
    " * File    : $f$\n",
    " * Author  : $U$\n",
    " * Created : $D$\n",
    " * Block   : $M$\n",
    " *\n",
    " * -----------------------------------------------------------------\n",
    " * Copyright $Y$. All rights reserved.\n",
    " *------------------------------------------------------------------\n",
    " */\n",
    "#ifndef __$F$\n",
    "#define __$F$ 1\n",
    "\n",
]

TRAILER = ["#endif\n"]

REG_TYPE = {
    8: "unsigned char*",
    16: "unsigned short*",
    32: "unsigned long*",
    64: "unsigned long long*",
}


class CDefines(RegsetWriter):
    """
    Writes out C defines representing the register addresses
    """

    def __init__(self, project: RegProject, regset: RegisterDb) -> None:
        super().__init__(project, regset)
        self._ofile = Optional[TextIO]

    def write_def(
        self, reg: Register, blk_name: str, reg_name: str, base: int
    ) -> None:
        """
        Writes the definition in the format of:

        #define register (address)
        """
        assert self._ofile is not None

        address = reg.address + base
        if reg.dimension > 1:
            for i in range(0, reg.dimension):
                self._ofile.write(
                    f"#define {blk_name.upper()}__{reg_name.upper()}__{reg.token}{{i}} (*((volatile {REG_TYPE[reg.width]})0x{(address + (i * reg.width)):x}))\n"
                )
        else:
            self._ofile.write(
                f"#define {blk_name.upper()}__{reg_name.upper()}__{reg.token} (*((volatile {REG_TYPE[reg.width]})0x{address:x}))\n"
            )

    def write(self, filename: Path) -> None:
        """
        Writes the output file
        """
        assert self._ofile is not None
        assert self._regset is not None

        with filename.open("w") as self._ofile:
            self.write_header(self._ofile, "".join(HEADER))

            addr_maps = self._project.get_address_maps()
            if len(addr_maps) > 0:
                maps = list(addr_maps)
                base = self._project.get_address_base(maps[0].uuid)
            else:
                base = 0

            for blkinst in self._project.block_insts:
                blk_base = blkinst.address_base
                block = self._project.blocks[blkinst.blkid]

                for reginst in block.regset_insts:
                    reg_base = reginst.offset
                    regset = block.regsets[reginst.regset_id]
                    if regset.uuid == self._regset.uuid:
                        for register in regset.get_all_registers():
                            self.write_def(
                                register,
                                blkinst.name,
                                reginst.name,
                                base + blk_base + reg_base,
                            )
                        self._ofile.write("\n")

            for line in TRAILER:
                self._ofile.write("%s\n" % line.replace("$M$", self._module))


EXPORTERS = [
    (
        ProjectType.REGSET,
        ExportInfo(
            CDefines,
            ("Header files", "C Defines"),
            "C header files",
            ".h",
            "headers-c",
        ),
    )
]
