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
from collections import namedtuple, defaultdict
from jinja2 import FileSystemLoader, Environment
from regenerate.db import TYPES, TYPE_TO_OUTPUT
from regenerate.writers.writer_base import WriterBase, ExportInfo
from regenerate.writers.verilog_reg_def import REG
from regenerate.db.enums import ShareType, ResetType

LOWER_BIT = {128: 4, 64: 3, 32: 2, 16: 1, 8: 0}


(F_FIELD, F_START_OFF, F_STOP_OFF, F_START,
 F_STOP, F_ADDRESS, F_REGISTER) = range(7)

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
    ["field", "start_offset", "stop_offset",
        "start", "stop", "address", "register"],
)


def full_reset_value(field):
    """returns the full reset value for the entire field"""

    if field.reset_type == ResetType.NUMERIC:
        return "{0}'h{1:0x}".format(field.width, field.reset_value)
    elif field.reset_type == ResetType.INPUT:
        return field.reset_input
    return field.reset_parameter


def reset_value(field, start, stop):
    """returns the full reset value for the field up to a byte"""

    if field.reset_type == ResetType.NUMERIC:
        field_width = (stop - start) + 1
        reset = int(field.reset_value >> int(start - field.lsb))
        return "{0}'h{1:x}".format(field_width, reset & int((2 ** field_width) - 1))
    elif field.reset_type == ResetType.INPUT:
        if stop == start:
            return field.reset_input
        return "{0}[{1}:{2}]".format(field.reset_input, stop, start)
    if stop == start:
        return field.reset_parameter
    return "{0}[{1}:{2}]".format(field.reset_parameter, stop, start)


def break_into_bytes(start, stop):
    """
    Return a list of byte boundaries from the start and stop values
    """
    index = start
    data = []

    while index <= stop:
        next_boundary = (int(index / 8) + 1) * 8
        data.append((index, min(stop, next_boundary - 1)))
        index = next_boundary
    return data


def in_range(lower, upper, lower_limit, upper_limit):
    """
    Checks to see if the range is within the specified range
    """
    return (
        (lower_limit <= lower <= upper_limit)
        or (lower_limit <= upper <= upper_limit)
        or (lower < lower_limit and upper >= upper_limit)
    )


def rshift(val, shift):
    return int(val) >> int(shift)


class Verilog(WriterBase):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(self, project, dbase):
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
            if not (reg.do_not_generate_code or reg.ram_size > 0)
        ]
        self._used_types = set()

    def _byte_info(self, field, register, lower, size, offset):
        """
        Returns the basic information from a field, broken out into byte
        quantities
        """
        start = max(field.lsb, lower)
        stop = min(field.msb, lower + size - 1)

        nbytes = int(size / 8)
        address = int(register.address / nbytes) * nbytes
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

    def __generate_group_list(self, reglist, size):
        """
        Breaks a set of bit fields along the specified boundary
        """
        item_list = {}
        for register in reglist:
            for field in register.get_bit_fields():
                self._used_types.add(field.field_type)
                offset = 0
                for lower in range(0, register.width, size):
                    if in_range(field.lsb, field.msb, lower, lower + size - 1):
                        data = self._byte_info(
                            field, register, lower, size, offset)
                        item_list.setdefault(data.address, []).append(data)
                        offset += size / 8
        return item_list

    def write(self, filename):
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """
        import copy

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
            r for r in self._dbase.get_all_registers() if not r.do_not_generate_code
        ]:
            if reg.dimension > 1:
                for i in range(0, reg.dimension):
                    new_reg = copy.copy(reg)
                    new_reg.address = reg.address + (i * int(reg.width / 8))
                    new_reg.dimension = i
                    reglist.append(new_reg)
            else:
                new_reg = copy.copy(reg)
                new_reg.dimension = -1
                reglist.append(new_reg)

        word_fields = self.__generate_group_list(reglist, self._data_width)

        if self._dbase.reset_active_level and not self._dbase.use_interface:
            reset_edge = "posedge"
        else:
            reset_edge = "negedge"

        reset_op = (
            ""
            if (self._dbase.reset_active_level and not self._dbase.use_interface)
            else "~"
        )

        parameters = []
        for reg in self._dbase.get_all_registers():
            for field in reg.get_bit_fields():
                if field.reset_type == ResetType.PARAMETER:
                    parameters.append(
                        (field.msb, field.lsb, field.reset_parameter))

        scalar_ports = []
        array_ports = defaultdict(list)
        dim = {}
        for reg in self._dbase.get_all_registers():
            if reg.do_not_generate_code:
                continue
            for field in reg.get_bit_fields():
                if TYPE_TO_OUTPUT[field.field_type] and field.use_output_enable:
                    sig = field.output_signal
                    root = sig.split("[")
                    wild = sig.split("*")
                    if len(root) == 1:
                        if field.msb == field.lsb:
                            scalar_ports.append((sig, "", reg.dimension))
                        else:
                            dim[sig] = reg.dimension
                            for i in range(field.lsb, field.msb + 1):
                                array_ports[sig].append(i)
                    elif len(wild) > 1:
                        dim[root[0]] = reg.dimension
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
                            dim[grp[0]] = reg.dimension
                            array_ports[grp[0]].append(int(grp[1]))
                            continue

        for key in array_ports:
            msb = max(array_ports[key])
            lsb = min(array_ports[key])
            if msb == lsb:
                scalar_ports.append((key, "[%d]" % lsb, dim[key]))
            else:
                scalar_ports.append((key, "[%d:%d]" % (msb, lsb), dim[key]))

        # TODO: fix 64 bit registers with 32 bit width

        with open(filename, "w") as ofile:
            ofile.write(
                template.render(
                    db=self._dbase,
                    rshift=rshift,
                    parameters=parameters,
                    cell_info=self._cell_info,
                    word_fields=word_fields,
                    break_into_bytes=break_into_bytes,
                    sorted_regs=sorted(reglist, key=lambda r: r.address),
                    full_reset_value=full_reset_value,
                    reset_value=reset_value,
                    input_logic=self.input_logic,
                    output_logic=self.output_logic,
                    always=self.always,
                    output_ports=scalar_ports,
                    reset_edge=reset_edge,
                    reset_op=reset_op,
                    reg_type=self.reg_type,
                    LOWER_BIT=LOWER_BIT,
                )
            )
            self.write_register_modules(ofile)

    def comment(self, ofile, text_list, border=None, precede_blank=0):
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
        """
        Writes the used register module types to the file.
        """

        if self._dbase.reset_active_level and not self._dbase.use_interface:
            edge = "posedge"
        else:
            edge = "negedge"

        if self._dbase.reset_active_level and not self._dbase.use_interface:
            condition = ""
        else:
            condition = "~"

        if self._dbase.byte_strobe_active_level or self._dbase.use_interface:
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
            Verilog, ("RTL", "Verilog 95"), "Verilog files", ".v", "rtl-verilog-95"
        ),
    ),
]
