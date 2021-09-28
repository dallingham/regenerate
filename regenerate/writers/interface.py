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
Provides the Verilog RTL generation
"""

import os
import re
import copy
import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, TextIO, Set, Dict, NamedTuple

from jinja2 import FileSystemLoader, Environment
from regenerate.db import (
    TYPES,
    TYPE_TO_OUTPUT,
    Register,
    BitField,
    ParamValue,
    BitType,
    RegisterDb,
    RegProject,
    ParameterFinder,
)
from regenerate.writers.writer_base import (
    RegsetWriter,
    ExportInfo,
    ProjectType,
)


class InterfaceGen(RegsetWriter):
    """"""

    def __init__(self, project: RegProject, regset: RegisterDb):
        super().__init__(project, regset)

    def write(self, filename: Path) -> None:
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """

        env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), "templates")
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        template = env.get_template("interface.template")

        with filename.open("w") as ofile:
            ofile.write(
                template.render(
                    ports=self._regset.ports,
                )
            )


EXPORTERS = [
    (
        ProjectType.REGSET,
        ExportInfo(
            InterfaceGen,
            ("RTL", "Register Set Interface"),
            "SystemVerilog files",
            ".sv",
            "rtl-interface",
        ),
    ),
]
