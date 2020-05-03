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


from enum import IntEnum


class InstCol(IntEnum):
    INST = 0
    ID = 1
    BASE = 2
    SORT = 3
    RPT = 4
    OFF = 5
    HDL = 6
    OBJ = 7


class AddrCol(IntEnum):
    NAME = 0
    BASE = 1
    FIXED = 2
    UVM = 3
    WIDTH = 4
    OBJ = 5


class BitCol(IntEnum):
    ICON = 0
    BIT = 1
    NAME = 2
    TYPE = 3
    RESET = 4
    RESET_TYPE = 5
    SORT = 6
    FIELD = 7


class Level(IntEnum):
    BLOCK = 0
    GROUP = 1
    PROJECT = 2


class BuildCol(IntEnum):
    MODIFIED = 0
    BASE = 1
    FORMAT = 2
    DEST = 3
    CLASS = 4
    DBASE = 5
    TYPE = 6


class MapOpt(IntEnum):
    ID = 0
    CLASS = 1
    REGISTER_SET = 2


class OptMap(IntEnum):
    DESCRIPTION = 0
    CLASS = 1
    REGISTER_SET = 2


class DbMap(IntEnum):
    DBASE = 0
    MODIFIED = 1


class FilterField(IntEnum):
    ADDR = 1
    NAME = 2
    TOKEN = 3


class PrjCol(IntEnum):
    NAME = 0
    ICON = 1
    FILE = 2
    MODIFIED = 3
    OOD = 4
    OBJ = 5


class RegCol(IntEnum):
    ICON = 0
    ADDR = 1
    NAME = 2
    DEFINE = 3
    DIM = 4
    WIDTH = 5
    SORT = 6
    TOOLTIP = 7
    OBJ = 8


class RegColType(IntEnum):
    TEXT = 0
    COMBO = 1
    ICON = 2
