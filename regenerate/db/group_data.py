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


class GroupData(object):
    """Basic group information."""

    def __init__(self,
                 name="",
                 base=0,
                 hdl="",
                 repeat=1,
                 repeat_offset=0x10000,
                 title=""):
        """Initialize the group data item."""
        self.name = name
        self.base = base
        self.hdl = hdl
        self.repeat = repeat
        self.repeat_offset = repeat_offset
        self.register_sets = []
        self.title = title
        self.docs = ""

    def __hash__(self):
        return id(self)

    def __ne__(self, other):
        """Compare for inequality."""
        return not self.__eq__(other)

    def __eq__(self, other):
        """Compare for equality."""
        if other is None:
            return False
        if self.name != other.name:
            return False
        if self.base != other.base:
            return False
        if self.hdl != other.hdl:
            return False
        if self.title != other.title:
            return False
        if self.repeat != other.repeat:
            return False
        if self.repeat_offset != other.repeat_offset:
            return False
        if self.docs != other.docs:
            return False
        if self.register_sets != other.register_sets:
            return False
        return True
