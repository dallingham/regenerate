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
"""

from typing import Dict, Any
from .param_data import ParameterFinder
from .param_value import ParamValue
from .name_base import Uuid


class Overrides:
    "Stores the override information"

    def __init__(self):
        self.finder = ParameterFinder()
        self.path: Uuid = Uuid("")
        self.parameter: Uuid = Uuid("")
        self.value = ParamValue()
        self.temp_name = ""

    def __repr__(self) -> str:
        param = self.finder.find(self.parameter)
        pval_str = str(self.value)
        if param:
            return f"Overrides(path={self.path}, parameter={param.name}, value={pval_str})"
        return f"Overrides(path={self.path}, parameter=<unknown>, value={pval_str})"

    def json(self) -> Dict[str, Any]:
        "Convert data to a dict for JSON export"

        return {
            "path": self.path,
            "parameter": self.parameter,
            "value": self.value,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        "Load the object from JSON data"

        self.path = Uuid(data["path"])
        self.parameter = Uuid(data["parameter"])
        val = data["value"]
        if isinstance(val, int):
            self.value = ParamValue(val)
        else:
            self.value = ParamValue()
            self.value.json_decode(val)
