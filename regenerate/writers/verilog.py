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
from regenerate.writers.verilog_reg_def import REG
from regenerate.db import BitField, TYPES, LOGGER

from regenerate.writers.writer_base import WriterBase


# Constants

LOWER_BIT = {128: 4, 64: 3, 32: 2, 16: 1, 8: 0}
BUS_ELEMENT = re.compile("([\w_]+)\[(\d+)\]")
SINGLE_BIT = re.compile("\s*(\S+)\[(\d+)\]")
MULTI_BIT = re.compile("\s*(\S+)\[(\d+):(\d+)\]")

(F_FIELD, F_START_OFF, F_STOP_OFF, F_START, F_STOP,
 F_ADDRESS, F_REGISTER) = range(7)


def binary(val, width):
    """Converts the integer value to a Verilog value"""
    return "%d'h%x" % (width, val)


def errmsg(msg):
    """Displays an error message"""
    LOGGER.error(msg)


def get_width(field, start=-1, stop=-1, force_index=False):
    """Returns with width if the bit range is greater than one."""
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


def build_name(signal, field):
    sigparts = signal.split("[*]")
    if len(sigparts) == 1:
        sig = field.output_signal
    elif field.start_position != field.stop_position:
        sig = "%s[%d:%d]" % (sigparts[0],
                             field.stop_position,
                             field.start_position)
    else:
        sig = "%s[%d]" % (sigparts[0], field.stop_position)
    return sig


def oneshot_name(name, index=None):
    """
    Returns the name of the oneshot signal associated with the signal. In this
    implementation, it is the name of the signal with a _1s appended.
    """
    if index is None:
        return name + "_1S"
    else:
        return "%s_%d_1S" % (name, index)


def write_strobe(address):
    """
    Generates the write strobe signal associated with a particular address.
    """
    return "write_r%02x" % address


def read_strobe(address):
    """
    Generates the read strobe signal associated with a particular address.
    """
    return "read_r%02x" % address


def get_signal_offset(address):
    """Returns the offset of the signal."""
    return address % 4


def full_reset_value(field):
    """returns the full reset value for the entire field"""

    if field.reset_type == BitField.RESET_NUMERIC:
        return "%d'h%0x" % (field.width, field.reset_value)
    elif field.reset_type == BitField.RESET_INPUT:
        return field.reset_input
    else:
        return field.reset_parameter


def reset_value(field, start, stop):
    """returns the full reset value for the field up to a byte"""

    if field.reset_type == BitField.RESET_NUMERIC:
        field_width = (stop - start) + 1
        reset = (field.reset_value >> (start - field.start_position))
        return "%d'h%x" % (field_width, reset & 0xff)
    elif field.reset_type == BitField.RESET_INPUT:
        return "%s[%d:%d]" % (field.reset_input, stop, start)
    else:
        return "%s[%d:%d]" % (field.reset_parameter, stop, start)


def break_on_byte_boundaries(start, stop):
    """
    Return a list of byte boundaries from the start and stop values
    """
    index = start
    data = []

    while index <= stop:
        next_boundary = ((index / 8) + 1) * 8
        data.append((index, min(stop, next_boundary - 1)))
        index = next_boundary
    return data


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
    control = field.input_signal
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
        (start, stop) = (int(data[1]), int(data[1]))
    else:
        match = MULTI_BIT.match(reset)
        if match:
            data = match.groups()
            reset = data[0]
            (start, stop) = (int(data[2]), int(data[1]))
        else:
            (start, stop) = (field.start_position, field.stop_position)

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

    def __init__(self, project, dbase):
        WriterBase.__init__(self, project, dbase)

        self._always = 'always'

        self.__sorted_regs = [
            reg for reg in dbase.get_all_registers()
            if not (reg.do_not_generate_code or reg.ram_size > 0)]

        self._coverage = self._dbase.enable_coverage

        max_column_str = ini.get('user', 'column_width', "80")
        try:
            self._max_column = max(int(max_column_str), 80)
        except ValueError:
            self._max_column = 80

        if dbase.reset_active_level:
            self._reset_edge = "posedge %s" % self._reset
            self._reset_condition = self._reset
        else:
            self._reset_edge = "negedge %s" % self._reset
            self._reset_condition = "~%s" % self._reset

        if dbase.byte_strobe_active_level:
            self.__be_condition = self._byte_enables
        else:
            self.__be_condition = "~%s" % self._byte_enables

        self._ofile = None
        self._lower_bit = LOWER_BIT[self._data_width]

        self._word_fields = self.__generate_group_list(self._data_width)

        self._field_type_map = {
            BitField.TYPE_READ_ONLY: self._register_read_only,
            BitField.TYPE_READ_ONLY_VALUE: self._register_read_only_value,
            }

        self._has_input = {}
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
            self._cell_name[i.type] = i.id.lower()
            self._has_input[i.type] = i.input
            self._has_control[i.type] = i.control
            self._has_oneshot[i.type] = i.oneshot
            self._type_descr[i.type] = i.description
            self._allows_wide[i.type] = i.wide
            self._has_data_out[i.type] = i.dataout
            self._has_rd[i.type] = i.read
            self._is_read_only[i.type] = i.readonly

    def _comment(self, text_list, border=None, precede_blank=0):
        """
        Creates a comment from the list of text strings
        """
        border_string = border * (self._max_column - 2) if border else ""

        if text_list:
            if precede_blank:
                self._wrln('\n')
            self._wrln("/*%s\n * " % border_string)
            self._wrln("\n * ".join(text_list))
            if border:
                text = "\n *%s" % border_string
                self._wrln(text.rstrip())
            self._wrln("\n */\n")

    def _not_implemented(self, reg, field):
        """
        Reported when an undefined register type has been requested.
        """
        self._wrln("/* Not yet implemented */\n")

    def _register_read_only(self, address, field):
        """
        A read only register is simply represented by a continuous assign
        """
        rname = get_base_signal(address, field)
        rvalue = full_reset_value(field)

        self._wrln('assign %s = %s;\n' % (rname, rvalue))
        self._wrln('\n')

    def _register_read_only_value(self, address, field):
        """
        Read only register assigned from an input signal
        """
        rname = get_base_signal(address, field)
        rvalue = field.input_signal

        self._wrln('assign %s = %s;\n' % (rname, rvalue))
        self._wrln('\n')

    def _register_normal(self, address, field):
        """
        Called when a know register type is requested that is known.
        """
        cell_name = self._cell_name[field.field_type]
        self._used_types.add(field.field_type)
        nbytes = self._data_width / 8

        for (start, stop) in break_on_byte_boundaries(field.start_position,
                                                      field.stop_position):
            parameters = []
            if start >= self._data_width:
                write_address = address + ((start / self._data_width) *
                                           (self._data_width / 8))
            else:
                write_address = (address / nbytes) * nbytes

            reg_start_bit = (address * 8) % self._data_width
            bus_start = start % self._data_width + reg_start_bit
            bus_stop = stop % self._data_width + reg_start_bit

            width = (stop - start) + 1

            bus_index = get_width(field, bus_start, bus_stop, True)
            index = get_width(field, start, stop)
            instance = "%s_%d" % (get_base_signal(address, field), start)

            self._wrln('%s_%s_reg ' % (self._module, cell_name))

            if self._allows_wide[field.field_type]:
                parameters.append('.WIDTH(%d)' % width)
            parameters.append('.RVAL(%s)' % reset_value(field, start, stop))

            if parameters:
                self._wrln(' #(')
                self._wrln(", ".join(parameters))
                self._wrln(') %s\n' % instance)

            self._wrln(' (\n')
            self._write_port('CLK', self._clock, first=1)
            self._write_port('RSTn', self._reset)

            lane = bus_start / 8 
            if not self._is_read_only[field.field_type]:
                self._write_port("WE", 'write_r%02x' % write_address)
                self._write_port("DI", '%s%s' % (self._data_in, bus_index))
                self._write_port('BE', '%s[%d]' % (self._byte_enables, lane))
            if self._has_rd[field.field_type]:
                self._write_port('RD', 'read_r%02x' % write_address)
            if self._has_data_out[field.field_type]:
                base = get_base_signal(address, field)
                self._write_port('DO', '%s%s' % (base, index))
            if self._has_control[field.field_type]:
                self._write_port('LD', field.control_signal)
            if self._has_input[field.field_type]:
                if index:
                    signal = field.input_signal.split("[")[0]
                else:
                    signal = field.input_signal
                self._write_port('IN', '%s%s' % (signal, index))
            if self._has_oneshot[field.field_type]:
                base = get_base_signal(address, field)
                one_shot_name = oneshot_name(base, start)
                self._write_port('DO_1S', one_shot_name)
            self._wrln('\n  );\n\n')

    def _write_port(self, pname, value, first=0):
        """
        Formats a port declaration for the register module instatiation
        """
        if not first:
            self._wrln(',\n')
        self._wrln('    .%-5s (%s)' % (pname, value))

    def _byte_info(self, field, register, lower, size):
        """
        Returns the basic information from a field, broken out into byte
        quantities
        """
        start = max(field.start_position, lower)
        stop = min(field.stop_position, lower + size - 1)

        nbytes = size / 8
        address = (register.address / nbytes) * nbytes
        bit_offset = (register.address * 8) % size

        return (field, start + bit_offset, stop + bit_offset,
                start, stop, address, register)

    def __generate_group_list(self, size):
        """
        Breaks a set of bit fields along the specified boundary
        """
        item_list = {}
        for register in self.__sorted_regs:
            for field in register.get_bit_fields():
                for lower in range(0, register.width, size):
                    if in_range(field.start_position, field.stop_position,
                                lower, lower + size - 1):
                        data = self._byte_info(field, register, lower, size)
                        item_list.setdefault(data[F_ADDRESS], []).append(data)
        return item_list

    def __generate_read_strobes(self, size):
        """
        Breaks a set of bit fields along the specified boundary
        """
        item_list = {}
        for reg in self.__sorted_regs:
            for field in [field for field in reg.get_bit_fields()
                          if self._has_rd[field.field_type]]:
                for lower in range(0, reg.width, size):
                    if in_range(field.start_position, field.stop_position,
                                lower, lower + size - 1):
                        data = self._byte_info(field, reg, lower, size)
                        item_list.setdefault(data[F_ADDRESS], []).append(data)
        return item_list

    def write(self, filename):
        """
        Writes the verilog code to the specified filename
        """
        self._ofile = open(filename, "w")
        self._write_header_comment(self._ofile, 'site_verilog.inc',
                                   comment_char='// ')
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

    def _wrln(self, text):
        """
        Shorthand for writing a line to the file
        """
        self._ofile.write(text)

    def _write_register_modules(self):
        """
        Writes the used register module types to the file.
        """
        edge = "posedge" if self._dbase.reset_active_level else "negedge"
        condition = "" if self._dbase.reset_active_level else "~"
        be_level = "" if self._dbase.byte_strobe_active_level else "~"

        name_map = {'MODULE': self._module,
                    'BE_LEVEL': be_level,
                    'RESET_CONDITION': condition,
                    'RESET_EDGE': edge}

        for i in self._used_types:
            self._wrln("\n\n")
            try:
                self._comment([self._type_descr[i]])
                self._wrln(REG[self._cell_name[i]] % name_map)
            except KeyError:
                self._comment(['No definition for %s_%s_reg\n' %
                               (self._module, self._cell_name[i])])

    def _write_module_header(self):
        """
        Writes the module statement, along with the arguments and port
        declarations
        """

        port_list = self._build_port_list()

        plist = []
        blist = []
        for register in self._dbase.get_all_registers():
            for field in register.get_bit_fields():
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.stop_position == field.start_position:
                        blist.append((field.reset_parameter,
                                      field.width,
                                      field.reset_value))
                    else:
                        plist.append((field.stop_position,
                                      field.start_position,
                                      field.reset_parameter,
                                      field.width,
                                      field.reset_value))

        if plist or blist:
            params = ["parameter %s = %d'h%x" % item for item in blist] + \
                     ["parameter [%d:%d] %s = %d'h%x" % item for item in plist]
            self._wrln('module %s #(\n  ' % self._module )
            self._wrln(",\n    ".join(params))
            self._wrln('\n  )(\n')
        else:
            self._wrln('module %s (\n' % self._module)

        port_signals = ", \n  ".join([f[2] for f in port_list])
        self._wrln(port_signals)
        self._wrln(');\n\n')

        commenter = textwrap.TextWrapper(width=(self._max_column - 52))
        sep = "\n" + " " * 46 + "// "

        max_len = max([len(i[2]) for i in port_list]) + 2
        fmt_string = "%%-6s %%-7s %%-%ds // %%s\n" % max_len

        for data in port_list:
            comment = sep.join(commenter.wrap(data[3]))
            self._wrln(fmt_string % (data[0], data[1], data[2] + ';', comment))

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
            ("input", '', self._read_strobe, "Read strobe"),
            ("input", be_width, self._byte_enables, "Byte enables"),
            ("input", addr_width, self._addr, "Address"),
            ("input", data_width, self._data_in, "Data in")
            ]

        for register in self.__sorted_regs:

            # loop through each bit field, looking for needed ports
            for field in register.get_bit_fields():

                # A parallel load requires an input signal
                if self._has_control[field.field_type]:
                    if not field.control_signal:
                        errmsg("No parallel load signal specified for %s:%s"
                               % (register.register_name, field.field_name))
                    parallel_load_port(field, port_list, output_list)

                # If the bit is controlled by an input value, we
                # need a signal
                if field.input_signal and self._has_input[field.field_type]:
                    input_signal_port(field, port_list, output_list)

                # Output oneshots require a signal
                if self._has_oneshot[field.field_type]:
                    if not field.output_signal:
                        errmsg("Empty output signal for %s:%s"
                               % (register.register_name, field.field_name))
                    port_list.append(('output', "",
                                      oneshot_name(field.output_signal),
                                      "one shot"))

                # As do output enables
                if field.use_output_enable and field.output_signal:
                    port_list.append(('output', get_width(field),
                                      build_name(field.output_signal, field),
                                      field.description))

                if field.reset_type == BitField.RESET_INPUT:
                    add_reset_input(reset_set, field)

        port_list.append(("output", '[%d:0]' % (self._data_width - 1),
                          self._data_out, "Data out"))
        port_list.append(("output reg", '', self._dbase.acknowledge_name,
                          "Acknowledge"))

        for key in reset_set:
            item = reset_set[key]
            if item[1] == item[2]:
                port_list.append((item[0], "", key, item[3]))
            else:
                port_list.append((item[0], "[%d:%d]" %
                                  (item[1], item[2]), key, item[3]))

        return self._cleanup_port_list(port_list)

    def _cleanup_port_list(self, port_list):
        new_list = []
        new_ports = {}
        for port in port_list:
            match = SINGLE_BIT.match(port[2])
            if match:
                groups = match.groups()
                name = groups[0]
                new_info = (port[0], int(groups[1]), -1, port[2])
                if name in new_ports:
                    new_ports[name].append(new_info)
                else:
                    new_ports[name] = [new_info]
                continue
            match = MULTI_BIT.match(port[2])
            if match:
                groups = match.groups()
                name = groups[0]
                new_info = (port[0], int(groups[1]), int(groups[2]), port[2])
                if name in new_ports:
                    new_ports[name].append(new_info)
                else:
                    new_ports[name] = [new_info]
                continue
            new_list.append(port)

        self.__unused_ports = []

        for key in new_ports:
            data = new_ports[key]
            high_ports = [a[1] for a in data if a[1] != -1]
            low_ports = [a[2] for a in data if a[2] != -1]
            min_index = min(high_ports + low_ports)
            max_index = max(high_ports + low_ports)

            used_ports = set(range(min_index, max_index + 1))
            for entry in data:
                if entry[2] == -1:
                    used_ports.remove(entry[1])
                else:
                    for i in range(entry[2], entry[1] + 1):
                        used_ports.remove(i)

            self.__unused_ports = self.__unused_ports + ["%s[%d]" % (key, i)
                                                         for i in used_ports]

            new_entry = (data[0][0], "[%d:%d]" % (max_index, min_index),
                         key, data[0][3])
            new_list.append(new_entry)

        return new_list

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

            for field in register.get_bit_fields():
                sindex = get_width(field)
                base = get_base_signal(addr, field)

                val = "wire %-10s %s;" % (sindex, base)
                local_regs.append(val)

                if self._has_oneshot[field.field_type]:
                    boundaries = break_on_byte_boundaries(field.start_position,
                                                          field.stop_position)
                    for pos in boundaries:
                        val = "wire %-10s %s;" % ("",
                                                  oneshot_name(base, pos[0]))
                        local_regs.append(val)

        if local_regs:
            self._comment(['Register Declarations'], precede_blank=1)
            self._wrln("\n".join(local_regs))
        self._wrln("\nreg [%d:0]      mux_%s;\n" % (self._data_width - 1,
                                                    self._data_out.lower()))

        if local_wires:
            self._comment(['Wire Declarations (Constants)'], precede_blank=1)
            self._wrln("\n".join(local_wires))

    def _write_address_selects(self):
        """
        Writes the address select lines
        """
        self._comment(['Address Selects'], precede_blank=1)

        for address in sorted(self._word_fields.keys()):
            width = self._addr_width - self._lower_bit
            self._wrln("wire %s = %s & (%s == %s);\n" % (
                write_strobe(address), self._write_strobe, self._addr,
                binary(address >> self._lower_bit, width)))

        addr_keys = sorted(self.__generate_read_strobes(self._data_width))
        for address in addr_keys:
            width = self._addr_width - self._lower_bit
            self._wrln("wire %s  = %s & (%s == %s);\n" % (
                read_strobe(address), self._read_strobe, self._addr,
                binary(address >> self._lower_bit, width)))

    def _write_output_assignments(self):
        """
        Writes the output assignments
        """
        self._comment(['Output Assignments'], precede_blank=1)

        max_len = 0

        for register in self.__sorted_regs:
            for field_key in register.get_bit_field_keys():
                field = register.get_bit_field(field_key)
                if self._has_oneshot[field.field_type]:
                    max_len = max(max_len,
                                  len(oneshot_name(field.output_signal)))
                if not field.use_output_enable:
                    continue
                max_len = max(max_len, len(field.output_signal))

        fmt_string = "assign %%-%ds = %%s;\n" % max_len

        for register in self.__sorted_regs:
            address = register.address
            for field_key in register.get_bit_field_keys():
                field = register.get_bit_field(field_key)
                if self._has_oneshot[field.field_type]:
                    base = get_base_signal(address, field)
                    boundaries = break_on_byte_boundaries(field.start_position,
                                                          field.stop_position)
                    names = " | ".join([oneshot_name(base, pos[0])
                                        for pos in boundaries])
                    self._wrln(fmt_string  % (
                        oneshot_name(field.output_signal), names))
                if not field.use_output_enable:
                    continue

                self._wrln(fmt_string % (
                    build_name(field.output_signal, field),
                    get_base_signal(address, field)))

        fmt_string = "assign %%-%ds = 1'b0;\n" % max_len
        for unused in self.__unused_ports:
            self._wrln(fmt_string % unused)

        fmt_string = "assign %%-%ds = mux_%%s;\n" % max_len
        self._wrln(fmt_string % (self._data_out, self._data_out.lower()))
        self._wrln("\n")

    def _write_register_rtl_code(self):
        """
        Sorts the register keys, interates of the corresponding registers,
        filtering out the registers that should not have associated code,
        and calls write_register to write the RTL code.
        """
        for reg in self.__sorted_regs:
            for field in reg.get_bit_fields():
                self._write_field(reg, field)

    def _write_field(self, reg, field):
        """
        Writes the register range that is specified
        """
        self._write_field_comment(reg.register_name, reg.address, field,
                                  field.start_position, field.stop_position)
        func = self._field_type_map.get(field.field_type,
                                        self._register_normal)
        func(reg.address, field)

    def _write_field_comment(self, reg_name, address, field, start, stop):
        """
        Writes the comment for a bit field
        """
        mlen = 11

        lines = ['%s : %s' % ('Field'.ljust(mlen), field.field_name)]
        lines.append('%s : %s' % ('Type'.ljust(mlen),
                                  self._type_descr[field.field_type]))

        if field.width == 1:
            lines.append('%s : %d' % ('Bit'.ljust(mlen), stop))
        else:
            lines.append('%s : %d:%d' %
                         ('Bits'.ljust(mlen), stop, start))
        lines.append('%s : %s' % ('Register'.ljust(mlen), reg_name))
        lines.append('%s : %08x' % ('Address'.ljust(mlen), address))
        if field.reset_type == BitField.RESET_NUMERIC:
            lines.append('%s : %d\'h%x' %
                         ('Reset Value'.ljust(mlen), field.width,
                          field.reset_value))
        elif field.reset_type == BitField.RESET_PARAMETER:
            lines.append('%s : %d\'h%x' %
                         ('Reset Value'.ljust(mlen), field.width,
                          field.reset_value))
        else:
            lines.append('%s : %s' %
                         ('Reset Value'.ljust(mlen), field.reset_input))

        comment = field.description
        if comment:
            comment = comment.replace(u'\2013', '-')
            fmt = textwrap.TextWrapper(width=self._max_column - 3)
            lines.append('')
            for i in fmt.wrap(comment):
                lines.append(i)

        self._comment(lines, border="-")

    def _define_outputs(self):
        """
        Writes the output declarations
        """
        self._comment(["", "Register Read Output Assignments", ""],
                      border="-")

        keys = sorted(self._word_fields.keys())
        for key in keys:
            current_pos = self._data_width - 1
            comma = False
            upper = self._data_width - 1
            self._wrln("wire [%d:0] r%02x = {" % (upper, key))

            for field_info in sorted(self._word_fields[key],
                                     reverse=True,
                                     cmp=lambda x, y: cmp(x[2], y[2])):
                if comma:
                    self._wrln(",")
                else:
                    comma = True

                stop = field_info[F_STOP_OFF] % self._data_width
                start = field_info[F_START_OFF] % self._data_width

                if stop != current_pos:
                    self._wrln("\n                  ")
                    self._wrln("%d'b0," % (current_pos - stop))
                    current_pos = stop - 1

                name_info = get_signal_info(field_info[F_REGISTER].address,
                                            field_info[F_FIELD],
                                            field_info[F_START],
                                            field_info[F_STOP])
                self._wrln("\n                  ")
                self._wrln("%s" % (name_info[1]))
                current_pos = start  - 1

            if current_pos != -1:
                self._wrln(",\n                  ")
                self._wrln("%d'b0" % (current_pos + 1))
            self._wrln("\n                  };\n")

        self._write_output_mux(keys, self._addr,
                               self._addr_width, self._data_out)

    def _write_acknowledge(self):
        """
        Writes the acknowledge signal generate logic.
        """
        self._comment(["Ensure that internal write is one clock wide"],
                      border="-")
        self._wrln("\nreg prev_write, prev_read;\n\n")
        self._wrln('%s @(posedge %s or %s) begin\n' %
                   (self._always, self._clock, self._reset_edge))
        self._wrln('  if (%s) begin\n' % self._reset_condition)
        self._wrln("     prev_write <= 1'b0;\n")
        self._wrln("     prev_read  <= 1'b0;\n")
        self._wrln("     %s <= 1'b0;\n" % self._dbase.acknowledge_name)
        self._wrln('  end else begin\n')
        self._wrln("     prev_write <= %s;\n" % self._dbase.write_strobe_name)
        self._wrln("     prev_read  <= %s;\n" % self._dbase.read_strobe_name)
        self._wrln("     %s <= (~prev_write & %s) | (~prev_read & %s);\n" %
                   (self._dbase.acknowledge_name,
                    self._dbase.write_strobe_name,
                    self._dbase.read_strobe_name))
        self._wrln('  end\nend\n\n')

    def _write_output_mux(self, out_address, addr_bus, addr_width, data_out):
        """
        Writes the output mux that controls the selection of the output data
        """
        dout = data_out.lower()
        self._wrln('\n%s @(posedge %s or %s) begin\n' %
                   (self._always, self._clock, self._reset_edge))
        self._wrln('  if (%s) begin\n' % self._reset_condition)
        self._wrln("     mux_%s <= %d'h0;\n" % (dout, self._data_width))
        self._wrln('  end else begin\n')

        self._wrln("     if (%s) begin\n" % self._dbase.read_strobe_name)
        self._wrln('        case (%s)\n' % addr_bus)
        for addr in out_address:
            width = addr_width - self._lower_bit
            self._wrln('         %s: mux_%s <= r%02x;\n' %
                       (binary(addr >> self._lower_bit, width),
                        data_out.lower(), addr))
        self._wrln('       default: mux_%s <= %d\'h0;\n' %
                   (data_out.lower(), self._data_width))
        self._wrln('       endcase\n')
        self._wrln('     end else begin\n')
        self._wrln('        mux_%s <= %d\'h0;\n' % (dout, self._data_width))
        self._wrln('     end\n')
        self._wrln('  end\n')
        self._wrln('end\n\n')

    def _write_trailer(self):
        """
        Closes the module. In Verilog, this is done with the endmodule
        statement. A comment is added to indicate which module is being
        closed.
        """
        self._wrln('endmodule // %s\n' % self._module)


class Verilog2001(Verilog):
    """
    Provides a SystemVerilog interface, derived from the Verilog class.
    Changes include:

    * Verilog 2001 style input/output declarations
    * Use of always_ff and always_comb instead of the usual always
    * Uses the endmodule : name syntax
    """

    def __init__(self, project, dbase):
        Verilog.__init__(self, project, dbase)
        self._always = 'always_ff'

    def _write_module_header(self):
        """
        Writes the module header using Verilog 2001 constructs
        """
        plist = []
        blist = []
        for register in self._dbase.get_all_registers():
            for field in register.get_bit_fields():
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.stop_position == field.start_position:
                        blist.append((field.reset_parameter,
                                      field.width,
                                      field.reset_value))
                    else:
                        plist.append((field.stop_position,
                                      field.start_position,
                                      field.reset_parameter,
                                      field.width,
                                      field.reset_value))

        if plist or blist:
            params = ["parameter %s = %d'h%x" % item for item in blist] + \
                ["parameter [%d:%d] %s = %d'h%x" % item for item in plist]
            self._wrln('module %s #(\n  ' % self._module )
            self._wrln(",\n    ".join(params))
            self._wrln('\n  )(\n')
        else:
            self._wrln('module %s (\n' % self._module )

        csep = "\n" + " " * 48 + "// "
        sep = ", "
        ports = self._build_port_list()
        cnt = 0
        total = len(ports)
        commenter = textwrap.TextWrapper(width=self._max_column - 52)

        max_len = max([len(i[2]) for i in ports]) + 2
        fmt_string = "  %%-10s %%-7s %%-%ds // %%s\n" % max_len

        for data in ports:
            comment = csep.join(commenter.wrap(data[3]))
            self._wrln(fmt_string % (data[0], data[1], data[2] + sep, comment))
            cnt += 1
            if cnt == total - 1:
                sep = ""
        self._wrln(');\n')

    def _write_output_mux(self, out_address, addr_bus, addr_width, data_out):
        """
        Writes the output mux that controls the selection of the output data
        """
        dout = data_out.lower()
        self._wrln('\n%s @(posedge %s or %s) begin\n' % (
            self._always, self._clock, self._reset_edge))
        self._wrln('   if (%s) begin\n' % self._reset_condition)
        self._wrln("      mux_%s <= %d'h0;\n" % (dout, self._data_width))
        self._wrln('   end else begin\n')

        self._wrln("      if (%s) begin\n" % self._dbase.read_strobe_name)
        self._wrln('         case (%s)\n' % addr_bus)
        for addr in out_address:
            width = addr_width - self._lower_bit
            self._wrln('            %s: mux_%s <= r%02x;\n' %
                       (binary(addr >> self._lower_bit, width), dout, addr))
        self._wrln('            default: mux_%s <= %d\'h0;\n' %
                   (dout, self._data_width))
        self._wrln('         endcase\n')
        self._wrln('      end else begin\n')
        self._wrln('         mux_%s <= %d\'h0;\n' % (dout, self._data_width))
        self._wrln('      end\n')
        self._wrln('   end\n')
        self._wrln('end\n\n')


class SystemVerilog(Verilog2001):
    """
    Provides a SystemVerilog interface, derived from the Verilog class.
    Changes include:

    * Verilog 2001 style input/output declarations
    * Use of always_ff and always_comb instead of the usual always
    * Uses the endmodule : name syntax
    """

    def __init__(self, project, dbase):
        Verilog2001.__init__(self, project, dbase)
        self._always = 'always_ff'

    def _write_trailer(self):
        """
        Writes the endmodule statement using the : name syntax instead
        of writing a comment.
        """
        self._wrln('endmodule : %s\n' % self._module)

    def _write_output_mux(self, out_address, addr_bus, addr_width, data_out):
        """
        Writes the always_ff syntax, instead of the always @(xxx) syntax
        """

        dout = data_out.lower()
        self._wrln('\n%s @(posedge %s or %s) begin\n' % (
            self._always, self._clock, self._reset_edge))
        self._wrln('   if (%s) begin\n' % self._reset_condition)
        self._wrln("      mux_%s <= %d'h0;\n" % (dout, self._data_width))
        self._wrln('   end else begin\n')

        self._wrln("     if (%s) begin\n" % self._dbase.read_strobe_name)
        self._wrln('        case (%s)\n' % addr_bus)
        for addr in out_address:
            width = addr_width - self._lower_bit
            self._wrln('           %s: mux_%s <= r%02x;\n' %
                       (binary(addr >> self._lower_bit, width), dout, addr))
        self._wrln('           default: mux_%s <= %d\'h0;\n' %
                   (dout, self._data_width))
        self._wrln('        endcase\n')
        self._wrln('      end else begin\n')
        self._wrln('         mux_%s <= %d\'h0;\n' % (dout, self._data_width))
        self._wrln('      end\n')
        self._wrln('   end\n')
        self._wrln('end\n\n')
