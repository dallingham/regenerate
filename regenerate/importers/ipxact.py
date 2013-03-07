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

import xml.parsers.expat

from regenerate.db import Register, BitField
text2field = {
    "read-only": BitField.TYPE_READ_ONLY,
    "read-write": BitField.TYPE_READ_WRITE,
    }


class IpXactParser(object):
    """
    Parses the XML file, loading up the register database.
    """

    def __init__(self, dbase):
        self.__db = dbase
        self.__reg = None
        self.__field = None
        self.__field_start = 0
        self.__field_width = 0
        self.__token_list = []
        self.__in_maps = False

    def import_data(self, input_file):
        """
        Parses the specified input file.
        """
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.characters
        f = open(input_file)
        parser.ParseFile(f)

    def start_element(self, tag, attrs):
        """
        Called every time an XML element begins
        """
        self.__token_list = []
        mname = 'start_' + tag.replace(":", "_")
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(attrs)

    def end_element(self, tag):
        """
        Called every time an XML element end
        """
        text = ''.join(self.__token_list)
        mname = 'end_' + tag.replace(":", "_")
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(text)

    def characters(self, data):
        """
        Called with segments of the character data. This is not predictable
        in how it is called, so we must collect the information for assembly
        later.
        """
        self.__token_list.append(data)

    def start_spirit_register(self, attrs):
        self.__reg = Register()

    def end_spirit_register(self, text):
        self.__db.add_register(self.__reg)
        self.__reg = None

    def end_spirit_addressOffset(self, text):
        if self.__reg:
            self.__reg.address = int(text)

    def end_spirit_size(self, text):
        size = int(text)
        if self.__reg:
            self.__reg.width = size

    def start_spirit_field(self, attrs):
        self.__field = BitField()

    def end_spirit_field(self, text):
        self.__field.start_position = self.__field_start
        self.__field.stop_position = self.__field_start + self.__field_width - 1
        self.__reg.add_bit_field(self.__field)
        self.__field = None

    def end_spirit_access(self, text):
        if self.__field:
            self.__field.field_type = text2field.get(text,
                                                     BitField.TYPE_READ_ONLY)

    def end_spirit_name(self, text):
        if self.__field:
            self.__field.field_name = text.upper()
        elif self.__reg:
            self.__reg.register_name = text.upper()
            self.__reg.token = text.upper()
        elif not self.__in_maps:
            self.__db.descriptive_title = text

    def end_spirit_description(self, text):
        if self.__field:
            self.__field.description = " ".join(text.split())
        elif self.__reg:
            self.__reg.description = " ".join(text.split())

    def end_spirit_bitOffset(self, text):
        self.__field_start = int(text)

    def end_spirit_bitWidth(self, text):
        self.__field_width = int(text)

    def start_spirit_memoryMaps(self, attrs):
        self.__in_maps = True

    def end_spirit_memoryMaps(self, text):
        self.__in_maps = False
