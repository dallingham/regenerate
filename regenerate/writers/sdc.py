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
Sdc - Writes out synthesis constraints
"""

from writer_base import WriterBase     # IGNORE:W0403


class Sdc(WriterBase):
    """
    Output file creation class that writes a set of synthesis constraints
    """

    def __init__(self, dbase):
        WriterBase.__init__(self, dbase)
        self._offset = 0
        self._ofile = None

    def find_static_outputs(self):
        static_signals = set()

        for reg in [self._dbase.get_register(reg_key)
                    for reg_key in self._dbase.get_keys()]:
            for field in [reg.get_bit_field(field_key)
                          for field_key in reg.get_bit_field_keys()]:
                if field.use_output_enable and field.output_is_static:
                    if field.output_signal:
                        static_signals.add(field.output_signal)
        return static_signals

    def write(self, filename):
        """
        Writes the output file
        """
        self._ofile = open(filename, "w")
        self._write_header_comment(self._ofile, 'site_sdc.inc',
                                   comment_char='// ')

        self._ofile.write("// current_design = %s;\n" %
                          self._dbase.module_name)
        for signal in self.find_static_outputs():
            self._ofile.write("// set multicycle -from %s to *;\n" % signal)

        self._ofile.close()
