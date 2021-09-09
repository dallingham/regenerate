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
Container for parameters, allowing adding, removing, and searching
"""

from typing import List, Optional
from .param_data import ParameterData


class ParameterContainer:
    "Parameter containing class"

    def __init__(self):
        self._parameters: List[ParameterData] = []

    def get(self):
        """Returns the parameter list"""
        return self._parameters

    def add(self, parameter: ParameterData):
        """Adds a parameter to the list"""
        self._parameters.append(parameter)

    def remove(self, name: str):
        """Removes a parameter from the list if it exists"""
        self._parameters = [p for p in self._parameters if p.name != name]

    def set(self, parameter_list: List[ParameterData]):
        """Sets the parameter list"""
        self._parameters = parameter_list

    def find(self, name: str) -> Optional[ParameterData]:
        "Finds the parameter from its name"
        for param in self._parameters:
            if param.name == name:
                return param
        return None

    def json(self):
        "Convert to a dictionary for serialization"
        return [parameter.json() for parameter in self._parameters]

    def json_decode(self, data):
        "Load data from JSON data"

        self._parameters = []
        for item_json in data:
            item = ParameterData()
            item.json_decode(item_json)
            self._parameters.append(item)
