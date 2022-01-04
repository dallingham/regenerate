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
Provides a common resource for finding parameters based on the UUID.

Allows searching independent of the owner. All parameters are registered
or unregistered to allow searching.

"""

from typing import Dict, Optional
from .name_base import Uuid


class ParameterFinder:
    """
    Finds a parameter in the project based on its UUID.

    Serves as a singleton.

    """

    data_map: Dict[Uuid, "ParameterData"] = {}

    def __new__(cls):
        """
        Class method new function.

        Creates a new class instance.
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(ParameterFinder, cls).__new__(cls)
        return cls.instance

    def find(self, uuid: Uuid) -> Optional["ParameterData"]:
        """
        Look up the UUID in the data map.

        Parameters:
            uuid (Uuid): UUID of the parameter that is to be found

        Returns:
            Optional[ParameterData]: parameter data or None if not found

        """
        return self.data_map.get(uuid)

    def register(self, parameter: "ParameterData") -> None:
        """
        Register a parameter with the system.

        Parameter:
            parameter (ParameterData): parameter to register

        """
        self.data_map[parameter.uuid] = parameter

    def unregister(self, parameter: "ParameterData") -> None:
        """
        Remove the parameter with the system.

        Parameter:
            parameter (ParameterData): parameter to remove

        """
        if parameter.uuid in self.data_map:
            del self.data_map[parameter.uuid]
