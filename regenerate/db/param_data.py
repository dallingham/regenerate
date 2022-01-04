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
Contains the information for register set parameters and project parameters.

ParameterData consists of default, min, and max values.

"""

from typing import Dict, Any
from .name_base import NameBase, Uuid
from .param_finder import ParameterFinder


class ParameterData(NameBase):
    """
    Parameter data.

    Parameters consist of min, max, and default values.

    """

    def __init__(
        self,
        name: str = "",
        value: int = 1,
        min_val: int = 0,
        max_val: int = 0xFFFF_FFFF,
    ):
        """
        Initialize the object.

        Parameters:
            name (str): Parameter name
            value (int): default value
            min_val (int): minimum value the parameter can hold
            max_val (int): maximum value the parameter can hold

        """
        super().__init__(name, Uuid(""))
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.finder = ParameterFinder()
        self.finder.register(self)

    def __repr__(self) -> str:
        """
        Return the string representation of the object.

        Returns:
            str: string describing the object

        """
        return f'ParameterData(name="{self.name}", uuid="{self.uuid}", value={self.value})'

    def json(self) -> Dict[str, Any]:
        """
        Encode the object to a JSON dictionary.

        Returns:
            Dict[str, Any]: JSON-ish dictionary

        """
        return {
            "uuid": self.uuid,
            "name": self.name,
            "value": self.value,
            "min_val": self.min_val,
            "max_val": self.max_val,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Decode the JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data to decode

        """
        self.finder.unregister(self)
        self.uuid = Uuid(data["uuid"])
        self.name = data["name"]
        self.value = data["value"]
        self.min_val = data["min_val"]
        self.max_val = data["max_val"]
        self.finder.register(self)
