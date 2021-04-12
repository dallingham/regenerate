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
Provide the enumerated types for the user interface.
"""

from enum import IntEnum


class InstCol(IntEnum):
    """Instance columns numbers for the InstanceList"""

    ID = 0
    INST = 1
    BASE = 2
    SORT = 3
    RPT = 4
    HDL = 5
    OBJ = 6


class AddrCol(IntEnum):
    """Address columns for the AddressMaps"""

    NAME = 0
    BASE = 1
    FLAGS = 2
    WIDTH = 3
    OBJ = 4


class BitCol(IntEnum):
    """BitField columns for the BitField List"""

    ICON = 0
    BIT = 1
    NAME = 2
    TYPE = 3
    RESET = 4
    RESET_TYPE = 5
    SORT = 6
    FIELD = 7


class Level(IntEnum):
    """Report level, indicating what type of data is included in a report"""

    BLOCK = 0
    GROUP = 1
    PROJECT = 2


class BuildCol(IntEnum):
    """Column numbers for the Build list"""

    MODIFIED = 0
    BASE = 1
    FORMAT = 2
    DEST = 3
    CLASS = 4
    DBASE = 5
    TYPE = 6


class MapOpt(IntEnum):
    """Positions for Exporter information in the report exporter map"""

    ID = 0
    CLASS = 1
    REGISTER_SET = 2


class OptMap(IntEnum):
    """Option map"""

    DESCRIPTION = 0
    CLASS = 1
    REGISTER_SET = 2


class DbMap(IntEnum):
    """Database column map"""

    DBASE = 0
    MODIFIED = 1


class FilterField(IntEnum):
    """Filter field columns"""

    ADDR = 1
    NAME = 2
    TOKEN = 3


class SelectCol(IntEnum):

    ICON = 0
    NAME = 1


class RegCol(IntEnum):
    """Column numbers for the Register List"""

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
    """Register column type"""

    TEXT = 0
    COMBO = 1
    ICON = 2


class ParameterCol(IntEnum):
    """Column numbers for the Parameter List"""

    NAME = 0
    VALUE = 1
    MIN = 2
    MAX = 3


class PrjParameterCol(IntEnum):
    """Column numbers for the Parameter List"""

    BLK = 0
    REG = 1
    NAME = 2
    VALUE = 3


class ExportPages(IntEnum):
    """Page names for the export builder"""

    REPORT_SELECT = 0
    REGSET_SELECT = 1
    GROUP_SELECT = 2
    FILE_SELECT = 3
    SUMMARY = 4
