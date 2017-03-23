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
RstDoc - Writes out a RestructuredText document that contains the register
descriptions
"""

import os
import re
from regenerate.settings.paths import ODTFILE, USERODTFILE
from regenerate.writers.writer_base import WriterBase, ExportInfo
from regenerate.db import BitField, RegisterDb
from regenerate.extras import RegisterRst


def norm_name(text):
    return text.lower().replace(" ", "-").replace("_", "-")


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

    def substitute(self, val):
        text = val.groups()[0]
        if text in self.reglist:
            return ":ref:`%s <%s-%s-%s>`" % (text,
                                             norm_name(self._inst),
                                             norm_name(self._group),
                                             norm_name(text))
        else:
            return "`" + text + "`_"
        
    def patch_links(self, text, db, inst, group):

        if db is None:
            return text
        p = re.compile("`([^`]+)`_")
        self._inst = inst
        self._group = group
        text = p.sub(self.substitute, text)
        return text


    def find_db_from_group_inst(self, group, inst):
        current_group = None
        for grp in self.project.get_grouping_list():
            if grp.name == group:
                current_group = grp
        if current_group is None:
            return None

        reg_set = None
        for gmd in current_group.register_sets:
            if gmd.inst == inst:
                reg_set = gmd.set
        if reg_set is None:
            return None

        for fullpath in self.project.get_register_set():
            if reg_set == os.path.splitext(os.path.split(fullpath)[1])[0]:
                return RegisterDb(fullpath)
        return None

    def write(self, filename):
        """
        Writes the output file
        """

        with open(filename, "w") as f:
            f.write("\n")
            f.write(".. section-numbering::\n\n")

            f.write("**********************************\n")
            f.write("General Information\n")
            f.write("**********************************\n\n")

            f.write(self.project.documentation)
            f.write("\n\n")

            for group in self.project.get_grouping_list():
                title = "{} ({})\n".format(group.title, group.name)
                f.write("*" * len(title))
                f.write("\n")
                f.write(title)
                f.write("*" * len(title))
                f.write("\n\n")

                f.write("Description\n")
                f.write('===========================================\n\n')

                f.write(group.docs)

                f.write("\n\n")

                f.write("Subblocks\n")
                f.write('--------------------------------------------\n\n')

                for regset in group.register_sets:

                    db = self.find_db_from_group_inst(group.name, regset.inst)

                    if db.internal_only:
                        continue

                    self.reglist = set([reg.register_name for reg in db.get_all_registers()])

                    if db.descriptive_title:
                        title = "{} ({})\n".format(db.descriptive_title, regset.inst)
                    else:
                        title = regset.inst
                    f.write(title)
                    f.write("^" * len(title))
                    f.write("\n\n")
                    f.write(self.patch_links(db.overview_text, db, regset.inst, group.name))
                    f.write("\n\n")

                    for reg in db.get_all_registers():
                        rst = RegisterRst(reg, regset.set, self.project, inst=regset.inst,
                                          show_defines=True, show_uvm=True, group=group.name,
                                          maxlines=25, db=db)
                        f.write(rst.restructured_text())
                    f.write("\n\n")
                            
                
EXPORTERS = [
    (WriterBase.TYPE_PROJECT, ExportInfo(RstDoc, ("Specification", "RestructuredText"),
                                         "RestructuredText files", ".rest", 'spec-rst'))
    ]
