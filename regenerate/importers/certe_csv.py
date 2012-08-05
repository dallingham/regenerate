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

REG_NAME     = "Register Name"
REG_DESCR    = "Register Description"
REG_ADDR     = "Register Address"
REG_WIDTH    = "Register Width"
REG_ACC      = "Register Access"
REG_RST      = "Register Reset Value"
REG_RMASK    = "Register Reset Mask"
FIELD_NAME   = "Field Name"
FIELD_DESCR  = "Field Description"
FIELD_OFFSET = "Field Offset"
FIELD_WIDTH  = "Field Width"
FIELD_ACCESS = "Field Access"
FIELD_RESET  = "Field Reset Value"
FIELD_MASK   = "Field Reset Mask"

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

def is_blank(item_list):
    length = 0
    for i in item_list:
        length += len(i.strip())
    return length == 0

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
        next_addr = 0
        field = None
        field_list = []
        reg_list = []
        col = {}
        name2addr = {}

        input_file = open(filename, "rU")

        titles = input_file.readline().split(",")
        for (i,name) in enumerate(titles):
            col[name] = i

        r_addr_col = col.get(REG_ADDR, -1)
        r_descr_col = col.get(REG_DESCR, -1)
        r_name_col = col.get(REG_NAME, -1)
        r_width_col = col.get(REG_WIDTH, -1)
        f_name_col = col.get(FIELD_NAME, -1)
        f_start_col = col.get(FIELD_OFFSET, -1)
        f_width_col = col.get(FIELD_WIDTH, -1)
        f_reset_col = col.get(FIELD_RESET, -1)
        f_type_col = col.get(FIELD_ACCESS, -1)
        f_descr_col = col.get(FIELD_DESCR, -1)

        for line in input_file:
            data = line.split(",")

            if is_blank(data):
                continue

            if r_name_col != -1:
                r_name = data[r_name_col].strip()
            else:
                r_name = "REG%04x" % r_addr

            r_token = r_name.upper().replace(" ", "_")

            if r_width_col != -1:
                r_width = parse_hex_value(data[r_width_col])
            else:
                r_width = 32
                
            if r_descr_col == -1:
                r_descr = ""
            else:
                r_descr = data[r_descr_col].strip()

            if data[r_addr_col].strip() == "":
                r_addr = name2addr.get(r_name, next_addr)
            else:
                r_addr = parse_hex_value(data[r_addr_col])
            
            next_addr = r_addr + r_width/8

            name2addr[r_name] = r_addr

            if f_start_col != -1:
                f_start = parse_hex_value(data[f_start_col])

                if f_width_col != -1:
                    width = parse_hex_value(data[col[FIELD_WIDTH]])
                    if width == 0:
                        f_stop = f_start
                    else:
                        f_stop = f_start + width - 1
                else:
                    f_stop = f_start

                if f_descr_col != -1:
                    f_descr = data[f_descr_col]
                else:
                    f_descr = ""
                    
                if f_name_col != -1:
                    f_name = data[f_name_col].strip()
                elif f_stop == f_start:
                    f_name = "BIT%d" % f_stop
                else:
                    f_name = "BITS_%d_%d" % (f_stop, f_start)

                if f_reset_col != -1:
                    f_reset = parse_hex_value(data[col[FIELD_RESET]])
                else:
                    f_reset = 0

                if f_type_col == -1:
                    if data[f_type_col] == "RW":
                        f_type = BitField.READ_WRITE
                    else:
                        f_type = BItField.READ_ONLY
                else:
                    f_type = BitField.READ_ONLY

            if r_addr in self.dbase.get_keys():
                reg = self.dbase.get_register(r_addr)
            else:
                reg = Register()
                reg.address = r_addr
                reg.description = r_descr
                reg.token = r_token
                reg.width = r_width
                reg.register_name = r_name
                self.dbase.add_register(reg)
            field = BitField()
            field.field_name = f_name
            field.description = f_descr
            field.start_position = f_start
            field.stop_position = f_stop
            field.field_type = f_type
            reg.add_bit_field(field)

        input_file.close()

