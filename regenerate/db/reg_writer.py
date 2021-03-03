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
Writes the XML file containing all the information in the register database
"""

from pathlib import Path
import xml.sax.saxutils

from .bitfield_types import TYPE_TO_ID
from .textutils import clean_text
from .enums import ResetType


def create_backup_file(filename: Path):
    """
    Creates the backup file, renaming the existing file to a .bak extension,
    removing the original backup if it exists.
    """

    if filename.is_file():
        backup = filename.with_suffix(".xml.bak")
        if backup.is_file():
            backup.unlink()
        filename.rename(backup)


class RegWriter:
    """Writes the XML file."""

    def __init__(self, dbase):
        self.dbase = dbase

    def save(self, filename: str):
        """Saves the data to the specified XML file."""

        dbase = self.dbase
        filepath = Path(filename)

        create_backup_file(filepath)

        if self.dbase.array_is_reg:
            array = "reg"
        else:
            array = "mem"

        with filepath.open("w") as ofile:

            ofile.write('<?xml version="1.0"?>\n')
            ofile.write(f'<module name="{dbase.module_name}" ')
            ofile.write(f'coverage="{int(dbase.coverage)}" ')
            ofile.write(f'internal="{int(dbase.internal_only)}">\n')

            ofile.write(f'  <base addr_width="{dbase.address_bus_width}" ')
            ofile.write(f'data_width="{dbase.data_bus_width}"/>\n')

            self.write_port_information(ofile)

            overview = cleanup(self.dbase.overview_text)
            if overview:
                ofile.write(f"  <overview>{overview}</overview>\n")
            if dbase.owner:
                ofile.write(f"  <owner>{dbase.owner}</owner>\n")
            if dbase.descriptive_title:
                ofile.write(f"  <title>{dbase.descriptive_title}</title>\n")
            if dbase.organization:
                ofile.write(f"  <org>{dbase.organization}</org>\n")
            ofile.write(f"  <array>{array}</array>\n")

            self.write_signal_list(ofile)
            self.write_parameter_list(ofile)
            ofile.write("</module>\n")

    def write_port_information(self, ofile):
        """ Writes the port information to the output file"""

        dbase = self.dbase

        ofile.write("  <ports>\n")
        ofile.write(f"    <interface>{int(dbase.use_interface)}</interface>\n")
        ofile.write(f"    <addr>{dbase.address_bus_name}</addr>\n")
        ofile.write(f"    <data_in>{dbase.write_data_name}</data_in>\n")
        ofile.write(f"    <data_out>{dbase.read_data_name}</data_out>\n")
        ofile.write(f'    <be active="{int(dbase.byte_strobe_active_level)}">')
        ofile.write(f"{dbase.byte_strobe_name}</be>\n")
        ofile.write(f"    <wr>{dbase.write_strobe_name}</wr>\n")
        ofile.write(f"    <ack>{dbase.acknowledge_name}</ack>\n")
        ofile.write(f"    <rd>{dbase.read_strobe_name}</rd>\n")
        ofile.write(f"    <clk>{dbase.clock_name}</clk>\n")
        ofile.write(f'    <reset active="{dbase.reset_active_level}">')
        ofile.write(f"{dbase.reset_name}</reset>\n")
        ofile.write("  </ports>\n")

    def write_signal_list(self, ofile):
        """Writes the signal list to the output file"""

        for reg in self.dbase.get_all_registers():
            write_register(ofile, reg)

    def write_parameter_list(self, ofile):
        """Writes the parameter list"""

        plist = self.dbase.get_parameters()
        if plist:
            ofile.write("  <parameters>\n")
            for (name, value, min_val, max_val) in plist:
                ofile.write(f'    <parameter name="{name}" ')
                ofile.write(f'value="{value}" ')
                ofile.write(f'min="{min_val}" ')
                ofile.write(f'max="{max_val}"/>\n')
            ofile.write("  </parameters>\n")


def write_register(ofile, reg):
    """Writes the specified register to the output file"""
    ofile.write("  <register>\n")
    ofile.write(f"    <name>{reg.name}</name>\n")
    ofile.write(f"    <token>{reg.token}</token>\n")
    ofile.write(f"    <uuid>{reg.uuid}</uuid>\n")
    ofile.write(f"    <dimension>{reg.dimension_str}</dimension>\n")
    ofile.write(f"    <address>{reg.address}</address>\n")
    ofile.write(
        f"    <nocode>{int(reg.flags.do_not_generate_code)}</nocode>\n"
    )
    ofile.write(f"    <dont_test>{int(reg.flags.do_not_test)}</dont_test>\n")
    ofile.write(
        f"    <dont_cover>{int(reg.flags.do_not_cover)}</dont_cover>\n"
    )
    ofile.write(f"    <hide>{int(reg.flags.hide)}</hide>\n")
    ofile.write(
        f"    <dont_use_uvm>{int(reg.flags.do_not_use_uvm)}</dont_use_uvm>\n"
    )
    ofile.write(f"    <share>{int(reg.share)}</share>\n")
    if reg.ram_size:
        ofile.write(f"    <ram_size>{reg.ram_size}</ram_size>\n")
    ofile.write(f"    <width>{reg.width}</width>\n")
    if reg.description:
        text = cleanup(reg.description)
        ofile.write(f"    <description>{text}</description>\n")
    for field in reg.get_bit_fields():
        write_field(ofile, field)
    ofile.write("  </register>\n")


def cleanup(data):
    "Remove some unicode characters with standard ASCII characters"
    return xml.sax.saxutils.escape(clean_text(data))


def write_field(ofile, field):
    """Writes the specified bit field to the output file"""
    low = min(field.start_position, field.stop_position)
    high = max(field.start_position, field.stop_position)

    ofile.write(f'    <range start="{low}" stop="{high}">\n')
    ofile.write(f"      <name>{field.name}</name>\n")
    ofile.write(f"      <uuid>{field.uuid}</uuid>\n")
    tid = TYPE_TO_ID[field.field_type]
    ofile.write(f"      <field_type>{tid}</field_type>\n")
    ofile.write(f"      <random>{int(field.flags.can_randomize)}</random>\n")
    ofile.write(
        f"      <side_effect>{int(field.output_has_side_effect)}</side_effect>\n"
    )
    ofile.write(f"      <volatile>{int(field.flags.volatile)}</volatile>\n")
    ofile.write(
        f"      <error_field>{int(field.flags.is_error_field)}</error_field>\n"
    )
    write_signal_info(ofile, field)
    write_input_info(ofile, field)
    write_reset_type(ofile, field)
    write_value_list(ofile, field)
    ofile.write(
        f"      <description>{cleanup(field.description)}</description>\n"
    )
    ofile.write("    </range>\n")


def write_input_info(ofile, field):
    """Writes the input information to the output file"""
    if field.control_signal:
        ldstr = f' load="{field.control_signal}"'
    else:
        ldstr = ""
    if field.input_signal:
        ofile.write(f"      <input{ldstr}>{field.input_signal}</input>\n")
    elif ldstr:
        ofile.write(f"      <input{ldstr}/>\n")


def write_signal_info(ofile, field):
    """Writes the signal information to the output file"""
    ofile.write(
        f'      <signal enb="{int(field.use_output_enable)}" '
        f'static="{int(field.output_is_static)}">'
    )
    ofile.write("{field.output_signal}</signal>\n")


def write_reset_type(ofile, field):
    """Writes the reset information to the output file"""
    if field.reset_type == ResetType.INPUT:
        ofile.write('      <reset type="1">%s</reset>\n' % field.reset_input)
    elif field.reset_type == ResetType.PARAMETER:
        ofile.write(
            '      <reset type="2" parameter="%s">%x</reset>\n'
            % (field.reset_parameter, field.reset_value)
        )
    else:
        ofile.write('      <reset type="0">%x</reset>\n' % field.reset_value)


def write_value_list(ofile, field):
    """Writes the value list information to the output file"""
    if field.values:
        ofile.write("      <values>\n")
        for value in field.values:
            ofile.write(
                '        <value val="%s" token="%s">%s</value>\n'
                % (value[0], value[1], cleanup(value[2]))
            )
        ofile.write("      </values>\n")
