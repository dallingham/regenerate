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
from regenerate.extras import full_token, in_groups
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

REG_TYPE = {
    8: "unsigned char*",
    16: "unsigned short*",
    32: "unsigned long*",
    64: "unsigned long long*",
    }


class CDefines(WriterBase):
    """
    Writes out C defines representing the register addresses
    """

    def __init__(self, project, dbase):
        WriterBase.__init__(self, project, dbase)
        self._ofile = None

    def write_def(self, reg, data, base):
        """
        Writes the definition in the format of:

        #define register (address)
        """

        address = reg.address + base + data.base
        if data.repeat > 1:
            for i in range(0, data.repeat):
                name = full_token(data.group, reg.token,
                                  self._dbase.module_name,
                                  i, data.format)
                address += (i * data.roffset)
                self._ofile.write("#define %-30s (*((volatile %s)0x%x))\n" %
                                  (name, REG_TYPE[reg.width], address))
        else:
            name = full_token(data.group, reg.token,
                              self._dbase.module_name,
                              -1, data.format)
            self._ofile.write("#define %-30s (*((volatile %s)0x%x))\n" %
                              (name, REG_TYPE[reg.width], address))

    def write(self, filename):
        """
        Writes the output file
        """
        self._filename = os.path.basename(filename)

        with open(filename, "w") as self._ofile:
            self.write_header(self._ofile, "".join(HEADER))

            addr_maps = self._project.get_address_maps()

            if len(addr_maps) > 0:
                base = self._project.get_address_base(addr_maps[0].name)
                for data in in_groups(self._dbase.module_name, self._project):
                    for register in self._dbase.get_all_registers():
                        self.write_def(register, data, base)
                    self._ofile.write('\n')

            for line in TRAILER:
                self._ofile.write('%s\n' % line.replace('$M$', self._module))
