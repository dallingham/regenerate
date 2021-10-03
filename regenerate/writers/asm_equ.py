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
EquWriter - Writes out Assembler defines (based off the GNU assembler)
"""

from typing import Union, Optional, TextIO
from pathlib import Path

from .writer_base import RegsetWriter, ExportInfo, ProjectType
from ..db import RegisterDb, Register, RegProject


class AsmEqu(RegsetWriter):
    """
    Output file creation class that writes a set of constants representing
    the token for the registers addresses.
    """

    def __init__(self, project: RegProject, regset: RegisterDb):
        super().__init__(project, regset)

        self._ofile: Optional[TextIO] = None
        self._prefix = ""

    def write_def(self, reg: Register, prefix: str, offset: int) -> None:
        """
        Writes the definition in the format of:

             .equ   register,  address
        """
        assert self._ofile is not None

        address = reg.address
        base = reg.token
        name = "%s%s, " % (prefix, base)
        self._ofile.write("\t.equ %-30s 0x%s\n" % (name, address + offset))

    def write(self, filename: Path) -> None:
        """
        Writes the output file
        """
        with filename.open("w") as self._ofile:
            for reg_key in self._regset.get_keys():
                self.write_def(
                    self._regset.get_register(reg_key),
                    self._prefix,
                    0,
                )
            self._ofile.write("\n")


EXPORTERS = [
    (
        ProjectType.REGSET,
        ExportInfo(
            AsmEqu,
            ("Header files", "Assembler Source"),
            "Assembler files",
            ".s",
            "headers-asm",
        ),
    )
]
