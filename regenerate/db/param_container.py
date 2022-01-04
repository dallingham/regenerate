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
Container for parameters.

Allows adding, removing, and searching.

"""

from typing import List, Optional
from .name_base import Uuid
from .param_data import ParameterData


class ParameterContainer:
    """
    Class that manages parameters.

    Allows the adding, removing, and searching for parameters.

    """

    def __init__(self):
        """
        Initialize the object.

        Sets the list to an empty list.

        """
        self._parameters: List[ParameterData] = []

    def get(self) -> List[ParameterData]:
        """
        Return the parameter list.

        Returns:
            List[ParameterData]: list of parameters

        """
        return self._parameters

    def add(self, parameter: ParameterData) -> None:
        """
        Add a parameter to the list.

        Parameter:
            parameter (ParameterData): Parameter to add

        """
        self._parameters.append(parameter)

    def remove(self, name: str) -> None:
        """
        Remove a parameter from the list if it exists.

        Parameter:
            name (str): Name of the parameter to remove

        """
        self._parameters = [p for p in self._parameters if p.name != name]

    def remove_by_uuid(self, uuid: Uuid) -> None:
        """
        Remove a parameter from the list if it exists.

        Parameter:
            name (str): Name of the parameter to remove

        """
        self._parameters = [p for p in self._parameters if p.uuid != uuid]

    def set(self, parameter_list: List[ParameterData]) -> None:
        """
        Set the parameter list.

        Parameters:
            parameter_list (List[ParameterData]): parameter list

        """
        self._parameters = parameter_list

    def find(self, name: str) -> Optional[ParameterData]:
        """
        Find a parameter from its name.

        Parameters:
            name (str): name to search for

        Returns:
            Optional[ParameterData]: the parameter data, if found

        """
        for param in self._parameters:
            if param.name == name:
                return param
        return None

    def json(self):
        """
        Encode the object to a JSON dictionary.

        Returns:
            Dict[str, Any]: JSON-ish dictionary

        """
        return [parameter.json() for parameter in self._parameters]

    def json_decode(self, data):
        """
        Decode the JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data to decode

        """
        self._parameters = []
        for item_json in data:
            item = ParameterData()
            item.json_decode(item_json)
            self._parameters.append(item)
