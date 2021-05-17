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

from typing import Dict
from .param_data import ParameterData


class ParameterResolver:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(ParameterResolver, cls).__new__(cls)
        return cls.instance

    top_overrides: Dict[str, Dict[str, "ParamValue"]] = {}
    reginst_overrides: Dict[str, Dict[str, "ParamValue"]] = {}
    blk_inst = ""
    reg_inst = ""

    def __init__(self):
        ...

    def set_reginst(self, name):
        self.reg_inst = name
        return ""

    def clear(self):
        self.top_overrides = {}
        self.reginst_overrides = {}

    def __repr__(self):
        return "ParameterResolver()"

    def add_regset_override(
        self, reg_inst_id: str, param_id: str, data: "ParamValue"
    ):
        if reg_inst_id not in self.reginst_overrides:
            self.reginst_overrides[reg_inst_id] = {param_id: data}
        else:
            self.reginst_overrides[reg_inst_id][param_id] = data

    def add_blockinst_override(
        self, blk_inst_id: str, param_id: str, data: "ParamValue"
    ):
        if blk_inst_id not in self.top_overrides:
            self.top_overrides[blk_inst_id] = {param_id: data}
        else:
            self.top_overrides[blk_inst_id][param_id] = data

    def resolve_reg(
        self,
        param: ParameterData,
    ):
        if not self.reg_inst:
            return param.value
        if (
            self.reg_inst in self.reginst_overrides
            and param.uuid in self.reginst_overrides[self.reg_inst]
        ):
            val = self.reginst_overrides[self.reg_inst][param.uuid]
            return val
        return param.value

    def resolve_blk(
        self,
        param: ParameterData,
    ):
        if not self.blk_inst:
            return param.value
        if (
            self.blk_inst in self.top_overrides
            and param.uuid in self.top_overrides[self.blk_inst]
        ):
            return self.top_overrides[self.blk_inst][param.uuid]
        return param.value

    def resolve(self, param: ParameterData):
        val = self.resolve_reg(param)
        if type(val) == int:
            return val
        new_val = self.resolve_blk(val)
        return new_val
