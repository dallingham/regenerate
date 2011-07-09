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

from regenerate.db import BitField
from writer_base import WriterBase

#
# Constants
#
MASK_VALUES = [0x01, 0x03, 0x07, 0x0f, 0x1f, 0x3f, 0x7f, 0xff]
LOWER_BIT = {128: 4, 64 : 3, 32 : 2, 16 : 1 , 8: 0}
BUS_ELEMENT = re.compile("([\w_]+)\[(\d+)\]")
SINGLE_BIT = re.compile("\s*(\S+)\[(\d+)\]")
MULTI_BIT = re.compile("\s*(\S+)\[(\d+):(\d+)\]")


def bin(val, width):
    """
    Converts the integer value to a Verilog value
    """
    return "%d'h%x" % (width, val)


def calc_init_value(field, start, stop):
    """
    Calculates the initial value of a field.
    """
    default_value = field.reset_value << field.start_position

    width_mask = MASK_VALUES[stop - start]
    return_val = (default_value >> start) & width_mask
    return return_val


def get_width(field, start=-1, stop=-1):
    """
    Returns with width if the bit range is greater than one.
    """
    if stop == -1:
        start = field.start_position
        stop = field.stop_position

    if field.width == 1:
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
    return name + "_1s"


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
    return "r%02x_%s" % (address, field.output_signal)


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


def split_bus_values(offset, width, bit_range):
    """
    Returns the start and stop values, breaking at byte values.
    """
    bit_values = []

    lower = bit_range.start_position
    stop = bit_range.stop_position
    for val in range(offset, (width / 8) + 2):
        rng = range(val * 8, (val + 1) * 8)
        if lower + (offset * 8) in rng or stop + (offset * 8) in rng:
            if lower > stop:
                break
            next_top = lower + 7 - (lower % 8)
            bit_values.append((lower, min(stop, next_top), val))
            lower = next_top + 1
    return bit_values


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
        reset_set[reset] = ('input',
                            max(stop, values[1]),
                            min(start, values[2]),
                            "%s, %s" % (values[3], field.field_name)
                            )
    else:
        reset_set[reset] = ('input',
                            stop,
                            start,
                            "reset value for %s" % field.field_name
                            )


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
#       self.__assertions = self._dbase.enable_assertions
#       self.__ovm = self._dbase.enable_ovm_messaging

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

        self._byte_fields = self.__generate_group_list(8)
        self._word_fields = self.__generate_group_list(self._data_width)

    def _byte_info(self, field, register, lower, size):
        """
        Returns the basic information from a field, broken out into byte
        quantities
        """
        width = self._data_width
        start = max(field.start_position, lower)
        stop = min(field.stop_position, lower + size - 1)

        address = register.address + (int(lower / width) * (width / 8))

        return (field, start, stop, address, register)

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

    def __terminate_line(self, need_comma):
        """
        Terminates the with a comma if needed.
        """
        if not need_comma:
            self._ofile.write(', ')
        else:
            need_comma = False
        self._ofile.write('\n                    ')
        return need_comma

    def __find_registers_in_range(self, current, rlimit):
        """
        Finds the registers between the starting address and the
        starting address plus the rlimit
        """
        rlist = []
        for i in range(0, rlimit):
            reg = self._dbase.get_register(current + i)
            if reg and reg.do_not_generate_code:
                rlist = [reg] + rlist
        return rlist

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
        if self._coverage:
            self._write_cover_groups()
        self._define_outputs()
#        if self.__assertions:
#            self._write_assertions()
        self._write_trailer()
        self._ofile.close()

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

        for data in port_list:
            comment = sep.join(commenter.wrap(data[3]))
            self._ofile.write('%-6s %-7s %-30s // %s\n' %
                             (data[0], data[1], data[2] + ';', comment))

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
            ("input", '', self._clock, "Input clock"),
            ("input", '', self._reset, "Reset"),
            ("input", '', self._write_strobe, "Write strobe"),
            ("input", be_width, self._byte_enables, "Byte enables"),
            ("input", addr_width, self._addr, "Address"),
            ("input", data_width, self._data_in, "Data in")
            ]

        if self._dbase.sync_read:
            port_list.append(("input", '', self._dbase.read_strobe_name, "Read strobe"))

        for register in self.__sorted_regs:

            # loop through each bit field, looking for needed ports
            for field in [register.get_bit_field(field_key)
                          for field_key in register.get_bit_field_keys()]:

                # A parallel load requires an input signal
                if field.input_function == BitField.FUNC_PARALLEL:
                    parallel_load_port(field, port_list, output_list)

                # If the bit is controlled by an input value, we
                # need a signal
                if (field.input_signal and
                    field.input_function != BitField.FUNC_ASSIGNMENT):
                    input_signal_port(field, port_list, output_list)

                # Output oneshots require a signal
                if field.one_shot_type != BitField.ONE_SHOT_NONE:
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

                if field.is_constant():
                    val = "wire %-8s %s;" % (sindex, base)
                else:
                    val = "reg %-9s %s;" % (sindex, base)
                local_regs.append(val)

                if field.one_shot_type != BitField.ONE_SHOT_NONE:
                    val = "reg %-9s %s;" % ("", oneshot_name(base))
                    local_regs.append(val)

        if local_regs:
            self._ofile.write('\n// Register Declarations\n\n')
            self._ofile.write("\n".join(local_regs))
        self._ofile.write("\nreg [%d:0]    mux_%s;\n" % (self._data_width-1,
                                                         self._data_out))

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

        for register in self.__sorted_regs:

            address = register.address

            for field_key in register.get_bit_field_keys():
                field = register.get_bit_field(field_key)
                if field.one_shot_type != BitField.ONE_SHOT_NONE:
                    self._ofile.write("assign %-20s = %s;\n" % (
                        oneshot_name(field.output_signal),
                        oneshot_name(get_base_signal(address, field))))
                if not field.use_output_enable:
                    continue

                self._ofile.write("assign %-20s = %s;\n" % (
                    field.output_signal, get_base_signal(address, field)))

        self._ofile.write("assign %-20s = mux_%s;\n" % (self._data_out,
                                                        self._data_out))
        self._ofile.write("\n")

    def _write_register_rtl_code(self):
        """
        Sorts the register keys, interates of the corresponding registers,
        filtering out the registers that should not have associated code,
        and calls write_register to write the RTL code.
        """

        one_shots = set()

        for key in sorted(self._byte_fields.keys()):
            for item in self._byte_fields[key]:

                (field, start, stop, reg_address, reg) = item
                reg_name = reg.register_name

            # if a oneshot is required, write the code to generate a one shot
                if field.one_shot_type != BitField.ONE_SHOT_NONE:
                    if field not in one_shots:
                        self.write_one_shot(reg_name, reg_address, field)
                        one_shots.add(field)

            # if the register field is a constant, write the constant value
            # otherwise, write the field information

                if field.is_constant():
                    self._write_constant(reg_name, reg_address, field,
                                         start, stop, reg.address)
                else:
                    self._write_field(reg_name, reg_address,
                                      field, start, stop, reg.address)

    def _write_field(self, reg_name, address, field, start, stop, regaddr):
        """
        Writes the register range that is specified
        """
        base_signal = get_base_signal(regaddr, field)
        self._write_field_comment(reg_name, address, field, start, stop)

        init_value = calc_init_value(field, start, stop)

        if field.reset_type == BitField.RESET_PARAMETER:
            if stop == start:
                rvalue = field.reset_parameter
            else:
                rvalue = "%s%s" % (field.reset_parameter,
                                   get_width(field, start, stop))
        elif field.reset_type == BitField.RESET_INPUT:
            if stop == start:
                rvalue = field.reset_input
            else:
                match = MULTI_BIT.match(field.reset_input)
                if match:
                    rvalue = field.reset_input
                else:
                    rvalue = "%s%s" % (field.reset_input,
                                       get_width(field, start, stop))
        else:
            rvalue = bin(init_value, stop - start + 1)

        self._start_always_ff(
            base_signal, rvalue, start, stop, field.width > 1)

        if field.input_function == BitField.FUNC_PARALLEL:
            self._write_parallel_load(address, field, start, stop, regaddr)
        elif field.input_function == BitField.FUNC_CLEAR_BITS:
            self._write_clear_bits(address, field, start, stop, regaddr)
        elif field.input_function == BitField.FUNC_SET_BITS:
            self._write_set_bits(address, field, start, stop, regaddr)
        else:
            self._write_normal_bits(address, field, start, stop, regaddr)

        self._end_always_ff()

    def _write_be_lines(self, offset, signal, bit_range, start, stop):
        """
        Writes the byte enable control lines
        """
        if bit_range.field_type == BitField.WRITE_1_TO_CLEAR:
            self._write_be_lines_w1c(
                offset, signal, bit_range, start, stop, int(start / 8))
        elif bit_range.field_type == BitField.WRITE_1_TO_SET:
            self._write_be_lines_w1s(
                offset, signal, bit_range, start, int(start / 8))
        else:
            self._write_be_lines_normal(
                offset, signal, bit_range, start, stop, int(start / 8))

    def _byte_enable(self, val):
        """
        Returns the active byte enable associated with the bit position
        """
        val = val % (self._data_width / 8)
        return '%s[%d]' % (self.__be_condition, val)

    def _write_be_lines_normal(self, offset, signal, bit_range,
                               start, stop, byte_pos):
        """
        Writes the byte enable lines for a normal access register
        """
        width = bit_range.stop_position - bit_range.start_position
        be_name = self._byte_enable(byte_pos)

        if start >= self._data_width:
            bus_start = (start - self._data_width) + (offset * 8)
            bus_stop = (stop - self._data_width) + (offset * 8)
        else:
            bus_start = start + (offset * 8)
            bus_stop = stop  + (offset * 8)

        if width == 0:
            sname = signal
            dname = "%s[%d]" % (self._data_in, bus_start)
        elif start == stop:
            sname = "%s[%d]" % (signal, start)
            dname = "%s[%d]" % (self._data_in, bus_start)
        else:
            sname = "%s[%d:%d]" % (signal, stop, start)
            dname = "%s[%d:%d]" % (self._data_in, bus_stop, bus_start)

        self._ofile.write('      %s <= ' % sname)
        self._ofile.write('(%s) ' % be_name)
        self._ofile.write('? %s : ' % dname)
        self._ofile.write('%s;\n' % sname)

    def _write_be_lines_w1s(self, offset, signal, bit_range, lower, val):
        """
        Writes the byte enables for a write-one-to-set register
        """
        start = bit_range.start_position
        stop = bit_range.stop_position
        if lower == stop:
            if start == stop:
                self._ofile.write('      %s <=' % signal)
            else:
                self._ofile.write('      %s[%d] <=' % (signal, lower))

            self._ofile.write(' %s ' % self._byte_enable(val))
            self._ofile.write('? (%s | %s[%d]) :' %
                             (signal, self._data_in, lower + offset * 8))

            if start == stop:
                self._ofile.write(' %s;\n' % signal)
            else:
                self._ofile.write(' %s[%d];\n' % (signal, lower))
        else:
            sname = "%s[%d:%d]" % (signal, stop, lower)

            self._ofile.write('      %s <= ' % sname)
            self._ofile.write('(%s) ' % self._byte_enable(val))
            self._ofile.write('%s;\n' % sname)

    def _write_be_lines_w1c(self, offset, signal, bit_range, lower,
                            next_top, val):
        """
        Writes the byte enable lines for a write-one-to-clear register
        """
        stop = bit_range.stop_position
        start = bit_range.start_position
        input_sig = bit_range.input_signal

        if lower == stop:
            if start == stop:
                self._ofile.write('      %s <=' % signal)
            else:
                self._ofile.write('      %s[%d] <=' % (signal, lower))

            self._ofile.write(' (%s ' % self._byte_enable(val))
            self._ofile.write('& %s[%d]) ? 1\'b0 :' %
                             (self._data_in,
                              (lower + offset * 8) % self._data_width))

            if start == stop:
                if input_sig != "":
                    self._ofile.write(' (%s | %s);\n' % (signal, input_sig))
                else:
                    self._ofile.write(' %s;\n' % signal)
            else:
                self._ofile.write(' %s[%d];\n' % (signal,
                                                  lower % self._data_width))
        else:
            bitrng = "[%d:%d]" % (next_top, lower)
            sname = "%s%s" % (signal, bitrng)
            ival = "%s%s" % (input_sig, bitrng)
            dname = "%s[%d:%d]" % (self._data_in,
                                   next_top + (8 * offset) % self._data_width,
                                   lower + (8 * offset) % self._data_width)

            self._ofile.write('      %s <= ' % sname)
            self._ofile.write(' (%s) ' % self._byte_enable(val))
            self._ofile.write('? ((%s & ~%s)) | %s :' % (sname, dname, ival))
            if input_sig != "":
                self._ofile.write('(%s|%s);\n' % (sname, ival))
            else:
                self._ofile.write('%s;\n' % sname)

    def _write_field_comment(self, reg_name, address, field, start, stop):
        """
        Writes the comment for a bit field
        """
        mlen = 11

        self._ofile.write("/*%s\n" % self.__comment_line)
        self._ofile.write(' * %s : %s\n' % ('Field'.ljust(mlen),
                                             field.field_name))

        if  field.width == 1:
            self._ofile.write(' * %s : %d\n' % ('Bit'.ljust(mlen), stop))
        else:
            self._ofile.write(' * %s : %d:%d\n' %
                             ('Bits'.ljust(mlen), stop, start))
        self._ofile.write(' * %s : %s\n' % ('Register'.ljust(mlen), reg_name))
        self._ofile.write(' * %s : %08x\n' % ('Address'.ljust(mlen), address))
        if field.reset_type == BitField.RESET_INPUT:
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

    def _write_parallel_load(self, address, field, start, stop, regaddr):
        """
        Writes the control values for a bit field with a parallel load control
        """

        (base_signal, signal, offset) = get_signal_info(regaddr, field)

        if field.field_type == BitField.READ_ONLY:
            index = get_width(field, start, stop)
            self._ofile.write('      %s%s <= (%s) ? %s%s : %s%s;\n' % (
                    base_signal, index,
                    field.control_signal,
                    field.input_signal, index,
                    base_signal, index))
        else:
            self._ofile.write('    if (%s) begin\n' % write_strobe(address))
            self._write_be_lines(offset, base_signal, field, start, stop)
            self._ofile.write('    end else begin\n')
            index = get_width(field, start, stop)
            self._ofile.write('      %s%s <= (%s) ? %s%s : %s%s;\n' % (
                    base_signal, index,
                    field.control_signal,
                    field.input_signal, index,
                    base_signal, index))
            self._ofile.write('    end\n')

    def _write_clear_bits(self, address, field, start, stop, regaddr):
        """
        Writes the control values for a bit field that has a synchronous
        clear signal.
        """
        (base_signal, signal, offset) = get_signal_info(regaddr, field)
        index = get_width(field, start, stop)

        self._ofile.write('    if (%s) begin\n' % (write_strobe(address)))
        self._write_be_lines(offset, base_signal, field, start, stop)
        self._ofile.write('    end else begin\n')
        self._ofile.write('      %s%s <= ~(%s%s) & %s%s;\n' %
                          (signal, index,
                           field.input_signal, index,
                           signal, index))
        self._ofile.write('    end\n')

    def _write_set_bits(self, address, field, start, stop, regaddr):
        """
        Writes the control values for a bit field that has a synchronous
        set signal
        """
        (base, signal, offset) = get_signal_info(regaddr, field, start, stop)
        index = get_width(field, start, stop)

        self._ofile.write('    if (%s) begin\n' % write_strobe(address))
        self._write_be_lines(offset, base, field, start, stop)
        self._ofile.write('    end else begin\n')
        self._ofile.write('      %s <= %s%s | %s;\n' %
                           (signal, field.input_signal, index, signal))
        self._ofile.write('    end\n')

    def _write_normal_bits(self, address, field, start, stop, regaddr):
        """
        Writes the control values for a bit field that has a normal assignment
        """
        (base, signal, offset) = get_signal_info(regaddr, field, start, stop)

        self._ofile.write('    if (%s) begin\n' % write_strobe(address))
        self._write_be_lines(offset, base, field, start, stop)
        self._ofile.write('    end else begin\n')
        self._ofile.write('      %s <= %s;\n' % (signal, signal))
        self._ofile.write('    end\n')

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
            upper = self._data_width-1
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

    def _write_output_mux(self, out_address, addr_bus, addr_width, data_out):
        """
        Writes the output mux that controls the selection of the output data
        """
        if self._dbase.sync_read:
            self._ofile.write('\nalways @(posedge %s or %s) begin\n' % (
                self._clock, self._reset_edge, base_signal, bits))
            self._ofile.write('  if (%s) begin\n' % self._reset_condition)
            self._ofile.write("     mux_%s <= %d'h0;\n" % (data_out, self._data_width))
            self._ofile.write('  end else begin\n')

            self._ofile.write("     if (%s) begin\n" % self._dbase.read_strobe_name)
            self._ofile.write('        case (%s)\n' % addr_bus)
            for addr in out_address:
                width = addr_width - self._lower_bit
                self._ofile.write('         %s: mux_%s <= r%02x;\n' %
                                  (bin(addr >> self._lower_bit, width),
                                   data_out, addr))
            self._ofile.write('       default: mux_%s <= %d\'h0;\n' %
                              (data_out, self._data_width))
            self._ofile.write('       endcase\n')
            self._ofile.write('     end else begin\n')
            self._ofile.write('        mux_%s <= %d\'h0;\n' % (data_out, self._data_width))
            self._ofile.write('     end')
            self._ofile.write('  end')
            self._ofile.write('end\n\n')
        else:
            self._ofile.write('\nalways @(%s\n' % addr_bus)
            for addr in out_address:
                self._ofile.write('         or r%02x\n' % (addr))
            self._ofile.write('         ) begin\n')
            self._ofile.write('  case (%s)\n' % addr_bus)
            for addr in out_address:
                width = addr_width - self._lower_bit
                self._ofile.write('    %s: mux_%s = r%02x;\n' %
                                  (bin(addr >> self._lower_bit, width),
                                   data_out, addr))
            self._ofile.write('    default: mux_%s = %d\'h0;\n' %
                              (data_out, self._data_width))
            self._ofile.write('  endcase\n')
            self._ofile.write('end\n\n')

    def _write_constant(self, reg_name, address, field, start, stop, regaddr):
        """
        Assigns a constant value to the wire. If no input signal is specified,
        then we assign the reset value. If an input signal is specified, we
        assign the input signal to the field.
        """

        # write the comment for the block
        self._write_field_comment(reg_name, address, field, start, stop)

        signal = get_base_signal(regaddr, field)

        if field.width > 1:
            signal = "%s[%d:%d]" % (signal, stop, start)

        if field.reset_type == BitField.RESET_NUMERIC:
            if field.input_signal == "":
                value = bin(field.reset_value, (stop + 1) - start)
            elif field.width > 1:
                value = "%s[%d:%d]" % (field.input_signal, stop, start)
            else:
                value = field.input_signal
        elif field.reset_type == BitField.RESET_PARAMETER:
            if field.width > 1:
                value = "%s[%d:%d]" % (field.reset_parameter, stop, start)
            else:
                value = field.reset_parameter
        else:
            value = field.reset_input

        self._ofile.write('assign %s = %s;\n\n' % (signal, value))

    def _start_always_ff(self, base_signal, reset_value, start, stop, is_bus):
        """
        Starts the always block, which consists of delecting the positive
        edge of the clock or the active edge of reset.
        """
        if start == stop:
            if is_bus:
                bits = "_%d" % start
                rng = "[%d]" % start
            else:
                bits = ""
                rng = ""
        else:
            bits = "_%d_%d" % (stop, start)
            rng = "[%d:%d]" % (stop, start)

        self._ofile.write('%s @(posedge %s or %s) begin : b_%s%s\n' % (
                self.ALWAYS_FF, self._clock, self._reset_edge,
                base_signal, bits))
        self._ofile.write('  if (%s) begin\n' % self._reset_condition)
        self._ofile.write('    %s%s <= %s;\n' % (base_signal, rng,
                                                 reset_value))
        self._ofile.write('  end else begin\n')

    def _end_always_ff(self):
        """
        Ends the always block by closing the always block and the if statement.
        """
        self._ofile.write('  end\n')
        self._ofile.write('end\n\n')

    def write_one_shot(self, reg_name, address, field):
        """
        Writes the one shot handling routine
        """

        start = field.start_position
        stop = field.stop_position

        # write the comment header
        self._write_field_comment(reg_name, address, field, start, stop)

        base_signal = get_base_signal(address, field)

        # build signals names

        ws_signal = oneshot_name(base_signal)
        ctrl_signal = write_strobe(address)
        ws_be = self._byte_enable_list(start, stop)
        if start == stop:
            insignal = "%s[%d]" % (self._data_in, stop)
        else:
            insignal = "(|%s[%d:%d])" % (self._data_in, stop, start)

        mode = field.one_shot_type

        # start the always block
        self._start_always_ff(oneshot_name(base_signal), "1'b0", 0, 0, False)
        self._ofile.write('    %s <= %s & %s' %
                           (ws_signal, ctrl_signal, ws_be))

        if mode == BitField.ONE_SHOT_ANY:
            self._ofile.write(';\n')
        elif mode == BitField.ONE_SHOT_ONE:
            self._ofile.write(' & %s;\n' % insignal)
        elif mode == BitField.ONE_SHOT_ZERO:
            self._ofile.write(' & ~%s;\n' % insignal)
        elif mode == BitField.ONE_SHOT_TOGGLE:
            if start == stop:
                self._ofile.write(' & (%s[%d] != %s);\n' % (
                        self._data_in, stop, base_signal))
            else:
                self._ofile.write(' & (%s[%d:%d] != %s[%d:%d]);\n' % (
                        self._data_in, stop, start, base_signal, stop, start))
        self._end_always_ff()

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

    def _write_cover_groups(self):
        """
        Writes covergroup information, checking for various test points
        """

        used_cover = set()

        self._ofile.write('`ifdef USE_COVERAGE\n')
        self._ofile.write('//synthesis off\n')

        self._write_address_covergroup()

        self._ofile.write('// Register specific coverage\n\n')

        for address in sorted(self._byte_fields.keys()):
            field_list = [item for item in self._byte_fields[address]
                          if not item[0].is_constant() ]

            if not field_list:
                continue

            field = field_list[0][0]
            self._write_covergroup_head(address, field)

            width = field_list[0][4].width

            if field.field_type == BitField.READ_WRITE:
                used_cover.add(field)
                self._write_normal_cover(address, field,
                                         field.start_position,
                                         field.stop_position)
            elif field.field_type == BitField.WRITE_1_TO_CLEAR:
                used_cover.add(field)
                self._write_cover_rw_w1c(address, field, width)
                if field.input_function == BitField.FUNC_SET_BITS:
                    self._write_cover_rw_set(address, field, width)
            elif field.field_type == BitField.WRITE_1_TO_SET:
                used_cover.add(field)
                self._write_cover_rw_w1s(address, field, width)
#                if field.input_function == BitField.FUNC_SET_BITS:
#                    self._write_cover_rw_set(address, field, width)

            self._write_covergroup_end()

        for reg in self.__sorted_regs:
            for field in [reg.get_bit_field(s)
                          for s in reg.get_bit_field_keys()
                          if reg.get_bit_field(s) in used_cover]:
                basename = get_base_signal(reg.address, field)
                self._ofile.write('cov_%s u_cov_%s = new;\n' %
                                   (basename, basename))


        self._ofile.write('//synthesis on\n\n')
        self._ofile.write('`endif\n')

    def _write_address_covergroup(self):
        """
        Writes the covergroup information for the address lines
        """
        self._ofile.write('\n// Make sure that all possible read '
                           'addresses have at least\n')
        self._ofile.write('// been seen. It does not prove that the '
                           'values were read, but\n')
        self._ofile.write('// if we did not detect it, we know that '
                           'there is no way that\n')
        self._ofile.write('// the register was read.\n\n')

        self._ofile.write('covergroup cov_address @(posedge %s);\n' %
                           self._clock)
        self._ofile.write('  type_option.comment = "Read addresses";\n')
        self._ofile.write('  %s_address_lines : coverpoint %s iff (!%s)\n' % (
                self._module, self._addr, self._write_strobe))
        self._ofile.write('  {\n')

        for address in sorted(self._word_fields.keys()):
            self._ofile.write("  bins r%02x = { %s };\n" % (
                    address,
                    bin(address >> self._lower_bit,
                        self._addr_width - self._lower_bit)))
        self._ofile.write('  }\n')
        self._ofile.write('endgroup\n\n')

    def _write_covergroup_head(self, address, field):
        """
        Write the start of a covergroup statement
        """
        signal_info = get_signal_info(address, field)
        self._ofile.write('covergroup cov_%s @(posedge %s);\n' %
                         (signal_info[0], self._clock))
        self._ofile.write('  type_option.comment = "Coverage for %s";\n' %
                         signal_info[0])
        self._ofile.write('  type_option.strobe = 1;\n')

    def _write_covergroup_end(self):
        """
        End the covergroup statement
        """
        self._ofile.write('endgroup\n\n')

    def _write_normal_cover(self, address, field, start, stop):
        """
        Writes a cover group for read/write bit fields
        """
        (base_signal, signal, offset) = get_signal_info(address, field,
                                                        start, stop)

        if field.values:
            name = "%s_%s" % (self._module, base_signal)
            self._ofile.write('  %s : coverpoint %s\n' % (name, base_signal))
            self._ofile.write('  {\n')
            index = 0
            for value in field.values:
                self._ofile.write("     bins %s%d = { %d'h%s };\n" %
                                  (base_signal, index, (stop - start + 1),
                                   value[0]))
                index += 1
            self._ofile.write('  }\n')
        else:
            name = "%s_%s_%x" % (self._module, base_signal, address)
            self._ofile.write('  %s : coverpoint %s;\n' % (name, signal))

    def _write_cover_rw_set(self, address, field, width):
        """
        Writes a cover group for read/write bit fields that have a set signal
        """
        base_signal = get_base_signal(address, field)
        offset = get_signal_offset(address)
        bit_values = split_bus_values(offset, width, field)

        for (lower, next_top, val) in bit_values:
            for i in range(lower, next_top + 1):
                name = "%s_%s_%d" % (self._module, base_signal, i)
                self._ofile.write('  %s : coverpoint %s[%d]\n' %
                                   (name, base_signal, i))
                self._ofile.write('  {\n')
                self._ofile.write('    bins b%d = (0 => 1);\n' % i)
                self._ofile.write('  }\n')

    def _write_cover_rw_clr(self, address, field, width):
        """
        Writes a cover group for read/write bit fields that have a clear
        signal
        """
        base_signal = get_base_signal(address, field)
        offset = get_signal_offset(address)
        bit_values = split_bus_values(offset, width, field)

        for (lower, next_top, val) in bit_values:
            for i in range(lower, next_top + 1):
                name = "%s_%s_%d" % (self._module, base_signal, i)
                self._ofile.write('  %s : coverpoint %s[%d] {\n' %
                                   (name, base_signal, i))
                self._ofile.write('    bins b%d = (1 => 0);\n' % i)
                self._ofile.write('  }\n')

    def _write_cover_rw_w1c(self, address, field, width):
        """
        Writes a cover group for read/write bit fields that have a write one
        to clear signal
        """
        base_signal = get_base_signal(address, field)
        offset = get_signal_offset(address)
        bit_values = split_bus_values(offset, width, field)

        for (lower, next_top, val) in bit_values:
            for i in range(lower, next_top + 1):
                name = "%s_%s_%d" % (self._module, base_signal, i)
                self._ofile.write('  W1C_%s : coverpoint %s[%d]\n' %
                                   (name, base_signal, i))
                self._ofile.write('  {\n')
                self._ofile.write('    bins b%d = (1 => 0);\n' % i)
                self._ofile.write('  }\n')

    def _write_cover_rw_w1s(self, address, field, width):
        """
        Writes a cover group for read/write bit fields that have a write one
        to clear signal
        """
        base_signal = get_base_signal(address, field)
        offset = get_signal_offset(address)
        bit_values = split_bus_values(offset, width, field)

        for (lower, next_top, val) in bit_values:
            byte_en = self._byte_enable(val)
            for i in range(lower, next_top + 1):
                name = "%s_%s_%d" % (self._module, base_signal, i)
                self._ofile.write('  W1S_%s : coverpoint %s[%d]\n' %
                                   (name, base_signal, i))
                self._ofile.write('  {\n')
                self._ofile.write('    bins b%d = (0 => 1);\n' % i)
                self._ofile.write('  }\n')

    def _write_cover_rw_pl(self, address, field, width):
        """
        Writes a cover group for read/write bit fields that have a parallel
        load signal
        """
        start = field.start_position
        stop = field.stop_position

        base_signal = get_base_signal(address, field)

        if field.values and (stop - start < 8):
            name = "%s_%s" % (self._module, base_signal)
            self._ofile.write('  PL%s : coverpoint %s iff (%s)\n' %
                               (name, base_signal, field.input_signal))
            self._ofile.write('  {\n')
            index = 0
            for value in field.values:
                self._ofile.write("     bins %s%d = { %d'h%s };\n" %
                                   (base_signal, index, (stop - start + 1),
                                    value[0]))
                index += 1
            self._ofile.write('  }\n')
        else:
            offset = get_signal_offset(address)
            bit_values = split_bus_values(offset, width, field)
            for (lower, next_top, val) in bit_values:
                name = "%s_%s_%d" % (self._module, base_signal, val)
                if stop == start:
                    target = base_signal
                elif lower == next_top:
                    target = "%s[%d]" % (base_signal, lower)
                else:
                    target = "%s[%d:%d]" % (base_signal, next_top, lower)
                self._ofile.write('  PL%s : coverpoint %s iff (%s);\n' %
                                   (name, target, field.input_signal))

    def _write_cover_readonly_set(self, address, field):
        """
        Writes a cover group for read-only bit fields
        """
        start = field.start_position
        stop = field.stop_position
        base_signal = get_base_signal(address, field)

        name = "%s_%s" % (self._module, base_signal)
        if field.values:

            self._ofile.write('  ROS%s : coverpoint %s\n' %
                               (name, base_signal))
            self._ofile.write('  {\n')
            index = 0
            for value in field.values:
                upper = stop - start + 1
                self._ofile.write("     bins %s%d = { %d'h%s };\n" %
                                   (base_signal, index, upper, value[0]))
                index += 1
            self._ofile.write('  }\n')
        else:
            self._ofile.write('  ROS%s : coverpoint %s;\n' %
                               (name, base_signal))


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

        for data in ports:
            comment = csep.join(commenter.wrap(data[3]))
            self._ofile.write('  %-6s %-9s %-28s // %s\n' %
                         (data[0], data[1], data[2] + sep, comment))
            cnt += 1
            if cnt == total-1:
                sep = ""
        self._ofile.write(');\n')

    def _write_output_mux(self, out_address, addr_bus, addr_width, data_out):
        """
        Writes the output mux that controls the selection of the output data
        """
        if self._dbase.sync_read:
            self._ofile.write('\nalways @(posedge %s or %s) begin\n' % (
                self._clock, self._reset_edge))
            self._ofile.write('   if (%s) begin\n' % self._reset_condition)
            self._ofile.write("      mux_%s <= %d'h0;\n" % (data_out, self._data_width))
            self._ofile.write('   end else begin\n')

            self._ofile.write("      if (%s) begin\n" % self._dbase.read_strobe_name)
            self._ofile.write('         case (%s)\n' % addr_bus)
            for addr in out_address:
                width = addr_width - self._lower_bit
                self._ofile.write('            %s: mux_%s <= r%02x;\n' %
                                  (bin(addr >> self._lower_bit, width),
                                   data_out, addr))
            self._ofile.write('            default: mux_%s <= %d\'h0;\n' %
                              (data_out, self._data_width))
            self._ofile.write('         endcase\n')
            self._ofile.write('      end else begin\n')
            self._ofile.write('         mux_%s <= %d\'h0;\n' % (data_out, self._data_width))
            self._ofile.write('      end\n')
            self._ofile.write('   end\n')
            self._ofile.write('end\n\n')
        else:
            self._ofile.write('\nalways @(*) begin\n')
            self._ofile.write('  case (%s)\n' % addr_bus)
            for addr in out_address:
                width = addr_width - self._lower_bit
                self._ofile.write('    %s: mux_%s = r%02x;\n' %
                                  (bin(addr >> self._lower_bit, width),
                                   data_out, addr))
            self._ofile.write('    default: mux_%s = %d\'h0;\n' %
                              (data_out, self._data_width))
            self._ofile.write('  endcase\n')
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
        if self._dbase.sync_read:
            self._ofile.write('\nalways_ff @(posedge %s or %s) begin\n' % (
                self._clock, self._reset_edge, base_signal, bits))
            self._ofile.write('   if (%s) begin\n' % self._reset_condition)
            self._ofile.write("      mux_%s <= %d'h0;\n" % (data_out, self._data_width))
            self._ofile.write('   end else begin\n')

            self._ofile.write("     if (%s) begin\n" % self._dbase.read_strobe_name)
            self._ofile.write('        case (%s)\n' % addr_bus)
            for addr in out_address:
                width = addr_width - self._lower_bit
                self._ofile.write('           %s: mux_%s <= r%02x;\n' %
                                  (bin(addr >> self._lower_bit, width),
                                   data_out, addr))
                self._ofile.write('         default: mux_%s <= %d\'h0;\n' %
                                  (data_out, self._data_width))
            self._ofile.write('         endcase\n')
            self._ofile.write('      end else begin\n')
            self._ofile.write('         mux_%s <= %d\'h0;\n' % (data_out, self._data_width))
            self._ofile.write('      end')
            self._ofile.write('   end')
            self._ofile.write('end\n\n')
        else:
            self._ofile.write('\nalways_comb begin\n')
            self._ofile.write('  case (%s)\n' % addr_bus)
            for addr in out_address:
                self._ofile.write('    %s: mux_%s = r%02x;\n' %
                                  (bin(addr >> 2, addr_width - 2), data_out, addr))
            self._ofile.write('    default: mux_%s = 32\'h0;\n' % data_out)
            self._ofile.write('  endcase\n')
            self._ofile.write('end\n\n')
