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

from .writer_base import WriterBase, ExportInfo, ProjectType
from ..db import RegisterDb, Register


class AsmEqu(WriterBase):
    """
    Output file creation class that writes a set of constants representing
    the token for the registers addresses.
    """

    def __init__(self, dbase: Union[None, RegisterDb]) -> None:
        super().__init__(dbase)
        self._offset = 0
        self._ofile: Optional[TextIO] = None

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
        assert self._ofile is not None
        assert self._dbase is not None

        with filename.open("w") as self._ofile:
            self._write_header_comment(
                self._ofile, "site_asm.inc", comment_char=";; "
            )
            for reg_key in self._dbase.get_keys():
                self.write_def(
                    self._dbase.get_register(reg_key),
                    self._prefix,
                    self._offset,
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
