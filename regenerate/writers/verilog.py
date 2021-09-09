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
Provides the Verilog RTL generation
"""

import os
import re
import copy
import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, TextIO, Set, Dict, NamedTuple

from jinja2 import FileSystemLoader, Environment
from regenerate.db import (
    TYPES,
    TYPE_TO_OUTPUT,
    Register,
    BitField,
    ParamValue,
    BitType,
    RegisterDb,
    RegProject,
    ParameterFinder,
)
from regenerate.writers.writer_base import WriterBase, ExportInfo, ProjectType
from regenerate.writers.verilog_reg_def import REG
from regenerate.db.enums import ShareType, ResetType

LOWER_BIT = {128: 4, 64: 3, 32: 2, 16: 1, 8: 0}
MODE_SEP = ["_", "_r_", "_w"]


BIT_SLICE = re.compile(r"(.*)\[(\d+)\]")
BUS_SLICE = re.compile(r"(.*)\[(\d+):(\d+)\]")


class LogicDef:
    "Holds the name and dimension for a definition"

    def __init__(self, name: str, dim: str):
        self.name = name
        self.dim = dim
        self.field_list: List[FieldInfo] = []


class LogicDefResolved:
    "Holds the name and dimension for a definition"

    def __init__(self, name: str, dim: str):
        self.name = name
        self.dim = dim
        self.field_list: List[str] = []


class CellInfo(NamedTuple):
    "Contains the definition of a particular register type"

    name: str
    has_input: bool
    has_control: bool
    has_oneshot: bool
    type_descr: str
    allows_wide: bool
    has_rd: bool
    is_read_only: bool


class ByteInfo(NamedTuple):
    "Contains the information for a byte of a bitfield"

    field: BitField
    start_offset: int
    stop_offset: int
    start: int
    stop: int
    address: int
    register: Register


class AssignInfo(NamedTuple):

    output: str
    register: str
    dimension: str


class FieldInfo(NamedTuple):

    name: str
    lsb: int
    msb: ParamValue
    offset: int


class DecodeInfo(NamedTuple):

    name: str
    addr: str
    register: Register


def full_reset_value(field: BitField) -> str:
    """returns the full reset value for the entire field"""

    if field.reset_type == ResetType.NUMERIC:
        return f"{field.width}'h{field.reset_value:0x}"
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
        return f"{field.reset_input}[{stop}:{start}]"
    if stop == start:
        return field.reset_parameter
    return f"{field.reset_parameter}[{stop}:{start}]"


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

        self.input_logic = "input"
        self.output_logic = "output"
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

    def byte_info(
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
        stop = min(field.msb.resolve(), lower + size - 1)

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

    def generate_group_list(
        self, reglist: List[Register], size: int
    ) -> Dict[int, List[ByteInfo]]:
        "Breaks a set of bit fields along the specified boundary"

        item_list: Dict[int, List[ByteInfo]] = {}

        for register in reglist:
            for field in register.get_bit_fields():
                self._used_types.add(field.field_type)
                offset = 0
                for lower in range(0, register.width, size):
                    if field.msb.is_parameter:
                        finder = ParameterFinder()
                        msb = finder.find(field.msb.txt_value)
                    else:
                        msb = field.msb.resolve()
                    if in_range(field.lsb, msb, lower, lower + size - 1):
                        data = self.byte_info(
                            field, register, lower, size, offset
                        )
                        item_list.setdefault(data.address, []).append(data)
                        offset += size // 8
        return item_list

    def build_register_list(self) -> List[Register]:

        reglist: List[Register] = []

        code_registers = [
            reg
            for reg in self._dbase.get_all_registers()
            if not reg.flags.do_not_generate_code
        ]

        for reg in code_registers:
            if reg.dimension.is_parameter:
                new_reg = copy.deepcopy(reg)
                reglist.append(new_reg)
            elif reg.dimension.resolve() > 1:
                for i in range(0, reg.dimension.resolve()):
                    new_reg = copy.deepcopy(reg)
                    new_reg.address = reg.address + (i * int(reg.width // 8))
                    new_reg.dimension.set_int(i)
                    reglist.append(new_reg)
            else:
                new_reg = copy.deepcopy(reg)
                new_reg.dimension.set_int(-1)
                reglist.append(new_reg)

        return reglist

    def write(self, filename: Path) -> None:
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

        reglist = self.build_register_list()

        word_fields = self.generate_group_list(reglist, self._data_width)

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

        parameters = self._dbase.parameters.get()

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

        reg_read_output = register_output_definitions(self._dbase)

        # TODO: fix 64 bit registers with 32 bit width

        with filename.open("w") as ofile:
            ofile.write(
                template.render(
                    year=datetime.datetime.now().date().strftime("%Y"),
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
            ofile.write(f"/*{border_string}\n * ")
            ofile.write("\n * ".join(text_list))
            if border:
                text = f"\n *{border_string}"
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
        self.input_logic = "input logic"
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
    return f"r{reg.address:02x}{MODE_SEP[reg.share]}{field.name.lower()}"


def build_write_address_selects(
    dbase: RegisterDb, word_fields: Dict[int, List[ByteInfo]]
) -> List[DecodeInfo]:
    "Returns the information needed to create the write selects"

    assigns: List[DecodeInfo] = []

    data_width = dbase.ports.data_bus_width
    addr_width = dbase.ports.address_bus_width

    for addr, val in word_fields.items():
        rval = addr >> LOWER_BIT[data_width]
        signal = f"write_r{addr:02x}"
        width = addr_width - LOWER_BIT[data_width]
        decode = f"{width}'h{rval:x}"
        register = val[0][-1]
        assigns.append(DecodeInfo(signal, decode, register))

    return assigns


def build_read_address_selects(
    dbase: RegisterDb, word_fields: Dict[int, List[ByteInfo]], cell_info
) -> List[DecodeInfo]:
    "Returns the information needed to create the read selects"

    assigns: List[DecodeInfo] = []

    data_width = dbase.ports.data_bus_width
    addr_width = dbase.ports.address_bus_width

    for addr, val in word_fields.items():

        for (field, *_) in val:
            if not cell_info[field.field_type].has_rd:
                continue

            rval = addr >> LOWER_BIT[data_width]
            signal = f"read_r{addr:02x}"
            width = addr_width - LOWER_BIT[data_width]
            decode = f"{width}'h{rval:x}"
            register = val[0][-1]

            assigns.append(DecodeInfo(signal, decode, register))

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
                    if field.msb.is_parameter:
                        scalar_ports.append(
                            (
                                sig,
                                f"[{field.msb.int_str()}:{field.lsb}]",
                                reg.dimension.param_name(),
                            )
                        )
                    elif field.msb.resolve() == field.lsb:
                        scalar_ports.append(
                            (sig, "", reg.dimension.param_name())
                        )
                    else:
                        dim[sig] = reg.dimension.param_name()
                        for i in range(field.lsb, field.msb.resolve() + 1):
                            array_ports[sig].append(i)
                elif len(wild) > 1:
                    dim[root[0]] = reg.dimension.param_name()
                    for i in range(field.lsb, field.msb.resolve() + 1):
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
                        dim[grp[0]] = reg.dimension.param_name()
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

    if isinstance(dim, str) or dim > 1:
        try:
            val = int(dim)
            if val > 1:
                return (f"{name}[{dim}]", vect)
            return (name, vect)
        except ValueError:
            return (f"{name}[{dim}]", vect)
    else:
        return (name, vect)


def build_logic_list(_dbase, word_fields, cell_info) -> List[Tuple[str, str]]:
    reg_list = []

    for addr in word_fields:
        val = word_fields[addr]
        for (field, _, _, start_pos, stop_pos, _, reg) in val:
            name = reg_field_name(reg, field)
            dim = reg.dimension.param_name()
            if not field.msb.is_parameter and field.msb.resolve() == field.lsb:
                if reg.dimension.is_parameter:
                    reg_list.append((f"{name}[{dim}]", ""))
                else:
                    reg_list.append((name, ""))
            else:
                vect = f"[{field.msb.int_str()}:{field.lsb}] "
                dim_name = f"{name}[{reg.dimension.param_name()}]"
                if reg.dimension.is_parameter:
                    reg_list.append((dim_name, vect))
                else:
                    reg_list.append((name, vect))

            if cell_info[field.field_type].has_oneshot:
                dim = f"[{stop_pos}:{start_pos}]"
                if reg.dimension.is_parameter:
                    reg_list.append((f"{name}_1S[{dim}]", dim))
                else:
                    reg_list.append((f"{name}_1S", dim))
    return reg_list


def build_input_signals(dbase: RegisterDb, cell_info) -> List[Tuple[str, str]]:
    signals = set()
    for reg in dbase.get_all_registers():
        for field in reg.get_bit_fields():
            cinfo = cell_info[field.field_type]
            if cinfo.has_control:
                if reg.dimension.is_parameter:
                    name = (
                        f"{field.control_signal}[{reg.dimension.param_name()}]"
                    )
                    signals.add((name, ""))
                elif reg.dimension.resolve() > 1:
                    name = f"{field.control_signal}[{reg.dimension.resolve()}]"
                    signals.add((name, ""))
                else:
                    signals.add((field.control_signal, ""))
            if (
                cinfo.has_input
                and field.input_signal
                and field.input_signal not in signals
            ):
                if field.width == 1:
                    vector = ""
                else:
                    vector = f"[{field.msb.int_str()}:{field.lsb}]"
                if reg.dimension.is_parameter:
                    signals.add(
                        (
                            f"{field.input_signal}[{reg.dimension.param_name()}]",
                            vector,
                        )
                    )
                elif reg.dimension.resolve() > 1:
                    signals.add(
                        (
                            f"{field.input_signal}[{reg.dimension.resolve()}]",
                            vector,
                        )
                    )
                else:
                    signals.add((field.input_signal, vector))
    return sorted(signals)


def build_oneshot_assignments(word_fields, cell_info):

    assign_list = []

    for addr in word_fields:
        val = word_fields[addr]
        for (fld, _, _, _, _, _, reg) in val:
            if cell_info[fld.field_type][3]:

                if reg.dimension.resolve() > 1:
                    name = f"{fld.output_signal}_1S[{reg.dimension.resolve()}]"
                else:
                    name = f"{fld.output_signal}_1S"
                value = f"(|r{reg.address:x}_{fld.name.lower()}_1S)"
                assign_list.append((name, value))
    return assign_list


def break_into_bytes(start: int, stop: int) -> List[Tuple[int, int]]:
    "Return a list of byte boundaries from the start and stop values"

    index = start
    data = []

    while index <= stop:
        next_boundary = (int(index // 8) + 1) * 8
        data.append((index, min(stop, next_boundary - 1)))
        index = next_boundary
    return data


def valid_output(field: BitField) -> bool:
    "Returns True if the output signal is valid"

    return field.use_output_enable and field.output_signal != ""


def build_assignments(word_fields):

    assign_list = []

    for word_field in word_fields.values():

        for (fld, _, _, _, _, _, reg) in word_field:

            if not valid_output(fld):
                continue

            mode = MODE_SEP[reg.share]
            reg_name = reg_field_name(reg, fld)

            if reg.dimension.is_parameter:
                signal_name = fld.output_signal
                dimension = reg.dimension.param_name()
            elif reg.dimension.resolve() != -1:
                signal_name = f"{fld.output_signal}[{reg.dimension.resolve()}]"
                dimension = ""
            else:
                signal_name = fld.resolved_output_signal()
                dimension = ""

            assign_list.append(AssignInfo(signal_name, reg_name, dimension))

    return assign_list


def register_output_definitions(dbase: RegisterDb) -> List[LogicDefResolved]:

    full_list: List[LogicDef] = []
    reg_share = {0: "_", 1: "_r_"}

    bus_width = dbase.ports.data_bus_width
    bytes_per_reg = bus_width // 8
    current_group = -1

    for reg in dbase.get_all_registers():

        current_offset = reg.address % bytes_per_reg
        base_addr = (reg.address // bytes_per_reg) * bytes_per_reg

        if base_addr // bytes_per_reg != current_group:
            if reg.dimension.is_parameter:
                wire_name = LogicDef(
                    f"r{base_addr:02x}[reg.dimension.param_name()]",
                    f"[{bus_width-1}:0]",
                )
            else:
                wire_name = LogicDef(f"r{base_addr:02x}", f"[{bus_width-1}:0]")

            full_list.append(wire_name)
            current_group = base_addr // bytes_per_reg

            for field in reg.get_bit_fields():
                field_info = FieldInfo(
                    reg_field_name(reg, field),
                    field.lsb,
                    field.msb,
                    current_offset * 8,
                )
                wire_name.field_list.append(field_info)

    new_list = []

    for wire_name in full_list:
        wire_name.field_list.reverse()

        new_wire = LogicDefResolved(wire_name.name, wire_name.dim)
        new_list.append(new_wire)
        last = bus_width
        for field_info in wire_name.field_list:
            start = last - field_info.offset
            if field_info.msb.is_parameter:
                local_param = copy.copy(field_info.msb)
                local_param.offset = local_param.offset + 1
                new_wire.field_list.append(
                    f"{{({start}-{local_param.int_str()}){{1'b0}}}}"
                )
            else:
                if (start - field_info.msb.resolve()) > 1:
                    new_wire.field_list.append(
                        f"{start-field_info.msb.resolve()-1}'b0"
                    )

            new_wire.field_list.append(field_info.name)
            last = field_info.lsb + field_info.offset
        if last != 0:
            new_wire.field_list.append(f"{last-0}'b0")

    return new_list


def build_standard_ports(dbase: RegisterDb):
    "Returns a dict that maps ports to the port names"

    ports = dbase.ports

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
            "addr": "MGMT.ADDR[%d:3]" % (ports.address_bus_width - 1,),
        }
    return {
        "clk": ports.clock_name,
        "reset": ports.reset_name,
        "write_strobe": ports.write_strobe_name,
        "read_strobe": ports.read_strobe_name,
        "byte_strobe": ports.byte_strobe_name,
        "write_data": ports.write_data_name,
        "read_data": ports.read_data_name,
        "ack": ports.acknowledge_name,
        "addr": ports.address_bus_name,
    }


def make_one_shot(name: str, reg: Register):
    """Builds the one shot signal from the name and dimenstion"""

    if reg.dimension.is_parameter:
        signal = (f"{name}_1S[{reg.dimension.param_name()}]", "")
    elif reg.dimension.resolve() > 1:
        signal = (f"{name}_1S[{reg.dimension.resolve()}]", "")
    else:
        signal = (f"{name}_1S", "")
    return signal


EXPORTERS = [
    (
        ProjectType.REGSET,
        ExportInfo(
            SystemVerilog,
            ("RTL", "SystemVerilog"),
            "SystemVerilog files",
            ".sv",
            "rtl-system-verilog",
        ),
    ),
    (
        ProjectType.REGSET,
        ExportInfo(
            Verilog2001,
            ("RTL", "Verilog 2001"),
            "Verilog files",
            ".v",
            "rtl-verilog-2001",
        ),
    ),
    (
        ProjectType.REGSET,
        ExportInfo(
            Verilog,
            ("RTL", "Verilog 95"),
            "Verilog files",
            ".v",
            "rtl-verilog-95",
        ),
    ),
]
