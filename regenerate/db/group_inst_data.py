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


class GroupInstData(object):

    def __init__(self, rset, inst, offset, repeat, repeat_offset, hdl,
                 no_uvm, no_decode, array, single_decode):
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

    def __eq__(self, other):
        return (self.set == other.set and
                self.inst == other.inst and
                self.offset == other.offset and
                self.repeat == other.repeat and
                self.hdl == other.hdl and
                self.no_uvm == other.no_uvm and
                self.no_decode == other.no_decode and
                self.array == other.array and
                self.single_decode == other.single_decode)
