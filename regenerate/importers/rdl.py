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
Imports data from a Denali RDL file
"""

from regenerate.db import Register, BitField
from regenerate.db.enums import BitType
import re


class FieldInfo:
    """
    Temporary storage mechanism for a 'field' instance in an RDL reg
    definition. Uses the common 'dispatch' mechanism to set certain
    items.
    """

    def __init__(self):
        self.description = ""
        self.software_access = ""
        self.start = 0
        self.stop = 0
        self.reset = 0
        self.name = ""

    def do_desc(self, text):
        """
        Strips off begining and ending quotes from the line of text and assigns
        the value to desc field.
        """
        text = text.strip()
        if text[-1] == '"':
            text = text[:-1]
        if text[0] == '"':
            text = text[1:]
        self.description = text

    def do_sw(self, text):
        """
        Assigns the text to the software_access field
        """
        self.software_access = text

    def do_reset(self, text):
        """
        Assigns the text to the software_access field
        """
        self.reset = parse_hex_value(text)

    def dispatch(self, command, text):
        """
        Takes the command and text, calls the function associated with
        the command (do_<command>), and passes the text to be assigned.
        """
        mname = "do_" + command
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(text)


class RDLParser:
    """
    Parses the RDL file and loads the database with the data extracted.
    """

    def __init__(self, dbase):
        self.dbase = dbase

    def import_data(self, filename):
        """
        Opens, parses, and extracts data from the input file.
        """
        field = None
        field_list = []
        reg_list = []
        default_reg = 32
        regwidth = 32

        input_file = open(filename)

        self.dbase.data_bus_width = default_reg

        i = 0
        for line in input_file:
            i += 1
            match = re.match("\s*reg\s+{", line)
            if match:
                field_list = []
                regwidth = default_reg
                continue

            match = re.search("\s*default\s+regwidth\s*=\s*(.*);", line)
            if match:
                groups = match.groups()
                default_reg = int(groups[0])
                self.dbase.data_bus_width = default_reg
                continue

            match = re.match("\s*regwidth\s*=\s*(.*);", line)
            if match:
                groups = match.groups()
                regwidth = int(groups[0])
                continue

            match = re.match("\s*field\s+{", line)
            if match:
                field = FieldInfo()
                continue

            match = re.match("\s*(\S+)\s*=\s*(.*);", line)
            if match:
                groups = match.groups()
                field.dispatch(groups[0], groups[1])
                continue

            match = re.match("\s*}\s*([^[]+)\[(\d+):(\d+)\]\s*;", line)
            if match:
                groups = match.groups()
                field.name = groups[0]
                field.stop = int(groups[1])
                field.start = int(groups[2])
                field_list.append(field)
                continue

            match = re.match("\s*}\s*([A-Za-z_0-9]+)\s*@(.+)\s*;", line)
            if match:
                groups = match.groups()
                reg_list.append(
                    (groups[0], groups[1], regwidth, field_list[:]))
                continue

        input_file.close()
        self.save(reg_list)

    def save(self, reg_list):
        """
        Converts the extracted data into register and bit field values, and
        loads the new data into the database.
        """
        lookup = {
            '"rw"': BitType.READ_WRITE,
            '"w"': BitType.WRITE_ONLY,
            '"r"': BitType.READ_ONLY,
        }

        for (reg_name, addr_txt, width, field_list) in reg_list:
            register = Register()
            register.address = int(addr_txt, 16)
            register.register_name = reg_name
            register.width = width
            register.token = reg_name
            self.dbase.add_register(register)

            for item in field_list:
                field = BitField()
                field.field_name = item.name
                try:
                    field.field_type = lookup[item.software_access]
                except IndexError:
                    field.field_type = BitType.READ_ONLY

                field.start_position = item.start
                field.stop_position = item.stop
                field.reset_value = item.reset
                field.description = item.description
                register.add_bit_field(field)


def parse_hex_value(value):
    """
    Parses the input string, trying to determine the appropriate format.
    SystemRDL files seem to use the C style 0x prefix, while the examples
    in the SystemRDL spec use verilog style (32'h<value>, 5'b<value>).
    """

    match = re.match("(0x)?[A-Fa-f0-9]+", value)
    if match:
        return int(value, 16)

    match = re.match("\d+'([hbd])(\S+)", value)
    if match:
        groups = match.groups()
        if groups[0] == "h":
            return int(groups[1].replace("_", ""), 16)
        elif groups[0] == "b":
            return int(groups[1].replace("_", ""), 2)
        else:
            return int(groups[1].replace("_", ""))

    try:
        return int(value, 16)
    except ValueError:
        return 0
