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

from typing import Dict, Tuple

from .parammap import ParameterData


class ParameterResolver:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(ParameterResolver, cls).__new__(cls)
        return cls.instance

    top_params: Dict[str, ParameterData] = {}
    block_params: Dict[str, ParameterData] = {}
    regset_params: Dict[str, ParameterData] = {}
    overrides: Dict[Tuple[str, str], int] = {}

    def __init__(self):
        self.def_regset = None
        self.def_reginst = None
        self.def_blkinst = None

    def default_regset(self, name: str):
        self.def_regset = name

    def default_reginst(self, name: str):
        self.def_reginst = name

    def default_blkinst(self, name: str):
        self.def_blkinst = name

    def __repr__(self):
        return "ParameterResolver()"

    def add_regset_parameter(self, regset: str, data: ParameterData):
        if regset in self.regset_params:
            self.regset_params[regset][data.name] = data
        else:
            self.regset_params[regset] = {data.name: data}

    def get_regset_parameters(self, regset: str):
        return self.regset_params[regset]

    def resolve(
        self,
        pname: str,
        regset: str = None,
        reg_inst: str = None,
        block_inst: str = None,
    ):
        if reg_inst:
            override = self.overrides.get((regset, pname))
            if override is not None:
                return override
        if regset and regset in self.regset_params:
            a = self.regset_params[regset][pname]
            return a.value
        if self.def_regset and self.def_regset in self.regset_params:
            b = self.regset_params[self.def_regset][pname]
            return b.value
        return 0
