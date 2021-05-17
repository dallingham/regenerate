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

from .param_data import ParameterData, ParameterFinder


class Overrides:
    def __init__(self):
        self.finder = ParameterFinder()
        self.path: str = ""
        self.parameter: str = ""
        self.value: int = 0
        self.temp_name = ""

    def __repr__(self):
        param = self.finder.find(self.parameter)
        return f"Overrides(path={self.path}, parameter={param.name}, value={self.value})"

    def json(self):
        return {
            "path": self.path,
            "parameter": self.parameter,
            "value": self.value,
        }

    def json_decode(self, data):
        self.path = data["path"]
        self.parameter = data["parameter"]
        self.value = data["value"]
