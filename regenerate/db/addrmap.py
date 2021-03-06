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
Contains the data in the address map
"""

from .json_base import JSONEncodable


class AddrMapData(JSONEncodable):
    """Address map data"""

    def __init__(
        self,
        name: str = "",
        base: int = 0,
        width: int = 0,
        fixed: int = 0,
        uvm: int = 0,
    ):
        self.name: str = name
        self.base: int = base
        self.width: int = width
        self.fixed: int = fixed
        self.uvm: int = uvm

    def json_decode(self, data):
        self.name = data["name"]
        self.base = data["base"]
        self.width = data["width"]
        self.fixed = data["fixed"]
        self.uvm = data["uvm"]
