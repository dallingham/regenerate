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

import re
import sys

from regenerate.db import TYPE_TO_SIMPLE_TYPE
from regenerate.extras.token import full_token, in_groups, uvm_name

try:
    from docutils.core import publish_parts

    _HTML = True
except ImportError:
    _HTML = False

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


if sys.version_info[0] == 3:
    REPORT_LEVEL = 4
else:
    REPORT_LEVEL = "quiet"


CSS = """
<style type="text/css">
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
"""


def reg_addr(register, offset):
    base = register.address + offset
    if register.ram_size > 32:
        return "%08x - %08x" % (base, base + register.ram_size)
    return "%08x" % base


def norm_name(text):
    if text is not None:
        return text.lower().replace(" ", "-").replace("_", "-")
    return ""


class RegisterRst(object):
    """
    Produces documentation from a register definition
    """

    def __init__(
        self,
        register,
        regset_name=None,
        project=None,
        inst=None,
        highlight=None,
        show_defines=True,
        show_uvm=False,
        decode=None,
        group=None,
        maxlines=9999999,
        dbase=None,
        max_values=24,
        bootstrap=False,
        header_level=1,
    ):

        self._max_values = max_values
        self._reg = register
        self._highlight = highlight
        self._prj = project
        self._regset_name = regset_name
        self._show_defines = show_defines
        self._show_uvm = show_uvm
        self._group = group
        self._inst = inst
        self._maxlines = maxlines
        self._bootstrap = bootstrap
        self._header_level = header_level

        if dbase is None:
            self.reglist = set()
        else:
            self.reglist = set(
                [reg.register_name for reg in dbase.get_all_registers()]
            )

        if decode:
            try:
                if isinstance(decode, (unicode, str)):
                    decode = int(decode, 16)
                elif isinstance(decode, int):
                    decode = decode
                else:
                    decode = None
            except ValueError:
                decode = None
        self._decode = decode
        self._db = dbase

    def html_css(self, text=""):
        """
        Returns the definition with the basic, default CSS provided
        """
        return CSS + self.html(text)

    def text(self, line):
        return line.strip()

    def restructured_text(self, text=""):
        """
        Returns the definition of the register in RestructuredText format
        """
        ofile = StringIO()

        self.str_title(ofile)

        self.str_overview(ofile)

        if self._reg.ram_size < 32:  # Temporary hack
            self._write_bit_fields(ofile)

        if self._show_defines:
            self._write_defines(ofile, True, False)

        ofile.write(text)
        return ofile.getvalue()

    def refname(self, reg_name):
        return "%s-%s-%s" % (
            norm_name(self._inst),
            norm_name(self._group),
            norm_name(reg_name),
        )

    def field_ref(self, name):
        return "%s-%s-%s-%s" % (
            norm_name(self._inst),
            norm_name(self._group),
            norm_name(self._reg.register_name),
            norm_name(name),
        )

    def str_title(self, ofile=None):
        ret_str = False

        if ofile is None:
            ofile = StringIO()
            ret_str = True

        rlen = len(self._reg.register_name) + 2
        ofile.write(".. _%s:\n\n" % self.refname(self._reg.register_name))
        ofile.write(self._reg.register_name)
        ofile.write("\n%s\n\n" % ("_" * rlen))

        if ret_str:
            return ofile.getvalue()
        return ""

    def str_overview(self, ofile=None):
        ret_str = False

        if ofile is None:
            ofile = StringIO()
            ret_str = True

        ofile.write(
            "%s\n\n"
            % self._reg.description.encode("utf-8", "replace").decode()
        )

        if ret_str:
            return ofile.getvalue()
        return ""

    def str_bit_fields(self, ofile=None):

        ret_str = False

        if ofile is None:
            ofile = StringIO()
            ret_str = True

        ofile.write(".. role:: resetvalue\n\n")
        ofile.write(".. role:: editable\n\n")
        ofile.write(".. role:: mono\n\n")
        ofile.write(".. list-table::\n")
        ofile.write("   :name: bit_table\n")
        ofile.write("   :widths: 8, 10, 7, 25, 50\n")
        if self._bootstrap:
            ofile.write(
                "   :class: table table-bordered table-striped table-condensed display\n"
            )
        else:
            ofile.write("   :class: bit-table\n")
        ofile.write("   :header-rows: 1\n\n")
        ofile.write("   * - Bits\n")
        if self._decode:
            ofile.write("     - Decode\n")
        else:
            ofile.write("     - Reset\n")
        ofile.write("     - Type\n")
        ofile.write("     - Name\n")
        ofile.write("     - Description\n")

        last_index = self._reg.width - 1
        extra_text = []

        for field in reversed(self._reg.get_bit_fields()):
            if field.msb != last_index:
                display_reserved(ofile, last_index, field.msb + 1)

            if field.width == 1:
                ofile.write("   * - %02d\n" % field.lsb)
            else:
                ofile.write("   * - %02d:%02d\n" % (field.msb, field.lsb))

            if self._decode:
                val = (self._decode & mask(field.msb, field.lsb)) >> field.lsb
                if val != field.reset_value:
                    ofile.write("     - :resetvalue:`0x%x`\n" % val)
                else:
                    ofile.write("     - 0x%x\n" % val)
            else:
                ofile.write("     - 0x%x\n" % field.reset_value)

            ofile.write("     - %s\n" % TYPE_TO_SIMPLE_TYPE[field.field_type])
            ofile.write("     - %s\n" % field.field_name)
            descr = field.description.strip()
            marked_descr = "\n       ".join(descr.split("\n"))
            encoded_descr = (
                marked_descr.encode("utf-8", "replace").rstrip().decode()
            )

            lines = encoded_descr.split("\n")

            if len(lines) > self._maxlines:
                ofile.write(
                    "     - See :ref:`Description for %s <%s>`\n"
                    % (field.field_name, self.field_ref(field.field_name))
                )
                extra_text.append(
                    (
                        self.field_ref(field.field_name),
                        field.field_name,
                        encoded_descr,
                    )
                )
            else:
                ofile.write("     - %s\n" % encoded_descr)

            if field.values and len(field.values) < self._max_values:
                ofile.write("\n")

                for val in sorted(
                    field.values, key=lambda x: int(int(x[0], 16))
                ):
                    if val[1] and val[2]:
                        ofile.write(
                            "        0x%x : %s\n            %s\n\n"
                            % (int(val[0], 16), val[1], val[2])
                        )
                    elif val[1]:
                        ofile.write(
                            "        0x%x : %s\n            %s\n\n"
                            % (
                                int(val[0], 16),
                                val[1],
                                "*no description available*",
                            )
                        )
                    else:
                        ofile.write(
                            "        0x%x : %s\n            %s\n\n"
                            % (int(val[0], 16), "*no token available*", val[2])
                        )
            last_index = field.lsb - 1
        if last_index >= 0:
            display_reserved(ofile, last_index, 0)

        for ref, name, descr in extra_text:
            ofile.write(".. _%s:\n\n" % ref)
            title = "Description for %s\n" % name
            ofile.write(title)
            ofile.write("+" * len(title))
            ofile.write("\n\n")
            ofile.write(descr)
            ofile.write("\n\n")

        if ret_str:
            return ofile.getvalue()
        return ""

    def _write_bit_fields(self, ofile):

        ofile.write("Bit fields\n+++++++++++++++++++++++++++\n\n")
        self.str_bit_fields(ofile)

    def _write_defines(self, ofile, use_uvm=True, use_id=True):

        ofile.write("\n\nAddresses\n+++++++++++++++++++++++\n\n")
        self.str_defines(ofile, use_uvm, use_id)

    def str_defines(self, ofile=None, use_uvm=True, use_id=True):

        ret_str = False

        if ofile is None:
            ofile = StringIO()
            ret_str = True

        x_addr_maps = self._prj.get_address_maps()
        instances = in_groups(self._regset_name, self._prj)
        addr_maps = set([])

        for inst in instances:
            for x_map in x_addr_maps:
                groups_in_addr_map = self._prj.get_address_map_groups(
                    x_map.name
                )
                if inst.group in groups_in_addr_map:
                    addr_maps.add(x_map)

        if not addr_maps:
            ofile.write(".. warning::\n")
            ofile.write("   :class: alert alert-warning\n\n")
            ofile.write(
                "   This register has not been mapped into any address space.\n\n"
            )

        elif in_groups(self._regset_name, self._prj):
            ofile.write(".. list-table::\n")
            ofile.write("   :header-rows: 1\n")
            if len(addr_maps) == 1:
                ofile.write("   :widths: 50, 50\n")
            elif len(addr_maps) == 2:
                ofile.write("   :widths: 50, 25, 25\n")
            elif len(addr_maps) == 3:
                ofile.write("   :widths: 50, 16, 16, 17\n")
            if self._bootstrap:
                ofile.write(
                    "   :class: table table-bordered table-striped table-condensed\n\n"
                )
            else:
                ofile.write("   :class: summary\n\n")
            ofile.write("   *")
            if use_uvm:
                ofile.write(" - Register Name\n")
            if use_id:
                if use_uvm:
                    ofile.write("    ")
                ofile.write(" - ID\n")
            for amap in addr_maps:
                ofile.write("     - %s\n" % amap.name)

            for inst in in_groups(self._regset_name, self._prj):
                if self._group and inst.group != self._group:
                    continue
                if self._inst and inst.inst != self._inst:
                    continue

                for grp_inst in range(0, inst.grpt):

                    if inst.repeat == 1 and not inst.array:
                        if self._reg.dimension <= 1:
                            self._addr_entry(
                                ofile,
                                inst,
                                use_uvm,
                                use_id,
                                addr_maps,
                                grp_inst,
                                -1,
                                -1,
                            )
                        else:
                            for i in range(self._reg.dimension):
                                self._addr_entry(
                                    ofile,
                                    inst,
                                    use_uvm,
                                    use_id,
                                    addr_maps,
                                    grp_inst,
                                    -1,
                                    i,
                                )
                    else:
                        for ginst in range(0, inst.repeat):

                            if self._reg.dimension <= 1:
                                self._addr_entry(
                                    ofile,
                                    inst,
                                    use_uvm,
                                    use_id,
                                    addr_maps,
                                    grp_inst,
                                    ginst,
                                    -1,
                                )
                            else:
                                for i in range(self._reg.dimension):
                                    self._addr_entry(
                                        ofile,
                                        inst,
                                        use_uvm,
                                        use_id,
                                        addr_maps,
                                        grp_inst,
                                        ginst,
                                        i,
                                    )

            ofile.write("\n\n")

        if ret_str:
            return ofile.getvalue()
        return ""

    def _addr_entry(
        self,
        ofile,
        inst,
        use_uvm,
        use_id,
        addr_maps,
        grp_inst,
        group_index,
        index,
    ):

        if inst.grpt == 1:
            u_grp_name = inst.group
            t_grp_name = inst.group
        else:
            u_grp_name = "{0}[{1}]".format(inst.group, grp_inst)
            t_grp_name = "{0}{1}".format(inst.group, grp_inst)

        ofile.write("   *")
        if use_uvm:
            name = uvm_name(
                u_grp_name, self._reg.token, inst.inst, group_index
            )
            if index < 0:
                ofile.write(" - %s\n" % name)
            else:
                ofile.write(" - %s[%d]\n" % (name, index))
        if use_id:
            name = full_token(
                t_grp_name,
                self._reg.token,
                inst.inst,
                group_index,
                inst.format,
            )
            if use_uvm:
                ofile.write("    ")
            ofile.write(" - %s\n" % name)
        for map_name in addr_maps:
            map_base = self._prj.get_address_base(map_name.name)
            offset = (
                map_base
                + inst.offset
                + inst.base
                + (grp_inst * inst.grpt_offset)
            )
            if group_index > 0:
                offset += group_index * inst.roffset

            if index < 0:
                ofile.write("     - ``%s``\n" % reg_addr(self._reg, offset))
            else:
                ofile.write(
                    "     - ``%s``\n"
                    % reg_addr(
                        self._reg, offset + (index * (self._reg.width // 8))
                    )
                )

    def _display_uvm_entry(self, inst, index, ofile):
        name = full_token(
            inst.group, self._reg.token, self._regset_name, index, inst.format
        )
        ofile.write("   * - %s\n" % name)
        name = uvm_name(inst.group, self._reg.token, inst.inst, index)
        ofile.write("     - %s\n" % name)

    def _write_uvm(self, ofile):
        """
        Writes the UVM path name(s) for the register as a table
        in restructuredText format.
        """
        ofile.write("\n\n")
        ofile.write("UVM names\n")
        ofile.write("---------\n")
        ofile.write(".. list-table::\n")
        ofile.write("   :header-rows: 1\n")
        if self._bootstrap:
            ofile.write(
                "   :class: table table-bordered table-striped table-condensed\n\n"
            )
        else:
            ofile.write("   :class: summary\n\n")
        ofile.write("   * - ID\n")
        ofile.write("     - UVM name\n")
        for inst in in_groups(self._regset_name, self._prj):
            if self._group and inst.group != self._group:
                continue
            if self._inst and inst.inst != self._inst:
                continue
            if inst.repeat == 1:
                self._display_uvm_entry(inst, -1, ofile)
            else:
                for i in range(0, inst.repeat):
                    self._display_uvm_entry(inst, i, ofile)
        ofile.write("\n\n")

    def html_from_text(self, text):
        if text is None:
            return "No data"
        if _HTML:
            try:
                if self._header_level > 1:
                    overrides = {
                        "initial_header_level": self._header_level,
                        "doctitle_xform": False,
                        "report_level": REPORT_LEVEL,
                    }
                else:
                    overrides = {"report_level": REPORT_LEVEL}
                parts = publish_parts(
                    text, writer_name="html", settings_overrides=overrides
                )
                if self._highlight is None:
                    return (
                        parts["html_title"]
                        + parts["html_subtitle"]
                        + parts["body"]
                    )
                paren_re = re.compile(
                    "(%s)" % self._highlight, flags=re.IGNORECASE
                )
                return (
                    parts["html_title"]
                    + parts["html_subtitle"]
                    + paren_re.sub(r"<mark>\1</mark>", parts["body"])
                )

            except TypeError as msg:
                return (
                    "<h3>TypeError</h3><p>"
                    + str(msg)
                    + "</p><pre>"
                    + text
                    + "</pre>"
                )
            except AttributeError as msg:
                return (
                    "<h3>AttributeError</h3><p>"
                    + str(msg)
                    + "</p><pre>"
                    + text
                    + "</pre>"
                )
            except ZeroDivisionError:
                return "<h3>ZeroDivisionError in Restructured Text</h3>Please contact the developer to get the documentation fixed"
        else:
            return "<pre>{0}</pre>".format(self.restructured_text())

    def html(self, text=""):
        """
        Produces a HTML subsection of the document (no header/body).
        """
        return self.html_from_text(self.restructured_text(text))

    def html_bit_fields(self, text=""):
        return self.html_from_text(self.str_bit_fields() + "\n" + text)

    def html_title(self):
        return self.html_from_text(self.str_title())

    def html_addresses(self, text=""):
        return self.html_from_text(
            self.str_defines(None, True, False) + "\n" + text
        )

    def html_overview(self, text=""):
        return self.html_from_text(
            self.str_overview() + "\n" + text
        ) + self.html_from_text(text)


def display_reserved(ofile, stop, start):
    if stop == start:
        ofile.write("   * - ``%02d``\n" % stop)
    else:
        ofile.write("   * - ``%02d:%02d``\n" % (stop, start))
    ofile.write("     - ``0x0``\n")
    ofile.write("     - RO\n")
    ofile.write("     - \n")
    ofile.write("     - *reserved*\n")


def mask(stop, start):
    value = 0
    for i in range(start, stop + 1):
        value |= 1 << i
    return value
