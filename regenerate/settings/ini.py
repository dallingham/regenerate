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

from configparser import ConfigParser, NoSectionError, NoOptionError
from typing import Optional
import os

PARSER = ConfigParser()
FILENAME = os.path.expanduser("~/.regenerate")


def get(section: str, option: str, default=None) -> Optional[str]:
    """
    Gets the value from the config file, returning the default if not found.
    """

    try:
        PARSER.read(FILENAME)
        return PARSER.get(section, option)
    except (NoSectionError, NoOptionError, IOError):
        return default


def set(section: str, option: str, value: str) -> None:
    """Sets the value in the config file"""

    if not PARSER.has_section(section):
        PARSER.add_section(section)
    PARSER.set(section, option, str(value))
    try:
        with open(FILENAME, "w") as ofile:
            PARSER.write(ofile)
    except IOError:
        return
