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
Includes the base instances in the module
"""

from .bitfield import BitField
from .bit_values import BitValues
from .bitfield_types import *
from .block import Block
from .block_inst import BlockInst
from .register import Register
from .reg_parser import RegParser
from .reg_project import RegProject
from .const import OLD_PRJ_EXT, PRJ_EXT, REG_EXT, BLK_EXT, OLD_REG_EXT
from .register_inst import RegisterInst
from .name_base import NameBase, Uuid
from .register_set import RegisterSet
from .param_resolver import ParameterResolver
from .proj_reader import ProjectReader
from .address_map import AddressMap
from .param_data import ParameterData, ParameterFinder
from .param_value import ParamValue
from .overrides import Overrides
from .enums import *
from .logger import *
from .export import ExportData
