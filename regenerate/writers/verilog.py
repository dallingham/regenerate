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
Actual program. Parses the arguments, and initiates the main window
"""

import os
import re
import copy
from collections import namedtuple, defaultdict
from typing import List, Tuple, TextIO, Set, Dict

from jinja2 import FileSystemLoader, Environment
from regenerate.db import (
    TYPES,
    TYPE_TO_OUTPUT,
    Register,
    BitField,
    BitType,
    RegisterDb,
    RegProject,
)
from regenerate.writers.writer_base import WriterBase, ExportInfo
from regenerate.writers.verilog_reg_def import REG
from regenerate.db.enums import ShareType, ResetType

LOWER_BIT = {128: 4, 64: 3, 32: 2, 16: 1, 8: 0}


BIT_SLICE = re.compile(r"(.*)\[(\d+)\]")
BUS_SLICE = re.compile(r"(.*)\[(\d+):(\d+)\]")

CellInfo = namedtuple(
    "CellInfo",
    [
        "name",
        "has_input",
        "has_control",
        "has_oneshot",
        "type_descr",
        "allows_wide",
        "has_rd",
        "is_read_only",
    ],
)

ByteInfo = namedtuple(
    "ByteInfo",
    [
        "field",
        "start_offset",
        "stop_offset",
        "start",
        "stop",
        "address",
        "register",
    ],
)


def full_reset_value(field: BitField) -> str:
    """returns the full reset value for the entire field"""

    if field.reset_type == ResetType.NUMERIC:
        return "{0}'h{1:0x}".format(field.width, field.reset_value)
    if field.reset_type == ResetType.INPUT:
        return field.reset_input
    return field.reset_parameter


def reset_value(field: BitField, start: int, stop: int) -> str:
    """returns the full reset value for the field up to a byte"""

    if field.reset_type == ResetType.NUMERIC:
        field_width = (stop - start) + 1
        reset = int(field.reset_value >> int(start - field.lsb))
        return "{0}'h{1:x}".format(
            field_width, reset & int((2 ** field_width) - 1)
        )
    if field.reset_type == ResetType.INPUT:
        if stop == start:
            return field.reset_input
        return "{0}[{1}:{2}]".format(field.reset_input, stop, start)
    if stop == start:
        return field.reset_parameter
    return "{0}[{1}:{2}]".format(field.reset_parameter, stop, start)


def break_into_bytes(start: int, stop: int) -> List[Tuple[int, int]]:
    """
    Return a list of byte boundaries from the start and stop values
    """
    index = start
    data = []

    while index <= stop:
        next_boundary = (int(index // 8) + 1) * 8
        data.append((index, min(stop, next_boundary - 1)))
        index = next_boundary
    return data


def in_range(
    lower: int, upper: int, lower_limit: int, upper_limit: int
) -> bool:
    """
    Checks to see if the range is within the specified range
    """
    return (
        (lower_limit <= lower <= upper_limit)
        or (lower_limit <= upper <= upper_limit)
        or (lower < lower_limit and upper >= upper_limit)
    )


def rshift(val: int, shift: int) -> int:
    """"Right shift the value by the specified number of bits"""
    return int(val) >> int(shift)


class Verilog(WriterBase):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(self, project: RegProject, dbase: RegisterDb):
        super().__init__(project, dbase)

        self.input_logic = "input       "
        self.output_logic = "output      "
        self.always = "always"
        self.reg_type = "reg"

        self._cell_info = {}
        for i in TYPES:
            self._cell_info[i.type] = CellInfo(
                i.id.lower(),
                i.input,
                i.control,
                i.oneshot,
                i.description,
                i.wide,
                i.read,
                i.readonly,
            )

        self.__sorted_regs = [
            reg
            for reg in dbase.get_all_registers()
            if not (reg.flags.do_not_generate_code or reg.ram_size > 0)
        ]

        self._used_types: Set[BitType] = set()

    def _byte_info(
        self,
        field: BitField,
        register: Register,
        lower: int,
        size: int,
        offset: int,
    ) -> ByteInfo:
        """
        Returns the basic information from a field, broken out into byte
        quantities
        """
        start = max(field.lsb, lower)
        stop = min(field.msb, lower + size - 1)

        nbytes = int(size // 8)
        address = int(register.address // nbytes) * nbytes
        bit_offset = int((register.address * 8) % size)

        return ByteInfo(
            field,
            start + bit_offset,
            stop + bit_offset,
            start,
            stop,
            address + offset,
            register,
        )

    def __generate_group_list(self, reglist: List[Register], size: int):
        """
        Breaks a set of bit fields along the specified boundary
        """
        item_list: Dict[int, List[ByteInfo]] = {}

        for register in reglist:
            for field in register.get_bit_fields():
                self._used_types.add(field.field_type)
                offset = 0
                for lower in range(0, register.width, size):
                    if in_range(field.lsb, field.msb, lower, lower + size - 1):
                        data = self._byte_info(
                            field, register, lower, size, offset
                        )
                        item_list.setdefault(data.address, []).append(data)
                        offset += size // 8
        return item_list

    def write(self, filename: str):
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """

        assert self._dbase is not None

        dirpath = os.path.dirname(__file__)

        env = Environment(
            loader=FileSystemLoader(os.path.join(dirpath, "templates")),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.filters["drop_write_share"] = drop_write_share

        template = env.get_template("verilog.template")

        reglist = []
        for reg in [
            r
            for r in self._dbase.get_all_registers()
            if not r.flags.do_not_generate_code
        ]:
            if reg.dimension_is_param():
                new_reg = copy.copy(reg)
                reglist.append(new_reg)
            elif reg.dimension > 1:
                for i in range(0, reg.dimension):
                    new_reg = copy.copy(reg)
                    new_reg.address = reg.address + (i * int(reg.width // 8))
                    new_reg.dimension = i
                    reglist.append(new_reg)
            else:
                new_reg = copy.copy(reg)
                new_reg.dimension = -1
                reglist.append(new_reg)

        word_fields = self.__generate_group_list(reglist, self._data_width)

        if (
            self._dbase.ports.reset_active_level
            and not self._dbase.use_interface
        ):
            reset_edge = "posedge"
        else:
            reset_edge = "negedge"

        reset_op = (
            ""
            if (
                self._dbase.ports.reset_active_level
                and not self._dbase.use_interface
            )
            else "~"
        )

        parameters = []
        for para in self._dbase.get_parameters():
            parameters.append((31, 0, para[0], para[1]))

        input_signals = build_input_signals(self._dbase, self._cell_info)
        standard_ports = build_standard_ports(self._dbase)
        port_widths = build_port_widths(self._dbase)
        output_signals = build_output_signals(self._dbase, self._cell_info)
        reg_list = build_logic_list(self._dbase, word_fields, self._cell_info)
        oneshot_assigns = build_oneshot_assignments(
            word_fields, self._cell_info
        )
        assign_list = build_assignments(word_fields)

        write_address_selects = build_write_address_selects(
            self._dbase, word_fields
        )
        read_address_selects = build_read_address_selects(
            self._dbase, word_fields, self._cell_info
        )

        reg_read_output = register_output_definitions(self._dbase, word_fields)

        # TODO: fix 64 bit registers with 32 bit width

        with open(filename, "w") as ofile:
            ofile.write(
                template.render(
                    db=self._dbase,
                    ports=standard_ports,
                    reg_list=reg_list,
                    port_width=port_widths,
                    input_signals=input_signals,
                    output_signals=output_signals,
                    oneshot_assigns=oneshot_assigns,
                    write_address_selects=write_address_selects,
                    read_address_selects=read_address_selects,
                    reg_read_output=reg_read_output,
                    rshift=rshift,
                    reg_field_name=reg_field_name,
                    parameters=parameters,
                    cell_info=self._cell_info,
                    word_fields=word_fields,
                    assign_list=assign_list,
                    break_into_bytes=break_into_bytes,
                    full_reset_value=full_reset_value,
                    reset_value=reset_value,
                    input_logic=self.input_logic,
                    output_logic=self.output_logic,
                    always=self.always,
                    reset_edge=reset_edge,
                    reset_op=reset_op,
                    reg_type=self.reg_type,
                    low_bit=LOWER_BIT[self._dbase.ports.data_bus_width],
                )
            )
            self.write_register_modules(ofile)

    def comment(
        self, ofile: TextIO, text_list: List[str], border=None, precede_blank=0
    ):
        """
        Creates a comment from the list of text strings
        """
        max_column = 78
        border_string = border * (max_column - 2) if border else ""

        if text_list:
            if precede_blank:
                ofile.write("\n")
            ofile.write("/*{0}\n * ".format(border_string))
            ofile.write("\n * ".join(text_list))
            if border:
                text = "\n *{0}".format(border_string)
                ofile.write(text.rstrip())
            ofile.write("\n */\n")

    def write_register_modules(self, ofile):
        """Writes the used register module types to the file."""

        if (
            self._dbase.ports.reset_active_level
            and not self._dbase.use_interface
        ):
            edge = "posedge"
        else:
            edge = "negedge"

        if (
            self._dbase.ports.reset_active_level
            and not self._dbase.use_interface
        ):
            condition = ""
        else:
            condition = "~"

        if (
            self._dbase.ports.byte_strobe_active_level
            or self._dbase.use_interface
        ):
            be_level = ""
        else:
            be_level = "~"

        name_map = {
            "MODULE": self._module,
            "BE_LEVEL": be_level,
            "RESET_CONDITION": condition,
            "RESET_EDGE": edge,
        }

        for i in self._used_types:
            ofile.write("\n\n")
            try:
                self.comment(ofile, [self._cell_info[i][4]])
                ofile.write(REG[self._cell_info[i][0]] % name_map)
            except KeyError:
                self.comment(
                    ofile,
                    [
                        "No definition for %s_%s_reg\n"
                        % (self._module, self._cell_info[i][0])
                    ],
                )


class SystemVerilog(Verilog):
    """Provides the SystemVerilog version"""

    def __init__(self, project, dbase):
        super().__init__(project, dbase)
        self.input_logic = "input logic "
        self.output_logic = "output logic"
        self.always = "always_ff"
        self.reg_type = "logic"


class Verilog2001(Verilog):
    def __init(self, project, dbase):
        super().__init__(project, dbase)


def drop_write_share(list_in):
    list_out = [l for l in list_in if l[6].share != ShareType.WRITE]
    return list_out


def build_port_widths(dbase: RegisterDb):
    return {
        "byte_strobe": "[{}:0]".format(dbase.ports.data_bus_width // 8 - 1),
        "addr": "[{}:{}]".format(
            dbase.ports.address_bus_width - 1,
            LOWER_BIT[dbase.ports.data_bus_width],
        ),
        "write_data": "[{}:0]".format(dbase.ports.data_bus_width - 1),
    }


def reg_field_name(reg: Register, field: BitField):
    mode = ["_", "_r_", "_w"]
    return "r%02x%s%s" % (
        reg.address,
        mode[reg.share],
        field.name.lower(),
    )


def build_write_address_selects(
    dbase: RegisterDb, word_fields: Dict[int, List[ByteInfo]]
):

    assigns = []

    for addr in word_fields:
        rval = addr >> LOWER_BIT[dbase.ports.data_bus_width]

        assigns.append(
            (
                "write_r%02x" % addr,
                "%d'h%x"
                % (
                    dbase.ports.address_bus_width
                    - LOWER_BIT[dbase.ports.data_bus_width],
                    rval,
                ),
                word_fields[addr][0][-1],
            )
        )
    return assigns


def build_read_address_selects(dbase, word_fields, cell_info):
    assigns = []
    for addr in word_fields:
        val = word_fields[addr]

        for (field, *_) in val:
            if not cell_info[field.field_type].has_rd:
                continue
            lower_bit = LOWER_BIT[dbase.ports.data_bus_width]
            assigns.append(
                (
                    "read_r%02x" % addr,
                    "%d'h%x"
                    % (
                        dbase.ports.address_bus_width - lower_bit,
                        addr >> lower_bit,
                    ),
                    word_fields[addr][0][-1],
                )
            )
    return assigns


def build_output_signals(dbase, cell_info):

    scalar_ports = []
    array_ports = defaultdict(list)
    dim = {}
    signals = []

    for reg in dbase.get_all_registers():
        if reg.flags.do_not_generate_code:
            continue
        for field in reg.get_bit_fields():
            if cell_info[field.field_type].has_oneshot:
                signals.append(make_one_shot(field.output_signal, reg))

            if TYPE_TO_OUTPUT[field.field_type] and field.use_output_enable:
                sig = field.output_signal
                root = sig.split("[")
                wild = sig.split("*")
                if len(root) == 1:
                    if field.msb == field.lsb:
                        scalar_ports.append((sig, "", reg.dimension_str))
                    else:
                        dim[sig] = reg.dimension_str
                        for i in range(field.lsb, field.msb + 1):
                            array_ports[sig].append(i)
                elif len(wild) > 1:
                    dim[root[0]] = reg.dimension_str
                    for i in range(field.lsb, field.msb + 1):
                        array_ports[root[0]].append(i)
                else:
                    match = BUS_SLICE.match(sig)
                    if match:
                        grp = match.groups()
                        for i in range(int(grp[1]), int(grp[2])):
                            array_ports[grp[0]].append(i)
                        continue

                    match = BIT_SLICE.match(sig)
                    if match:
                        grp = match.groups()
                        dim[grp[0]] = reg.dimension_str
                        array_ports[grp[0]].append(int(grp[1]))
                        continue

    for key in array_ports:
        msb = max(array_ports[key])
        lsb = min(array_ports[key])
        if msb == lsb:
            scalar_ports.append((key, f"[{lsb}]", dim[key]))
        else:
            scalar_ports.append((key, f"[{msb}:{lsb}]", dim[key]))

    for (name, vect, dim) in scalar_ports:
        signals.append(make_scalar(name, vect, dim))

    return sorted(signals)


def make_scalar(name, vect, dim):
    """Converts the name, vect, and dim into a signal"""

    vect = vect + "         "
    if isinstance(dim, str) or dim > 1:
        try:
            val = int(dim)
            if val > 1:
                return (f"{name}[{dim}]", vect[0:8])
            return (name, vect[0:8])
        except ValueError:
            return (f"{name}[{dim}]", vect[0:8])
    else:
        return (name, vect[0:8])


def build_logic_list(_dbase, word_fields, cell_info):
    reg_list = []

    for addr in word_fields:
        val = word_fields[addr]
        for (field, _, _, start_pos, stop_pos, _, reg) in val:
            if field.msb == field.lsb:
                if reg.dimension_is_param():
                    reg_list.append(
                        (
                            reg_field_name(reg, field)
                            + "[%s]" % reg.dimension_str,
                            "        ",
                        )
                    )
                else:
                    reg_list.append((reg_field_name(reg, field), "        "))
            else:
                vect = f"[{stop_pos}:{start_pos}]      "
                if reg.dimension_is_param():
                    reg_list.append(
                        (
                            reg_field_name(reg, field)
                            + "[%s]" % reg.dimension_str,
                            vect[0:8],
                        )
                    )
                else:
                    reg_list.append((reg_field_name(reg, field), vect[0:8]))
            if cell_info[field.field_type].has_oneshot:
                for byte in break_into_bytes(start_pos, stop_pos):
                    if reg.dimension_is_param():
                        reg_list.append(
                            (
                                (
                                    "{}_{}_1S[{}]".format(
                                        reg_field_name(reg, field),
                                        byte[0],
                                        reg.dimension_str,
                                    )
                                ),
                                "        ",
                            )
                        )
                    else:
                        reg_list.append(
                            (
                                (
                                    "{}_{}_1S".format(
                                        reg_field_name(reg, field), byte[0]
                                    )
                                ),
                                "        ",
                            )
                        )
    return reg_list


def build_input_signals(dbase, cell_info):
    signals = set()
    for reg in dbase.get_all_registers():
        for field in reg.get_bit_fields():
            cinfo = cell_info[field.field_type]
            if cinfo.has_control:
                if reg.dimension_is_param():
                    name = "{}[{}]".format(
                        field.control_signal, reg.dimension_str
                    )
                    signals.add((name, "        "))
                elif reg.dimension > 1:
                    name = "{}[{}]".format(field.control_signal, reg.dimension)
                    signals.add((name, "        "))
                else:
                    signals.add((field.control_signal, "        "))
            if (
                cinfo.has_input
                and field.input_signal
                and field.input_signal not in signals
            ):
                if field.width == 1:
                    vector = "        "
                else:
                    vector = "[{}:{}]      ".format(field.msb, field.lsb)
                if reg.dimension_is_param():
                    signals.add(
                        (
                            "{}[{}]".format(
                                field.input_signal, reg.dimension_str
                            ),
                            vector[0:8],
                        )
                    )
                elif reg.dimension > 1:
                    signals.add(
                        (
                            "{}[{}]".format(field.input_signal, reg.dimension),
                            vector[0:8],
                        )
                    )
                else:
                    signals.add((field.input_signal, vector[0:8]))
    return sorted(signals)


def build_oneshot_assignments(word_fields, cell_info):

    assign_list = []

    for addr in word_fields:
        val = word_fields[addr]
        for (fld, _, _, _, _, _, reg) in val:
            if cell_info[fld.field_type][3]:

                if reg.dimension > 1:
                    name = f"{fld.output_signal}_1S[{reg.dimension}]"
                else:
                    name = f"{fld.output_signal}_1S"
                or_list = []
                for byte in break_into_bytes(fld.lsb, fld.msb):
                    or_list.append(
                        "r{:x}_{}_{}_1S".format(
                            reg.address, fld.name.lower(), byte[0]
                        )
                    )
                assign_list.append((name, " | ".join(or_list)))
    return assign_list


def build_assignments(word_fields):

    assign_list = []

    for addr in word_fields:
        val = word_fields[addr]
        for (fld, _, _, _, _, _, reg) in val:
            if reg.share == 0:
                mode = "_"
            elif reg.share == 1:
                mode = "_r_"
            else:
                mode = "_w_"
            if fld.use_output_enable and fld.output_signal != "":
                if reg.dimension_is_param():
                    assign_list.append(
                        (
                            fld.output_signal,
                            "r%02x%s%s"
                            % (reg.address, mode, fld.name.lower()),
                            reg.dimension_str,
                        )
                    )
                elif reg.dimension != -1:
                    assign_list.append(
                        (
                            f"{fld.output_signal}[{reg.dimension}]",
                            "r%02x%s%s"
                            % (reg.address, mode, fld.name.lower()),
                            "",
                        )
                    )
                else:
                    assign_list.append(
                        (
                            fld.resolved_output_signal(),
                            "r%02x%s%s"
                            % (reg.address, mode, fld.name.lower()),
                            "",
                        )
                    )
    return assign_list


def register_output_definitions(dbase, word_fields):

    full_list = []

    for addr in word_fields:
        val = word_fields[addr]

        last = dbase.ports.data_bus_width - 1
        reg = val[0][-1]
        if reg.dimension_is_param():
            wire_name = (
                "r%02x[%s]" % (addr, reg.dimension_str),
                "[%d:0]" % (dbase.ports.data_bus_width - 1,),
            )
        else:
            wire_name = (
                "r%02x" % addr,
                "[%d:0]" % (dbase.ports.data_bus_width - 1,),
            )
        clist = []

        val = reversed(val)
        last_offset = 63

        for (field, start_offset, _, start_pos, stop_pos, _, reg) in val:

            width = stop_pos - start_pos + 1
            if reg.share == 0:
                mode = "_"
            elif reg.share == 1:
                mode = "_r_"
            else:
                continue

            if start_offset + width <= last:
                clist.append("%d'b0" % (last - (start_offset + width) + 1,))
            if start_pos == stop_pos:
                clist.append(
                    "r%02x%s%s" % (reg.address, mode, field.name.lower())
                )
            else:
                clist.append(
                    "r%02x%s%s[%d:%d]"
                    % (
                        reg.address,
                        mode,
                        field.name.lower(),
                        stop_pos,
                        start_pos,
                    )
                )
            last = start_offset - 1
            last_offset = start_offset

        if last_offset != 0:
            clist.append("%d'b0" % last_offset)
        full_list.append((wire_name, clist))
    return full_list


def build_standard_ports(dbase):
    if dbase.use_interface:
        return {
            "clk": "MGMT.CLK",
            "reset": "MGMT.RSTn",
            "write_strobe": "MGMT.WR",
            "read_strobe": "MGMT.RD",
            "byte_strobe": "MGMT.BE",
            "write_data": "MGMT.WDATA",
            "read_data": "MGMT.RDATA",
            "ack": "MGMT.ACK",
            "addr": "MGMT.ADDR[%d:3]" % (dbase.ports.address_bus_width - 1,),
        }
    return {
        "clk": dbase.ports.clock_name,
        "reset": dbase.ports.reset_name,
        "write_strobe": dbase.ports.write_strobe_name,
        "read_strobe": dbase.ports.read_strobe_name,
        "byte_strobe": dbase.ports.byte_strobe_name,
        "write_data": dbase.ports.write_data_name,
        "read_data": dbase.ports.read_data_name,
        "ack": dbase.ports.acknowledge_name,
        "addr": dbase.ports.address_bus_name,
    }


def make_one_shot(name: str, reg: Register):
    """Builds the one shot signal from the name and dimenstion"""

    if reg.dimension_is_param():
        signal = (f"{name}_1S[{reg.dimension_str}]", "        ")
    elif reg.dimension > 1:
        signal = (f"{name}_1S[{reg.dimension}]", "        ")
    else:
        signal = (f"{name}_1S", "        ")
    return signal


EXPORTERS = [
    (
        WriterBase.TYPE_BLOCK,
        ExportInfo(
            SystemVerilog,
            ("RTL", "SystemVerilog"),
            "SystemVerilog files",
            ".sv",
            "rtl-system-verilog",
        ),
    ),
    (
        WriterBase.TYPE_BLOCK,
        ExportInfo(
            Verilog2001,
            ("RTL", "Verilog 2001"),
            "Verilog files",
            ".v",
            "rtl-verilog-2001",
        ),
    ),
    (
        WriterBase.TYPE_BLOCK,
        ExportInfo(
            Verilog,
            ("RTL", "Verilog 95"),
            "Verilog files",
            ".v",
            "rtl-verilog-95",
        ),
    ),
]
