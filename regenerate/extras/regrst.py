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
Produces RestructuredText documentation from the definition of the register.
Docutils is used to convert the output to the desired format. Currently, only
HTML is supported now.
"""

try:
    from docutils.core import publish_parts
    _HTML = True
except:
    _HTML = False

from cStringIO import StringIO
from regenerate.db import TYPES
import re
from collections import namedtuple


# Formating token names
#
DEFAULT_FORMAT = "%(G)s%(D)s_%(R)s"
InstData = namedtuple("InstData",
                      "group set base offset repeat roffset format")


TYPE_STR = {}
for i in TYPES:
    TYPE_STR[i.type] = i.simple_type


CSS = '''
<style type="text/css">
.search {
    background-color: #FFFF00;
}
table td{
    padding: 3pt;
    font-size: 10pt;
}
table th{
    padding: 3pt;
    font-size: 11pt;
}
table th.field-name{
    padding-bottom: 0pt;
    padding-left: 5pt;
    font-size: 10pt;
}
table td.field-body{
    padding-bottom: 0pt;
    font-size: 10pt;
}
table{
    border-spacing: 0pt;
}
h1{
    font-family: Arial,Helvetica,Sans;
    font-size: 12pt;
}
h1.title{
    font-family: Arial,Helvetica,Sans;
    font-size: 14pt;
}
body{
    font-size: 10pt;
    font-family: Arial,Helvetica,Sans;
}
</style>
'''


class RegisterRst:
    """
    Produces documentation from a register definition
    """

    def __init__(self, register, regset_name=None, project=None,
                 highlight=None, prefix_list=[]):
        self._reg = register
        self._prefix_list = prefix_list
        self._highlight = highlight
        self._project = project
        self._regset_name = regset_name

    def in_groups(self):
        groups = []
        if self._regset_name and self._project:
            for group_data in self._project.get_grouping_list():
                for regset in self._project.get_group_map(group_data.name):
                    if regset.set == self._regset_name:
                        if regset.format:
                            fmt = regset.format
                        else:
                            fmt = DEFAULT_FORMAT
                        groups.append(InstData(group_data.name,
                                               self._regset_name,
                                               group_data.base,
                                               regset.offset,
                                               regset.repeat,
                                               regset.repeat_offset,
                                               fmt))
        return groups

    def html_css(self):
        """
        Returns the definition with the basic, default CSS provided
        """
        return CSS + self.html()

    def text(self, line):
        if self._highlight:
            return re.sub(self._highlight, ":search:``%s``" % self._highlight,
                          line)
        else:
            return line

    def restructured_text(self):
        """
        Returns the defintion of the register in RestructuredText format
        """
        o = StringIO()
        rlen = len(self._reg.register_name) + 2
        o.write("%s\n" % ("=" * rlen))
        o.write(" " + self.text(self._reg.register_name))
        o.write("\n%s\n" % ("=" * rlen))
        o.write("\n%s\n\n" % self.text(self._reg.description))
        o.write(".. list-table::\n")
        o.write("   :class: summary\n\n")
        o.write("   * - Token\n")
        o.write("     - %s\n" % self.text(self._reg.token))
        o.write("   * - Width\n")
        o.write("     - %0d bits\n\n\n" % self._reg.width)

        addr_maps = self._project.get_address_maps().keys()

        if addr_maps:
            o.write("\n\nAddresses\n---------\n")
            o.write(".. list-table::\n")
            o.write("   :header-rows: 1\n")
            o.write("   :class: summary\n\n")
            o.write("   * - ID\n")
            o.write("     - Offset\n")
            for amap in addr_maps:
                o.write("     - %s\n" % self.text(amap))
            for inst in self.in_groups():
                if inst.repeat == 1:
                    name_data = {"G": inst.group.upper(),
                                 "D": "",
                                 "R": self._reg.token.upper(),
                                 "S": self._regset_name,
                                 }
                    name = self.text(inst.format % name_data)
                    o.write("   * - %s\n" % name)
                    o.write("     - %s\n" % self.text("0x%08x" %
                                                      self._reg.address))
                    addr = self._reg.address + inst.offset + inst.base
                    for map_name in addr_maps:
                        faddr = addr + self._project.get_address_base(map_name)
                        o.write("     - %s\n" % self.text("0x%08x" % faddr))
                else:
                    for i in range(0, inst.repeat):
                        name_data = {"G": inst.group.upper(),
                                     "g": inst.group.lower(),
                                     "D": "%d" % i,
                                     "R": self._reg.token.upper(),
                                     "r": self._reg.token.lower(),
                                     "S": self._regset_name.upper(),
                                     "s": self._regset_name.lower()
                                     }
                        name = self.text(inst.format % name_data)
                        o.write("   * - %s\n" % name)
                        addr = self._reg.address + inst.base + \
                            inst.offset  + (i * inst.roffset)
                        o.write("     - %s\n" % self.text("0x%08x" % addr))
                        for map_name in addr_maps:
                            faddr = addr + self._project.get_address_base(map_name)
                            o.write("     - %s\n" % self.text("0x%08x" % faddr))
            o.write("\n\n")

        o.write("Bit fields\n---------------\n")
        o.write(".. list-table::\n")
        o.write("   :widths: 10 10 5 25 50\n")
        o.write("   :header-rows: 1\n\n")
        o.write("   * - Bit(s)\n")
        o.write("     - Reset\n")
        o.write("     - Type\n")
        o.write("     - Name\n")
        o.write("     - Description\n")

        last_index = self._reg.width - 1

        for key in reversed(self._reg.get_bit_field_keys()):
            field = self._reg.get_bit_field(key)
            start = field.start_position
            stop = field.stop_position

            if stop != last_index:
                display_reserved(o, last_index, stop + 1)

            if start == stop:
                o.write("   * - ``%d``\n" % start )
            else:
                o.write("   * - ``%d:%d``\n" % (stop, start))
            o.write("     - ``0x%x``\n" % field.reset_value)
            o.write("     - ``%s``\n" %
                    self.text(TYPE_STR[field.field_type]))
            o.write("     - ``%s``\n" % self.text(field.field_name))
            descr = self.text(field.description)
            marked_descr = "\n       ".join(descr.split("\n"))
            o.write("     - %s\n" % marked_descr)
            if field.values:
                o.write("\n")
                for val in sorted(field.values,
                                  key=lambda x: int(int(x[0], 16))):
                    o.write("       :%d: %s\n" % (int(val[0], 16),
                                                  self.text(val[1])))
            last_index = start - 1
        if last_index >= 0:
            display_reserved(o, last_index, 0)

        o.write("\n")
        return o.getvalue()

    def html(self):
        """
        Produces a HTML subsection of the document (no header/body).
        """
        if _HTML:
            parts = publish_parts(self.restructured_text(), writer_name="html")
            return parts['html_title'] + parts['html_subtitle'] + parts['body']
        else:
            return "<pre>" + self.restructured_text() + "</pre>"


def display_reserved(o, stop, start):
    if stop == start:
        o.write("   * - ``%d``\n" % stop)
    else:
        o.write("   * - ``%d:%d``\n" % (start, stop))
    o.write('     - ``0x0``\n')
    o.write('     - ``RO``\n')
    o.write('     - \n')
    o.write('     - *reserved*\n')
