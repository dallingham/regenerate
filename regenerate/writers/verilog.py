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
VerilogWriter - produces a verilog RTL description of the registers
"""

import re
import textwrap
from regenerate.settings import ini
from verilog_reg_def import REG
from regenerate.db import BitField, TYPES, BFT_TYPE, BFT_ID, BFT_INP, BFT_CTRL, BFT_1S, BFT_DESC, BFT_WIDE, BFT_DO, BFT_RD, BFT_RO

from writer_base import WriterBase

#
# Constants
#
LOWER_BIT = {128: 4, 64 : 3, 32 : 2, 16 : 1 , 8: 0}
BUS_ELEMENT = re.compile("([\w_]+)\[(\d+)\]")
SINGLE_BIT = re.compile("\s*(\S+)\[(\d+)\]")
MULTI_BIT = re.compile("\s*(\S+)\[(\d+):(\d+)\]")


def bin(val, width):
    """
    Converts the integer value to a Verilog value
    """
    return "%d'h%x" % (width, val)


def get_width(field, start=-1, stop=-1, force_index=False):
    """
    Returns with width if the bit range is greater than one.
    """
    if stop == -1:
        start = field.start_position
        stop = field.stop_position

    if field.width == 1 and not force_index:
        signal = ""
    elif start == stop:
        signal = "[%d]" % stop
    else:
        signal = "[%d:%d]" % (stop, start)
    return signal


def oneshot_name(name):
    """
    Returns the name of the oneshot signal associated with the signal. In this
    implementation, it is the name of the signal with a _1s appended.
    """
    return name + "_1S"


def write_strobe(address):
    """
    Generates the write strobe signal associated with a particular address.
    """
    return "write_r%02x" % address


def get_signal_offset(address):
    """
    Returns the offset of the signal.
    """
    return address % 4


def get_base_signal(address, field):
    """
    Returns the base signal derived from the address and the output field
    """
    return "r%02x_%s" % (address, field.field_name.lower())


def get_signal_info(address, field, start=-1, stop=-1):
    """
    Returns the base signal name (derived from the address and output
    field, the signal name (derived from the base name and the start
    and stop index), and the register offset.
    """
    offset = get_signal_offset(address)
    base_signal = get_base_signal(address, field)

    signal = base_signal + get_width(field, start, stop)
    return (base_signal, signal, offset)


def extract_base(control):
    """
    Extracts the base name of a signal, removing any bus indexes
    """
    match = BUS_ELEMENT.match(control)
    if match:
        return match.groups()[0]
    else:
        return control


def parallel_load_port(field, port_list, control_set):
    """
    Extracts the base signal of the parallel control signal, make sure
    that it is not in the existing set, and the adds it to the port list
    """
    control = extract_base(field.control_signal)

    if control not in control_set:
        port_list.append(('input', '', control, "parallel load signal"))
        control_set.add(control)


def input_signal_port(field, port_list, control_set):
    """
    Extracts the base signal of the input control signal, make sure
    that it is not in the existing set, and the adds it to the port list
    """
    control = extract_base(field.input_signal)
    if control not in control_set:
        port_list.append(('input', get_width(field), control, "input signal"))
        control_set.add(control)


def in_range(lower, upper, lower_limit, upper_limit):
    """
    Checks to see if the range is within the specified range
    """
    return ((lower_limit <= lower <= upper_limit) or
            (lower_limit <= upper <= upper_limit) or
            (lower < lower_limit and upper >= upper_limit))


def add_reset_input(reset_set, field):
    """
    Adds the reset value to a field
    """
    reset = field.reset_input

    match = SINGLE_BIT.match(reset)
    if match:
        data = match.groups()
        reset = data[0]
        start = int(data[1])
        stop = start
    else:
        match = MULTI_BIT.match(reset)
        if match:
            data = match.groups()
            reset = data[0]
            start = int(data[2])
            stop = int(data[1])
        else:
            start = field.start_position
            stop = field.stop_position

    if reset in reset_set:
        values = reset_set[reset]
        reset_set[reset] = ('input', max(stop, values[1]),
                            min(start, values[2]),
                            "%s, %s" % (values[3], field.field_name)
                            )
    else:
        reset_set[reset] = ('input', stop, start,
                            "reset value for %s" % field.field_name)


class Verilog(WriterBase):
    """
    Write an RTL description of the registers, suitable for synthesis.
    """

    ALWAYS_FF = 'always'

    def __init__(self, dbase):
        WriterBase.__init__(self, dbase)
        self.__sorted_regs = [
            dbase.get_register(key) for key in dbase.get_keys()
            if not self._dbase.get_register(key).do_not_generate_code ]

        self._coverage = self._dbase.enable_coverage

        max_column_str = ini.get('user', 'column_width', "80")
        try:
            self._max_column = max(int(max_column_str), 80)
        except ValueError:
            self._max_column = 80
        self.__comment_line = '-' * (self._max_column-2)

        if dbase.reset_active_level:
            self._reset_edge = "posedge %s" % self._reset
            self._reset_condition = self._reset
        else:
            self._reset_edge = "negedge %s" % self._reset
            self._reset_condition = "~%s" % self._reset

        if dbase.byte_strobe_active_level:
            self.__be_condition = "%s" % self._byte_enables
        else:
            self.__be_condition = "~%s" % self._byte_enables

        self._ofile = None
        self._lower_bit = LOWER_BIT[self._data_width]

        self._word_fields = self.__generate_group_list(self._data_width)

        self._field_type_map = {
            BitField.TYPE_READ_ONLY : self._register_read_only,
            }

        self._has_input   = {}
        self._has_oneshot = {}
        self._has_control = {}
        self._has_data_out = {}
        self._has_rd = {}
        self._allows_wide = {}
        self._cell_name = {}
        self._type_descr = {}
        self._is_read_only = {}
        self._used_types = set()
        
        for i in TYPES:
            self._cell_name[i[BFT_TYPE]]    = i[BFT_ID].lower()
            self._has_input[i[BFT_TYPE]]    = i[BFT_INP]
            self._has_control[i[BFT_TYPE]]  = i[BFT_CTRL]
            self._has_oneshot[i[BFT_TYPE]]  = i[BFT_1S]
            self._type_descr[i[BFT_TYPE]]   = i[BFT_DESC]
            self._allows_wide[i[BFT_TYPE]]  = i[BFT_WIDE]
            self._has_data_out[i[BFT_TYPE]] = i[BFT_DO]
            self._has_rd[i[BFT_TYPE]]       = i[BFT_RD]
            self._is_read_only[i[BFT_TYPE]] = i[BFT_RO]

    def _not_implemented(self, reg, field):
        self._ofile.write("/* Not yet implemented */\n")

    def _break_on_byte_boundaries(self, start, stop):
        index = start
        data = []
        
        while index <= stop:
            next_boundary = ((index/8) + 1) * 8
            data.append((index, min(stop, next_boundary - 1)))
            index = next_boundary
        return data

    def _reset_value(self, field, start, stop):
        if field.reset_type == BitField.RESET_NUMERIC:
            return "%d'h%x" % (((stop - start) + 1), (field.reset_value >> (start - field.start_position)) & 0xff)
        elif field.reset_type == BitField.RESET_INPUT:
            return "%s[%d:%d]" % (field.reset_input, stop, start)
        else:
            return "%s[%d:%d]" % (field.reset_parameter, stop, start)

    def _full_reset_value(self, field):
        if field.reset_type == BitField.RESET_NUMERIC:
            return "%d'h%0x" % (((field.stop_position - field.start_position) + 1), field.reset_value)
        elif field.reset_type == BitField.RESET_INPUT:
            return field.reset_input
        else:
            return field.reset_parameter

    def _register_read_only(self, address, field):
        field_name = field.field_name.lower()
        rvalue = self._full_reset_value(field)
        
        self._ofile.write('assign r%02x_%s = %s;\n' % (address, field_name, rvalue))
        self._ofile.write('\n')

    def _register_normal(self, address, field):
        field_name = field.field_name.lower()
        cell_name = self._cell_name[field.field_type]
        self._used_types.add(field.field_type)
        bytes = self._data_width / 8

        for (start, stop) in self._break_on_byte_boundaries(field.start_position, field.stop_position):

            if start >= self._data_width:
                write_address = address + ((start / self._data_width) * (self._data_width / 8))
            else:
                write_address = (address / bytes) * bytes

            reg_start_bit = (address * 8) % (self._data_width)
            bus_start = start % self._data_width + reg_start_bit
            bus_stop = stop % self._data_width + reg_start_bit
            
            width = (stop - start) + 1

            bus_index = get_width(field, bus_start, bus_stop, True)
            index = get_width(field, start, stop)
            instance = "r%02x_%s_%d" % (address, field_name, start)
            
            self._ofile.write('%s_%s_reg ' % (self._module, cell_name))
            if self._allows_wide[field.field_type]:
                self._ofile.write('#(.WIDTH(%d)) ' % width)
            self._ofile.write('%s\n' % instance)
            
            self._ofile.write('  (\n')
            self._ofile.write('    .CLK   (%s),\n' % self._clock)
            self._ofile.write('    .RSTn  (%s),\n' % self._reset)

            byte_lane = (reg_start_bit + start) / 8
            if not self._is_read_only[field.field_type]:
                self._ofile.write('    .WE    (write_r%02x),\n' % write_address)
                self._ofile.write('    .DI    (%s%s),\n' % (self._data_in, bus_index))
                self._ofile.write('    .BE    (%s[%d]),\n' % (self._byte_enables, byte_lane))
            if self._has_rd[field.field_type]:
                self._ofile.write('    .RD    (%s),\n' % self._read_strobe)
            if self._has_data_out[field.field_type]:
                self._ofile.write('    .DO    (r%02x_%s%s),\n' % (address, field_name, index))
            if self._has_control[field.field_type]:
                self._ofile.write('    .LD    (%s),\n' % field.control_signal)
            if self._has_input[field.field_type]:
                self._ofile.write('    .IN    (%s%s),\n' % (field.input_signal, index))
            if self._has_oneshot[field.field_type]:
                self._ofile.write('    .DO_1S (r%02x_%s_1S),\n' % (address, field_name))
                
            self._ofile.write('    .RVAL  (%s)\n' % self._reset_value(field, start, stop))
            self._ofile.write('  );\n\n')

    def _byte_info(self, field, register, lower, size):
        """
        Returns the basic information from a field, broken out into byte
        quantities
        """
        width = self._data_width
        start = max(field.start_position, lower)
        stop = min(field.stop_position, lower + size - 1)

        bytes = size / 8
        address = (register.address / bytes) * bytes
        bit_offset = (register.address * 8) % size

        return (field, start + bit_offset, stop + bit_offset, address, register)

    def __generate_group_list(self, size):
        """
        Breaks a set of bit fields along the specified boundary
        """
        item_list = {}
        for register in self.__sorted_regs:
            for field in [register.get_bit_field(field_key)
                          for field_key in register.get_bit_field_keys()]:

                for lower in range(0, register.width, size):
                    if in_range(field.start_position, field.stop_position,
                                lower, lower + size - 1):
                        data = self._byte_info(field, register, lower, size)
                        item_list.setdefault(data[3], []).append(data)
        return item_list

    def write(self, filename):
        """
        Writes the verilog code to the specified filename
        """
        self._ofile = open(filename, "w")
        self._write_header_comment(self._ofile, 'site_verilog.inc',
                                   comment_char='//')
        self._write_module_header()
        self._write_locals()
        self._write_address_selects()
        self._write_output_assignments()
        self._write_register_rtl_code()
        self._write_acknowledge()
        self._define_outputs()
        self._write_trailer()
        self._write_register_modules()
        self._ofile.close()

    def _write_register_modules(self):

        edge = "posedge" if self._dbase.reset_active_level else "negedge"
        condition = "" if self._dbase.reset_active_level else "~"
        be_level = "" if self._dbase.byte_strobe_active_level else "~"

        name_map = { 'MODULE'          : self._module,
                     'BE_LEVEL'        : be_level,
                     'RESET_CONDITION' : condition,
                     'RESET_EDGE'      : edge }
        
        for i in self._used_types:
            self._ofile.write("\n\n")
            try:
                self._ofile.write("// %s\n" % self._type_descr[i])
                self._ofile.write(REG[self._cell_name[i]] % name_map)
            except KeyError:
                self._ofile.write('// No definition for %s_%s_reg\n' % (self._module, self._cell_name[i]))

    def _write_module_header(self):
        """
        Writes the module statement, along with the arguments and port
        declarations
        """

        port_list = self._build_port_list()

        plist = []
        blist = []
        for register in [self._dbase.get_register(key)
                         for key in self._dbase.get_keys()]:
            for field in [register.get_bit_field(key)
                          for key in register.get_bit_field_keys()]:
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.stop_position == field.start_position:
                        blist.append((field.reset_parameter,
                                      field.stop_position - field.start_position + 1,
                                      field.reset_value))
                    else:
                        plist.append((field.stop_position,
                                      field.start_position,
                                      field.reset_parameter,
                                      field.stop_position - field.start_position + 1,
                                      field.reset_value))

        if plist or blist:
            params = ["parameter %s = %d'h%x" % item for item in blist] + \
                     ["parameter [%d:%d] %s = %d'h%x" % item for item in plist]
            self._ofile.write('module %s #(\n  ' % self._module )
            self._ofile.write(",\n    ".join(params))
            self._ofile.write('\n  )(\n')
        else:
            self._ofile.write('module %s (\n' % self._module )

        self._ofile.write(", \n  ".join([f[2] for f in port_list]))
        self._ofile.write(');\n\n')

        commenter = textwrap.TextWrapper(width=(self._max_column-52))
        sep = "\n" + " " * 46 + "// "

        max_len = max([len(i[2]) for i in port_list]) + 2
        fmt_string = "%%-6s %%-7s %-%ds // %s\n" % max_len

        for data in port_list:
            comment = sep.join(commenter.wrap(data[3]))
            self._ofile.write(fmt_string % (data[0], data[1], data[2] + ';', comment))

    def err(self, msg):
        print msg

    def _build_port_list(self):
        """
        Returns the port list of the design. We have several fixed
        signals (clock, reset, write strobe, byte enables, address,
        data_in, data_out), along with control signals - parallel
        loads, input control signals, one shot output signals. The
        function returns a list of tuples, with each tuple returning
        a set of four strings:

          ( signal_type, register_bits, signal_name, signal_comment )

        """

        output_list = set()
        reset_set = {}

        addr_width = '[%d:%d]' % (self._addr_width - 1, self._lower_bit)
        data_width = "[%d:0]" % (self._data_width - 1)
        be_width   = "[%d:0]" % ((self._data_width / 8) - 1)

        port_list = [
            ("input", '',         self._clock,        "Input clock"),
            ("input", '',         self._reset,        "Reset"),
            ("input", '',         self._write_strobe, "Write strobe"),
            ("input", '',         self._read_strobe,  "Read strobe"),
            ("input", be_width,   self._byte_enables, "Byte enables"),
            ("input", addr_width, self._addr,         "Address"),
            ("input", data_width, self._data_in,      "Data in")
            ]

        for register in self.__sorted_regs:

            # loop through each bit field, looking for needed ports
            for field in [register.get_bit_field(field_key)
                          for field_key in register.get_bit_field_keys()]:

                # A parallel load requires an input signal
                if self._has_control[field.field_type]:
                    if not field.control_signal:
                        self.err("No parallel load signal specified for %s:%s" % (register.register_name, field.field_name))
                    parallel_load_port(field, port_list, output_list)

                # If the bit is controlled by an input value, we
                # need a signal
                if field.input_signal and self._has_input[field.field_type]:
                    input_signal_port(field, port_list, output_list)

                # Output oneshots require a signal
                if self._has_oneshot[field.field_type]:
                    if not field.output_signal:
                        self.err("Empty output signal for %s:%s" % (register.register_name, field.field_name))
                    port_list.append(('output', "",
                                      oneshot_name(field.output_signal),
                                      "one shot"))

                # As do output enables
                if field.use_output_enable:
                    port_list.append(('output', get_width(field),
                                      field.output_signal,
                                      field.description))

                if field.reset_type == BitField.RESET_INPUT:
                    add_reset_input(reset_set, field)

        port_list.append(("output", '[%d:0]' % (self._data_width - 1),
                          self._data_out, "Data out"))
        port_list.append(("output reg", '', self._dbase.acknowledge_name, "Acknowledge"))

        for key in reset_set:
            item = reset_set[key]
            if item[1] == item[2]:
                port_list.append((item[0], "", key, item[3]))
            else:
                port_list.append((item[0], "[%d:%d]" %
                                  (item[1], item[2]), key, item[3]))

        return port_list

    def _write_locals(self):
        """
        Writes the local wire and register declarations needed. These are
        internal values representing the registers. If the value is a
        constant, then a wire statement is used. If the value can change,
        then a reg statement is used. If a register has a oneshot associated
        with it, then a reg statement is generated for the oneshot generator.
        """
        local_regs = []
        local_wires = []

        for register in self.__sorted_regs:

            addr = register.address

            for field in [register.get_bit_field(k)
                          for k in register.get_bit_field_keys()]:

                sindex = get_width(field)
                base = get_base_signal(addr, field)

                val = "wire %-10s %s;" % (sindex, base)
                local_regs.append(val)

                if self._has_oneshot[field.field_type]:
                    val = "wire %-10s %s;" % ("", oneshot_name(base))
                    local_regs.append(val)

        if local_regs:
            self._ofile.write('\n// Register Declarations\n\n')
            self._ofile.write("\n".join(local_regs))
        self._ofile.write("\nreg [%d:0]      mux_%s;\n" % (self._data_width-1,
                                                           self._data_out.lower()))

        if local_wires:
            self._ofile.write('\n// Wire Declarations (Constants)\n\n')
            self._ofile.write("\n".join(local_wires))

    def _write_address_selects(self):
        """
        Writes the address select lines
        """
        self._ofile.write('\n\n// Address Selects\n\n')

        for address in sorted(self._word_fields.keys()):
            width = self._addr_width - self._lower_bit
            self._ofile.write("wire %s = %s & (%s == %s);\n" % (
                write_strobe(address), self._write_strobe, self._addr,
                bin(address >> self._lower_bit, width)))

    def _write_output_assignments(self):
        """
        Writes the output assignments
        """
        self._ofile.write('\n// Output Assignments\n\n')

        max_len = 0

        for register in self.__sorted_regs:
            for field_key in register.get_bit_field_keys():
                field = register.get_bit_field(field_key)
                if self._has_oneshot[field.field_type]:
                    max_len = max(max_len, len(oneshot_name(field.output_signal)))
                if not field.use_output_enable:
                    continue
                max_len = max(max_len, len(field.output_signal))

        fmt_string = "assign %%-%ds = %%s;\n" % max_len

        for register in self.__sorted_regs:
            address = register.address
            for field_key in register.get_bit_field_keys():
                field = register.get_bit_field(field_key)
                if self._has_oneshot[field.field_type]:
                    self._ofile.write(fmt_string  % (
                        oneshot_name(field.output_signal),
                        oneshot_name(get_base_signal(address, field))))
                if not field.use_output_enable:
                    continue

                self._ofile.write(fmt_string % (
                    field.output_signal, get_base_signal(address, field)))

        fmt_string = "assign %%-%ds = mux_%%s;\n" % max_len
        self._ofile.write(fmt_string % (self._data_out,
                                        self._data_out.lower()))
        self._ofile.write("\n")

    def _write_register_rtl_code(self):
        """
        Sorts the register keys, interates of the corresponding registers,
        filtering out the registers that should not have associated code,
        and calls write_register to write the RTL code.
        """
        for reg in self.__sorted_regs:
            for field in [reg.get_bit_field(k) for k in reg.get_bit_field_keys()]:
                self._write_field(reg, field)

    def _write_field(self, reg, field):
        """
        Writes the register range that is specified
        """
        base_signal = get_base_signal(reg.address, field)
        self._write_field_comment(reg.register_name, reg.address, field, field.start_position,
                                  field.stop_position)
        func = self._field_type_map.get(field.field_type, self._register_normal)
        func(reg.address, field)

    def _write_field_comment(self, reg_name, address, field, start, stop):
        """
        Writes the comment for a bit field
        """
        mlen = 11

        self._ofile.write("/*%s\n" % self.__comment_line)
        self._ofile.write(' * %s : %s\n' % ('Field'.ljust(mlen),
                                             field.field_name))
        self._ofile.write(' * %s : %s\n' % ('Type'.ljust(mlen),
                                             self._type_descr[field.field_type]))

        if  field.width == 1:
            self._ofile.write(' * %s : %d\n' % ('Bit'.ljust(mlen), stop))
        else:
            self._ofile.write(' * %s : %d:%d\n' %
                             ('Bits'.ljust(mlen), stop, start))
        self._ofile.write(' * %s : %s\n' % ('Register'.ljust(mlen), reg_name))
        self._ofile.write(' * %s : %08x\n' % ('Address'.ljust(mlen), address))
        if field.reset_type == BitField.RESET_NUMERIC:
            self._ofile.write(' * %s : %d\'h%x\n' %
                              ('Reset Value'.ljust(mlen), field.width,
                               field.reset_value))
        elif field.reset_type == BitField.RESET_PARAMETER:
            self._ofile.write(' * %s : %d\'h%x\n' %
                              ('Reset Value'.ljust(mlen), field.width,
                               field.reset_value))
        else:
            self._ofile.write(' * %s : %s\n' %
                              ('Reset Value'.ljust(mlen), field.reset_input))

        comment = field.description
        if comment:
            fmt = comment.replace(u'\2013', '-')
            fmt = textwrap.TextWrapper(width=self._max_column-8,
                                       initial_indent=" * ",
                                       subsequent_indent=" * ")
            self._ofile.write(' *\n')
            self._ofile.write("\n".join(fmt.wrap(comment)))
            self._ofile.write('\n')

        self._ofile.write(' *%s' % self.__comment_line)
        self._ofile.write('\n */\n')

    def _define_outputs(self):
        """
        Writes the output declarations
        """
        self._ofile.write('/*%s\n' % self.__comment_line)
        self._ofile.write(' *\n')
        self._ofile.write(' * Register Read Output Assignments\n')
        self._ofile.write(' *\n')
        self._ofile.write(' *%s\n' % self.__comment_line)
        self._ofile.write(' */\n\n')

        keys = sorted(self._word_fields.keys())
        for key in keys:
            current_pos = self._data_width - 1
            comma = False
            upper = self._data_width - 1
            self._ofile.write("wire [%d:0] r%02x = {" % (upper, key))

            for field_info in sorted(self._word_fields[key],
                                     reverse=True,
                                     cmp=lambda x, y: cmp(x[2], y[2])):
                if comma:
                    self._ofile.write(",")
                else:
                    comma = True

                stop = field_info[2] % self._data_width
                start = field_info[1] % self._data_width

                if stop != current_pos:
                    self._ofile.write("\n                  ")
                    self._ofile.write("%d'b0," % (current_pos - stop))
                    current_pos = stop - 1

                name_info = get_signal_info(field_info[-1].address,
                                            field_info[0],
                                            field_info[1],
                                            field_info[2])
                self._ofile.write("\n                  ")
                self._ofile.write("%s" % (name_info[1]))
                current_pos = start  - 1

            if current_pos != -1:
                self._ofile.write(",\n                  ")
                self._ofile.write("%d'b0" % (current_pos + 1))
            self._ofile.write("\n                  };\n")

        self._write_output_mux(keys, self._addr,
                               self._addr_width, self._data_out)

    def _write_acknowledge(self):
        self._ofile.write("\nreg prev_write, prev_read;\n\n")
        self._ofile.write('\nalways @(posedge %s or %s) begin\n' %
                          (self._clock, self._reset_edge))
        self._ofile.write('  if (%s) begin\n' % self._reset_condition)
        self._ofile.write("     prev_write <= 1'b0;\n")
        self._ofile.write("     prev_read  <= 1'b0;\n")
        self._ofile.write("     %s <= 1'b0;\n" % self._dbase.acknowledge_name);
        self._ofile.write('  end else begin\n')
        self._ofile.write("     prev_write <= %s;\n" % self._dbase.write_strobe_name)
        self._ofile.write("     prev_read  <= %s;\n" % self._dbase.read_strobe_name)
        self._ofile.write("     %s <= (~prev_write & %s) | (~prev_read & %s);\n" %
                          (self._dbase.acknowledge_name,
                           self._dbase.write_strobe_name,
                           self._dbase.read_strobe_name));
        self._ofile.write('  end\nend\n\n')

    def _write_output_mux(self, out_address, addr_bus, addr_width, data_out):
        """
        Writes the output mux that controls the selection of the output data
        """
        
        self._ofile.write('\nalways @(posedge %s or %s) begin\n' %
                          (self._clock, self._reset_edge))
        self._ofile.write('  if (%s) begin\n' % self._reset_condition)
        self._ofile.write("     mux_%s <= %d'h0;\n" % (data_out.lower(), self._data_width))
        self._ofile.write('  end else begin\n')

        self._ofile.write("     if (%s) begin\n" % self._dbase.read_strobe_name)
        self._ofile.write('        case (%s)\n' % addr_bus)
        for addr in out_address:
            width = addr_width - self._lower_bit
            self._ofile.write('         %s: mux_%s <= r%02x;\n' %
                              (bin(addr >> self._lower_bit, width),
                               data_out.lower(), addr))
        self._ofile.write('       default: mux_%s <= %d\'h0;\n' %
                          (data_out.lower(), self._data_width))
        self._ofile.write('       endcase\n')
        self._ofile.write('     end else begin\n')
        self._ofile.write('        mux_%s <= %d\'h0;\n' % (data_out.lower(), self._data_width))
        self._ofile.write('     end')
        self._ofile.write('  end')
        self._ofile.write('end\n\n')

    def _byte_enable_list(self, start, stop):
        """
        Writes the byte enables associated with the start/stop range,
        Uses list operations to find each byte enable used, which is
        each byte position between the start and the stop bit positions.

        For simplicity, we check the entire range, from 0 to the data
        bus with, in 8 bit increments.

        Then each used bit position in the list is joined together in a
        logical or function. Producing something in the form of:

           (byte_enable[0])

        or

           (byte_enable[0]|byte_enable[1]|byte_enable[2])

        """
        name = [self._byte_enable(int(x / 8))
                for x in range(0, self._data_width-1, 8)
                if start <= x + 7 and stop >= x]

        return "(%s)" % '|'.join(name)

    def _write_trailer(self):
        """
        Closes the module. In Verilog, this is done with the endmodule
        statement. A comment is added to indicate which module is being
        closed.
        """
        self._ofile.write('endmodule // %s\n' % self._module)


class Verilog2001(Verilog):
    """
    Provides a SystemVerilog interface, derived from the Verilog class.
    Changes include:

    * Verilog 2001 style input/output declarations
    * Use of always_ff and always_comb instead of the usual always
    * Uses the endmodule : name syntax
    """

    def _write_module_header(self):
        """
        Writes the module header using Verilog 2001 constructs
        """
        plist = []
        blist = []
        for register in [self._dbase.get_register(key)
                         for key in self._dbase.get_keys()]:
            for field in [register.get_bit_field(key)
                          for key in register.get_bit_field_keys()]:
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.stop_position == field.start_position:
                        blist.append((field.reset_parameter,
                                      field.stop_position - field.start_position + 1,
                                      field.reset_value))
                    else:
                        plist.append((field.stop_position,
                                      field.start_position,
                                      field.reset_parameter,
                                      field.stop_position - field.start_position + 1,
                                      field.reset_value))

        if plist or blist:
            params = ["parameter %s = %d'h%x" % item for item in blist] + \
                     ["parameter [%d:%d] %s = %d'h%x" % item for item in plist]
            self._ofile.write('module %s #(\n  ' % self._module )
            self._ofile.write(",\n    ".join(params))
            self._ofile.write('\n  )(\n')
        else:
            self._ofile.write('module %s (\n' % self._module )

        csep = "\n" + " " * 48 + "// "
        sep = ", "
        ports = self._build_port_list()
        cnt = 0
        total = len(ports)
        commenter = textwrap.TextWrapper(width=self._max_column-52)

        max_len = max([len(i[2]) for i in ports]) + 2
        fmt_string = "  %%-10s %%-7s %%-%ds // %%s\n" % max_len
        
        for data in ports:
            comment = csep.join(commenter.wrap(data[3]))
            self._ofile.write(fmt_string % (data[0], data[1], data[2] + sep, comment))
            cnt += 1
            if cnt == total-1:
                sep = ""
        self._ofile.write(');\n')

    def _write_output_mux(self, out_address, addr_bus, addr_width, data_out):
        """
        Writes the output mux that controls the selection of the output data
        """
        self._ofile.write('\nalways @(posedge %s or %s) begin\n' % (
            self._clock, self._reset_edge))
        self._ofile.write('   if (%s) begin\n' % self._reset_condition)
        self._ofile.write("      mux_%s <= %d'h0;\n" % (data_out.lower(), self._data_width))
        self._ofile.write('   end else begin\n')
        
        self._ofile.write("      if (%s) begin\n" % self._dbase.read_strobe_name)
        self._ofile.write('         case (%s)\n' % addr_bus)
        for addr in out_address:
            width = addr_width - self._lower_bit
            self._ofile.write('            %s: mux_%s <= r%02x;\n' %
                              (bin(addr >> self._lower_bit, width),
                               data_out.lower(), addr))
        self._ofile.write('            default: mux_%s <= %d\'h0;\n' %
                          (data_out.lower(), self._data_width))
        self._ofile.write('         endcase\n')
        self._ofile.write('      end else begin\n')
        self._ofile.write('         mux_%s <= %d\'h0;\n' % (data_out.lower(), self._data_width))
        self._ofile.write('      end\n')
        self._ofile.write('   end\n')
        self._ofile.write('end\n\n')

class SystemVerilog(Verilog2001):
    """
    Provides a SystemVerilog interface, derived from the Verilog class.
    Changes include:

    * Verilog 2001 style input/output declarations
    * Use of always_ff and always_comb instead of the usual always
    * Uses the endmodule : name syntax
    """

    ALWAYS_FF = 'always_ff'

    def _write_trailer(self):
        """
        Writes the endmodule statement using the : name syntax instead
        of writing a comment.
        """
        self._ofile.write('endmodule : %s\n' % self._module)

    def _write_output_mux(self, out_address, addr_bus, addr_width, data_out):
        """
        Writes the always_comb syntax, instead of the always @(xxx) syntax
        """
        self._ofile.write('\nalways_ff @(posedge %s or %s) begin\n' % (
            self._clock, self._reset_edge))
        self._ofile.write('   if (%s) begin\n' % self._reset_condition)
        self._ofile.write("      mux_%s <= %d'h0;\n" % (data_out.lower(), self._data_width))
        self._ofile.write('   end else begin\n')

        self._ofile.write("     if (%s) begin\n" % self._dbase.read_strobe_name)
        self._ofile.write('        case (%s)\n' % addr_bus)
        for addr in out_address:
            width = addr_width - self._lower_bit
            self._ofile.write('           %s: mux_%s <= r%02x;\n' %
                              (bin(addr >> self._lower_bit, width),
                               data_out.lower(), addr))
            self._ofile.write('         default: mux_%s <= %d\'h0;\n' %
                              (data_out.lower(), self._data_width))
        self._ofile.write('         endcase\n')
        self._ofile.write('      end else begin\n')
        self._ofile.write('         mux_%s <= %d\'h0;\n' % (data_out.lower(), self._data_width))
        self._ofile.write('      end')
        self._ofile.write('   end')
        self._ofile.write('end\n\n')
