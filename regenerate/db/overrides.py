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
Manages overriding parameter values from a lower level.

Maps the override values for parameters. The override could be a parameter
or an integer.

"""

from typing import Dict, Any
from .param_data import ParameterFinder
from .param_value import ParamValue
from .name_base import Uuid


class Overrides:
    """
    Stores the override information.

    This includes the ParameterFinder, the path UUID, parameter UUID,
    and the parameter's value.

    """

    def __init__(self):
        """
        Initialize the object.

        Set the values to their default values.

        """
        self.finder = ParameterFinder()
        self.path: Uuid = Uuid("")
        self.parameter: Uuid = Uuid("")
        self.value = ParamValue()
        self.temp_name = ""

    def __repr__(self) -> str:
        """
        Provide the string representation of the object.

        Returns:
            str: string representation

        """
        param = self.finder.find(self.parameter)
        pval_str = str(self.value)
        if param:
            return f'Overrides(path="{self.path}", parameter="{param.name}", value="{pval_str}")'
        return f'Overrides(path="{self.path}", parameter=<unknown>, value="{pval_str}")'

    def json(self) -> Dict[str, Any]:
        """
        Encode the object to a JSON dictionary.

        Returns:
            Dict[str, Any]: JSON-ish dictionary

        """
        return {
            "path": self.path,
            "parameter": self.parameter,
            "value": self.value,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Decode the JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data to decode

        """
        self.path = Uuid(data["path"])
        self.parameter = Uuid(data["parameter"])
        val = data["value"]
        if isinstance(val, int):
            self.value = ParamValue(val)
        else:
            self.value = ParamValue()
            self.value.json_decode(val)
