from .token import in_groups

def _reg_addr(register, offset):
    return register.address + offset

def find_addresses(project, regset_name, register, offset_only=True):

    address_list = []
    found_groups = in_groups(regset_name, project)

    x_addr_maps = project.get_address_maps()
    addr_maps = set([])

    for inst in found_groups:
        for x_map in x_addr_maps:
            groups_in_addr_map = project.get_address_map_groups(x_map.name)
            if inst.group in groups_in_addr_map:
                addr_maps.add(x_map)

    for inst in found_groups:

        for grp_inst in range(0, inst.grpt):
            if inst.repeat == 1 and not inst.array:
                if offset_only:
                    offset = inst.offset + inst.base + (
                        grp_inst * inst.grpt_offset)
                    address_list.append(_reg_addr(register, offset))
                else:
                    for map_name in addr_maps:
                        map_base = project.get_address_base(map_name.name)
                        offset = map_base + inst.offset + inst.base + (
                            grp_inst * inst.grpt_offset)
                        address_list.append(_reg_addr(register, offset))
            else:
                for i in range(0, inst.repeat):
                    if offset_only:
                        offset = inst.base + inst.offset + (
                            i * inst.roffset
                            ) + (grp_inst * inst.grpt_offset)
                        address_list.append(_reg_addr(register, offset))
                    else:
                        for map_name in addr_maps:
                            base = project.get_address_base(map_name.name)
                            offset = inst.base + inst.offset + (
                                i * inst.roffset
                                ) + (grp_inst * inst.grpt_offset)
                            address_list.append(_reg_addr(register, offset + base))
    return address_list
