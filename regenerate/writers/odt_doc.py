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
OdtDoc - Writes out an OpenDocument document that contains the register
         descriptions
"""

import os
from pathlib import Path
import zipfile
import xml
from xml.sax.saxutils import escape
from io import StringIO

from ..settings.paths import ODTFILE, USERODTFILE

from .writer_base import WriterBase, ExportInfo, ProjectType
from ..db import BitField
from ..db.enums import ResetType

TYPE_MAP = ["R", "R/W", "W1C", "W1S", "WO"]

HEADING1 = "Heading_20_1"
HEADING2 = "Heading_20_2"
CELLHEAD = "Table_20_Heading"
CELLBODY = "Table_20_Contents"
CELLITEM = "Table_20_Contents_20_Item"
DEFAULT = "Default"
REGADDR = "RegAddress"
REGNAME = "RegMnemonic"
PARHEAD = "ParentHead"
PAREND = "ParentEnd"
PARTBL = "ParentTable"
BTMCNTS = "BottomContents"
TXTCNTS = "TextContents"
BTMEND = "BottomEnd"
TXTEND = "TextEnd"

NEEDED_FORMATS = [
    HEADING1,
    HEADING2,
    CELLHEAD,
    CELLBODY,
    CELLITEM,
    REGADDR,
    REGNAME,
]

HEAD = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" xmlns:math="http://www.w3.org/1998/Math/MathML" xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" xmlns:dom="http://www.w3.org/2001/xml-events" xmlns:xforms="http://www.w3.org/2002/xforms" office:class="text" office:version="1.0">
  <office:scripts/>
  <office:font-face-decls>
    <style:font-face style:name="Courier" svg:font-family="Courier" style:font-family-generic="modern" style:font-pitch="fixed"/>
    <style:font-face style:name="DejaVu Serif" svg:font-family="'DejaVu Serif'" style:font-family-generic="roman" style:font-pitch="variable"/>
    <style:font-face style:name="Verdana" svg:font-family="Verdana" style:font-family-generic="swiss" style:font-pitch="variable"/>
  </office:font-face-decls>
  <office:automatic-styles>
  <style:style style:name="ParentTable" style:family="table-properties"><style:table-properties-properties style:width="16.51cm"/></style:style>
  <style:style style:name="ParentTable.A" style:family="table-column"><style:table-column-properties style:column-width="1.2500cm"/></style:style>
  <style:style style:name="ParentTable.B" style:family="table-column"><style:table-column-properties style:column-width="1.0cm"/></style:style>
  <style:style style:name="ParentTable.C" style:family="table-column"><style:table-column-properties style:column-width="1.7cm"/></style:style>
  <style:style style:name="ParentTable.D" style:family="table-column"><style:table-column-properties style:column-width="3.1cm"/></style:style>
  <style:style style:name="ParentTable.E" style:family="table-column"><style:table-column-properties style:column-width="9.500cm"/></style:style>
  <style:style style:name="BottomContents" style:family="table-cell">
    <style:table-cell-properties fo:padding="0.10cm" fo:border-top="none" fo:border-bottom="0.002cm solid #000000" fo:border-left="0.002cm solid #000000" fo:border-right="none"/>
  </style:style>
  <style:style style:name="ParentHead" style:family="table-cell">
    <style:table-cell-properties fo:padding="0.10cm" fo:border-top="0.002cm solid #000000" fo:border-bottom="0.002cm solid #000000" fo:border-left="0.002cm solid #000000" fo:border-right="none"/>
  </style:style>
  <style:style style:name="ParentEnd" style:family="table-cell">
    <style:table-cell-properties fo:padding="0.10cm" fo:border-top="0.002cm solid #000000" fo:border-bottom="0.002cm solid #000000" fo:border-left="0.002cm solid #000000" fo:border-right="0.002cm solid #000000"/>
  </style:style>
  <style:style style:name="BottomEnd" style:family="table-cell">
    <style:table-cell-properties fo:padding="0.10cm" fo:border-top="none" fo:border-bottom="0.002cm solid #000000" fo:border-left="0.002cm solid #000000" fo:border-right="0.002cm solid #000000"/>
  </style:style>
  <style:style style:name="TextEnd" style:family="table-cell">
    <style:table-cell-properties fo:padding="0.10cm" fo:border-top="none" fo:border-bottom="0.002cm solid #000000" fo:border-left="0.002cm solid #000000" fo:border-right="0.002cm solid #000000"/>
  </style:style>
  <style:style style:name="TextContents" style:family="table-cell">
    <style:table-cell-properties fo:padding="0.10cm" fo:border-top="none" fo:border-bottom="0.002cm solid #000000" fo:border-left="0.002cm solid #000000" fo:border-right="none"/>
  </style:style>
  <style:style style:name="Tbold" style:family="text">
    <style:text-properties fo:font-weight="bold"/>
  </style:style>
</office:automatic-styles>
<office:body>
  <office:text>
    <office:forms form:automatic-focus="false" form:apply-design-mode="false"/>
"""

TAIL = """</office:text>
  </office:body>
</office:document-content>
"""


class OdtDoc(WriterBase):
    """
    Writes out an OpenDocument document that contains the register
    descriptions
    """

    def __init__(self, dbase, rlist=None):
        super().__init__(dbase)
        self.tblcnt = 0
        self.rlist = rlist
        self.zip = None
        self.cnt = None

    def start_row(self, header=False):
        """Starts a row in a table"""
        if header:
            self.cnt.write("<table:table-header-rows>")
        self.cnt.write("<table:table-row>")

    def end_row(self, header=False):
        """Ends a row in a table"""
        self.cnt.write("</table:table-row>")
        if header:
            self.cnt.write("</table:table-header-rows>")

    def end_table(self):
        """Ends a table"""
        self.cnt.write("</table:table>")

    def start_table(self):
        """Starts a table"""
        self.tblcnt += 1
        self.cnt.write('<table:table table:name="mytable%d"' % self.tblcnt)
        self.cnt.write(' table:style-name="ParentTable">')
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.A"/>'
        )
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.B"/>'
        )
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.C"/>'
        )
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.D"/>'
        )
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.E"/>'
        )

    def write_paragraph(self, para_name, text, level=0):
        """
        Writes a paragraph to the output file, based on the paragraph type
        """
        if level:
            self.cnt.write('<text:h text:style-name="%s" ' % para_name)
            self.cnt.write('text:outline-level="%d">' % level)
        else:
            self.cnt.write('<text:p text:style-name="%s">' % para_name)

        text = escape(text)
        text = text.replace("&lt;b&gt;", '<text:span text:style-name="Tbold">')
        text = text.replace("\t", "<text:tab/>")
        self.cnt.write(text.replace("&lt;/b&gt;", "</text:span>"))
        if level:
            self.cnt.write("</text:h>")
        else:
            self.cnt.write("</text:p>")

    def write_table_cell(self, cell_name, para_name, text, values=None):
        """Writes a paragraph of text as a table cell"""
        self.cnt.write("<table:table-cell")
        self.cnt.write(' table:style-name="%s"' % cell_name)
        self.cnt.write(' table:value-type="string">')
        for line in text.split("\n"):
            self.write_paragraph(para_name, line)
        if values:
            for value in values:
                if value[1]:
                    self.write_paragraph(
                        CELLITEM, "<b>%s</b>: \t[<b>%s</b>] %s" % value
                    )
                else:
                    self.write_paragraph(
                        CELLITEM, "<b>%s</b>: \t%s" % (value[0], value[2])
                    )
        self.cnt.write("</table:table-cell>")

    def __write_register_header(self, reg):
        """
        Writes the text above a register table. This includes the name, address
        mnemonic name, and description
        """
        self.write_paragraph(HEADING2, reg.name, 2)

        caddr = reg.address + self._offset
        self.write_paragraph(REGADDR, "<b>Address</b>:\t0x%08x" % caddr)
        self.write_paragraph(REGNAME, "<b>Mnemonic:</b>\t%s" % reg.token)
        descr = reg.description
        if descr:
            self.write_paragraph(DEFAULT, descr)
        self.write_paragraph(DEFAULT, "")

    def __write_table_header(self):
        """
        Writes the top of the bit definition table. This consists of the
        header row that defines the columns.
        """
        self.start_table()
        self.start_row(True)

        headers = [
            ("Bit(s)", PARHEAD),
            ("R/W", PARHEAD),
            ("Reset", PARHEAD),
            ("Name", PARHEAD),
            ("Description/Function", PAREND),
        ]

        for name in headers:
            self.write_table_cell(name[1], CELLHEAD, name[0])
        self.end_row(True)

    def __finish_table(self):
        """
        Ends the bit definition table
        """
        self.end_table()
        self.write_paragraph(DEFAULT, "")

    def _write_register(self, reg):
        """
        Writes the description for a registers, including the header and
        the table.
        """
        self.__write_register_header(reg)

        if not reg.get_bit_field_keys():
            return

        self.__write_table_header()

        regkeys = reg.get_bit_field_keys()
        regkeys.reverse()

        last_index = reg.width - 1

        for key in regkeys:
            last = key == regkeys[-1]

            bit_range = reg.get_bit_field(key)

            if bit_range.msb != last_index:
                self.print_reserved(bit_range.bit_range())
            last_index = bit_range.lsb - 1

            self.start_row()
            if last:
                table_cell = BTMCNTS
                table_end_cell = BTMEND
            else:
                table_cell = TXTCNTS
                table_end_cell = TXTEND

            text = bit_range.bit_range()
            self.write_table_cell(table_cell, CELLBODY, text)

            if bit_range.reset_type == ResetType.NUMERIC:
                cols = [
                    TYPE_MAP[bit_range.field_type],
                    rst_val(bit_range.reset_value),
                    bit_range.name,
                ]
                description = bit_range.description
            else:
                cols = [
                    TYPE_MAP[bit_range.field_type],
                    "-",
                    bit_range.name,
                ]
                description = (
                    '%s\n\nReset value is loaded from the input "%s"'
                    % (bit_range.description, bit_range.reset_input)
                )

            for val in cols:
                self.write_table_cell(table_cell, CELLBODY, val)

            self.write_table_cell(
                table_end_cell, CELLBODY, description, bit_range.values
            )
            self.end_row()

        if last_index > 0:
            self.print_reserved("%d:0" % last_index)
        elif last_index == 0:
            self.print_reserved("0")

        self.__finish_table()

    def print_reserved(self, rng):
        """
        Prints a row for reserved bits
        """
        self.start_row()
        cols = [
            (rng, TXTCNTS),
            ("R", TXTCNTS),
            ("0", TXTCNTS),
            ("", TXTCNTS),
            ("unused", TXTEND),
        ]
        for (val, style) in cols:
            self.write_table_cell(style, CELLBODY, val)
        self.end_row()

    def write(self, filename: Path):
        """
        Writes the output file
        """
        original = find_odt_template()
        if not original:
            return

        self.zip = zipfile.ZipFile(str(filename), "w")

        save_info = self.__copy_odt_contents(original)
        self.__write_contents_file(save_info)

        self.zip.close()

    def __write_contents_file(self, save_info):
        """
        Writes the contents.xml file to the zip file. Copies the header
        information, writes the registers, the writes the trailing
        information. The passed ZipInfo object is used to create store
        the information back into the zip file.
        """
        self.cnt = StringIO()
        self.cnt.write(HEAD)

        if self.rlist:
            for reg in self.rlist:
                self.__write_register_set(reg[0], reg[1])
        else:
            self.__write_register_set(self._module, self._dbase)

        self.cnt.write(TAIL)
        self.zip.writestr(save_info, self.cnt.getvalue())

    def __copy_odt_contents(self, original):
        """
        Copies all files but the content.xml file from the original
        file into a copy, returning the copy.
        """
        for fname in original.infolist():
            if fname.filename != "content.xml":
                data = original.read(fname.filename)
                self.zip.writestr(fname, data)
            else:
                save_info = fname
        original.close()
        return save_info

    def __write_register_set(self, module, dbase):
        """
        Write each register to the file
        """
        self.write_paragraph(HEADING1, module, 1)

        text = self._comments.strip()
        if text != "":
            for pdata in text.split("\n"):
                self.write_paragraph(DEFAULT, pdata)

        for key in dbase.get_keys():
            self._write_register(dbase.get_register(key))


def find_odt_template():
    """
    Finds the ODT template file, verifying that the needed styles exist.
    """
    try:
        if os.path.isfile(USERODTFILE):
            odtfile = USERODTFILE
        else:
            odtfile = ODTFILE
        original = zipfile.ZipFile(odtfile)
    except IOError as msg:
        from ..ui.error_dialogs import ErrorMsg

        ErrorMsg("Could not open OpenDocument template", str(msg))
        return None

    parser = StylesXmlParser(NEEDED_FORMATS[:])
    status = parser.parse(StringIO(original.read("styles.xml")))

    if status:
        from ..ui.error_dialogs import ErrorMsg

        ErrorMsg(
            "Bad OpenDocument template",
            "The %s file is missing the following "
            "paragraph formats:\n" % odtfile + "\n".join(status),
        )
        return None
    return original


def rst_val(val):
    """
    formats the value for 8 characters if the value is greater than 0xffff
    """
    if val > 0xFFFF:
        return "%08x" % val
    else:
        return "%x" % val


class StylesXmlParser(object):
    """
    Checks the styles listed in the input string (from a ODT styles.xml file),
    reporting paragraph formats (defined by format_list) that have not been
    defined.
    """

    def __init__(self, format_list):
        self.format_list = format_list

    def parse(self, styles_file):
        """
        Parses the style xml file
        """
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.start_element
        parser.ParseFile(styles_file)
        return self.format_list

    def start_element(self, tag, attrs):
        """
        called when a new element is found in the XML file. We only care about
        the style:style tag.
        """
        if tag == "style:style":
            name = attrs.get("style:name")
            if name in self.format_list:
                self.format_list.remove(name)


EXPORTERS = [
    (
        ProjectType.REGSET,
        ExportInfo(
            OdtDoc,
            ("Documentation", "OpenDocument"),
            "OpenDocument files",
            ".odt",
            "doc-odt",
        ),
    )
]
