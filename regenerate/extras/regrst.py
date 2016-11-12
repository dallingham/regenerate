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

/* Structures */
span.overline, span.bar {
	text-decoration: overline;
}
.fraction, .fullfraction {
	display: inline-block;
	vertical-align: middle;
	text-align: center;
}
.fraction .fraction {
	font-size: 80%;
	line-height: 100%;
}
span.numerator {
	display: block;
}
span.denominator {
	display: block;
	padding: 0ex;
	border-top: thin solid;
}
sup.numerator, sup.unit {
	font-size: 70%;
	vertical-align: 80%;
}
sub.denominator, sub.unit {
	font-size: 70%;
	vertical-align: -20%;
}
span.sqrt {
	display: inline-block;
	vertical-align: middle;
	padding: 0.1ex;
}
sup.root {
	font-size: 70%;
	position: relative;
	left: 1.4ex;
}
span.radical {
	display: inline-block;
	padding: 0ex;
	font-size: 150%;
	vertical-align: top;
}
span.root {
	display: inline-block;
	border-top: thin solid;
	padding: 0ex;
	vertical-align: middle;
}
span.symbol {
	line-height: 125%;
	font-size: 125%;
}
span.bigsymbol {
	line-height: 150%;
	font-size: 150%;
}
span.largesymbol {
	font-size: 175%;
}
span.hugesymbol {
	font-size: 200%;
}
span.scripts {
	display: inline-table;
	vertical-align: middle;
}
.script {
	display: table-row;
	text-align: left;
	line-height: 150%;
}
span.limits {
	display: inline-table;
	vertical-align: middle;
}
.limit {
	display: table-row;
	line-height: 99%;
}
sup.limit, sub.limit {
	line-height: 100%;
}
span.symbolover {
	display: inline-block;
	text-align: center;
	position: relative;
	float: right;
	right: 100%;
	bottom: 0.5em;
	width: 0px;
}
span.withsymbol {
	display: inline-block;
}
span.symbolunder {
	display: inline-block;
	text-align: center;
	position: relative;
	float: right;
	right: 80%;
	top: 0.3em;
	width: 0px;
}

</style>
'''


def reg_addr(register, offset):
    base = register.address + offset
    if register.ram_size > 32:
        return "%08x - %08x" % (base, base + register.ram_size)
    else:
        return "%08x" % base

def norm_name(text):
    if text is not None:
        return text.lower().replace(" ", "-").replace("_", "-")
    else:
        return ""

class RegisterRst:
    """
    Produces documentation from a register definition
    """

    def __init__(self, register,
                 regset_name=None,
                 project=None,
                 inst=None,
                 highlight=None,
                 show_defines=True,
                 show_uvm=False,
                 decode=None,
                 group=None,
                 maxlines=9999999,
                 db=None):
        self._reg = register
        self._highlight = highlight
        self._prj = project
        self._regset_name = regset_name
        self._show_defines = show_defines
        self._show_uvm = show_uvm
        self._group = group
        self._inst = inst
        self._maxlines = maxlines

        if db is None:
            self.reglist = set()
        else:
            self.reglist = set([reg.register_name for reg in db.get_all_registers()])

        if decode:
            if isinstance(decode, str):
                decode = int(decode, 16)
            elif isinstance(decode, int):
                decode = decode
            else:
                decode = None
        self._decode = decode
        self._db = db

    def html_css(self, text=""):
        """
        Returns the definition with the basic, default CSS provided
        """
        return CSS + self.html(text)

    def text(self, line):
        if self._highlight:
            replacer = re.compile(self._highlight, re.IGNORECASE)
            line = replacer.sub(lambda m: '\ :search:`%s`\ ' % m.group(0),
                                line.strip())
            return re.sub(r"_\\ ", r"\\_\\ ", line)
        else:
            return line.strip()

    def substitute(self, val):
        text = val.groups()[0]
        if text in self.reglist:
            return ":ref:`%s <%s-%s-%s>`" % (text,
                                             norm_name(self._inst),
                                             norm_name(self._group),
                                             norm_name(text))
        else:
            return "`" + text + "`_"

    def patch_links(self, text):
        if self._db is None:
            return text
        p = re.compile("`([^`]+)`_")
        text = p.sub(self.substitute, text)
        return text

    def restructured_text(self, text=""):
        """
        Returns the definition of the register in RestructuredText format
        """
        o = StringIO()
        rlen = len(self._reg.register_name) + 2
        if self._highlight:
            o.write(".. role:: search\n\n")
            o.write(" " + self.text(self._reg.register_name))

        o.write(".. _%s:\n\n" % self.refname(self._reg.register_name))

        o.write(self.text(self._reg.register_name))
        o.write("\n%s\n\n" % ('_' * rlen))
        o.write("%s\n\n" %
                self.text(self._reg.description.encode('ascii', 'replace')))

        if self._reg.ram_size < 32:  # Temporary hack
            self._write_bit_fields(o)

        if self._show_defines:
            self._write_defines(o, True, False)

        o.write(text)

        return self.patch_links(o.getvalue())

    def refname(self, reg_name):
        return "%s-%s-%s" % (norm_name(self._inst),
                             norm_name(self._group),
                             norm_name(reg_name))

    def field_ref(self, name):
        return "%s-%s-%s-%s" % (norm_name(self._inst),
                             norm_name(self._group),
                             norm_name(self._reg.register_name),
                             norm_name(name))

    def _write_bit_fields(self, o):
        o.write("Bit fields\n+++++++++++++++++++++++++++\n\n")
        o.write(".. list-table::\n")
        o.write("   :widths: 8, 10, 7, 25, 50\n")
        o.write("   :class: bit-table\n")
        o.write("   :header-rows: 1\n\n")
        o.write("   * - Bits\n")
        if self._decode:
            o.write("     - Decode\n")
        else:
            o.write("     - Reset\n")
        o.write("     - Type\n")
        o.write("     - Name\n")
        o.write("     - Description\n")

        last_index = self._reg.width - 1
        extra_text = []

        for field in reversed(self._reg.get_bit_fields()):
            if field.msb != last_index:
                display_reserved(o, last_index, field.msb + 1)

            if field.width == 1:
                o.write("   * - %d\n" % field.lsb)
            else:
                o.write("   * - %d:%d\n" % (field.msb, field.lsb))

            if self._decode:
                val = (self._decode & mask(field.msb, field.lsb)) >> field.lsb
                if val != field.reset_value:
                    o.write("     - **0x%x**\n" % val)
                else:
                    o.write("     - 0x%x\n" % val)
            else:
                o.write("     - 0x%x\n" % field.reset_value)

            o.write(
                "     - %s\n" % self.text(TYPE_TO_SIMPLE_TYPE[field.field_type]))
            o.write("     - %s\n" % self.text(field.field_name))
            descr = self.text(field.description.rstrip())
            marked_descr = "\n       ".join(descr.split("\n"))
            encoded_descr = marked_descr.encode('ascii', 'replace').rstrip()

            lines = encoded_descr.split("\n")

            if len(lines) > self._maxlines:
                o.write("     - See :ref:`Description for %s <%s>`\n" % (field.field_name, self.field_ref(field.field_name)))
                extra_text.append((self.field_ref(field.field_name), field.field_name, encoded_descr))
            else:
                o.write("     - %s\n" % encoded_descr)


            if field.values and len(field.values) < 24:
                o.write("\n")
                for val in sorted(field.values,
                                  key=lambda x: int(int(x[0], 16))):
                    if val[1]:
                        o.write("        0x%x : %s\n            %s\n\n" %
                                (int(val[0], 16), self.text(val[2]),
                                 self.text(val[1])))
                    else:
                        o.write("        0x%x : %s\n\n" %
                                (int(val[0], 16), self.text(val[2])))
            last_index = field.lsb - 1
        if last_index >= 0:
            display_reserved(o, last_index, 0)

        o.write("\n")

        for ref, name, descr in extra_text:
            o.write(".. _%s:\n\n" % ref)
            title = "Description for %s\n" % name
            o.write(title)
            o.write("+" * len(title))
            o.write("\n\n")
            o.write(descr)
            o.write("\n\n")
                    

    def _write_defines(self, o, use_uvm=True, use_id=True):

        x_addr_maps = self._prj.get_address_maps()
        instances = in_groups(self._regset_name, self._prj)
        addr_maps = set([])

        for inst in instances:
            for x in x_addr_maps:
                groups_in_addr_map = self._prj.get_address_map_groups(x.name)
                if inst.group in groups_in_addr_map:
                    addr_maps.add(x)

        if not addr_maps:
            return

        o.write("\n\nAddresses\n+++++++++++++++++++++++\n\n")
        if not in_groups(self._regset_name, self._prj):
            o.write(
                ".. WARNING::\n   Register set was not added to any groups\n\n")
        else:
            o.write(".. list-table::\n")
            o.write("   :header-rows: 1\n")
            if len(addr_maps) == 1:
                o.write("   :widths: 50, 50\n")
            elif len(addr_maps) == 2:
                o.write("   :widths: 50, 25, 25\n")
            elif len(addr_maps) == 3:
                o.write("   :widths: 50, 16, 16, 17\n")
            o.write("   :class: summary\n\n")
            o.write("   *")
            if use_uvm:
                o.write(" - Register Name\n")
            if use_id:
                if use_uvm:
                    o.write("    ")
                o.write(" - ID\n")
            for amap in addr_maps:
                o.write("     - %s\n" % self.text(amap.name))
            for inst in in_groups(self._regset_name, self._prj):
                if self._group and inst.group != self._group:
                    continue
                if self._inst and inst.inst != self._inst:
                    continue

                for grp_inst in range(0, inst.grpt):
                    if inst.grpt == 1:
                        u_grp_name = inst.group
                        t_grp_name = inst.group
                    else:
                        u_grp_name = "{0}[{1}]".format(inst.group, grp_inst)
                        t_grp_name = "{0}{1}".format(inst.group, grp_inst)

                    if inst.repeat == 1 and not inst.array:
                        o.write("   *")
                        if use_uvm:
                            name = uvm_name(u_grp_name, self._reg.token,
                                            inst.inst, -1)
                            o.write(" - %s\n" % self.text(name))
                        if use_id:
                            name = full_token(t_grp_name, self._reg.token,
                                              inst.inst, -1, inst.format)
                            if use_uvm:
                                o.write("    ")
                            o.write(" - %s\n" % self.text(name))
                        for map_name in addr_maps:
                            map_base = self._prj.get_address_base(map_name.name)
                            offset = map_base + inst.offset + inst.base + (
                                grp_inst * inst.grpt_offset)
                            o.write("     - %s\n" % reg_addr(self._reg, offset))
                    else:
                        for i in range(0, inst.repeat):
                            o.write("   *")
                            if use_uvm:
                                name = uvm_name(u_grp_name, self._reg.token,
                                                inst.inst, i)
                                o.write(" - %s\n" % self.text(name))
                            if use_id:
                                name = full_token(t_grp_name, self._reg.token,
                                                  inst.inst, i, inst.format)
                                if use_uvm:
                                    o.write("    ")
                                o.write(" - %s\n" % self.text(name))
                            for map_name in addr_maps:
                                base = self._prj.get_address_base(map_name.name)
                                offset = inst.base + inst.offset + (
                                    i * inst.roffset
                                ) + (grp_inst * inst.grpt_offset)
                                o.write("     - %s\n" %
                                        reg_addr(self._reg, offset + base))

        o.write("\n\n")

    def _display_uvm_entry(self, inst, index, o):
        name = full_token(inst.group, self._reg.token, self._regset_name,
                          index, inst.format)
        o.write("   * - %s\n" % self.text(name))
        name = uvm_name(inst.group, self._reg.token, inst.inst, index)
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
            if self._inst and inst.inst != self._inst:
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
            try:
                parts = publish_parts(
                    self.restructured_text(text),
                    writer_name="html",
                    settings_overrides={'report_level': 'quiet'}, )
                return parts['html_title'] + parts['html_subtitle'] + parts['body']
            except ZeroDivisionError:
                return "<h3>Error in Restructured Text</h3>Please contact the developer to get the documentation fixed"
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
