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

from collections import namedtuple

InstData = namedtuple("InstData",
                      "group inst set base offset repeat roffset format")

DEFAULT_FORMAT = "%(I)s%(D)s_%(R)s"


def full_token(group_name, inst_name, reg_name, set_name, index, fmt_string):

    index_str = "%d" % index if index >= 0 else ""

    name_data = {"G": group_name.upper(),
                 "g": group_name.lower(),
                 "D": index_str,
                 "R": reg_name.upper(),
                 "r": reg_name.lower(),
                 "I": inst_name.upper(),
                 "i": inst_name.lower(),
                 "S": set_name.upper(),
                 "s": set_name.lower()
                 }

    return fmt_string % name_data


def uvm_name(group_name, reg_name, set_name, index, fmt_string):

    if index >= 0:
        return "<top>.%s.%s[%d].%s" % (group_name.lower(), set_name.lower(),
                                       index, reg_name.lower())
    else:
        return "<top>.%s.%s.%s" % (group_name.lower(), set_name.lower(),
                                   reg_name.lower())


def in_groups(regset_name, project):
    groups = []
    if regset_name and project:
        for group_data in project.get_grouping_list():
            for regset in project.get_group_map(group_data.name):
                if regset.set == regset_name:
                    if regset.format:
                        fmt = regset.format
                    else:
                        fmt = DEFAULT_FORMAT
                    groups.append(InstData(group_data.name,
                                           regset.inst,
                                           regset.set,
                                           group_data.base,
                                           regset.offset,
                                           regset.repeat,
                                           regset.repeat_offset,
                                           fmt))
    return groups
