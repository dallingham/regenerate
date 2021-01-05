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
Reads the iorules.conf file to determine the naming rules. First, we look in
the site_local directory for the file. If we do not find this, we load the
default file from the data directory.

This allows the end user to customize their installation without the fear of
the next update overwriting their modifications.
"""

from configparser import SafeConfigParser, NoSectionError, NoOptionError
import os
from .paths import INSTALL_PATH

__Rules = SafeConfigParser()

__SITE_IO = os.path.join(INSTALL_PATH, "site_local", "iorules.conf")
__DEF_IO = os.path.join(INSTALL_PATH, "data", "iorules.conf")

if os.path.isfile(__SITE_IO):
    __Rules.read(__SITE_IO)
else:
    __Rules.read(__DEF_IO)


def get(section, option, default=""):
    try:
        return __Rules.get(section, option)
    except (NoSectionError, NoOptionError, IOError):
        return default
