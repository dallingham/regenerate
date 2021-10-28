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

import re
import copy
import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, TextIO, Set, Dict, NamedTuple, Any

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
from regenerate.db.enums import ShareType, ResetType
from regenerate.settings.version import PROGRAM_VERSION

from .writer_base import (
    find_template,
    RegsetWriter,
    ProjectType,
)
from .export_info import ExportInfo
from .verilog_reg_def import REG

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


class OneShots(NamedTuple):
    "List of one-shots and their values"

    name: str
    value: str


class AssignInfo(NamedTuple):
    "Holds the information for output assignments"

    output: str
    register: str
    dimension: str


class Scalar(NamedTuple):
    "Scalar value"

    name: str
    vector: str


class RegDecl(NamedTuple):
    "Holds the infomration for register declarations"

    name: str
    dimension: str


class FieldInfo(NamedTuple):
    "Holds the field information"

    name: str
    lsb: int
    msb: ParamValue
    offset: int


class DecodeInfo(NamedTuple):
    "Holds the register decode information"

    name: str
    addr: str
    register: Register


class LanguageTerms(NamedTuple):
    "Holds the Verilog language variations"

    input_logic: str
    output_logic: str
    always: str
    reg_type: str


class PortInfo(NamedTuple):
    "Holds the information on the stanard module ports"

    clk: str
    reset: str
    alt_reset: str
    interface: str
    modport: str
    write_strobe: str
    read_strobe: str
    byte_strobe: str
    write_data: str
    read_data: str
    ack: str
    addr: str


class RegData:
    def __init__(self):
        self.ci = None
        self.reg_name = None
        self.reg_addr = None
        self.type_descr = None
        self.msb = None
        self.lsb = None
        self.localparam = None
        self.rval = None
        self.dim = None
        self.byte_offset = None
        self.byte_addr = None
        self.byte_offset_str = None
        self.field_width = None
        self.reset_val = None
        self.generate = None
        self.pos = None
        self.bytepos = None
        self.wpos = None


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


class Verilog(RegsetWriter):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(
        self, project: RegProject, regset: RegisterDb, options: Dict[str, Any]
    ):
        super().__init__(project, regset, options)

        self.lang = LanguageTerms("input", "output", "always", "reg")

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
            for reg in regset.get_all_registers()
            if not (reg.flags.do_not_generate_code or reg.ram_size > 0)
        ]

        self._used_types: Set[BitType] = set()

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
                        data = make_byte_info(
                            field, register, lower, size, offset
                        )
                        item_list.setdefault(data.address, []).append(data)
                        offset += size // 8
        return item_list

    def build_register_list(self) -> List[Register]:
        "Builds the register list"

        reglist: List[Register] = []

        code_registers = [
            reg
            for reg in self._regset.get_all_registers()
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

        template = find_template(
            "verilog.template", [("drop_write_share", drop_write_share)]
        )

        word_fields = self.generate_group_list(
            self.build_register_list(), self._regset.ports.data_bus_width
        )

        if self._regset.ports.reset_active_level:
            reset_edge = "posedge"
            reset_op = ""
        else:
            reset_edge = "negedge"
            reset_op = "!"

        reg_list = build_logic_list(self._regset, word_fields, self._cell_info)
        oneshot_assigns = build_oneshot_assignments(
            word_fields, self._cell_info
        )

        write_address_selects = build_write_address_selects(
            self._regset, word_fields
        )
        read_address_selects = build_read_address_selects(
            self._regset, word_fields, self._cell_info
        )

        # TODO: fix 64 bit registers with 32 bit width

        signal_list = self.build_signal_list()

        self.test()

        with filename.open("w") as ofile:
            ofile.write(
                template.render(
                    year=datetime.datetime.now().date().strftime("%Y"),
                    date=datetime.datetime.now().strftime("%Y-%m-%d %X"),
                    version=PROGRAM_VERSION,
                    db=self._regset,
                    ports=build_standard_ports(self._regset),
                    reg_list=reg_list,
                    signal_list=signal_list,
                    oneshot_assigns=oneshot_assigns,
                    write_address_selects=write_address_selects,
                    read_address_selects=read_address_selects,
                    reg_read_output=register_output_definitions(self._regset),
                    rshift=rshift,
                    reg_field_name=reg_field_name,
                    parameters=self._regset.parameters.get(),
                    cell_info=self._cell_info,
                    word_fields=word_fields,
                    assign_list=build_assignments(word_fields),
                    full_reset_value=full_reset_value,
                    reset_value=reset_value,
                    lang=self.lang,
                    reset_edge=reset_edge,
                    reset_op=reset_op,
                    low_bit=LOWER_BIT[self._regset.ports.data_bus_width],
                )
            )
            self.write_register_modules(ofile)

    def build_signal_list(self):

        input_signals = build_input_signals(self._regset, self._cell_info)
        output_signals = build_output_signals(self._regset, self._cell_info)
        in_logic = self.lang.input_logic
        out_logic = self.lang.output_logic
        port_width = build_port_widths(self._regset)
        ports = build_standard_ports(self._regset)

        if self._regset.use_interface:
            new_input_signals = [f"{ports.interface}.{ports.modport} MGMT"]
        else:
            new_input_signals = [
                f"{in_logic}          {ports.clk}",
                f"{in_logic}          {ports.reset}",
                f"{in_logic}          {ports.write_strobe}",
                f"{in_logic}          {ports.read_strobe}",
                f"{in_logic}  {port_width['byte_strobe']:7s} {ports.byte_strobe}",
                f"{in_logic}  {port_width['addr']:7s} {ports.addr}",
                f"{in_logic}  {port_width['write_data']:7s} {ports.write_data}",
                f"{out_logic} {port_width['write_data']:7s} {ports.read_data}",
                f"{out_logic}         {ports.ack}",
            ]

        if self._regset.ports.secondary_reset:
            new_input_signals.append(f"{in_logic}          {ports.alt_reset}")
        for scalar in input_signals:
            new_input_signals.append(
                f"{in_logic}  {scalar.vector:7s} {scalar.name}"
            )
        for scalar in output_signals:
            new_input_signals.append(
                f"{out_logic} {scalar.vector:7s} {scalar.name}"
            )
        return new_input_signals

    def write_register_modules(self, ofile):
        """Writes the used register module types to the file."""

        if self._regset.ports.reset_active_level:
            edge = "posedge"
            condition = ""
            rst_name = "RST"
        else:
            edge = "negedge"
            condition = "!"
            rst_name = "RSTn"

        if self._regset.ports.byte_strobe_active_level:
            be_level = ""
        else:
            be_level = "~"

        if self._regset.ports.sync_reset:
            trigger = ""
        else:
            if self._regset.ports.reset_active_level:
                trigger = f" or posedge RST"
            else:
                trigger = f" or negedge RSTn"

        name_map = {
            "MODULE": self._regset.name,
            "RST": rst_name,
            "BE_LEVEL": be_level,
            "RESET_CONDITION": condition,
            "RESET_TRIGGER": trigger,
            "RESET_EDGE": edge,
        }

        for i in self._used_types:
            ofile.write("\n\n")
            try:
                comment(ofile, [self._cell_info[i][4]])
                ofile.write(REG[self._cell_info[i][0]] % name_map)
            except KeyError:
                comment(
                    ofile,
                    [
                        "No definition for %s_%s_reg\n"
                        % (self._regset.name, self._cell_info[i][0])
                    ],
                )

    def test(self):
        db = self._regset
        bytes_per_word = db.ports.data_bus_width // 8

        full_list = []
        for reg in db.get_all_registers():
            for field in reg.get_bit_fields():

                reg_field = RegData()
                reg_field.ci = self._cell_info[field.field_type]
                if field.reset_type != 1:
                    reg_field.rval = "pRST{reg.address:02x}_{field.name}"
                else:
                    reg_field.rval = field.reset_input
                if reg.dimension:
                    reg_field.dim = "[dim]"
                else:
                    reg_field.dim = None
                reg_field.byte_offset = reg.address % bytes_per_word
                reg_field.byte_addr = (
                    reg.address // bytes_per_word
                ) * bytes_per_word
                if reg_field.byte_offset:
                    reg_field.byte_offset_str = f"+{reg_field.byte_offset}"
                else:
                    reg_field.byte_offset_str = ""
                if not field.msb.is_parameter and field.width == 1:
                    reg_field.field_width = ""
                else:
                    reg_field.field_width = (
                        f"[{field.msb.int_str()}:{field.lsb}]"
                    )
                reg_field.reset_val = field.reset_vstr()

                if field.msb.is_parameter or field.msb.resolve() > field.lsb:
                    reg_field.pos = "[bitpos]"
                    if reg_field.byte_offset == 0:
                        reg_field.bytepos = "bitpos >> 3"
                        reg_field.wpos = "[bitpos]"
                    else:
                        reg_field.bytepos = (
                            "(bitpos >> 3)+%d" % reg_field.byte_offset
                        )
                        reg_field.wpos = "[bitpos+%d]" % (
                            reg_field.byte_offset * 8,
                        )
                    reg_field.generate = True
                else:
                    reg_field.generate = False
                    reg_field.pos = ""
                    reg_field.bytepos = "%d" % (
                        (field.lsb // 8) + reg_field.byte_offset,
                    )
                    reg_field.wpos = "[%d]" % (
                        field.lsb + reg_field.byte_offset * 8,
                    )

                full_list.append(reg_field)
        return full_list


class SystemVerilog(Verilog):
    """Provides the SystemVerilog version"""

    def __init__(self, project, regset, options: Dict[str, Any]):
        super().__init__(project, regset, options)
        self.lang = LanguageTerms(
            "input logic", "output logic", "always_ff", "logic"
        )


class Verilog2001(Verilog):
    "Provides the Verilog2001 version"

    def __init(self, project, regset, options: Dict[str, Any]):
        super().__init__(project, regset, options)


def drop_write_share(list_in):
    "Drops the write-share registers from the list"

    list_out = [l for l in list_in if l[6].share != ShareType.WRITE]
    return list_out


def make_byte_info(
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


def build_port_widths(regset: RegisterDb):
    "Returns the port widths for the signals"

    awidth = regset.ports.address_bus_width - 1
    dwidth = regset.ports.data_bus_width

    return {
        "byte_strobe": f"[{dwidth // 8 - 1}:0]",
        "addr": f"[{awidth}:{LOWER_BIT[dwidth]}]",
        "write_data": f"[{dwidth - 1}:0]",
    }


def reg_field_name(reg: Register, field: BitField):
    "Returns the register name"

    return f"r{reg.address:02x}{MODE_SEP[reg.share]}{field.name.lower()}"


def build_write_address_selects(
    regset: RegisterDb, word_fields: Dict[int, List[ByteInfo]]
) -> List[DecodeInfo]:
    "Returns the information needed to create the write selects"

    assigns: List[DecodeInfo] = []

    data_width = regset.ports.data_bus_width
    addr_width = regset.ports.address_bus_width

    for addr, val in word_fields.items():
        rval = addr >> LOWER_BIT[data_width]
        signal = f"write_r{addr:02x}"
        width = addr_width - LOWER_BIT[data_width]
        decode = f"{width}'h{rval:x}"
        register = val[0][-1]
        assigns.append(DecodeInfo(signal, decode, register))

    return assigns


def build_read_address_selects(
    regset: RegisterDb, word_fields: Dict[int, List[ByteInfo]], cell_info
) -> List[DecodeInfo]:
    "Returns the information needed to create the read selects"

    assigns: List[DecodeInfo] = []

    data_width = regset.ports.data_bus_width
    addr_width = regset.ports.address_bus_width

    for addr, val in word_fields.items():

        for byte_info in val:
            if not cell_info[byte_info.field.field_type].has_rd:
                continue

            rval = addr >> LOWER_BIT[data_width]
            signal = f"read_r{addr:02x}"
            width = addr_width - LOWER_BIT[data_width]
            decode = f"{width}'h{rval:x}"
            register = val[0][-1]

            assigns.append(DecodeInfo(signal, decode, register))

    return assigns


def build_output_signals(regset, cell_info) -> List[Scalar]:
    "Builds the output signal list"

    scalar_ports = []
    array_ports = defaultdict(list)
    dim = {}
    signals = []

    reg_list = [
        reg
        for reg in regset.get_all_registers()
        if not reg.flags.do_not_generate_code
    ]

    for reg in reg_list:
        for field in reg.get_bit_fields():

            if cell_info[field.field_type].has_oneshot:
                signals.append(make_one_shot(field.output_signal, reg))

            if not (
                TYPE_TO_OUTPUT[field.field_type] and field.use_output_enable
            ):
                continue

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
                    scalar_ports.append((sig, "", reg.dimension.param_name()))
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
                return Scalar(f"{name}[{dim}]", vect)
            return Scalar(name, vect)
        except ValueError:
            return Scalar(f"{name}", vect)
    else:
        return Scalar(name, vect)


def build_logic_list(_regset, word_fields, cell_info) -> List[RegDecl]:
    "Builds the logic definition list"

    reg_list = []

    for addr in word_fields:
        val = word_fields[addr]
        for byte_info in val:
            name = reg_field_name(byte_info.register, byte_info.field)
            dim = byte_info.register.dimension
            msb = byte_info.field.msb
            lsb = byte_info.field.lsb

            if not msb.is_parameter and msb.resolve() == lsb:
                if dim.is_parameter:
                    new_reg = RegDecl(f"{name}[{dim.param_name()}]", "")
                else:
                    new_reg = RegDecl(name, "")
            else:
                vect = f"[{msb.int_str()}:{lsb}] "
                if dim.is_parameter:
                    new_reg = RegDecl(f"{name}[{dim.param_name()}]", vect)
                else:
                    new_reg = RegDecl(name, vect)

            reg_list.append(new_reg)

            if cell_info[byte_info.field.field_type].has_oneshot:
                dim_str = f"[{byte_info.stop}:{byte_info.start}]"
                if dim.is_parameter:
                    new_reg = RegDecl(f"{name}_1S[{dim_str}]", dim_str)
                else:
                    new_reg = RegDecl(f"{name}_1S", dim_str)

                reg_list.append(new_reg)

    return reg_list


def build_input_signals(regset: RegisterDb, cell_info) -> List[Scalar]:
    "Builds the input list"

    signals = set()
    for reg in regset.get_all_registers():
        for field in reg.get_bit_fields():
            cinfo = cell_info[field.field_type]
            signal = field.control_signal
            dim = reg.dimension

            if field.reset_type == ResetType.INPUT:
                rval = field.reset_input
                if field.width == 1:
                    vec_width = ""
                else:
                    vec_width = f"[{field.width-1}:0]"
                if reg.dimension.is_parameter:
                    signals.add(
                        Scalar(f"{rval}[{dim.param_name()}]", vec_width)
                    )
                elif reg.dimension.resolve() > 1:
                    signals.add(Scalar(f"{rval}[{dim.resolve()}]", vec_width))
                else:
                    signals.add(Scalar(rval, vec_width))

            if cinfo.has_control:
                if reg.dimension.is_parameter:
                    signals.add(Scalar(f"{signal}[{dim.param_name()}]", ""))
                elif reg.dimension.resolve() > 1:
                    signals.add(Scalar(f"{signal}[{dim.resolve()}]", ""))
                else:
                    signals.add(Scalar(field.control_signal, ""))

            if (
                cinfo.has_input
                and field.input_signal
                and field.input_signal not in signals
            ):
                signal = field.input_signal

                if field.width == 1:
                    vector = ""
                else:
                    vector = f"[{field.msb.int_str()}:{field.lsb}]"

                if reg.dimension.is_parameter:
                    signals.add(
                        Scalar(f"{signal}[{dim.param_name()}]", vector)
                    )
                elif reg.dimension.resolve() > 1:
                    signals.add((f"{signal}[{dim.resolve()}]", vector))
                else:
                    signals.add(Scalar(signal, vector))

    return sorted(signals)


def build_oneshot_assignments(word_fields, cell_info) -> List[OneShots]:
    "Build a list of the one shots and their assigned values"

    assign_list = []

    for addr in word_fields:
        val = word_fields[addr]
        for byte_info in val:
            reg = byte_info.register
            fld = byte_info.field

            if cell_info[fld.field_type][3]:

                if reg.dimension.resolve() > 1:
                    name = f"{fld.output_signal}_1S[{reg.dimension.resolve()}]"
                else:
                    name = f"{fld.output_signal}_1S"

                value = f"(|r{reg.address:x}_{fld.name.lower()}_1S)"

                assign_list.append(OneShots(name, value))
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
    "Build the general assignments"

    assign_list = []

    for word_field in word_fields.values():

        for byte_info in word_field:

            reg = byte_info.register
            fld = byte_info.field

            if not valid_output(fld):
                continue

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


def register_output_definitions(regset: RegisterDb) -> List[LogicDefResolved]:
    "Build the register output definitions"

    full_list: List[LogicDef] = []
    new_list: List[LogicDefResolved] = []

    bus_width = regset.ports.data_bus_width
    bytes_per_reg = bus_width // 8
    current_group = -1

    for reg in regset.get_all_registers():

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


def build_standard_ports(regset: RegisterDb) -> PortInfo:
    "Returns a dict that maps ports to the port names"

    ports = regset.ports

    if ports.reset_active_level:
        rst = "MGMT.RST"
    else:
        rst = "MGMT.RSTn"

    if regset.use_interface:
        return PortInfo(
            "MGMT.CLK",
            rst,
            ports.secondary_reset_name,
            ports.interface_name,
            ports.modport_name,
            "MGMT.WR",
            "MGMT.RD",
            "MGMT.BE",
            "MGMT.WDATA",
            "MGMT.RDATA",
            "MGMT.ACK",
            f"MGMT.ADDR[{ports.address_bus_width - 1}:{LOWER_BIT[ports.data_bus_width]}]",
        )
    return PortInfo(
        ports.clock_name,
        ports.reset_name,
        ports.secondary_reset_name,
        ports.interface_name,
        ports.modport_name,
        ports.write_strobe_name,
        ports.read_strobe_name,
        ports.byte_strobe_name,
        ports.write_data_name,
        ports.read_data_name,
        ports.acknowledge_name,
        ports.address_bus_name,
    )


def make_one_shot(name: str, reg: Register) -> Scalar:
    """Builds the one shot signal from the name and dimenstion"""

    if reg.dimension.is_parameter:
        signal = Scalar(f"{name}_1S[{reg.dimension.param_name()}]", "")
    elif reg.dimension.resolve() > 1:
        signal = Scalar(f"{name}_1S[{reg.dimension.resolve()}]", "")
    else:
        signal = Scalar(f"{name}_1S", "")
    return signal


def comment(
    ofile: TextIO, text_list: List[str], border=None, precede_blank=0
) -> None:
    "Creates a comment from the list of text strings"

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


EXPORTERS = [
    (
        ProjectType.REGSET,
        ExportInfo(
            SystemVerilog,
            "RTL",
            "Register RTL (SystemVerilog)",
            "SystemVerilog files",
            "RTL module for the registers in SystemVerilog format",
            ".sv",
            "{}.sv",
            {},
            "rtl-system-verilog",
        ),
    ),
    (
        ProjectType.REGSET,
        ExportInfo(
            Verilog2001,
            "RTL",
            "Register RTL (Verilog 2001)",
            "Verilog files",
            "RTL module for the registers in Verilog 2001 format",
            ".v",
            "{}.v",
            {},
            "rtl-verilog-2001",
        ),
    ),
    (
        ProjectType.REGSET,
        ExportInfo(
            Verilog,
            "RTL",
            "Register RTL (Verilog 95)",
            "Verilog files",
            "RTL module for the registers in Verilog 95 format",
            ".v",
            "{}.v",
            {},
            "rtl-verilog-95",
        ),
    ),
]
