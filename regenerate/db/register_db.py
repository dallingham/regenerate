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
Provides the container database for a set of registers.
"""
import os
import re
import regenerate.db
from regenerate.settings import rules

DEF_CLK_NAME = "CLK"
DEF_RST_NAME = "RSTn"
DEF_WDATA_NAME = "WDATA"
DEF_RDATA_NAME = "RDATA"
DEF_WR_NAME = "WR"
DEF_RD_NAME = "RD"
DEF_ADDR_NAME = "ADDR"
DEF_BE_NAME = "BE"
DEF_ACK_NAME = "ACK"


class RegisterDb(object):
    """
    Container database for a set of registers.
    """

    def __init__(self, filename=None):
        self.__clock = rules.get('rules', 'clock_default', DEF_CLK_NAME)
        self.__reset = rules.get('rules', 'reset_default', DEF_RST_NAME)
        self.__write_data = rules.get('rules', 'write_data_default',
                                      DEF_WDATA_NAME)
        self.__read_data = rules.get('rules', 'read_data_default',
                                     DEF_RDATA_NAME)
        self.__write_strobe = rules.get('rules', 'write_strobe_default',
                                        DEF_WR_NAME)
        self.__read_strobe = rules.get('rules', 'read_strobe_default',
                                       DEF_RD_NAME)
        self.__addr = rules.get('rules', 'address_default', DEF_ADDR_NAME)
        self.__be = rules.get('rules', 'byte_strobe_default', DEF_BE_NAME)
        self.__ack = rules.get('rule', 'ack_default', DEF_ACK_NAME)
        self.__module = "unnamed_regs"
        self.__title = ""
        self.__registers = {}

        self.array_is_reg = False
        self.internal_only = False
        self.reset_active_level = 0
        self.data_bus_width = 32
        self.address_bus_width = 12
        self.owner = ""
        self.byte_strobe_active_level = 1
        self.overview_text = ""
        self.coverage = True
        self.set_name = ""

        if filename is not None:
            self.read_xml(filename)

    def total_bits(self):
        """Returns bits in register"""
        bits = 0
        for key in self.__registers:
            reg = self.__registers[key]
            for field in reg.get_bit_fields():
                bits += field.width
        return bits

    def get_keys(self):
        """
        Returns the register keys, which is the address of the register
        """
        return sorted(self.__registers.keys())

    def get_all_registers(self):
        """
        Returns the register keys, which is the address of the register
        """
        return iter(sorted(self.__registers.values()))

    def get_register(self, key):
        """
        Returns the register from the specified key, which should be the
        address.
        """
        return self.__registers.get(key)

    def add_register(self, reg):
        """
        Adds the register to the database.
        """
        self.__registers[reg.address] = reg

    def delete_register(self, reg):
        """
        Removes the register to the database.
        """
        del self.__registers[reg.address]

    def read_xml(self, filename):
        """
        Reads the XML file, loading the databsae.
        """
        with open(filename) as ifile:
            self.set_name = os.path.splitext(os.path.basename(filename))[0]
            parser = regenerate.db.RegParser(self)
            parser.parse(ifile)
        return self

    def save_xml(self, filename):
        """
        Saves the database to the specified XML file
        """
        writer = regenerate.db.RegWriter(self)
        writer.save(filename)

    @property
    def write_data_name(self):
        """
        Gets __write_data, which is accessed via the write_data_name property
        """
        return self.__write_data

    @write_data_name.setter
    def write_data_name(self, name):
        """
        Sets __write_data, which is accessed via the write_data_name property
        """
        self.__write_data = name.strip()

    @property
    def read_data_name(self):
        """
        Gets __read_data, which is accessed via the read_data_name property
        """
        return self.__read_data

    @read_data_name.setter
    def read_data_name(self, name):
        """
        Sets __read_data, which is accessed via the read_data_name property
        """
        self.__read_data = name.strip()

    @property
    def write_strobe_name(self):
        """
        Gets __write_strobe, which is accessed via the write_strobe_name
        property
        """
        return self.__write_strobe

    @write_strobe_name.setter
    def write_strobe_name(self, name):
        """
        Sets __write_strobe, which is accessed via the write_strobe_name
        property
        """
        self.__write_strobe = name.strip()

    @property
    def acknowledge_name(self):
        """
        Gets __ack, which is accessed via the acknowledge_name property
        """
        return self.__ack

    @acknowledge_name.setter
    def acknowledge_name(self, name):
        """
        Sets __ack, which is accessed via the acknowledge_name property
        """
        self.__ack = name.strip()

    @property
    def read_strobe_name(self):
        """
        Gets __read_strobe, which is accessed via the read_strobe_name
        property
        """
        return self.__read_strobe

    @read_strobe_name.setter
    def read_strobe_name(self, name):
        """
        Sets __read_strobe, which is accessed via the read_strobe_name
        property
        """
        self.__read_strobe = name.strip()

    @property
    def address_bus_name(self):
        """
        Gets __addr, which is accessed via the address_bus_name property
        """
        return self.__addr

    @address_bus_name.setter
    def address_bus_name(self, name):
        """
        Sets __addr, which is accessed via the address_bus_name property
        """
        self.__addr = name.strip()

    @property
    def byte_strobe_name(self):
        """
        Gets __be, which is accessed via the byte_strobe_name property
        """
        return self.__be

    @byte_strobe_name.setter
    def byte_strobe_name(self, name):
        """
        Sets __be, which is accessed via the byte_strobe_named property
        """
        self.__be = name.strip()

    @property
    def module_name(self):
        """
        Gets __module, which is accessed via the module_name property
        """
        return self.__module

    @module_name.setter
    def module_name(self, name):
        """
        Sets __module, which is accessed via the module_name property
        """
        self.__module = name.replace(' ', '_')

    @property
    def clock_name(self):
        """
        Gets __clock, which is accessed via the clock_name property
        """
        return self.__clock

    @clock_name.setter
    def clock_name(self, name):
        """
        Sets __clock, which is accessed via the clock_name property
        """
        self.__clock = name.strip()

    @property
    def reset_name(self):
        """
        Gets __reset, which is accessed via the reset_name property
        """
        return self.__reset

    @reset_name.setter
    def reset_name(self, name):
        """
        Sets __reset, which is accessed via the reset_name property
        """
        self.__reset = name.strip()

    @property
    def descriptive_title(self):
        """
        Gets __title, which is accessed via the descriptive_title property
        """
        return self.__title

    @descriptive_title.setter
    def descriptive_title(self, name):
        """
        Sets __title, which is accessed via the descriptive_title property
        """
        self.__title = name.strip()

    def find_register_by_name(self, name):
        """Finds a register with the given name, or None if not found"""
        for i in self.__registers:
            if self.__registers[i].register_name == name:
                return self.__registers[i]
        return None

    def find_register_by_token(self, name):
        """Finds a register with the given token name, or None if not found"""
        for i in self.__registers:
            if self.__registers[i].token == name:
                return self.__registers[i]
        return None

    def find_registers_by_name_regexp(self, name):
        """Finds a register with the given name, or None if not found"""
        regexp = re.compile(name)
        return [self.__registers[i] for i in self.__registers
                if regexp.match(self.__registers[i].register_name)]

    def find_registers_by_token_regexp(self, name):
        """Finds a register with the given name, or None if not found"""
        regexp = re.compile(name)
        return [self.__registers[i] for i in self.__registers
                if regexp.match(self.__registers[i].token)]

    def address_size_in_bytes(self):
        return 1 << self.address_bus_width
