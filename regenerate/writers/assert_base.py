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


class AssertBase(object):

    def __init__(self, dbase):
        self.dbase = dbase
        self.clock = dbase.clock_name
        self.reset = dbase.reset_name
        self.polarity = dbase.reset_active_level
        self.data_in = dbase.WriteDataIn
        self.byte_enables = dbase.byte_strobe_name

    def write_assertions(self, ofile):
        raise NotImplementedError
