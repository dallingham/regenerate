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
Provides the signals for a module
"""

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


class Signals:
    """
    Provides the signals for a module. This include:

    Clock
    Reset
    Write Data
    Write Strobe
    Read Data
    Read Strobe
    Byte Enbles
    Acknowledge
    Address
    """

    def __init__(self):
        self._clock = rules.get("rules", "clock_default", DEF_CLK_NAME)
        self._reset = rules.get("rules", "reset_default", DEF_RST_NAME)
        self._write_data = rules.get(
            "rules", "write_data_default", DEF_WDATA_NAME
        )
        self._read_data = rules.get(
            "rules", "read_data_default", DEF_RDATA_NAME
        )
        self._write_strobe = rules.get(
            "rules", "write_strobe_default", DEF_WR_NAME
        )
        self._read_strobe = rules.get(
            "rules", "read_strobe_default", DEF_RD_NAME
        )
        self._addr = rules.get("rules", "address_default", DEF_ADDR_NAME)
        self._be = rules.get("rules", "byte_strobe_default", DEF_BE_NAME)
        self._ack = rules.get("rule", "ack_default", DEF_ACK_NAME)

        self.reset_active_level = 0
        self.byte_strobe_active_level = 1
        self.data_bus_width = 32
        self.address_bus_width = 12

    def address_size_in_bytes(self):
        """Returns the address size in bytes"""
        return 1 << self.address_bus_width

    @property
    def write_data_name(self):
        """
        Gets _write_data, which is accessed via the write_data_name property
        """
        return self._write_data

    @write_data_name.setter
    def write_data_name(self, name):
        """
        Sets _write_data, which is accessed via the write_data_name property
        """
        self._write_data = name.strip()

    @property
    def read_data_name(self):
        """
        Gets _read_data, which is accessed via the read_data_name property
        """
        return self._read_data

    @read_data_name.setter
    def read_data_name(self, name):
        """
        Sets _read_data, which is accessed via the read_data_name property
        """
        self._read_data = name.strip()

    @property
    def write_strobe_name(self):
        """
        Gets _write_strobe, which is accessed via the write_strobe_name
        property
        """
        return self._write_strobe

    @write_strobe_name.setter
    def write_strobe_name(self, name):
        """
        Sets _write_strobe, which is accessed via the write_strobe_name
        property
        """
        self._write_strobe = name.strip()

    @property
    def acknowledge_name(self):
        """
        Gets _ack, which is accessed via the acknowledge_name property
        """
        return self._ack

    @acknowledge_name.setter
    def acknowledge_name(self, name):
        """
        Sets _ack, which is accessed via the acknowledge_name property
        """
        self._ack = name.strip()

    @property
    def read_strobe_name(self):
        """
        Gets _read_strobe, which is accessed via the read_strobe_name
        property
        """
        return self._read_strobe

    @read_strobe_name.setter
    def read_strobe_name(self, name):
        """
        Sets _read_strobe, which is accessed via the read_strobe_name
        property
        """
        self._read_strobe = name.strip()

    @property
    def address_bus_name(self):
        """
        Gets _addr, which is accessed via the address_bus_name property
        """
        return self._addr

    @address_bus_name.setter
    def address_bus_name(self, name):
        """
        Sets _addr, which is accessed via the address_bus_name property
        """
        self._addr = name.strip()

    @property
    def byte_strobe_name(self):
        """
        Gets _be, which is accessed via the byte_strobe_name property
        """
        return self._be

    @byte_strobe_name.setter
    def byte_strobe_name(self, name):
        """
        Sets _be, which is accessed via the byte_strobe_named property
        """
        self._be = name.strip()

    @property
    def clock_name(self):
        """
        Gets _clock, which is accessed via the clock_name property
        """
        return self._clock

    @clock_name.setter
    def clock_name(self, name):
        """
        Sets _clock, which is accessed via the clock_name property
        """
        self._clock = name.strip()

    @property
    def reset_name(self):
        """
        Gets _reset, which is accessed via the reset_name property
        """
        return self._reset

    @reset_name.setter
    def reset_name(self, name):
        """
        Sets _reset, which is accessed via the reset_name property
        """
        self._reset = name.strip()

    def json(self):
        """Converts the data into a dictionary used for JSON"""

        return {
            "clock": self._clock,
            "reset": self._reset,
            "write_data": self._write_data,
            "read_data": self._read_data,
            "write_strobe": self._write_strobe,
            "read_strobe": self._read_strobe,
            "address": self._addr,
            "byte_en": self._be,
            "ack": self._ack,
            "reset_level": self.reset_active_level,
            "be_level": self.byte_strobe_active_level,
            "data_bus_width": self.data_bus_width,
            "address_bus_width": self.address_bus_width,
        }

    def json_decode(self, data):
        """Converts JSON data back into a Signal"""

        self._clock = data["clock"]
        self._reset = data["reset"]
        self._write_data = data["write_data"]
        self._read_data = data["read_data"]
        self._write_strobe = data["write_strobe"]
        self._read_strobe = data["read_strobe"]
        self._addr = data["address"]
        self._be = data["byte_en"]
        self._ack = data["ack"]
        self.reset_active_level = data["reset_level"]
        self.byte_strobe_active_level = data["be_level"]
        self.data_bus_width = data["data_bus_width"]
        self.address_bus_width = data["address_bus_width"]
