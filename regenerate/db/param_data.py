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
Contains the information for register set parameters and
project parameters.
"""

from typing import Dict, Any, Optional
from .name_base import NameBase, Uuid


class ParameterFinder:
    """
    Finds a parameter in the project based on its UUID.
    """

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(ParameterFinder, cls).__new__(cls)
        return cls.instance

    data_map: Dict[Uuid, "ParameterData"] = {}

    def find(self, uuid: Uuid) -> Optional["ParameterData"]:
        "Look up the UUID in the data map, returning None if not found"
        return self.data_map.get(uuid)

    def register(self, parameter: "ParameterData") -> None:
        "Registers the parameter with the system"
        self.data_map[parameter.uuid] = parameter

    def unregister(self, parameter: "ParameterData") -> None:
        "Removes the parameter with the system"
        if parameter.uuid in self.data_map:
            del self.data_map[parameter.uuid]

    def dump(self) -> None:
        "Dumps the data map to stdout"
        print(self.data_map)


class ParameterData(NameBase):
    """Register set parameter data"""

    def __init__(
        self,
        name: str = "",
        value: int = 1,
        min_val: int = 0,
        max_val: int = 0xFFFF_FFFF,
    ):
        super().__init__(name, Uuid(""))
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.finder = ParameterFinder()
        self.finder.register(self)

    def __repr__(self) -> str:
        return f'ParameterData(name="{self.name}", uuid="{self.uuid}", value={self.value})'

    def json(self) -> Dict[str, Any]:
        "Converts the object to a dict for JSON serialization"

        return {
            "uuid": self.uuid,
            "name": self.name,
            "value": self.value,
            "min_val": self.min_val,
            "max_val": self.max_val,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        "Converts a JSON dict into the object"

        self.finder.unregister(self)
        self.uuid = Uuid(data["uuid"])
        self.name = data["name"]
        self.value = data["value"]
        self.min_val = data["min_val"]
        self.max_val = data["max_val"]
        self.finder.register(self)
