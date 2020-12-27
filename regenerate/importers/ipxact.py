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
Parses the register database, loading the database.
"""

import re
import xml.etree.ElementTree as ET
from regenerate.db import Register, BitField
from regenerate.db.enums import BitType, ResetType


text2field = {
    "read-only": BitType.READ_ONLY,
    "read-write": BitType.READ_WRITE,
    "write-only": BitType.WRITE_ONLY,
    "writeOnce": BitType.WRITE_ONLY,
}


text2write = {
    "oneToClear": BitType.WRITE_1_TO_CLEAR_SET,
    "oneToSet": BitType.WRITE_1_TO_SET,
}


class IpXactParser:
    """
    Parses the XML file, loading up the register database.
    """

    def __init__(self, dbase):
        self._db = dbase
        self._reg = None
        self._field = None
        self._fld_start = 0
        self._fld_width = 0
        self._token_list = []
        self._in_maps = False
        self._block_offset = 0
        self._block_list = [0]
        self._in_field_reset = False
        self._in_reg_reset = False
        self._reg_reset = (False, 0)

    def import_data(self, input_file):
        """Parses the specified input file."""

        tree = ET.parse(input_file)
        root = tree.getroot()

        for mem_map in root.find(
            "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009}memoryMaps"
        ):
            name = mem_map.find(
                "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009}name"
            )
            descr = mem_map.find(
                "{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009}description"
            )

        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.characters
        with open(input_file) as ifile:
            parser.ParseFile(ifile)
        # #crossreference(self._db)

    def start_element(self, tag, attrs):
        """
        Called every time an XML element begins
        """
        self._token_list = []

        fields = tag.split(":")
        if len(fields) == 1:
            mname = f"start_{tag}"
        else:
            mname = f"start_{fields[1]}"

        if hasattr(self, mname):
            method = getattr(self, mname)
            method(attrs)

    def end_element(self, tag):
        """
        Called every time an XML element end
        """
        text = "".join(self._token_list)
        fields = tag.split(":")
        if len(fields) == 1:
            mname = f"end_{tag}"
        else:
            mname = f"end_{fields[1]}"

        if hasattr(self, mname):
            method = getattr(self, mname)
            method(text)

    def characters(self, data):
        """
        Called with segments of the character data. This is not predictable
        in how it is called, so we must collect the information for assembly
        later.
        """
        self._token_list.append(data)

    def start_register(self, _attrs):
        "Register opening tag encountered. Create a new register"

        self._reg = Register()

    def end_register(self, _text):
        "register ending tag encountered. Add the register to the database"

        self._db.add_register(self._reg)
        self._reg = None
        self._reg_reset = (False, 0)

    def end_addressOffset(self, text):
        "Address offset end. Convert gathered text into an address"

        if self._reg:
            self._reg.address = int(text, 0) + self._block_offset

    def end_dim(self, text):
        "Dim end. Convert text to the dimension of the register"

        if self._reg:
            self._reg.dimension = int(text, 0)

    def end_addressBlock(self, _text):
        self._block_offset = self._block_list.pop()

    def end_baseAddress(self, text):
        self._block_list.append(self._block_offset)
        self._block_offset = self._block_offset + int(text, 0)

    def end_size(self, text):
        size = int(text, 0)
        if self._reg:
            self._reg.width = size

    def start_reset(self, _attrs):
        if self._field:
            self._in_field_reset = True
        elif self._reg:
            self._in_reg_reset = True

    def end_reset(self, text):
        self._in_field_reset = False
        self._in_reg_reset = False

    def end_value(self, text):
        if self._in_field_reset:
            if self._field:
                self._field.reset_value = int(text, 16)
                self._field.reset_type = ResetType.NUMERIC
        elif self._in_reg_reset:
            self._reg_reset = (True, int(text, 16))

    def start_field(self, __attrs):
        self._field = BitField()

    def end_field(self, _text):
        if not self._field.field_name.startswith("RESERVED"):
            self._field.start_position = self._fld_start
            self._field.stop_position = self._fld_start + self._fld_width - 1
            self._reg.add_bit_field(self._field)
            if self._reg_reset[0]:
                self._field.reset_value = (
                    self._reg_reset[1] >> self._fld_start
                ) & ((1 << self._field.width) - 1)
                self._field.reset_type = ResetType.NUMERIC

        self._field = None

    def end_access(self, text):
        if self._field:
            if self._field.field_type not in (
                BitType.WRITE_1_TO_SET,
                BitType.WRITE_1_TO_CLEAR_SET,
            ):
                self._field.field_type = text2field.get(
                    text, BitType.READ_ONLY
                )

    def end_modifiedWriteValue(self, text):
        if self._field:
            self._field.field_type = text2write.get(
                text, BitType.WRITE_1_TO_CLEAR_SET
            )

    def end_name(self, text):
        if self._field:
            self._field.field_name = text.upper()
        elif self._reg:
            self._reg.register_name = text.replace("_", " ")
            self._reg.token = text.upper()
        elif not self._in_maps and not self._db.descriptive_title:
            self._db.descriptive_title = text.strip()

    def end_description(self, text):
        if self._field:
            self._field.description = text.strip()
        elif self._reg:
            self._reg.description = text.strip()

    def end_bitOffset(self, text):
        self._fld_start = int(text, 0)

    def end_bitWidth(self, text):
        self._fld_width = int(text, 0)

    def start_memoryMaps(self, _attrs):
        self._in_maps = True

    def end_memoryMaps(self, _text):
        self._in_maps = False


def crossreference(dbase):
    names = sorted(
        [reg.register_name for reg in dbase.get_all_registers()],
        key=len,
        reverse=True,
    )

    re_list = [r"([^`])({0}) ((R|r)egister)".format(name) for name in names]

    for reg in dbase.get_all_registers():
        for regex in re_list:
            reg.description = re.sub(regex, r"\1`\2`_ \3", reg.description)
        for field in reg.get_bit_fields():
            for regex in re_list:
                field.description = re.sub(
                    regex, r"\1`\2`_ \3", field.description
                )
