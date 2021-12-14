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
Provides a simple JSON encode/decode function for use with very
simple classes.
"""

from typing import Dict, Any
from .logger import LOGGER


class JSONEncodable:
    """
    JSON encoder base class. Only works if you are okay with:

    * All class variables saved in JSON
    * Variable names match JSON names

    The decode function works with the above rules, but add that
    no class member can be another class, list, dict, tuple, or set_access
    of classes.
    """

    def json(self) -> Dict[str, Any]:
        """Converts the local variables to a dictionary"""

        return vars(self)

    def json_decode(self, data: Dict[str, Any]) -> None:
        """Converts the dictionary back into local variables"""

        key = ""
        try:
            for key, value in data.items():
                self.__setattr__(key, value)
        except ValueError:
            LOGGER.error("JSON tag (%s) did not map to a variable", key)
