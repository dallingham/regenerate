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
Sdc - Writes out synthesis constraints
"""

from writer_base import WriterBase     # IGNORE:W0403


class Sdc(WriterBase):
    """
    Output file creation class that writes a set of synthesis constraints
    """

    def __init__(self, project, dblist):
        WriterBase.__init__(self, project, None)
        self._offset = 0
        self.dblist = dblist
        self._ofile = None

    def write(self, filename):
        """
        Writes the output file
        """
        of = open(filename, "w")

        # Write register blocks
        for dbase in self.dblist:

            for group in self._project.get_grouping_list():
                used = set()
                for grp in group.register_sets:
                    if grp.set == dbase.set_name and grp.set not in used and grp.hdl:
                        used.add(grp.set)
                        for field in all_fields(dbase):
                            for i in range(0, grp.repeat):
                                base = get_signal_base(field)
                                for j in range(0, group.repeat):
                                    path = build_format(grp.hdl, j, i)
                                    signal_name = "%s/%s" % (path, base)
                                    of.write("set_multicycle -from [get_cells(%s)] -setup 2\n" % signal_name)
        of.close()

def build_format(hdl, top_count, lower_count):
    hdl = hdl.replace(".", "/")
    hdl = hdl.replace("%0g", "%(g)d")
    hdl = hdl.replace("%g", "%(g)d")
    hdl = hdl.replace("%0d", "%(d)d")
    hdl = hdl.replace("%d", "%(d)d")
    return hdl % { 'g': top_count, 'd': lower_count } 

def all_fields(dbase):
    f = []
    for reg in dbase.get_all_registers():
        for field in reg.get_bit_fields():
            if has_static_output(field):
                f.append(field)
    return f

def has_static_output(field):
    return (field.use_output_enable and field.output_signal and 
            field.output_is_static)


def get_signal_base(field):
    base = field.output_signal.split('*')
    if len(base) > 1:
        base = "%s%d%s" % (base[0], field.start_position, base[1])
    else:
        base = base[0]
    return base
