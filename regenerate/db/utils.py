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
Common utility functions
"""

from typing import Dict, Any
from pathlib import Path
import json
from operator import methodcaller

from .logger import LOGGER


def save_json(data: Dict[str, Any], path: Path):
    "Saves the data to the specifed file in JSON format"
    try:
        with path.open("w") as ofile:
            ofile.write(
                json.dumps(data, default=methodcaller("json"))
            )
    except FileNotFoundError as msg:
        LOGGER.error(str(msg))


def get_register_paths(project):
    name2path = {}
    
    for blk_inst in project.get_block_instances():
        block = project.get_block_from_block_inst(blk_inst)
        for reg_inst in block.get_regset_insts():
            regset = block.get_regset_from_reg_inst(reg_inst)
            for reg in regset.get_all_registers():
                name2path[reg.name] = (blk_inst.name, reg_inst.name, reg.token.lower())
    return name2path
