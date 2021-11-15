from typing import List, Dict
from copy import deepcopy

from regenerate.db import RegisterDb, Register, ParameterFinder, ResetType
from regenerate.extras.regutils import (
    calculate_next_address,
    following_address,
)


def insert_registers(
    dest: RegisterDb,
    registers: List[Register],
    below_reg: Register,
    param_old_to_new,
):

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
        old_regs = [
            reg
            for reg in dest.get_all_registers()
            if reg.address > below_reg.address
        ]
    else:
        old_regs = []

    for reg in old_regs:
        if reg.address <= start_addr:
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


def copy_parameters(dest: RegisterDb, param_list) -> Dict[str, str]:
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
