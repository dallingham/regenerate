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

from regenerate.writers.writer_base import WriterBase, ExportInfo


class AsmEqu(WriterBase):
    """
    Output file creation class that writes a set of constants representing
    the token for the registers addresses.
    """

    def __init__(self, dbase):
        super(AsmEqu, self).__init__(dbase)
        self._offset = 0
        self._ofile = None

    def write_def(self, reg, prefix, offset):
        """
        Writes the definition in the format of:

             .equ   register,  address
        """
        address = reg.address
        base = reg.token
        name = "%s%s, " % (prefix, base)
        self._ofile.write("\t.equ %-30s 0x%s\n" % (name, address + offset))

    def write(self, filename):
        """
        Writes the output file
        """
        with open(filename, "w") as self._ofile:
            self._write_header_comment(self._ofile, 'site_asm.inc',
                                       comment_char=';; ')
            for reg_key in self._dbase.get_keys():
                self.write_def(self._dbase.get_register(reg_key), self._prefix,
                               self._offset)
            self._ofile.write('\n')


EXPORTERS = [
    (WriterBase.TYPE_BLOCK,
     ExportInfo(
         AsmEqu,
         ("Header files", "Assembler Source"),
         "Assembler files",
         ".s",
         'headers-asm')
     )
]
