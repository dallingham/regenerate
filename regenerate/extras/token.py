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

from typing import List
from collections import namedtuple
from regenerate.db import RegProject


InstData = namedtuple(
    "InstData",
    "inst set base offset repeat roffset format grpt grpt_offset array",
)

DEFAULT_FORMAT = "%(G)s_%(S)s%(D)s_%(R)s"


def full_token(
    group_name: str, reg_name: str, set_name: str, index: int, fmt_string: str
) -> str:

    index_str = f"{index}" if index >= 0 else ""

    name_data = {
        "G": group_name.upper(),
        "g": group_name.lower(),
        "D": index_str,
        "R": reg_name.upper(),
        "r": reg_name.lower(),
        "S": set_name.upper(),
        "s": set_name.lower(),
    }

    return fmt_string % name_data


def uvm_name(group_name: str, reg_name: str, set_name: str, index: int) -> str:

    if index >= 0:
        return "<top>.%s.%s[%d].%s" % (
            group_name.lower(),
            set_name.lower(),
            index,
            reg_name.lower(),
        )
    return "<top>.%s.%s.%s" % (
        group_name.lower(),
        set_name.lower(),
        reg_name.lower(),
    )


def in_groups(name: str, project: RegProject) -> List[InstData]:
    groups = []
    if name and project:
        for blkinst in project.block_insts:
            block = project.blocks[blkinst.blkid]

            for regset in [rs for rs in block.regset_insts if rs.name == name]:
                fmt = DEFAULT_FORMAT
                groups.append(
                    InstData(
                        blkinst,
                        regset.name,
                        blkinst.address_base,
                        regset.offset,
                        regset.repeat,
                        regset.repeat_offset,
                        fmt,
                        blkinst.repeat,
                        block.address_size,
                        regset.array,
                    )
                )

    return groups
