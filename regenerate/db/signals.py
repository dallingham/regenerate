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
from typing import Dict, Any
from regenerate.settings import rules

DEF_CLK_NAME = "CLK"
DEF_RST_NAME = "RSTn"
DEF_SEC_RESET_NAME = "SEC_RSTn"
DEF_WDATA_NAME = "WDATA"
DEF_RDATA_NAME = "RDATA"
DEF_WR_NAME = "WR"
DEF_RD_NAME = "RD"
DEF_ADDR_NAME = "ADDR"
DEF_BE_NAME = "BE"
DEF_ACK_NAME = "ACK"
DEF_INTERFACE = "mgmt_interface"
DEF_MODPORT = "target"
DEF_IMODPORT = "initiator"


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
        self.clock_name = DEF_CLK_NAME
        self.reset_name = DEF_RST_NAME
        self._interface = rules.get(
            "rules", "interface_default", DEF_INTERFACE
        )
        self._modport = rules.get("rules", "modport_default", DEF_MODPORT)
        self._imodport = rules.get(
            "rules", "initiator_modport_default", DEF_IMODPORT
        )
        self.write_data_name = DEF_WDATA_NAME
        self.read_data_name = DEF_RDATA_NAME
        self.write_strobe_name = DEF_WR_NAME
        self.read_strobe_name = DEF_RD_NAME
        self.address_bus_name = DEF_ADDR_NAME
        self.byte_strobe_name = DEF_BE_NAME
        self.acknowledge_name = DEF_ACK_NAME
        self.secondary_reset = False
        self.secondary_reset_name = DEF_SEC_RESET_NAME
        self.reset_active_level = 0
        self.byte_strobe_active_level = 1
        self.data_bus_width = 32
        self.address_bus_width = 12
        self.sync_reset = False

    def address_size_in_bytes(self) -> int:
        """Returns the address size in bytes"""
        return 1 << self.address_bus_width

    @property
    def interface_name(self) -> str:
        """
        Gets _interface, which is accessed via the interface_name property
        """
        return self._interface

    @interface_name.setter
    def interface_name(self, name: str) -> None:
        """
        Sets _interface, which is accessed via the interface_name property
        """
        self._interface = name.strip()

    @property
    def modport_name(self) -> str:
        """
        Gets _modport, which is accessed via the modport_name property
        """
        return self._modport

    @modport_name.setter
    def modport_name(self, name: str) -> None:
        """
        Sets _modport, which is accessed via the modport_name property
        """
        self._modport = name.strip()

    @property
    def imodport_name(self) -> str:
        """
        Gets _modport, which is accessed via the modport_name property
        """
        return self._imodport

    @imodport_name.setter
    def imodport_name(self, name: str) -> None:
        """
        Sets _modport, which is accessed via the modport_name property
        """
        self._imodport = name.strip()

    def json(self) -> Dict[str, Any]:
        """Converts the data into a dictionary used for JSON"""

        return {
            "interface": self._interface,
            "modport": self._modport,
            "imodport": self._imodport,
            "reset_level": self.reset_active_level,
            "data_bus_width": self.data_bus_width,
            "secondary_reset": self.secondary_reset,
            "sync_reset": self.sync_reset,
            "address_bus_width": self.address_bus_width,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        """Converts JSON data back into a Signal"""

        self._interface = data.get("inteface", DEF_INTERFACE)
        self._modport = data.get("modport", DEF_MODPORT)
        self._imodport = data.get("imodport", DEF_IMODPORT)
        self.reset_active_level = data["reset_level"]
        self.secondary_reset = data.get("secondary_reset", False)
        self.data_bus_width = data["data_bus_width"]
        self.address_bus_width = data["address_bus_width"]
        self.sync_reset = data.get("sync_reset", False)
