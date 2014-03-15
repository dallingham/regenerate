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
import re
import os
import xml
from regenerate.db.reg_parser import RegParser
from regenerate.db.reg_writer import RegWriter

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

    def __init__(self):
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

        self.reset_active_level = 0
        self.data_bus_width = 32
        self.address_bus_width = 32
        self.owner = ""
        self.byte_strobe_active_level = 1
        self.__title = ""
        self.overview_text = ""
        self.enable_coverage = False
        self.__registers = {}
        self.set_name = ""

    def get_keys(self):
        """
        Returns the register keys, which is the address of the register
        """
        return sorted(self.__registers.keys())

    def get_all_registers(self):
        """
        Returns the register keys, which is the address of the register
        """
        return [self.__registers[key]
                for key in sorted(self.__registers.keys())]

    def get_register(self, key):
        """
        Returns the register from the specified key, which should be the
        address.
        """
        assert (key == self.__registers.get(key).address)
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
        try:
            ifile = open(filename)
            self.set_name = os.path.splitext(os.path.basename(filename))[0]
            parser = RegParser(self)
            parser.parse(ifile)
            ifile.close()
            return None
        except xml.parsers.expat.ExpatError, msg:
            return str(msg)

    def save_xml(self, filename):
        """
        Saves the database to the specified XML file
        """
        writer = RegWriter(self)
        writer.save(filename)

    def __get_write_data(self):
        """
        Gets __write_data, which is accessed via the write_data_name property
        """
        return self.__write_data

    def __set_write_data(self, name):
        """
        Sets __write_data, which is accessed via the write_data_name property
        """
        self.__write_data = name.strip()

    write_data_name = property(__get_write_data, __set_write_data, None,
                               "Name of the write data signal")

    def __get_read_data(self):
        """
        Gets __read_data, which is accessed via the read_data_name property
        """
        return self.__read_data

    def __set_read_data(self, name):
        """
        Sets __read_data, which is accessed via the read_data_name property
        """
        self.__read_data = name.strip()

    read_data_name = property(__get_read_data, __set_read_data, None,
                              "Name of the read data signal")

    def __get_write_strobe(self):
        """
        Gets __write_strobe, which is accessed via the write_strobe_name
        property
        """
        return self.__write_strobe

    def __set_write_strobe(self, name):
        """
        Sets __write_strobe, which is accessed via the write_strobe_name
        property
        """
        self.__write_strobe = name.strip()

    write_strobe_name = property(__get_write_strobe, __set_write_strobe, None,
                                 "Name of the write strobe")

    def __get_ack(self):
        """
        Gets __ack, which is accessed via the acknowledge_name property
        """
        return self.__ack

    def __set_ack(self, name):
        """
        Sets __ack, which is accessed via the acknowledge_name property
        """
        self.__ack = name.strip()

    acknowledge_name = property(__get_ack, __set_ack, None,
                                "Name of the acknowledge")

    def __get_read_strobe(self):
        """
        Gets __read_strobe, which is accessed via the read_strobe_name
        property
        """
        return self.__read_strobe

    def __set_read_strobe(self, name):
        """
        Sets __read_strobe, which is accessed via the read_strobe_name
        property
        """
        self.__read_strobe = name.strip()

    read_strobe_name = property(__get_read_strobe, __set_read_strobe, None,
                                "Name of the read strobe")

    def __get_addr(self):
        """
        Gets __addr, which is accessed via the address_bus_name property
        """
        return self.__addr

    def __set_addr(self, name):
        """
        Sets __addr, which is accessed via the address_bus_name property
        """
        self.__addr = name.strip()

    address_bus_name = property(__get_addr, __set_addr, None,
                                "Name of the address bus")

    def __get_be(self):
        """
        Gets __be, which is accessed via the byte_strobe_named property
        """
        return self.__be

    def __set_be(self, name):
        """
        Sets __be, which is accessed via the byte_strobe_named property
        """
        self.__be = name.strip()

    byte_strobe_name = property(__get_be, __set_be, None,
                                "Name of the byte enables")

    def __set_module(self, name):
        """
        Sets __module, which is accessed via the module_name property
        """
        self.__module = name.replace(' ', '_')

    def __get_module(self):
        """
        Gets __module, which is accessed via the module_name property
        """
        return self.__module

    module_name = property(__get_module, __set_module, None,
                           "Name of the module")

    def __set_clock(self, name):
        """
        Sets __clock, which is accessed via the clock_name property
        """
        self.__clock = name.strip()

    def __get_clock(self):
        """
        Gets __clock, which is accessed via the clock_name property
        """
        return self.__clock

    clock_name = property(__get_clock, __set_clock, None,
                          "Signal name of the clock")

    def __set_reset(self, name):
        """
        Sets __reset, which is accessed via the reset_name property
        """
        self.__reset = name.strip()

    def __get_reset(self):
        """
        Gets __reset, which is accessed via the reset_name property
        """
        return self.__reset

    reset_name = property(__get_reset, __set_reset, None,
                          "Signal name of the reset")

    def __set_title(self, name):
        """
        Sets __title, which is accessed via the descriptive_title property
        """
        self.__title = name.strip()

    def __get_title(self):
        """
        Gets __title, which is accessed via the descriptive_title property
        """
        return self.__title

    descriptive_title = property(__get_title, __set_title, None,
                                 "Description of the module")

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
