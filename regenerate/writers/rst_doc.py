#! /usr/bin/env python
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
OdtDoc - Writes out an OpenDocument document that contains the register
             descriptions
"""

from regenerate.settings.paths import ODTFILE, USERODTFILE
from regenerate.writers.writer_base import WriterBase
from regenerate.db import BitField
from regenerate.db import RegisterDb

class RstDoc(WriterBase):
    """
    Writes out an OpenDocument document that contains the register
    descriptions
    """

    def __init__(self, project, dblist):
        WriterBase.__init__(self, project, None)
        self.tblcnt = 0
        self.project = project
        self.dblist = dblist
        self.zip = None
        self.cnt = None
        self.already_defined = {}
        self.refindex = 0
        self.img_cnt = 0
        self.images = []

    def write(self, filename):
        """
        Writes the output file
        """

        with open(filename, "w") as f:
            f.write("\n")
            f.write("=========================================================\n")
            f.write("{} - {}\n".format(self.project.short_name, self.project.name))
            f.write("=========================================================\n\n")

            f.write("Project Information\n")
            f.write(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n")


            f.write("Description\n")
            f.write("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n\n")

            f.write(self.project.documentation)
            f.write("\n\n")

            f.write("\n=================================\n")
            f.write("Top level blocks")
            f.write("\n=================================\n")


            for group in self.project.get_grouping_list():
                f.write("{}\n".format(group.name))
                f.write(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n")

                f.write("Description\n")
                f.write("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n\n")

                f.write(group.docs)
                f.write("\n\n")

                f.write("Subblocks\n")
                f.write("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n\n")



