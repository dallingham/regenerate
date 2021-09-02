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
Provides an object that can either be an integer or a parameter
"""

from .param_resolver import ParameterResolver
from .param_data import ParameterFinder
from .enums import ParamFunc


class ParamValue:
    "A value that can be either an integer or a parameter"

    def __init__(self, value=0, is_parameter=False):
        self.is_parameter = is_parameter
        self.offset = 0
        self.func = ParamFunc.NONE
        self.int_value: int = value
        self.txt_value: str = ""

    def __repr__(self) -> str:
        if self.is_parameter:
            if self.offset == 0:
                offset = ""
            elif self.offset > 0:
                offset = f"+{self.offset}"
            else:
                offset = f"{self.offset}"
            return f'ParamValue(value="{self.txt_value}{offset}", is_parameter=True)'
        return f" ParamValue(value=0x{self.int_value:x}, is_parameter=False)"

    def __str__(self) -> str:
        if self.is_parameter:
            pval = ParameterFinder().find(self.txt_value)
            if pval:
                if self.offset > 0:
                    return f"{pval.name}+{self.offset}"
                if self.offset < 0:
                    return f"{pval.name}{self.offset}"
                return f"{pval.name}"
            return ""
        return self.int_str()

    def param_name(self):
        if self.is_parameter:
            pval = ParameterFinder().find(self.txt_value)
            return pval.name
        else:
            return ""

    def int_str(self) -> str:
        "Prints the parameter with integers in decimal format"

        if self.is_parameter:
            pval = ParameterFinder().find(self.txt_value)
            if pval:
                if self.offset > 0:
                    return f"{pval.name}+{self.offset}"
                if self.offset < 0:
                    return f"{pval.name}{self.offset}"
                return f"{pval.name}"
            return ""
        return f"{self.int_value:}"

    def int_vstr(self) -> str:
        "Prints the parameter with integers in Verilog hex format"

        if self.is_parameter:
            pval = ParameterFinder().find(self.txt_value)
            if pval:
                if self.offset > 0:
                    return f"{pval.name}+{self.offset}"
                if self.offset < 0:
                    return f"{pval.name}{self.offset}"
                return f"{pval.name}"
            return ""
        return f"'h{self.int_value:x}"

    def set_int(self, value: int) -> None:
        "Set the value as an integer value"
        self.int_value = value
        self.is_parameter = False

    def set_param(self, uuid: str, offset: int = 0) -> None:
        "Set the parameter as parameter"
        self.txt_value = uuid
        self.offset = offset
        self.is_parameter = True

    def resolve(self) -> int:
        "Map the parameter to an integer file, resolving references"

        if not self.is_parameter:
            return self.int_value

        resolver = ParameterResolver()
        finder = ParameterFinder()
        value = finder.find(self.txt_value)
        if value:
            return resolver.resolve(value) + self.offset
        return 0

    def json_decode(self, data):
        "Decode from a JSON compatible dictionary"

        self.is_parameter = data["is_parameter"]
        self.offset = data["offset"]
        self.func = ParamFunc(data.get("func", 0))
        if self.is_parameter:
            self.txt_value = data["value"]
            self.int_value = 0
        else:
            self.txt_value = ""
            self.int_value = int(data["value"], 0)

    def json(self):
        "Convert to JSON compatible dictionary"

        val = {
            "is_parameter": self.is_parameter,
            "offset": self.offset,
            "func": int(self.func),
        }
        if self.is_parameter:
            val["value"] = self.txt_value
        else:
            val["value"] = f"{self.int_value}"
        return val
