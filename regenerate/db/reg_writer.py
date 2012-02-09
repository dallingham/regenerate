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

import time
import os
from xml.sax.saxutils import escape
from regenerate.db import BitField


def create_backup_file(filename):
    """
    Creates the backup file, renaming the existing file to a .bak extension,
    removing the original backup if it exists.
    """
    if os.path.exists(filename):
        backup = filename + ".bak"
        if os.path.exists(backup):
            os.unlink(backup)
        os.rename(filename, backup)


class RegWriter(object):
    """
    Writes the XML file.
    """

    def __init__(self, dbase):
        self.dbase = dbase

    def save(self, filename):
        """
        Saves the data to the specified XML file.
        """
        curtime = int(time.time())

        create_backup_file(filename)
        ofile = open(filename, "w")
        ofile.write('<?xml version="1.0"?>\n')
        ofile.write('<module name="%s" title="%s" owner="%s">\n' %
                (self.dbase.module_name, self.dbase.descriptive_title,
                 self.dbase.owner))

        ofile.write('  <code sync_rd="%d"/>\n' % self.dbase.sync_read)

        ofile.write('  <base addr_width="%d" ' % self.dbase.address_bus_width)
        ofile.write('data_width="%d"/>\n' % self.dbase.data_bus_width)

        self.write_instances(ofile)
        self.write_port_information(ofile)

        ofile.write("  <overview>%s</overview>\n" %
                    cleanup(self.dbase.overview_text))

        self.write_signal_list(ofile, curtime)
        ofile.write('</module>\n')
        ofile.close()

    def write_instances(self, ofile):
        """
        Write instance information to the output file.
        """
        if self.dbase.instances:
            ofile.write('  <instances>\n')
            for instance in self.dbase.instances:
                ofile.write('    <instance id="%s" base="%x"/>\n' % instance)
            ofile.write('  </instances>\n')

    def write_port_information(self, ofile):
        """
        Writes the port information to the output file
        """
        ofile.write('  <ports>\n')
        ofile.write('    <addr>%s</addr>\n' % self.dbase.address_bus_name)
        ofile.write('    <data_in>%s</data_in>\n' % self.dbase.write_data_name)
        ofile.write('    <data_out>%s</data_out>\n' %
                    self.dbase.read_data_name)
        ofile.write('    <be active="%d">%s</be>\n' %
                    (self.dbase.byte_strobe_active_level,
                     self.dbase.byte_strobe_name))
        ofile.write('    <wr>%s</wr>\n' % self.dbase.write_strobe_name)
        ofile.write('    <rd>%s</rd>\n' % self.dbase.read_strobe_name)
        ofile.write('    <clk>%s</clk>\n' % self.dbase.clock_name)
        ofile.write('    <reset active="%d">%s</reset>\n' %
                (self.dbase.reset_active_level, self.dbase.reset_name))
        ofile.write('  </ports>\n')

    def write_signal_list(self, ofile, curtime):
        """
        Writes the signal list to the output file
        """
        for reg in [self.dbase.get_register(rkey)
                    for rkey in self.dbase.get_keys()]:
            write_register(ofile, reg, curtime)


def write_register(ofile, reg, curtime):
    """
    Writes the specified register to the output file
    """
    ofile.write('  <register nocode="%d" dont_test="%d" hide="%d">\n' %
                (reg.do_not_generate_code, reg.do_not_test, reg.hide))
    ofile.write('    <token modified="%d">%s</token>\n' %
            (calc_mod_time(reg.get_token_obj(), curtime),
             reg.token))
    ofile.write('    <name modified="%d">%s</name>\n' %
                (calc_mod_time(reg.get_name_obj(), curtime),
                 reg.register_name))
    ofile.write('    <address modified="%d">%d</address>\n' %
                (calc_mod_time(reg.get_address_obj(), curtime),
                 reg.address))
    ofile.write('    <width modified="%d">%s</width>\n' %
                (calc_mod_time(reg.get_width_obj(), curtime),
                 reg.width))
    ofile.write('    <description modified="%d">%s</description>\n' %
                (calc_mod_time(reg.get_description_obj(), curtime),
                 cleanup(reg.description)))
    for field in [reg.get_bit_field(key)
                   for key in reg.get_bit_field_keys() ]:
        write_field(ofile, field, curtime)
    ofile.write('  </register>\n')


def cleanup(data):
    data = data.replace(u"\u2013", "-")
    data = data.replace(u"\u201c", "\"")
    data = data.replace(u"\ue280a2", "*")
    return escape(data.replace(u"\u201d", "\""))


def write_field(ofile, field, curtime):
    """
    Writes the specified bit field to the output file
    """
    low = min(field.start_position, field.stop_position)
    high = max(field.start_position, field.stop_position)

    if field.modified:
        field.last_modified = curtime
        field.modified = False

    ofile.write('    <range start="%d" stop="%d">\n' % (low, high))
    ofile.write('      <modified time="%d"/>\n' % field.last_modified)
    ofile.write('      <name>%s</name>\n' % field.field_name)
    write_signal_info(ofile, field)
    write_input_info(ofile, field)
    write_reset_type(ofile, field)
    write_value_list(ofile, field)
    ofile.write('      <description>%s</description>\n' %
                cleanup(field.description))
    ofile.write('    </range>\n')


def write_input_info(ofile, field):
    """
    Writes the input information to the output file
    """
    ofile.write('      <input function="%d" load="%s">' %
                (field.input_function, field.control_signal))
    ofile.write('%s</input>\n' % field.input_signal)


def write_signal_info(ofile, field):
    """
    Writes the signal information to the output file
    """
    ofile.write('      <signal enb="%d" static="%d" '
                % (field.use_output_enable, field.output_is_static))
    ofile.write('type="%d" ' % field.field_type)
    ofile.write('side_effect="%d" oneshot="%d">'
                % (field.output_has_side_effect, field.one_shot_type))
    ofile.write('%s</signal>\n' % field.output_signal)


def write_reset_type(ofile, field):
    """
    Writes the reset information to the output file
    """
    if field.reset_type == BitField.RESET_INPUT:
        ofile.write('      <reset type="1">%s</reset>\n' %
                    field.reset_input)
    elif field.reset_type == BitField.RESET_PARAMETER:
        ofile.write('      <reset type="2" parameter="%s">%x</reset>\n' %
                    (field.reset_parameter, field.reset_value))
    else:
        ofile.write('      <reset type="0">%x</reset>\n' %
                    field.reset_value)


def write_value_list(ofile, field):
    """
    Writes the value list information to the output file
    """
    if field.values:
        ofile.write('      <values>\n')
        for value in field.values:
            ofile.write('        <value val="%s" token="%s">%s</value>\n' %
                        (value[0], value[1], cleanup(value[2])))
        ofile.write('      </values>\n')


def calc_mod_time(obj, curtime):
    """
    Returns the modified time
    """
    if obj.modified:
        return curtime
    else:
        return obj.last_modified
