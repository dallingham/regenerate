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

from pathlib import Path
import datetime
from .writer_base import ProjectWriter, ExportInfo, ProjectType


class Xdc(ProjectWriter):
    """
    Output file creation class that writes a set of synthesis constraints
    """

    def __init__(self, project):
        super().__init__(project)
        self._offset = 0
        self.dblist = [dbase[1] for dbase in project.regsets.items()]
        self._ofile = None

    def find_static_outputs(self):
        static_signals = set()

        for reg in [
            self._dbase.get_register(reg_key)
            for reg_key in self._dbase.get_keys()
        ]:
            for field in [
                reg.get_bit_field(field_key)
                for field_key in reg.get_bit_field_keys()
            ]:
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

        base = field.output_signal.split("*")
        if len(base) > 1:
            base = "%s%d%s" % (base[0], field.start_position, base[1])
        else:
            base = base[0]
        return base

    def get_static_ports(self, dbase):
        fields = []
        for reg in dbase.get_all_registers():
            for field in reg.get_bit_fields():
                if (
                    field.use_output_enable
                    and field.output_signal
                    and field.output_is_static
                ):
                    fields.append((reg.address, field))
        return fields

    def write_header(self, of):
        t = datetime.datetime.now()
        tstr = t.strftime("%H:%M on %Y-%m-%d")
        of.write(
            "#----------------------------------------------------------\n"
        )
        of.write("#\n")
        of.write("# Xilinx XDC Constraints generated %s\n" % tstr)
        of.write("#\n")
        of.write(
            "#----------------------------------------------------------\n\n"
        )

    def write(self, filename: Path):
        """Writes the output file"""

        name2db = {}
        for db in self.dblist:
            name2db[db.name] = db

        with filename.open("w") as of:
            self.write_header(of)
            for blk_inst in self._project.block_insts:
                block = self._project.blocks[blk_inst.blkid]
                
                of.write("#\n# %s group\n#\n\n" % blk_inst.name)

                for regset_inst in block.regset_insts:
                    dbase = block.regsets[regset_inst.regset_id]
                    
                    ports = self.get_static_ports(dbase)
                    of.write(
                        "# %s - %s\n\n"
                        % (dbase.name, dbase.descriptive_title)
                    )
                    for (addr, field) in ports:
                        if field.is_constant():
                            continue
                        signal_name = field.name
                        if regset_inst.repeat.resolve() > 1:
                            for i in range(0, group_inst.repeat):
                                hdl = ""
                                if blk_inst.hdl_path != "":
                                    hdl = "%s/" % blk_inst.hdl_path.replace(
                                        ".", "/"
                                    ).replace("]/", "].")
                                if regset_inst.hdl != "":
                                    hdl = hdl + "%s/" % regset_inst.hdl.replace(
                                        ".", "/"
                                    ).replace("]/", "].")
                                    hdl = hdl % i
                                of.write(
                                    "set_multicycle_path 4 -setup -from [get_pins %sr%02x_%s*/DO_reg[*]/C]\n"
                                    % (hdl, addr, signal_name.lower())
                                )
                                of.write(
                                    "set_multicycle_path 3 -hold -from [get_pins %sr%02x_%s*/DO_reg[*]/C]\n"
                                    % (hdl, addr, signal_name.lower())
                                )
                        else:
                            hdl = ""
                            if blk_inst.hdl_path != "":
                                hdl = "%s/" % blk_inst.hdl_path.replace(
                                    ".", "/"
                                ).replace("]/", "].")
                            if regset_inst.hdl != "":
                                hdl = hdl + "%s/" % regset_inst.hdl.replace(
                                    ".", "/"
                                ).replace("]/", "].")
                            of.write(
                                "set_multicycle_path 4 -setup -from [get_pins %sr%02x_%s*/DO_reg[*]/C]\n"
                                % (hdl, addr, signal_name.lower())
                            )
                            of.write(
                                "set_multicycle_path 3 -hold -from [get_pins %sr%02x_%s*/DO_reg[*]/C]\n"
                                % (hdl, addr, signal_name.lower())
                            )
                    of.write("\n")


EXPORTERS = [
    (
        ProjectType.PROJECT,
        ExportInfo(
            Xdc,
            ("Synthesis", "Vivado Constraints"),
            "XDC files",
            ".xdc",
            "xdc-constraints",
        ),
    )
]
