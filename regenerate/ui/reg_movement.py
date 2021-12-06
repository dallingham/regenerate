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
Utilities for copying and moving registers within a register set
"""

from typing import List, Dict, Set, Tuple
from copy import deepcopy

from regenerate.db import (
    RegisterDb,
    Register,
    ParameterFinder,
    ResetType,
    Uuid,
)
from regenerate.extras.regutils import (
    calculate_next_address,
    following_address,
)


def insert_registers_after(
    dest: RegisterDb,
    registers: List[Register],
    below_reg: Register,
    param_old_to_new,
):
    """
    Inserts the registers into the target register set after the specified
    register in the target register set, incrementing the addresses to
    compact the address space, and move down any registers that overlap
    with the target.
    """
    if below_reg:
        initial_addr = following_address(
            below_reg.address,
            below_reg.dimension,
            registers[0].width,
            dest.ports.data_bus_width,
        )
    else:
        initial_addr = calculate_next_address(dest, registers[0].width)

    start_addr = initial_addr

    for reg in registers:
        reg.address = start_addr
        start_addr = following_address(
            start_addr,
            reg.dimension,
            reg.width,
            dest.ports.data_bus_width,
        )
        replace_parameter_uuids(param_old_to_new, reg)

    if below_reg:
        for reg in dest.get_all_registers():
            if below_reg.address < reg.address <= start_addr:
                reg.address = start_addr
                start_addr = following_address(
                    start_addr,
                    reg.dimension,
                    reg.width,
                    dest.ports.data_bus_width,
                )
            else:
                break

    for reg in registers:
        dest.add_register(reg)


def insert_register_at(dest: RegisterDb, source_reg: Register) -> Register:
    """
    Insert a new register at the selected register's address.

    Alters the address of the selected register and any other register
    until there are no overlaps.

    Parameters:
       dest (RegisterDb): target register set
       source_reg (Register): register that marks where the new register
          should go

    Returns:
       Register: New register with the address the source reg originally
          had

    """

    start_addr = source_reg.address
    register = Register()
    register.address = source_reg.address
    register.width = source_reg.width

    for reg in dest.get_all_registers():
        if reg.address >= register.address and reg.address <= start_addr:
            start_addr = following_address(
                start_addr,
                reg.dimension,
                reg.width,
                dest.ports.data_bus_width,
            )
            reg.address = start_addr

    dest.add_register(register)
    return register


def copy_registers(
    dest_regset: RegisterDb, register_list: List[Register]
) -> Tuple[List[Register], Set[str]]:
    "Copies the register list to the destination register set"
    used_addrs = _build_used_addresses(dest_regset.get_all_registers())

    parameter_set = set()
    new_reglist: List[Register] = []
    for reg in register_list:
        new_reg = Register()
        new_reg.json_decode(reg.json())
        new_reg.uuid = Uuid("")
        for field in new_reg.get_bit_fields():
            field.uuid = Uuid("")

        reg_addrs = _get_addresses(new_reg)

        while reg_addrs.intersection(used_addrs):
            new_reg.address = new_reg.address + new_reg.width // 8
            reg_addrs = _get_addresses(new_reg)

        new_reglist.append(new_reg)
        used_addrs = used_addrs.union(reg_addrs)

        if reg.dimension.is_parameter:
            parameter_set.add(reg.dimension.txt_value)

    return new_reglist, parameter_set


def copy_parameters(dest: RegisterDb, param_list: Set[str]) -> Dict[str, str]:
    "Copies the parameters to the target register set"

    param_map: Dict[str, str] = {}

    finder = ParameterFinder()
    for param_uuid in param_list:
        if param_uuid not in param_map:
            param = finder.find(param_uuid)
            if param is not None:
                new_param = deepcopy(param)
                new_param.uuid = ""
                finder.register(new_param)
                param_map[param.uuid] = new_param.uuid
                dest.add_parameter(new_param)
    return param_map


def _get_addresses(reg: Register) -> Set[int]:
    "Returns the set of addresses that the register occupies"

    used_addrs: Set[int] = set()
    used_addrs.add(reg.address)

    if reg.width >= 16:
        used_addrs.add(reg.address + 1)
    if reg.width >= 32:
        used_addrs.add(reg.address + 2)
        used_addrs.add(reg.address + 3)
    if reg.width == 64:
        used_addrs.add(reg.address + 4)
        used_addrs.add(reg.address + 5)
        used_addrs.add(reg.address + 6)
        used_addrs.add(reg.address + 7)

    return used_addrs


def _build_used_addresses(register_list) -> Set[int]:
    "Builds the used address from the register list"

    used_addrs: Set[int] = set()
    for reg in register_list:
        used_addrs = used_addrs.union(_get_addresses(reg))
    return used_addrs


def replace_parameter_uuids(uuid_map: Dict[str, str], reg: Register) -> None:
    if reg.dimension.is_parameter:
        if reg.dimension.txt_value in uuid_map:
            reg.dimension.txt_value = uuid_map[reg.dimension.txt_value]
    for field in reg.get_bit_fields():
        if field.reset_type == ResetType.PARAMETER:
            if field.reset_parameter in uuid_map:
                field.reset_parameter = uuid_map[field.reset_parameter]
        if field.msb.is_parameter:
            if field.msb.txt_value in uuid_map:
                field.msb.txt_value = uuid_map[field.msb.txt_value]
