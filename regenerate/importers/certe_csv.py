#
# Manage registers in a hardware design
#
# Copyright (C) 2011  Donald N. Allingham
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

def parse_hex_value(value):
    """
    Parses the input string, trying to determine the appropriate format.
    SystemRDL files seem to use the C style 0x prefix, while the examples
    in the SystemRDL spec use verilog style (32'h<value>, 5'b<value>).
    """

    match = re.match("0x[A-Fa-f0-9]+", value)
    if match:
        return int(value, 16)

    match = re.match("\d+'([hbd])(\S+)", value)
    if match:
        groups = match.groups()
        if groups[0] == 'h':
            return int(groups[1].replace('_', ''), 16)
        elif groups[0] == 'b':
            return int(groups[1].replace('_', ''), 2)
        else:
            return int(groups[1].replace('_', ''))

    try:
        return int(value, 10)
    except ValueError:
        return 0

class CerteCSVParser:
    """
    Parses the csv file and loads the database with the data extracted.
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

        input_file = open(filename, "rU")

        titles = input_file.readline()

        for line in input_file:
            data = line.split(",")

            r_addr = parse_hex_value(data[1])
            r_name = data[0].strip()
            r_token = data[0].upper().replace(" ", "_")
            r_width = parse_hex_value(data[2])
            f_name = data[6].strip()
            f_start = parse_hex_value(data[7])
            f_stop = f_start + parse_hex_value(data[8]) - 1
            f_reset = parse_hex_value(data[10])
            if data[9] == "RW":
                f_type = BitField.READ_WRITE
            elif data[9] == "RO":
                f_type = BItField.READ_ONLY

            if r_addr in self.dbase.get_keys():
                reg = self.dbase.get_register(r_addr)
            else:
                reg = Register()
                reg.address = r_addr
                reg.token = r_token
                reg.width = r_width
                reg.register_name = r_name
                self.dbase.add_register(reg)
            field = BitField()
            field.field_name = f_name
            field.start_position = f_start
            field.stop_position = f_stop
            field.field_type = f_type
            reg.add_bit_field(field)

        input_file.close()

