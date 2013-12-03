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
from regenerate.db import TYPE_TO_SIMPLE_TYPE
import re
from token import full_token, in_groups, uvm_name
from types import *

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
div.admonition, div.attention, div.caution, div.danger, div.error,
div.hint, div.important, div.note, div.tip, div.warning {
  margin: 2em ;
  border: medium outset ;
  padding: 1em }

div.admonition p.admonition-title, div.hint p.admonition-title,
div.important p.admonition-title, div.note p.admonition-title,
div.tip p.admonition-title {
  font-weight: bold ;
  font-family: sans-serif }

div.attention p.admonition-title, div.caution p.admonition-title,
div.danger p.admonition-title, div.error p.admonition-title,
div.warning p.admonition-title {
  color: red ;
  font-weight: bold ;
  font-family: sans-serif }

</style>
'''


def reg_addr(register, offset):
    base = register.address + offset
    if register.ram_size:
        return "%08x - %08x" % (base, base + register.ram_size)
    else:
        return "%08x" % base


class RegisterRst:
    """
    Produces documentation from a register definition
    """

    def __init__(self, register, regset_name=None, project=None,
                 highlight=None, show_defines=True, show_uvm=False,
                 decode=None, group=None):
        self._reg = register
        self._highlight = highlight
        self._prj = project
        self._regset_name = regset_name
        self._show_defines = show_defines
        self._show_uvm = show_uvm
        self._group = group
        if decode:
            if type(decode) is StringType:
                decode = int(decode, 16)
            elif type(decode) is IntType:
                decode = decode
            else:
                decode = None
        self._decode = decode

    def html_css(self, text=""):
        """
        Returns the definition with the basic, default CSS provided
        """
        return CSS + self.html(text)

    def text(self, line):
        if self._highlight:
            line = re.sub(self._highlight, "\ :search:`%s`" % self._highlight,
                          line)
            return re.sub(r"_\\ ", r"\\_\\ ", line)
        else:
            return line

    def restructured_text(self, text=""):
        """
        Returns the defintion of the register in RestructuredText format
        """
        o = StringIO()
        rlen = len(self._reg.register_name) + 2
        o.write(".. role:: search\n\n")
        o.write("%s\n" % ("=" * rlen))
        o.write(" " + self.text(self._reg.register_name))
        o.write("\n%s\n" % ("=" * rlen))
        o.write("\n%s\n\n" % self.text(self._reg.description))

        if self._reg.ram_size == 0:
            self._write_bit_fields(o)

        if self._show_defines:
            self._write_defines(o)

        if self._show_uvm:
            self._write_uvm(o)

        return o.getvalue()

    def _write_bit_fields(self, o):
        o.write("Bit fields\n---------------\n")
        o.write(".. list-table::\n")
        o.write("   :widths: 8 10 7 25 50\n")
        o.write("   :class: bit_table\n")
        o.write("   :header-rows: 1\n\n")
        o.write("   * - Bit(s)\n")
        if self._decode:
            o.write("     - Decode\n")
        else:
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
                o.write("   * - %d\n" % start)
            else:
                o.write("   * - %d:%d\n" % (stop, start))

            if self._decode:
                dec_val = (self._decode & mask(stop, start)) >> start
                if dec_val != field.reset_value:
                    o.write("     - **0x%x**\n" % dec_val)
                else:
                    o.write("     - 0x%x\n" % dec_val)
            else:
                o.write("     - 0x%x\n" % field.reset_value)

            o.write("     - %s\n" %
                    self.text(TYPE_TO_SIMPLE_TYPE[field.field_type]))
            o.write("     - %s\n" % self.text(field.field_name))
            descr = self.text(field.description)
            marked_descr = "\n       ".join(descr.split("\n"))
            o.write("     - %s\n" % marked_descr)
            if field.values:
                o.write("\n")
                for val in sorted(field.values,
                                  key=lambda x: int(int(x[0], 16))):
                    if val[1]:
                        o.write("       :%d: %s (%s)\n" % (int(val[0], 16),
                                                           self.text(val[2]),
                                                           self.text(val[1])))
                    else:
                        o.write("       :%d: %s\n" % (int(val[0], 16),
                                                      self.text(val[2])))
            last_index = start - 1
        if last_index >= 0:
            display_reserved(o, last_index, 0)

        o.write("\n")

    def _write_defines(self, o):

        addr_maps = self._prj.get_address_maps()
        if not addr_maps:
            return

        o.write("\n\nAddresses\n---------\n")
        if not in_groups(self._regset_name, self._prj):
            o.write(".. WARNING::\n   Register set was not added to any groups\n\n")
        else:
            o.write(".. list-table::\n")
            o.write("   :header-rows: 1\n")
            o.write("   :class: summary\n\n")
            o.write("   * - ID\n")
            for amap in addr_maps:
                o.write("     - %s\n" % self.text(amap.name))
            for inst in in_groups(self._regset_name, self._prj):
                if self._group and inst.group != self._group:
                    continue
                if inst.repeat == 1:
                    name = full_token(inst.group, inst.inst, self._reg.token,
                                      self._regset_name, -1, inst.format)
                    o.write("   * - %s\n" % self.text(name))
                    for map_name in addr_maps:
                        map_base = self._prj.get_address_base(map_name.name)
                        offset = map_base + inst.offset + inst.base
                        o.write("     - %s\n" % reg_addr(self._reg, offset))
                else:
                    for i in range(0, inst.repeat):
                        name = full_token(inst.group, inst.inst, self._reg.token,
                                          self._regset_name, i, inst.format)
                        o.write("   * - %s\n" % self.text(name))
                        for map_name in addr_maps:
                            base = self._prj.get_address_base(map_name.name)
                            offset = inst.base + inst.offset + (i * inst.roffset)
                            o.write("     - %s\n" % reg_addr(self._reg,
                                                                 offset + base))
        o.write("\n\n")

    def _display_uvm_entry(self, inst, index, o):
        name = full_token(inst.group, inst.inst, self._reg.token,
                          self._regset_name, index, inst.format)
        o.write("   * - %s\n" % self.text(name))
        name = uvm_name(inst.group, self._reg.token, inst.inst, index,
                        inst.format)
        o.write("     - %s\n" % self.text(name))

    def _write_uvm(self, o):
        """
        Writes the UVM path name(s) for the register as a table
        in restructuredText format.
        """
        o.write("\n\n")
        o.write("UVM names\n")
        o.write("---------\n")
        o.write(".. list-table::\n")
        o.write("   :header-rows: 1\n")
        o.write("   :class: summary\n\n")
        o.write("   * - ID\n")
        o.write("     - UVM name\n")
        for inst in in_groups(self._regset_name, self._prj):
            if self._group and inst.group != self._group:
                continue
            if inst.repeat == 1:
                self._display_uvm_entry(inst, -1, o)
            else:
                for i in range(0, inst.repeat):
                    self._display_uvm_entry(inst, i, o)
        o.write("\n\n")

    def html(self, text=""):
        """
        Produces a HTML subsection of the document (no header/body).
        """

        if _HTML:
            parts = publish_parts(self.restructured_text(text),
                                  writer_name="html")
            return parts['html_title'] + parts['html_subtitle'] + parts['body']
        else:
            return "<pre>" + self.restructured_text() + "</pre>"


def display_reserved(o, stop, start):
    if stop == start:
        o.write("   * - %d\n" % stop)
    else:
        o.write("   * - %d:%d\n" % (stop, start))
    o.write('     - 0x0\n')
    o.write('     - RO\n')
    o.write('     - \n')
    o.write('     - *reserved*\n')

def mask(stop, start):
    value = 0
    for i in range(start, stop + 1):
        value |= (1 << i)
    return value

    
