#! /usr/bin/python
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
Actual program. Parses the arguments, and initiates the main window
"""

import os
from regenerate.writers.writer_base import WriterBase, ExportInfo


def find_range(address, range_map):
    for i in range_map:
        lower, upper = range_map[i]
        if (lower <= address <= upper):
            return i
    else:
        return None


class VerilogConstRegPackage(WriterBase):
    def __init__(self, project, dblist):
        WriterBase.__init__(self, None)
        self.dblist = dblist

    def write(self, filename):
        with open(filename, "w") as cfile:
            base = os.path.splitext(os.path.basename(filename))[0]
            cfile.write('package %s;\n' % base)
            cfile.write('import vlsi_pkg::*;\n')

            for db in self.dblist:

                cfile.write("// %s\n" % db.descriptive_title)
                for i in db.instances:
                    for key in db.get_keys():
                        reg = db.get_register(key)
                        addr = i[1] + reg.address
                        cfile.write("const xfer_addr %s_%s = 64'h%x;\n" %
                                    (i[0], reg.token, addr))
            cfile.write('\nendpackage : %s\n' % base)


EXPORTERS = [
    (WriterBase.TYPE_PROJECT,
     ExportInfo(
         VerilogConstRegPackage,
         ("Headers", "SystemVerilog Register Constants"),
         "SystemVerilog files",
         ".sv",
         'headers-system-verilog')
     ),
]
