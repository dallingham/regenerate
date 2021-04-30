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

from typing import Union
from .param_resolver import ParameterResolver
from .parammap import ParameterFinder


class ParamValue:
    def __init__(self, value=0, is_parameter=False):
        self.is_parameter = is_parameter
        self.offset = 0
        self.value: Union(int, str) = value

    def __repr__(self) -> str:
        if self.is_parameter:
            if self.offset == 0:
                offset = ""
            elif self.offset > 0:
                offset = f"+{self.offset}"
            else:
                offset = f"{self.offset}"
            return (
                f'ParamValue(value="{self.value}{offset}", is_parameter=True)'
            )
        return f" ParamValue(value=0x{self.value:x}, is_parameter=False)"

    def __str__(self) -> str:
        if self.is_parameter:
            pval = ParameterFinder().find(self.value)
            if self.offset > 0:
                return f"{pval.name}+{self.offset}"
            if self.offset < 0:
                return f"{pval.name}{self.offset}"
            return f"{pval.name}"
        return f"0x{self.value:x}"

    def int_str(self) -> str:
        if self.is_parameter:
            pval = ParameterFinder().find(self.value)
            if self.offset > 0:
                return f"{pval.name}+{self.offset}"
            if self.offset < 0:
                return f"{pval.name}{self.offset}"
            return f"{pval.name}"
        return f"{self.value:}"

    def int_vstr(self) -> str:
        if self.is_parameter:
            pval = ParameterFinder().find(self.value)
            if self.offset > 0:
                return f"{pval.name}+{self.offset}"
            if self.offset < 0:
                return f"{pval.name}{self.offset}"
            return f"{pval.name}"
        return f"'h{self.value:x}"

    def set_int(self, value: int) -> None:
        self.value = value
        self.is_parameter = False

    def set_param(self, value: str, offset: int = 0) -> None:
        self.value = value
        self.offset = offset
        self.is_parameter = True

    def resolve(self) -> int:
        if not self.is_parameter:
            return self.value

        resolver = ParameterResolver()
        finder = ParameterFinder()
        return resolver.resolve(finder.find(self.value)) + self.offset

    def json_decode(self, data):
        self.is_parameter = data["is_parameter"]
        self.offset = data["offset"]
        if self.is_parameter:
            self.value = data["value"]
        else:
            self.value = int(data["value"], 0)

    def json(self):
        val = {"is_parameter": self.is_parameter, "offset": self.offset}
        if self.is_parameter:
            val["value"] = self.value
        else:
            val["value"] = f"{self.value}"
        return val
