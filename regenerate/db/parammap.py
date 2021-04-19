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

from .name_base import NameBase
import uuid


class ParameterData(NameBase):
    """Register set parameter data"""

    def __init__(
        self,
        name: str = "",
        value: int = 1,
        min_val: int = 0,
        max_val: int = 0xFFFF_FFFF,
    ):
        super().__init__(name, "")
        self.value = value
        self.min_val = min_val
        self.max_val = max_val

    def __hash__(self):
        return hash(self._id)

    def json(self):
        return {
            "uuid": self._id,
            "name": self.name,
            "value": self.value,
            "min_val": self.min_val,
            "max_val": self.max_val,
        }

    def json_decode(self, data):
        self._id = data["uuid"]
        self.name = data["name"]
        self.value = data["value"]
        self.min_val = data["min_val"]
        self.max_val = data["max_val"]


# class PrjParameterData(JSONEncodable):
#     """Project parameter data"""

#     def __init__(self, name, value):
#         self.name = name
#         self.value = value
