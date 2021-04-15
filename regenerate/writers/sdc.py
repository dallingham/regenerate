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
from regenerate.db import RegProject
from .writer_base import ExportInfo, ProjectWriter, ProjectType


class Sdc(ProjectWriter):
    """
    Output file creation class that writes a set of synthesis constraints
    """

    def __init__(self, project: RegProject):
        super().__init__(project)
        self.ofile = None

        self.dblist = set()
        for block_inst in project.block_insts:
            block = project.blocks[block_inst.block]

            for regset in block.regsets:
                self.dblist.add(block.regsets[regset])

    def write(self, filename: Path):
        "Writes the output file"

        with filename.open("w") as self.ofile:
            for dbase in self.dblist:
                self.write_regset(dbase)

    def write_regset(self, dbase):
        for block_inst in self._project.block_insts:
            used = set()
            block = self._project.blocks[block_inst.block]

            for reginst in block.regset_insts:
                if (
                    reginst.set_name == dbase.set_name
                    and reginst.set_name not in used
                    and reginst.hdl
                ):
                    used.add(reginst.set_name)
                    for reg, field in all_fields(dbase):
                        for i in range(0, reginst.repeat.resolve()):
                            base = get_signal_info(reg.address, field)[0]
                            for j in range(0, block_inst.repeat):
                                path = build_format(
                                    block_inst.hdl_path, j, reginst.hdl, i
                                )
                                self.write_statements(f"{path}/{base}")

    def write_statements(self, signal_name: str):
        self.ofile.write(
            f"set_multicycle -from [get_cells{signal_name}] -setup 4\n"
        )
        self.ofile.write(
            f"set_false_path -from [get_cells{signal_name}] -hold\n"
        )


def build_format(top_hdl, top_count, lower_hdl, lower_count):
    if top_hdl and lower_hdl:
        top_hdl = top_hdl.replace("%0d", "%(d)d")
        top_hdl = top_hdl.replace(".", "/") % {"d": top_count}
        lower_hdl = lower_hdl.replace("%0d", "%(d)d")
        lower_hdl = lower_hdl.replace(".", "/")
        lower_hdl = lower_hdl % {"d": lower_count}
        return f"{top_hdl}/{lower_hdl}"
    elif lower_hdl:
        lower_hdl = lower_hdl.replace("%0d", "%(d)d")
        lower_hdl = lower_hdl.replace(".", "/") % {"d": lower_count}
        return lower_hdl
    return ""


def all_fields(dbase):
    """Return a list of all the fields"""

    fld_list = []
    for reg in dbase.get_all_registers():
        for field in reg.get_bit_fields():
            if has_static_output(field):
                fld_list.append((reg, field))
    return fld_list


def has_static_output(field):
    """Return true if the output field is static"""

    return (
        field.use_output_enable
        and field.output_signal
        and field.output_is_static
    )


def get_signal_base(field):
    base = field.output_signal.split("*")
    if len(base) > 1:
        base = "%s%d%s" % (base[0], field.start_position, base[1])
    else:
        base = base[0]
    return base


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


def get_signal_offset(address):
    """Returns the offset of the signal."""
    return address % 4


def get_width(field, start=-1, stop=-1, force_index=False):
    """Returns with width if the bit range is greater than one."""
    if stop == -1:
        start = field.lsb
        stop = field.msb

    if field.width == 1 and not force_index:
        signal = ""
    elif start == stop:
        signal = "[{0}]".format(stop)
    else:
        signal = "[{0}:{1}]".format(stop, start)
    return signal


def get_base_signal(address, field):
    """
    Returns the base signal derived from the address and the output field
    """
    return "r{0:02x}_{1}".format(address, field.name.lower())


EXPORTERS = [
    (
        ProjectType.PROJECT,
        ExportInfo(
            Sdc,
            ("Synthesis", "SDC Constraints"),
            "SDC files",
            ".sdc",
            "syn-constraints",
        ),
    )
]
