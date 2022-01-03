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
Provides the signals for a module.

Provides the default names for the signals.
"""
from typing import Dict, Any

_DEF_CLK_NAME = "CLK"
_DEF_RST_NAME_P = "RST"
_DEF_RST_NAME = "RSTn"
_DEF_SEC_RESET_NAME = "SEC_RSTn"
_DEF_WDATA_NAME = "WDATA"
_DEF_RDATA_NAME = "RDATA"
_DEF_WR_NAME = "WR"
_DEF_RD_NAME = "RD"
_DEF_ADDR_NAME = "ADDR"
_DEF_BE_NAME = "BE"
_DEF_ACK_NAME = "ACK"
_DEF_INTERFACE = "mgmt_interface"
_DEF_MODPORT = "target"
_DEF_IMODPORT = "initiator"


class Signals:
    """
    Provides the signal information for a register set.

    This includes signal names, bus widths, and reset information.

    """

    def __init__(self):
        """
        Initialize the object.

        Sets the signals names to their default values.

        """
        self.clock_name = _DEF_CLK_NAME
        self._interface = _DEF_INTERFACE
        self._modport = _DEF_MODPORT
        self._imodport = _DEF_IMODPORT
        self.write_data_name = _DEF_WDATA_NAME
        self.read_data_name = _DEF_RDATA_NAME
        self.write_strobe_name = _DEF_WR_NAME
        self.read_strobe_name = _DEF_RD_NAME
        self.address_bus_name = _DEF_ADDR_NAME
        self.byte_strobe_name = _DEF_BE_NAME
        self.acknowledge_name = _DEF_ACK_NAME
        self.secondary_reset = False
        self.secondary_reset_name = _DEF_SEC_RESET_NAME
        self.reset_active_level = 0
        self.data_bus_width = 32
        self.address_bus_width = 12
        self.sync_reset = False

    def address_size_in_bytes(self) -> int:
        """
        Return the address size in byte.

        Returns:
            int: address size in bytes

        """
        return 1 << self.address_bus_width

    @property
    def reset_name(self) -> str:
        """
        Return the reset signal name based on signal polarity.

        Returns:
            str: reset signal name

        """
        if self.reset_active_level:
            return _DEF_RST_NAME_P
        return _DEF_RST_NAME

    @property
    def interface_name(self) -> str:
        """
        Return the name of the SystemVerilog interface.

        Returns:
            str: interface name

        """
        return self._interface

    @interface_name.setter
    def interface_name(self, name: str) -> None:
        """
        Set the name of the SystemVerilog interface.

        Parameters:
            name (str): interface name

        """
        self._interface = name.strip()

    @property
    def modport_name(self) -> str:
        """
        Return the name of the target SystemVerilog modport.

        Returns:
            str: name of the modport

        """
        return self._modport

    @modport_name.setter
    def modport_name(self, name: str) -> None:
        """
        Set SystemVerilog target modport name.

        Parameters:
            name (str): name of the modport

        """
        self._modport = name.strip()

    @property
    def imodport_name(self) -> str:
        """
        Return the name of the initiator SystemVerilog modport.

        Returns:
            str: name of the modport

        """
        return self._imodport

    @imodport_name.setter
    def imodport_name(self, name: str) -> None:
        """
        Set SystemVerilog initiator modport name.

        Parameters:
            name (str): name of the modport

        """
        self._imodport = name.strip()

    def json(self) -> Dict[str, Any]:
        """
        Convert the object to a JSON compatible dictionary.

        Returns:
            Dict[str, Any]: dictionary in JSON format

        """
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
        """
        Load the object from JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data describing the object

        """
        self._interface = data.get("interface", _DEF_INTERFACE)
        self._modport = data.get("modport", _DEF_MODPORT)
        self._imodport = data.get("imodport", _DEF_IMODPORT)
        self.reset_active_level = data["reset_level"]
        self.secondary_reset = data.get("secondary_reset", False)
        self.data_bus_width = data["data_bus_width"]
        self.address_bus_width = data["address_bus_width"]
        self.sync_reset = data.get("sync_reset", False)
