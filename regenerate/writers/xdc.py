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

from .writer_base import WriterBase, ExportInfo


class Xdc(WriterBase):
    """
    Output file creation class that writes a set of synthesis constraints
    """

    def __init__(self, project, dblist):
        super(Xdc, self).__init__(project, None)
        self._offset = 0
        self.dblist = dblist
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

    def _build_group_maps(self):
        group_maps = {}
        for group in self._project.get_grouping_list():
            in_maps = set()
            for addr_map in self._project.get_address_maps():
                map_list = self._project.get_address_map_groups(addr_map.name)
                if not map_list or group.name in map_list:
                    in_maps.add(addr_map.name)
            group_maps[group] = in_maps
        return group_maps

    def _build_name(self, field):

        base = field.output_signal.split('*')
        if len(base) > 1:
            base = "%s%d%s" % (base[0], field.start_position, base[1])
        else:
            base = base[0]
        return base

    def get_static_ports(self, dbase):
        fields = []
        for reg in dbase.get_all_registers():
            for field in reg.get_bit_fields():
                if (field.use_output_enable and field.output_signal and
                        field.output_is_static):
                    fields.append(field)
        return fields

    def write(self, filename):
        """Writes the output file"""

        with open(filename, "w") as of:
            for dbase in self.dblist:
                ports = self.get_static_ports(dbase)
                if ports:
                    of.write("\n\ncurrent_design %s\n\n" % dbase.module_name)
                    for field in ports:
                        signal_name = self._build_name(field)
                        of.write(
                            "set_false_path -from [get_pins reg_%02d_%s*/DO_reg[*]/C]\n" %
                            (field.lsb, signal_name.lower())
                        )


EXPORTERS = [
    (WriterBase.TYPE_PROJECT,
     ExportInfo(
         Xdc,
         ("Synthesis", "Vivado Constraints"),
         "XDC files",
         ".xdc",
         'xdc-constraints')
     )
]
