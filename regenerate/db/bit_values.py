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
Provides the bit values for a bit field
"""

from .json_base import JSONEncodable


class BitValues(JSONEncodable):
    """
    Provides the bit values for a field - roughly the equivalent
    to and enumerated type. This BitValue consists of:

    value - numerical value
    token - a symbolic name
    description - a description of the value
    """

    def __init__(self):
        self.value: int = 0
        self.token: str = ""
        self.description: str = ""

    def json_decode(self, data):
        """Converts the json data into a BitValue"""

        self.value = data["value"]
        self.token = data["token"]
        self.description = data["description"]
