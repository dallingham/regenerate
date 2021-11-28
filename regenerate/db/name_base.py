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
Provides the base cass for the register and bitfield
"""

import secrets
from typing import NewType
from .json_base import JSONEncodable

Uuid = NewType("Uuid", str)


class NameBase(JSONEncodable):
    """
    Provides the command items between a Register and a BitField
    """

    def __init__(self, name: str = "", id_val: Uuid = Uuid("")):
        self._name = name
        self._id: Uuid = id_val
        self.description = ""

    @property
    def name(self) -> str:
        """
        Returns the value of the _name flag. This cannot be accessed
        directly, but only via the property 'name'
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """
        Sets the __name flag. This cannot be accessed directly, but only
        via the property 'name'
        """
        self._name = name.strip()

    @property
    def uuid(self) -> Uuid:
        """Returns the UUID or creates a new unique one if one doesn't exist"""

        if self._id == "":
            self._id = Uuid(secrets.token_hex(6))
        return self._id

    @uuid.setter
    def uuid(self, value: Uuid) -> None:
        """Sets the UUID"""

        self._id = value

    def __hash__(self) -> int:
        "Return the ID as the hash for the instance"
        return id(self.uuid)
