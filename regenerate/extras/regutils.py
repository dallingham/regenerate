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

import copy
import re
from regenerate.ui.register_list import build_define

REGNAME = re.compile("^(.*)(\d+)(.*)$")


def duplicate_register(dbase, reg):
    """
    Returns a new register which is a dupilcate of the original register,
    changing the register description, signals, and token based on the original
    register.
    """
    reglist = set([dbase.get_register(key).register_name
                   for key in dbase.get_keys()])
    deflist = set([dbase.get_register(key).token for key in dbase.get_keys()])
    signals = build_signal_set(dbase)

    new_name = build_new_name(reg.register_name, reglist)

    def_name = build_new_name(reg.token, deflist)
    if not def_name:
        def_name = build_define(new_name)

    new_reg = copy.deepcopy(reg)
    # force the generation of a new UUID
    new_reg.uuid = ""

    for key in reg.get_bit_field_keys():
        fld = reg.get_bit_field(key)
        nfld = new_reg.get_bit_field(key)
        nfld.input_signal = signal_from_source(fld.input_signal, signals)
        nfld.output_signal = signal_from_source(fld.output_signal, signals)
        nfld.control_signal = signal_from_source(fld.control_signal, signals)

    new_reg.address = calculate_next_address(dbase)
    new_reg.register_name = new_name
    new_reg.token = def_name
    return new_reg


def build_signal_set(dbase):
    """
    Builds a set of all input, output and control signal name in
    the database.
    """
    signal_list = set()
    for reg in dbase.get_all_registers():
        for field in reg.get_bit_fields():
            if field.input_signal:
                signal_list.add(field.input_signal)
            if field.output_signal:
                signal_list.add(field.output_signal)
            if field.control_signal:
                signal_list.add(field.control_signal)
    return signal_list


def calculate_next_address(dbase, width):
    """
    Calculates the next address based on the last address that was
    used.
    """
    keys = dbase.get_keys()
    if keys:
        last_reg = dbase.get_register(keys[-1])
        dim = max(last_reg.dimension, 1)
        byte_width = last_reg.width >> 3
        addr = last_reg.address + (dim * byte_width)
        byte_width = width >> 3
        if addr % byte_width != 0:
            addr += (addr % byte_width)
    else:
        addr = 0
    return addr


def signal_from_source(source_name, existing_list):
    """
    Builds a copy of a signal name. The existing list contains the names
    that have already been used. The build_new_name is calleded to try to
    derive a name based on the passed, looking to replace numerical values
    embedded in the name. If none is found, then _COPY is appended.
    """
    if source_name:
        signal = build_new_name(source_name, existing_list)
        if signal:
            return signal
        else:
            return source_name + "_COPY"
    else:
        return ""


def build_new_name(name, reglist):
    match = REGNAME.match(name)
    if match:
        groups = match.groups()
        index = int(groups[1]) + 1
        while "".join([groups[0], str(index), groups[2]]) in reglist:
            index += 1
        return "".join([groups[0], str(index), groups[2]])
    else:
        index = 2
        while "%s %d" % (name, index) in reglist:
            index += 1
        return "%s %d" % (name, index)
