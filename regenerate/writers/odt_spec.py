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

import gtk
import os
import hashlib
import zipfile
import tempfile
import time
import xml
from xml.sax.saxutils import escape
from cStringIO import StringIO

from regenerate.settings.paths import ODTFILE, USERODTFILE
from regenerate.writers.writer_base import WriterBase, ExportInfo
from regenerate.db import BitField, RegisterDb

TYPE_MAP = ["R", "R/W", "W1C", "W1S", "WO"]

HEADING1 = "Heading_20_1"
HEADING2 = "Heading_20_2"
HEADING3 = "Heading_20_3"
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


def find_range(address, range_map):
    for i in range_map:
        lower, upper = range_map[i]
        if (lower <= address <= upper):
            return i
    else:
        return None


NEEDED_FORMATS = [HEADING1, HEADING2, HEADING3, CELLHEAD, CELLBODY, CELLITEM,
                  REGADDR, REGNAME]

HEAD = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" xmlns:math="http://www.w3.org/1998/Math/MathML" xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" xmlns:dom="http://www.w3.org/2001/xml-events" xmlns:xforms="http://www.w3.org/2002/xforms" office:class="text" office:version="1.0">
  <office:scripts/>
  <office:font-face-decls>
    <style:font-face style:name="Courier" svg:font-family="Courier" style:font-family-generic="modern" style:font-pitch="fixed"/>
    <style:font-face style:name="DejaVu Serif" svg:font-family="'DejaVu Serif'" style:font-family-generic="roman" style:font-pitch="variable"/>
    <style:font-face style:name="Verdana" svg:font-family="Verdana" style:font-family-generic="swiss" style:font-pitch="variable"/>
  </office:font-face-decls>
  <office:automatic-styles>
  <style:style style:name="fr1" style:family="graphic" style:parent-style-name="Graphics">
  <style:graphic-properties style:wrap="none" style:mirror="none" fo:clip="rect(0in, 0in, 0in, 0in)" draw:luminance="0%" draw:contrast="0%" draw:red="0%" draw:green="0%" draw:blue="0%" draw:gamma="100%" draw:color-inversion="false" draw:image-opacity="100%" draw:color-mode="standard"/>
  </style:style>
  <style:style style:name="ParentTable" style:family="table-properties"><style:table-properties-properties style:width="16.51cm"/></style:style>
  <style:style style:name="ParentTable.A" style:family="table-column"><style:table-column-properties style:column-width="1.2500cm"/></style:style>
  <style:style style:name="ParentTable.B" style:family="table-column"><style:table-column-properties style:column-width="1.0cm"/></style:style>
  <style:style style:name="ParentTable.C" style:family="table-column"><style:table-column-properties style:column-width="1.7cm"/></style:style>
  <style:style style:name="ParentTable.D" style:family="table-column"><style:table-column-properties style:column-width="3.6cm"/></style:style>
  <style:style style:name="ParentTable.E" style:family="table-column"><style:table-column-properties style:column-width="9.00cm"/></style:style>
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
'''

TAIL = '''</office:text>
  </office:body>
</office:document-content>
'''


class OdtSpec(WriterBase):
    """
    Writes out an OpenDocument document that contains the register
    descriptions
    """

    def __init__(self, project, dblist):
        super(OdtSpec, self).__init__(project, None)
        self.tblcnt = 0
        self.project = project
        self.dblist = dblist
        self.zip = None
        self.cnt = None
        self.already_defined = {}
        self.refindex = 0
        self.img_cnt = 0
        self.images = []

    def start_row(self, header=False):
        """Starts a row in a table"""
        if header:
            self.cnt.write('<table:table-header-rows>')
        self.cnt.write('<table:table-row>')

    def end_row(self, header=False):
        """Ends a row in a table"""
        self.cnt.write('</table:table-row>')
        if header:
            self.cnt.write('</table:table-header-rows>')

    def end_table(self):
        """Ends a table"""
        self.cnt.write('</table:table>')

    def start_table(self):
        """Starts a table"""
        self.tblcnt += 1
        self.cnt.write('<table:table table:name="mytable%d"' % self.tblcnt)
        self.cnt.write(' table:style-name="ParentTable">')
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.A"/>')
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.B"/>')
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.C"/>')
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.D"/>')
        self.cnt.write(
            '<table:table-column table:style-name="ParentTable.E"/>')

    def add_image(self, path):
        img = gtk.gdk.pixbuf_new_from_file(path)
        width = img.get_width()
        height = img.get_height()

        self.cnt.write('<text:p text:style-name="Default">\n')
        self.cnt.write(
            '<draw:frame draw:style-name="fr1" draw:name="graphics%d" ' % self.
            img_cnt)
        self.cnt.write('svg:width="%.2fin" svg:height="%.2fin" ' %
                       (width / 144.0, height / 144.0))
        self.cnt.write('text:anchor-type="paragraph" draw:z-index="0">\n')
        self.cnt.write(
            '<draw:image xlink:href="Pictures/graphics%d.png" ' % self.img_cnt)
        self.cnt.write(
            'xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/>\n')
        self.cnt.write('</draw:frame>\n')
        self.cnt.write('</text:p>\n')
        self.images.append(
            ("Pictures/graphics%d.png" % self.img_cnt, file(path).read()))
        self.img_cnt += 1

    def write_paragraph(self, para_name, text, level=0, new_id=None):
        """
        Writes a paragraph to the output file, based on the paragraph type
        """
        if level:
            self.cnt.write('<text:h text:style-name="%s" ' % para_name)
            self.cnt.write('text:outline-level="%d">' % level)
        else:
            self.cnt.write('<text:p text:style-name="%s">' % para_name)

        text = escape(text)
        text = text.replace('&lt;b&gt;', '<text:span text:style-name="Tbold">')
        text = text.replace("\t", "<text:tab/>")
        text = text.replace('&lt;/b&gt;', '</text:span>')
        if new_id:
            hashid = hashlib.md5("%s-%s" %
                                 (self._dbase.module_name, new_id)).hexdigest()
            self.cnt.write(
                '<text:bookmark-start text:name="__RefHeading__%s"/>' % hashid)
            self.cnt.write(text.encode('ascii', 'replace'))
            self.cnt.write(
                '<text:bookmark-end text:name="__RefHeading__%s"/>' % hashid)
        else:
            self.cnt.write(text.encode('ascii', 'replace'))
        if level:
            self.cnt.write('</text:h>')
        else:
            self.cnt.write('</text:p>')

    def write_table_cell(self, cell_name, para_name, text, values=None):
        """Writes a paragraph of text as a table cell"""
        self.cnt.write('<table:table-cell')
        self.cnt.write(' table:style-name="%s"' % cell_name)
        self.cnt.write(' table:value-type="string">')
        for line in text.split("\n"):
            self.write_paragraph(para_name, line)
        if values:
            for value in values:
                if value[1]:
                    self.write_paragraph(CELLITEM,
                                         "<b>%s</b>: \t[<b>%s</b>] %s" % value)
                else:
                    descr = value[2].encode('ascii', 'replace')
                    self.write_paragraph(CELLITEM, "<b>%s</b>: \t%s" %
                                         (value[0], descr))
        self.cnt.write('</table:table-cell>')

    def __write_register_header(self, reg, new_id=None):
        """
        Writes the text above a register table. This includes the name, address
        mnemonic name, and description
        """
        self.write_paragraph(HEADING3, reg.register_name, 3, new_id)

        offset_addr = reg.address + self._offset
        name = "%s%s" % (self._prefix, reg.token)
        self.write_paragraph(REGNAME, '<b>Define:</b>\t%s' % name)
        self.write_paragraph(REGADDR,
                             '<b>Offset Address</b>:\t0x%08x' % offset_addr)
        addr_map = self.project.get_address_maps()
        for i in addr_map:
            self.write_paragraph(REGADDR, '<b>%s Address</b>:\t0x%08x' %
                                 (i, offset_addr + addr_map[i]))
        if new_id:
            descr = reg.description
            if descr:
                self.convert(DEFAULT, descr)
            self.write_paragraph(DEFAULT, '')

    def convert(self, ptype, data):
        ul_data = []
        in_wave = False
        for line in data.split("\n"):
            if in_wave:
                if line.startswith(".WAVEEND"):
                    try:
                        in_wave = False
                        f1 = tempfile.mktemp()
                        f2 = tempfile.mktemp() + ".png"
                        with open(f1, "w") as data:
                            data.write("\n".join(ul_data))
                        os.system("wavegen %s %s" % (f1, f2))
                        self.add_image(f2)
                        os.unlink(f1)
                        os.unlink(f2)
                    except:
                        pass
                else:
                    ul_data.append(line)
            elif line.startswith(".WAVEBEGIN"):
                in_wave = True
                ul_data = []
            else:
                self.write_paragraph(ptype, line)

    def __write_table_header(self):
        """
        Writes the top of the bit definition table. This consists of the
        header row that defines the columns.
        """
        self.start_table()
        self.start_row(True)

        headers = [('Bit(s)', PARHEAD), ('R/W', PARHEAD), ('Reset', PARHEAD),
                   ('Name', PARHEAD), ('Description/Function', PAREND)]

        for name in headers:
            self.write_table_cell(name[1], CELLHEAD, name[0])
        self.end_row(True)

    def __finish_table(self):
        """
        Ends the bit definition table
        """
        self.end_table()
        self.write_paragraph(DEFAULT, '')

    def _write_register(self, reg):
        """
        Writes the description for a registers, including the header and the
        table.
        """
        new_id = reg.register_name
        if self.already_defined.has_key((self._dbase, reg.address)):
            self.__write_register_header(reg)
            self._write_register_reference(reg, new_id)
            self.refindex += 1
        else:
            self.__write_register_header(reg, new_id)
            self.already_defined[(self._dbase, reg.address)] = new_id
            if reg.get_bit_field_keys():
                self._write_register_table(reg)

    def _write_register_reference(self, reg, new_id):
        hashid = hashlib.md5("%s-%s" %
                             (self._dbase.module_name, new_id)).hexdigest()
        self.cnt.write('<text:p text:stype-name="Default">See section ')
        self.cnt.write(
            '<text:bookmark-ref text:reference-format="number-all-superior" ')
        self.cnt.write(
            'text:ref-name="__RefHeading__%s">1.1</text:bookmark-ref>' % hashid)
        self.cnt.write(' (%s) on page ' % reg.register_name)
        self.cnt.write('<text:bookmark-ref text:reference-format="page" ')
        self.cnt.write(
            'text:ref-name="__RefHeading__%s">1</text:bookmark-ref>' % hashid)
        self.cnt.write('</text:p>')

    def _write_register_table(self, reg):
        self.__write_table_header()

        regkeys = reg.get_bit_field_keys()
        regkeys.reverse()

        last_index = reg.width - 1

        for key in regkeys:
            last = (key == regkeys[-1])

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

            if bit_range.reset_type == BitField.RESET_NUMERIC:
                cols = [TYPE_MAP[bit_range.field_type],
                        rst_val(bit_range.reset_value), bit_range.field_name]
                description = bit_range.description
            else:
                cols = [TYPE_MAP[bit_range.field_type], "-",
                        bit_range.field_name]
                description = '%s\n\nReset value is loaded from the input "%s"' % \
                    (bit_range.description, bit_range.reset_input)

            for val in cols:
                self.write_table_cell(table_cell, CELLBODY, val)

            self.write_table_cell(table_end_cell, CELLBODY, description,
                                  bit_range.values)
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
        cols = [(rng, TXTCNTS), ('R', TXTCNTS), ("0", TXTCNTS), ("", TXTCNTS),
                ("unused", TXTEND)]
        for (val, style) in cols:
            self.write_table_cell(style, CELLBODY, val)
        self.end_row()

    def write(self, filename):
        """
        Writes the output file
        """
        original = find_odt_template()
        if not original:
            return

        self.zip = zipfile.ZipFile(filename, "w")

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

        self.cnt.write(
            '''<text:table-of-content text:style-name="Sect1" text:protected="true" text:name="Table of Contents1">\n
            <text:table-of-content-source text:outline-level="2">
            <text:index-title-template text:style-name="Contents_20_Heading">Table of Contents</text:index-title-template>
            <text:table-of-content-entry-template text:outline-level="1" text:style-name="Contents_20_1">
            <text:index-entry-chapter/>
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
            </text:table-of-content-entry-template>
            <text:table-of-content-entry-template text:outline-level="2" text:style-name="Contents_20_2">
            <text:index-entry-chapter/>
            <text:index-entry-text/>
            <text:index-entry-tab-stop style:type="right" style:leader-char="."/>
            <text:index-entry-page-number/>
            </text:table-of-content-entry-template>
            </text:table-of-content-source>
            <text:index-body>
            <text:index-title text:style-name="Sect1" text:name="Table of Contents1_Head">
            <text:p text:style-name="Contents_20_Heading">Table of Contents</text:p>
            </text:index-title>
            </text:index-body>
            </text:table-of-content>''')

        db = {}

        my_list = {}

        addr_rng = {}
        for rng in self.project.get_grouping_list():
            addr_rng[rng.name] = (rng[1], rng[2])

        for my_db in self.dblist:
            db[my_db.module_name] = my_db

            for inst in my_db.instances:
                name = find_range(inst[1], addr_rng)
                if name:
                    my_list.setdefault(name, []).append(
                        (my_db, inst[0], inst[1]))

        keys = addr_rng.items()
        keys.sort(key=lambda x: x[1])
        for name in [n[0] for n in keys if my_list.has_key(n[0])]:
            self.prev_heading = ""
            self.write_paragraph(HEADING1, name, 1)
            category = my_list[name]

            for reg in category:
                self._dbase = reg[0]
                self._set_values_init(self._dbase, reg[1])
                if self._dbase.descriptive_title:
                    title = self._dbase.descriptive_title
                else:
                    title = self._dbase.module_name
                self.__write_register_set(title, self._dbase)

        self.cnt.write(TAIL)
        self.zip.writestr(save_info, self.cnt.getvalue())
        t = time.localtime(time.time())[:6]
        for z in self.images:
            zipinfo = zipfile.ZipInfo(z[0])
            zipinfo.date_time = t
            zipinfo.compress_type = zipfile.ZIP_DEFLATED
            self.zip.writestr(zipinfo, z[1])

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
        if self.prev_heading != module:
            self.write_paragraph(HEADING2, module, 2)
            self.prev_heading = module

        self.convert(DEFAULT, dbase.overview_text.strip())

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
        from ui.error_dialogs import ErrorMsg
        ErrorMsg('Could not open OpenDocument template', str(msg))
        return None

    parser = StylesXmlParser(NEEDED_FORMATS[:])
    status = parser.parse(StringIO(original.read('styles.xml')))

    if status:
        from ui.error_dialogs import ErrorMsg
        ErrorMsg('Bad OpenDocument template',
                 'The %s file is missing the following '
                 'paragraph formats:\n' % odtfile + "\n".join(status))
        return None
    return original


def rst_val(val):
    """
    formats the value for 8 characters if the value is greater than 0xffff
    """
    if val > 0xffff:
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
            name = attrs.get('style:name')
            if name in self.format_list:
                self.format_list.remove(name)
