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

from writer_base import WriterBase
import os


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

TRAILER = [
    "#endif\n"
    ]


class CDefines(WriterBase):
    """
    Writes out C defines representing the register addresses
    """

    def __init__(self, dbase):
        WriterBase.__init__(self, dbase)
        self._ofile = None

    def write_def(self, reg, prefix, offset):
        """
        Writes the definition in the format of:

        #define register (address)
        """
        address = reg.address
        name = reg.token
        if not name:
            name = "ADDR%04x" % address
        name = "%s%s" % (prefix, name)

        if reg.width == 8:
            reg_type = "unsigned char*"
        elif reg.width == 16:
            reg_type = "unsigned short*"
        elif reg.width == 32:
            reg_type = "unsigned long*"
        else:
            reg_type = "unsigned long long*"

        self._ofile.write("#define %-30s (*((volatile %s)0x%x))\n" %
                          (name, reg_type, (address + offset)))

    def write(self, filename):
        """
        Writes the output file
        """
        self._filename = os.path.basename(filename)
        self._ofile = open(filename, "w")
        self.write_header(self._ofile, "".join(HEADER))

        for (prefix, offset) in self._dbase.instances:
            name = "%s_%s_BASE_PTR" % (prefix, self._dbase.module_name.upper())

            self._ofile.write("// Base address of the block\n")
            self._ofile.write("#define %-30s (0x%x)\n" %
                              (name, offset))

            for reg_key in self._dbase.get_keys():
                register = self._dbase.get_register(reg_key)
                self.write_def(register, prefix, offset)
            self._ofile.write('\n')

        for line in TRAILER:
            self._ofile.write('%s\n' % line.replace('$M$', self._module))
        self._ofile.close()
