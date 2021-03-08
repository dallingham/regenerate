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
Parses the register database, loading the database.
"""

import json


class RegParserJSON:
    """
    Parses the XML file, loading up the register database.
    """

    def __init__(self, dbase):
        self.__db = dbase

    def parse(self, input_file):
        """Convert JSON back to the database information."""

        json_data = json.loads(input_file.read())
        self.__db.json_decode(json_data)
