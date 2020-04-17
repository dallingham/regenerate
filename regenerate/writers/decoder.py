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

from collections import namedtuple
import os
from jinja2 import Template
from regenerate.writers.writer_base import WriterBase, ExportInfo

# Define named tuple to hold the data to pass to the template

Ginfo = namedtuple("Ginfo", ["inst", "lower", "upper", "repeat", "offset"])


def find_group_data(proj, name):
    """
    Finds the group structure based on the name provided
    """
    for grp in proj.get_grouping_list():
        if grp.name == name:
            group = grp
            return group
    return None


def build_group_info(proj, group, dblist):
    """
    For each block instance in the group, return:

      * block instance name
      * base address of the block (dropping lower 3 bits to align to 64-bit boundary)
      * size of the address range (dropping lower 3 bits to align to 64-bit boundary)
      * number of times the instance is repeated (if any)
      * space between repeated block instances (again, aligned to 64-bit boundary)
    """
    # Find the group in the project file
    used_dbs = set()

    # Load database files, keeping the ones that belong to the group
    for dbinfo in group.register_sets:
        used_dbs.add(dbinfo.set)

    blk_map = {}
    for dbase in dblist:
        if dbase.set_name in used_dbs:
            blk_map[dbase.set_name] = dbase

    # Build the data to send to the template
    ginfo_list = []
    for dbinfo in group.register_sets:
        dbase = blk_map[dbinfo.set]
        size = 1 << dbase.address_bus_width
        if dbinfo.no_decode == 0:
            ginfo_list.append(
                Ginfo(
                    dbinfo.inst,
                    (dbinfo.offset) >> 3,
                    size >> 3,
                    dbinfo.repeat,
                    dbinfo.repeat_offset >> 3,
                )
            )

    return ginfo_list


class AddressDecode(WriterBase):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(self, project, group, dblist):
        super(AddressDecode, self).__init__(project, None)
        self.dblist = dblist
        self.group = group

    def write(self, filename):
        with open(filename, "w") as ofile:
            self.build(ofile)

    def build(self, ofile):
        group = find_group_data(self._project, self.group)

        if group is None:
            return

        ginfo_list = build_group_info(self._project, group, self.dblist)

        # Find the RTL template
        dirpath = os.path.dirname(__file__)
        template_file = os.path.join(dirpath, "templates", "regblk_mux.template")

        with open(template_file) as ifile:
            template = Template(ifile.read(), trim_blocks=True, lstrip_blocks=True)

        ofile.write(
            template.render(group_name=group.name, blk_insts=ginfo_list, mda=False)
        )


EXPORTERS = [
    (
        WriterBase.TYPE_GROUP,
        ExportInfo(
            AddressDecode,
            ("RTL", "Address decoder"),
            "SystemVerilog files",
            ".sv",
            "grp-decode",
        ),
    )
]
