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
Register utilities
"""

import copy
import re
from typing import Set, List

from regenerate.db import Register, RegisterDb
from .remap import REMAP_NAME

REGNAME = re.compile(r"^(.*)(\d+)(.*)$")


def _make_transtable():
    import string

    return "".maketrans(
        string.ascii_lowercase + " ",
        string.ascii_uppercase + "_",
        r"/-@!#$%^&*()+=|{}[]:\"';\\,.?",
    )


_TRANSTABLE = _make_transtable()


def build_define(text: str) -> str:
    """
    Converts a register name into a define token
    """
    text = text.translate(_TRANSTABLE)
    if text in REMAP_NAME:
        text = f"{text}_REG"
    return text


def duplicate_register(dbase: RegisterDb, reg: Register) -> Register:
    """
    Returns a new register which is a dupilcate of the original register,
    changing the register description, signals, and token based on the original
    register.
    """
    reglist = {reg.name for reg in dbase.get_all_registers()}
    deflist = {reg.token for reg in dbase.get_all_registers()}

    signals = build_signal_set(dbase)
    new_name = build_new_name(reg.name, reglist)
    def_name = build_new_name(reg.token, deflist)
    if not def_name:
        def_name = build_define(new_name)

    new_reg = copy.deepcopy(reg)
    # force the generation of a new UUID
    new_reg.uuid = ""

    for key in reg.get_bit_field_keys():
        fld = reg.get_bit_field(key)
        nfld = new_reg.get_bit_field(key)
        if fld and nfld:
            nfld.input_signal = signal_from_source(fld.input_signal, signals)
            nfld.output_signal = signal_from_source(fld.output_signal, signals)
            nfld.control_signal = signal_from_source(
                fld.control_signal, signals
            )

    new_reg.address = calculate_next_address(dbase, reg.width)
    new_reg.name = new_name
    new_reg.token = def_name
    return new_reg


def build_signal_set(dbase: RegisterDb) -> Set[str]:
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


def calculate_next_address(dbase: RegisterDb, width: int) -> int:
    """
    Calculates the next address based on the last address that was
    used.
    """
    keys = dbase.get_keys()
    if keys:
        last_reg = dbase.get_register(keys[-1])
        if last_reg:
            dim = max(last_reg.dimension, 1)
            byte_width = last_reg.width >> 3
            addr = last_reg.address + (dim * byte_width)
            byte_width = width >> 3
            if addr % byte_width != 0:
                addr += addr % byte_width
            return addr
    return 0


def signal_from_source(source_name: str, existing_list: Set[str]) -> str:
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
        return source_name + "_COPY"
    return ""


def build_new_name(name: str, reglist: Set[str]) -> str:
    """Build a new name from a existing name, making sure it is
    similar, but unique"""

    match = REGNAME.match(name)
    if match:
        groups = match.groups()
        index = int(groups[1]) + 1
        while "".join([groups[0], str(index), groups[2]]) in reglist:
            index += 1
        return "".join([groups[0], str(index), groups[2]])
    index = 2
    while f"{name} {index}" in reglist:
        index += 1
    return f"{name} {index}"
