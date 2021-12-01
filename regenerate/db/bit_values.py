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
Provides the bit values for a bit field.

Bit values consist of 3 bits of information:

  * value
  * token
  * description

"""

from typing import Dict, Any


class BitValues:
    """
    Provides the bit values for a field.

    This is roughly the equivalent to an enumerated type in the
    bit field. This BitValue consists of:

    value - numerical value
    token - a symbolic name
    description - a description of the value
    """

    def __init__(self, value=0, token="", description=""):
        """
        Initialize the object.

        Parameters:
           value (int): numerical value
           token (str): symbolic name
           description (str): text description of the value

        """
        self.value: int = value
        self.token: str = token
        self.description: str = description

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Convert the json data into a BitValue.

        Parameters:
           data (Dict[str, Any]): data to decode

        """
        self.value = int(data["value"], 0)
        self.token = data["token"]
        self.description = data["description"]

    def json(self) -> Dict[str, Any]:
        """
        Convert the object into a Dict for JSON encoding.

        Returns:
           Dict[str, Any]: encoded data in JSON format

        """
        return {
            "value": f"{self.value}",
            "token": self.token,
            "description": self.description,
        }
