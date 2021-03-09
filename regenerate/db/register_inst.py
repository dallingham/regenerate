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
Manages the instance of a register within a group.
"""

from .json_base import JSONEncodable


class RegisterInstance(JSONEncodable):
    """Instance information when contained in a group"""

    def __init__(
        self,
        rset: str = "",
        inst: str = "",
        offset: int = 0,
        repeat: int = 0,
        repeat_offset: int = 0,
        hdl: str = "",
        no_uvm: bool = False,
        no_decode: bool = False,
        array: bool = False,
        single_decode: bool = False,
    ) -> None:
        self.set = rset
        self.inst = inst
        self.offset = offset
        self.repeat = repeat
        self.repeat_offset = repeat_offset
        self.hdl = hdl
        self.no_uvm = no_uvm
        self.no_decode = no_decode
        self.array = array
        self.single_decode = single_decode

    def __eq__(self, other) -> bool:
        return (
            self.set == other.set
            and self.inst == other.inst
            and self.offset == other.offset
            and self.repeat == other.repeat
            and self.hdl == other.hdl
            and self.no_uvm == other.no_uvm
            and self.no_decode == other.no_decode
            and self.array == other.array
            and self.single_decode == other.single_decode
        )

    def json_decode(self, data) -> None:
        self.set = data["set"]
        self.inst = data["inst"]
        self.offset = data["offset"]
        self.repeat = data["repeat"]
        self.hdl = data["hdl"]
        self.no_uvm = data["no_uvm"]
        self.no_decode = data["no_decode"]
        self.array = data["array"]
        self.single_decode = data["single_decode"]
