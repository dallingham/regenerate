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

from pathlib import Path

from jinja2 import FileSystemLoader, Environment
from .writer_base import (
    RegsetWriter,
    ProjectType,
    find_template,
)
from .export_info import ExportInfo


class InterfaceGen(RegsetWriter):
    "Interface generator"

    def write(self, filename: Path) -> None:
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """

        template = find_template("interface.template")

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
            "RTL",
            "Register Set Interface",
            "SystemVerilog files",
            "SystemVerilog interface for the register module control bus",
            ".sv",
            "{}_if.sv",
            {},
            "rtl-interface",
        ),
    ),
]
