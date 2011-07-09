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
Imports the exporters. Makes an attempt to load the site_local versions
first. This allows the end user to override the standard version without
fears that it will get overwritten on the next install.
"""

from rdl import RDLParser
from denali import DenaliRDLParser

#
# Lists the exporters. The format is:
#
#  (PythonModule, Menu Item, FileDescription, Extenstion,
#   ShortCmdFlag, LongCmdFlag)
#

IMPORTERS = [
    (RDLParser, "SystemRDL", "SystemRDL files", ".rdl", '-r', '--import-rdl'),
    (DenaliRDLParser, "DenaliRDL", "SystemRDL files", ".rdl", '-r', '--import-drdl'),
]
