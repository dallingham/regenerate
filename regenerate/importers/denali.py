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
import re


class RegInfo:
    def __init__(self):
        self.description = ""
        self.address = 0
        self.token = ""
        self.width = 32
        self.reg_name = ""
        self.field_list = []

    def dispatch(self, command, text):
        """
        Takes the command and text, calls the function associated with
        the command (do_<command>), and passes the text to be assigned.
        """
        mname = 'do_' + command
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(text)

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

    def do_name(self, text):
        """
        Strips off begining and ending quotes from the line of text and assigns
        the value to desc field.
        """
        text = text.strip()
        if text[-1] == '"':
            text = text[:-1]
        if text[0] == '"':
            text = text[1:]
        self.reg_name = text


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
        self.volatile = False

    def do_reset(self, text):
        """
        Strips off begining and ending quotes from the line of text and assigns
        the value to desc field.
        """
        text = text.strip()
        if text[-1] == '"':
            text = text[:-1]
        if text[0] == '"':
            text = text[1:]
        self.reset = parse_hex_value(text)

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

    def do_hw(self, text):
        """
        Assigns the text to the software_access field
        """
        if text and text[0] == "w":
            self.volatile = True
        else:
            self.volatile = False

    def dispatch(self, command, text):
        """
        Takes the command and text, calls the function associated with
        the command (do_<command>), and passes the text to be assigned.
        """
        mname = 'do_' + command
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(text)


class DenaliRDLParser:
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
        reg = None
        reg_list = []
        addr = 0

        with open(filename) as input_file:

            for line in input_file:
                match = re.match(
                    "addrmap\s+(.*)\s*{\s*default\s+regwidth\s*=\s*(\d+)\s*;",
                    line)
                if match:
                    groups = match.groups()
                    self.dbase.descriptive_title = groups[0].strip()
                    self.dbase.data_bus_width = int(groups[1])
                    continue

                match = re.match("\s*reg\s+{", line)
                if match:
                    reg = RegInfo()
                    reg_list.append(reg)
                    reg.address = addr
                    continue

                match = re.match("\s*reg\s+(\S+)\s*{", line)
                if match:
                    groups = match.groups()
                    reg = RegInfo()
                    reg.token = groups[0]
                    reg.reg_name = reg.token
                    reg.address = addr
                    addr = reg.address + (reg.width / 8)
                    reg_list.append(reg)
                    continue

                match = re.match("\s*field\s+{", line)
                if match:
                    field = FieldInfo()
                    continue

                match = re.match("\s*(\S+)\s*=\s*(.*);", line)
                if match:
                    groups = match.groups()
                    if field:
                        field.dispatch(groups[0], groups[1])
                    elif reg:
                        reg.dispatch(groups[0], groups[1])
                    continue

                match = re.match(
                    "\s*}\s*([^[]+)\[(\d+):(\d+)\]\s*=\s*([\dx]+)\s*;", line)
                if match:
                    groups = match.groups()
                    field.name = groups[0].strip()
                    field.stop = int(groups[1])
                    field.start = int(groups[2])
                    field.reset = parse_hex_value(groups[3])
                    reg.field_list.append(field)
                    continue

                match = re.match("\s*}\s*([^[]+)\[(\d+):(\d+)\]\s*;", line)
                if match:
                    groups = match.groups()
                    field.name = groups[0].strip()
                    field.stop = int(groups[1])
                    field.start = int(groups[2])
                    reg.field_list.append(field)
                    field = None
                    continue

                match = re.match(
                    "\s*}\s*([_A-Za-z_0-9]+)\s*@([0-9A-Fa-fx]+)\s*;", line)
                if match:
                    groups = match.groups()
                    reg.reg_name = groups[0]
                    reg.address = int(groups[1], 16)
                    addr = reg.address + (reg.width / 8)
                    continue

                match = re.match("\s*}\s*;", line)
                if match:
                    continue

        self.save(reg_list)

    def save(self, reg_list):
        """
        Converts the extracted data into register and bit field values, and
        loads the new data into the database.
        """
        lookup = {
            'rw': BitField.TYPE_READ_WRITE,
            'w': BitField.TYPE_WRITE_ONLY,
            'r': BitField.TYPE_READ_ONLY
        }

        name_count = {}
        for reg in reg_list:
            for item in reg.field_list:
                if item.name in name_count:
                    name_count[item.name] = name_count[item.name] + 1
                else:
                    name_count[item.name] = 1
        duplicates = set([key for key in name_count if name_count[key] > 1])
        current_duplicates = {}

        offset = self.dbase.data_bus_width / 8

        for reg in reg_list:
            register = Register()
            register.address = reg.address
            register.register_name = reg.reg_name
            register.token = reg.token
            if not reg.description:
                register.description = reg.description
            else:
                register.description = reg.reg_name
            register.width = self.dbase.data_bus_width

            for item in reg.field_list:
                if item.name.startswith("OBSOLETE"):
                    continue

                delta = (register.address % offset) * 8

                if item.name in duplicates:
                    if item.name in current_duplicates:
                        index = current_duplicates[item.name] + 1
                    else:
                        index = 1
                    current_duplicates[item.name] = index
                    name = "%s_%d" % (item.name, index)
                else:
                    name = item.name

                field = BitField()
                field.field_name = name
                field.field_type = lookup.get(item.software_access,
                                              BitField.READ_ONLY)
                field.start_position = item.start - delta
                field.stop_position = item.stop - delta
                field.reset_value = item.reset
                field.volatile = item.volatile
                field.description = item.description
                register.add_bit_field(field)
            self.dbase.add_register(register)


def parse_hex_value(value):
    """
    Parses the input string, trying to determine the appropriate format.
    SystemRDL files seem to use the C style 0x prefix, while the examples
    in the SystemRDL spec use verilog style (32'h<value>, 5'b<value>).
    """

    match = re.match("(0x)?[A-Fa-f0-9]+$", value)
    if match:
        return int(value, 16)

    match = re.match("\"?\d+\'([hbd])(\S+)\"?", value)
    if match:
        groups = match.groups()
        if groups[0] == 'h':
            return int(groups[1].replace('_', ''), 16)
        elif groups[0] == 'b':
            return int(groups[1].replace('_', ''), 2)
        elif groups[0] == 'd':
            return int(groups[1].replace('_', ''), 10)
        else:
            return int(groups[1].replace('_', ''))

    try:
        return int(value, 16)
    except ValueError:
        return 0
