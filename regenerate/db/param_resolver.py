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
Provides the ability to resolve parameters into their final integer
ovalues based of the default value and any overrides.
"""

from typing import Dict

from .param_data import ParameterData, ParameterFinder


class ParameterResolver:
    """
    Resolves parameters into their final integer value
    """

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(ParameterResolver, cls).__new__(cls)
        return cls.instance

    top_overrides: Dict[str, Dict[str, int]] = {}
    reginst_overrides: Dict[str, Dict[str, int]] = {}
    blkinst_id = ""
    reginst_id = ""

    def __init__(self):
        ...

    def set_reginst(self, uuid: str) -> None:
        "Sets the instance name"

        self.reginst_id = uuid

    def set_blkinst(self, uuid: str) -> None:
        "Sets the instance name"

        self.blkinst_id = uuid

    def clear(self) -> None:
        """
        Clears out all overrides. Typically called when a new project is
        loaded.
        """
        self.top_overrides = {}
        self.reginst_overrides = {}

    def __repr__(self) -> str:
        return "ParameterResolver()"

    def add_regset_override(
        self, reginst_id: str, param_id: str, data: int
    ) -> None:
        "Adds an override for a parameter in a register set"

        if reginst_id not in self.reginst_overrides:
            self.reginst_overrides[reginst_id] = {param_id: data}
        else:
            self.reginst_overrides[reginst_id][param_id] = data

    def add_blockinst_override(
        self, blkinst_id: str, param_id: str, data: int
    ) -> None:
        "Adds an override for a parameter a block instance"

        if blkinst_id not in self.top_overrides:
            self.top_overrides[blkinst_id] = {param_id: data}
        else:
            self.top_overrides[blkinst_id][param_id] = data

    def resolve_reg(self, param: ParameterData) -> int:
        "Resolve a parameter looking for overrides"

        if not self.reginst_id:
            return param.value
        if (
            self.reginst_id in self.reginst_overrides
            and param.uuid in self.reginst_overrides[self.reginst_id]
        ):
            val = self.reginst_overrides[self.reginst_id][param.uuid]
            return val
        return param.value

    def resolve_blk(self, value) -> int:
        "Resolve a parameter looking for overrides"

        if not self.blkinst_id:
            if value.is_parameter:
                new_param = ParameterFinder().find(value.txt_value)
                if new_param:
                    return new_param.value
                return 0
            return value.int_value
        if (
            self.blkinst_id in self.top_overrides
            and value.is_parameter
            and value.txt_value in self.top_overrides[self.blkinst_id]
        ):
            new_val = self.top_overrides[self.blkinst_id][value.txt_value]
            if new_val.is_parameter:
                new_param = ParameterFinder().find(new_val.txt_value)
                return new_param.value
            else:
                return new_val.int_value
        return value.value

    def resolve(self, param: ParameterData) -> int:
        "Resolve a parameter looking for overrides"
        val = self.resolve_reg(param)
        if isinstance(val, int):
            return val
        new_val = self.resolve_blk(val)
        return new_val
