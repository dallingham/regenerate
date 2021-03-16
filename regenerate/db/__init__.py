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
from .bitfield_types import *
from .group_data import GroupData
from .block import Block
from .register import Register
from .reg_parser import RegParser
from .reg_project import RegProject
from .const import OLD_PRJ_EXT, PRJ_EXT, REG_EXT, BLK_EXT
from .register_inst import RegisterInst
from .reg_writer import RegWriter
from .reg_writer_json import RegWriterJSON
from .register_db import RegisterDb
from .proj_reader import ProjectReader
from .proj_writer import ProjectWriter
from .addrmap import AddrMapData
from .parammap import ParameterData, PrjParameterData
from .enums import *
from .logger import *
