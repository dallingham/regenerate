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
WriterBase - base class for objects that product output from the
             register database.
"""

import os
import time
from regenerate.settings.paths import INSTALL_PATH


if os.name == 'nt':
    def get_username():
        import getpass
        return getpass.getuser()
else:
    def get_username():
        import pwd
        return pwd.getpwnam(os.environ['USER'])[4].split(',')[0]


class WriterBase(object):   # IGNORE:R0921 - we know this is a abstract class
    """
    Writes the register information to the output file determined
    by the derived class.
    """

    def __init__(self, project, dbase):
        self._dbase = dbase
        self._project = project
        self._project_name = ""
        if dbase:
            self._set_values_init(dbase)

    def set_project(self, obj):
        self._project = obj
        self._project_name = obj.short_name

    def _set_values_init(self, dbase, instance_name=None):
        self._comments = dbase.overview_text
        self._module = dbase.module_name
        self._clock = dbase.clock_name
        self._addr = dbase.address_bus_name
        self._addr_width = dbase.address_bus_width
        prefix = ""

        self._data_width = dbase.data_bus_width
        self._reset = dbase.reset_name
        self._reset_level = dbase.reset_active_level
        self._byte_enables = dbase.byte_strobe_name
        self._be_level = dbase.byte_strobe_active_level
        self._data_in = dbase.write_data_name
        self._data_out = dbase.read_data_name
        self._write_strobe = dbase.write_strobe_name
        self._read_strobe = dbase.read_strobe_name
        self._filename = "UNKNOWN"
        self._project_name = "UNKNOWN"
        self._local_path = os.path.join(INSTALL_PATH, "site_local")
        self._data_path = os.path.join(INSTALL_PATH, "data")

        if prefix:
            self._prefix = "%s_" % prefix.replace(' ', '_').upper()
        else:
            self._prefix = ""

    def _write_header_comment(self, ofile, default_path, comment_char='#'):
        """
        Looks for the header include file to allow users to define their own
        header. If not, default to the built in header.
        """
        try:
            cfile = os.path.join(self._data_path, default_path)
            data = "".join(file(cfile).readlines())
        except IOError:
            try:
                cfile = os.path.join(self._data_path, "site_comment.txt")
                data = comment_char.join(file(cfile).readlines())
            except IOError:
                try:
                    cfile = os.path.join(INSTALL_PATH, "comment.txt")
                    data = comment_char.join(file(cfile).readlines())
                except IOError:
                    data = "\n"
            data = comment_char + data

        self.write_header(ofile, data)

    def write_header(self, ofile, line):
        """
        Goes through the specified text, substituting information if needed.
        """
        t = time.time()
        year = str(time.localtime(t)[0])
        date = time.asctime(time.localtime(t))

        user = get_username()

        if self._module == "":
            module = "I_forgot_to_give_the_module_a_name"
        else:
            module = self._module

        fixed = self._filename.upper().replace('.', '_')
        line = line.replace('$M$', module)
        line = line.replace('$Y$', year)
        line = line.replace('$f$', self._filename)
        line = line.replace('$F$', fixed)
        line = line.replace('$D$', date)
        line = line.replace('$U$', user)
        ofile.write(line)

    def write(self, filename):
        """
        The child class must override this to provide an implementation.
        """
        raise NotImplementedError
