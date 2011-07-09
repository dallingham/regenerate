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
Provides the interface to the users .ini file. This is a standard ConfigParser
module that is used to remember paths for exporters.
"""

import ConfigParser
import os

PARSER = ConfigParser.ConfigParser()
FILENAME = os.path.expanduser("~/.regenerate")


def get(section, option, default=None):
    try:
        PARSER.read(FILENAME)
        val = PARSER.get(section, option, default)
        return val
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError, IOError):
        return default


def set(section, option, value):
    if not PARSER.has_section(section):
        PARSER.add_section(section)
    PARSER.set(section, option, value)
    try:
        ofile = open(FILENAME, "w")
        PARSER.write(ofile)
        ofile.close()
    except IOError:
        return
