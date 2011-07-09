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


class Coverage(object):

    def __init__(self, ofile, dbase):
        self._ofile = ofile
        self.dbase = dbase

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
                          if not item[0].is_constant()]

            if not field_list:
                continue

            field = field_list[0][0]
            self._write_covergroup_head(address, field)

            width = field_list[0][4].width

            if field.field_type == BitField.READ_WRITE:
                used_cover.add(field)
                for (subfield, start, stop, addr, reg) in field_list:
                    self._write_normal_cover(address, subfield, start, stop)
            elif field.field_type == BitField.WRITE_1_TO_CLEAR:
                used_cover.add(field)
                self._write_cover_rw_w1c(address, field, width)
                if field.input_function == BitField.FUNC_SET_BITS:
                    self._write_cover_rw_set(address, field, width)
            elif field.field_type == BitField.READ_ONLY:
                used_cover.add(field)
                if field.input_function == BitField.FUNC_SET_BITS:
                    self._write_cover_readonly_set(address, field)

            self._write_covergroup_end()

        for reg in self.__sorted_regs:
            for field in [ reg.get_bit_field(s)
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
                    bin(address>>self.__lower_bit, self._addr_width-self.__lower_bit)))
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
        (base_signal, signal, offset) = get_signal_info(address, field, start, stop)
#        bit_values = split_bus_values(offset, stop - start + 1, field)

        if field.values and (stop - start < 8):
            val = bit_values[0][2]
            name = "%s_%s" % (self._module, base_signal)
            byte_en = self._byte_enable(val)
            self._ofile.write('  %s : coverpoint %s ' % (name, base_signal))
            self._ofile.write('iff (!(write_r%02x & %s))\n' %
                               (address, byte_en))
            self._ofile.write('  {\n')
            index = 0
            for value in field.values:
                self._ofile.write("     bins %s%d = { %d'h%s };\n" %
                             (base_signal, index, (stop-start+1), value[0]))
                index += 1
            self._ofile.write('  }\n')
        else:
            name = "%s_%s_%x_%d" % (self._module, base_signal, address, start)
            byte_en = self._byte_enable(start/8)
            self._ofile.write('  %s : coverpoint %s ' % (name, signal))
            self._ofile.write('iff (write_r%02x & %s);\n' %
                               (address, byte_en))

    def _write_cover_rw_set(self, address, field, width):
        """
        Writes a cover group for read/write bit fields that have a set signal
        """
        base_signal = get_base_signal(address, field)
        offset = get_signal_offset(address)
        bit_values = split_bus_values(offset, width, field)

        for (lower, next_top, val) in bit_values:
            byte_en = self._byte_enable(val)
            for i in range(lower, next_top+1):
                name = "%s_%s_%d" % (self._module, base_signal, i)
                self._ofile.write('  %s : coverpoint %s[%d] ' %
                                   (name, base_signal, i))
                self._ofile.write('iff (!(write_r%02x & %s))\n' %
                                   (address, byte_en))
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
            byte_en = self._byte_enable(val)
            for i in range(lower, next_top+1):
                name = "%s_%s_%d" % (self._module, base_signal, i)
                self._ofile.write('  %s : coverpoint %s[%d] ' %
                                   (name, base_signal, i))
                self._ofile.write('iff (!(write_r%02x & %s))\n' %
                                   (address, byte_en))
                self._ofile.write('  {\n')
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
            byte_en = self._byte_enable(val)
            for i in range(lower, next_top+1):
                name = "%s_%s_%d" % (self._module, base_signal, i)
                self._ofile.write('  W1C_%s : coverpoint %s[%d] ' %
                                   (name, base_signal, i))
                self._ofile.write('iff (!(write_r%02x & %s))\n' %
                                   (address, byte_en))
                self._ofile.write('  {\n')
                self._ofile.write('    bins b%d = (1 => 0);\n' % i)
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
                                   (base_signal, index, (stop-start+1),
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
                upper = stop-start+1
                self._ofile.write("     bins %s%d = { %d'h%s };\n" %
                                   (base_signal, index, upper, value[0]))
                index += 1
            self._ofile.write('  }\n')
        else:
            self._ofile.write('  ROS%s : coverpoint %s;\n' %
                               (name, base_signal))
