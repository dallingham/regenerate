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
Provides the base class for the classes with names and UUIDs.

All unique classes (registers, blocks, address maps, parameters, etc.)
should inherit from this class to that the are all treated in a common
manner.
"""

import secrets
from typing import NewType
from .json_base import JSONEncodable

Uuid = NewType("Uuid", str)


class NameBase(JSONEncodable):
    """
    Base class for named objects.

    Provides base for named objects in the design. These items all have a
    name, a UUID, and a description.
    """

    def __init__(self, name: str = "", id_val: Uuid = Uuid("")):
        """
        Initialize the base with a name and UUID.

        name - object's name
        idval - UUID
        """
        self._name = name
        self._id: Uuid = id_val
        self.description = ""

    @property
    def name(self) -> str:
        """
        Return the value of the _name flag.

        This cannot be accessed directly, but only via the property 'name'.
        """
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """
        Set the _name value.

        This cannot be accessed directly, but only via the property 'name'.
        This function strips off leading and trailing spaces.
        """
        self._name = name.strip()

    @property
    def uuid(self) -> Uuid:
        """
        Return the UUID.

        The UUID is created using the secrets.token_hex function to create
        a unique ID and assign it to the ID value.
        """
        if self._id == "":
            self._id = Uuid(secrets.token_hex(6))
        return self._id

    @uuid.setter
    def uuid(self, value: Uuid) -> None:
        """
        Set the UUID.

        The value used for a UUID is a string, and should be created
        by either loading from a file, or using secrets.token_hex
        """
        self._id = value

    def __hash__(self) -> int:
        """
        Return the ID as the hash for the instance.

        Create the hash id by using the built in id function
        """
        return id(self.uuid)
