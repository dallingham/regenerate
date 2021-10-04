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
IP-XACT register definition exporter. Writes an IP-XACT (or the older Spirit)
XML files describing the registers.
"""

from pathlib import Path
from regenerate.db import BitType, RegisterDb, RegProject
from .writer_base import RegsetWriter, ExportInfo, ProjectType, find_template

#
# Map regenerate types to UVM type strings
#
ACCESS_MAP = {
    BitType.READ_ONLY: "read-only",
    BitType.READ_ONLY_LOAD: "read-only",
    BitType.READ_ONLY_VALUE: "read-only",
    BitType.READ_ONLY_CLEAR_LOAD: "read-only",
    BitType.READ_ONLY_VALUE_1S: "read-only",
    BitType.READ_WRITE: "read-write",
    BitType.READ_WRITE_1S: "read-write",
    BitType.READ_WRITE_1S_1: "read-write",
    BitType.READ_WRITE_LOAD: "read-write",
    BitType.READ_WRITE_LOAD_1S: "read-write",
    BitType.READ_WRITE_LOAD_1S_1: "read-write",
    BitType.READ_WRITE_SET: "read-write",
    BitType.READ_WRITE_SET_1S: "read-write",
    BitType.READ_WRITE_SET_1S_1: "read-write",
    BitType.READ_WRITE_CLR: "read-write",
    BitType.READ_WRITE_CLR_1S: "read-write",
    BitType.READ_WRITE_CLR_1S_1: "read-write",
    BitType.WRITE_1_TO_CLEAR_SET: "read-write",
    BitType.WRITE_1_TO_CLEAR_SET_CLR: "read-write",
    BitType.WRITE_1_TO_CLEAR_SET_1S: "read-write",
    BitType.WRITE_1_TO_CLEAR_SET_1S_1: "read-write",
    BitType.WRITE_1_TO_CLEAR_LOAD: "read-write",
    BitType.WRITE_1_TO_CLEAR_LOAD_1S: "read-write",
    BitType.WRITE_1_TO_CLEAR_LOAD_1S_1: "read-write",
    BitType.WRITE_1_TO_SET: "read-write",
    BitType.WRITE_ONLY: "write-only",
    BitType.READ_WRITE_PROTECT: "read-write",
    BitType.READ_WRITE_PROTECT_1S: "read-write",
}

WRITE_MAP = {
    BitType.WRITE_1_TO_CLEAR_SET: "oneToClear",
    BitType.WRITE_1_TO_CLEAR_SET_CLR: "oneToClear",
    BitType.WRITE_1_TO_CLEAR_SET_1S: "oneToClear",
    BitType.WRITE_1_TO_CLEAR_SET_1S_1: "oneToClear",
    BitType.WRITE_1_TO_CLEAR_LOAD: "oneToClear",
    BitType.WRITE_1_TO_CLEAR_LOAD_1S: "oneToClear",
    BitType.WRITE_1_TO_CLEAR_LOAD_1S_1: "oneToClear",
    BitType.WRITE_1_TO_SET: "oneToSet",
}


class IpXactWriter(RegsetWriter):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(self, project: RegProject, regset: RegisterDb):
        super().__init__(project, regset)
        self.scope = "ipxact"
        self.schema = [
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            'xmlns:ipxact="http://www.accellera.org/XMLSchema/IPXACT/1685-2014"',
            'xsi:schemaLocation="http://www.accellera.org/XMLSchema/IPXACT/1685-2014 http://www.accellera.org/XMLSchema/IPXACT/1685-2014/index.xsd"',
        ]

    def write(self, filename: Path):
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """

        template = find_template("ipxact.template")

        with filename.open("w") as ofile:
            text = template.render(
                db=self._regset,
                WRITE_MAP=WRITE_MAP,
                ACCESS_MAP=ACCESS_MAP,
                scope=self.scope,
                refs=self.schema,
            )
            ofile.write(text)


class SpiritWriter(IpXactWriter):
    def __init__(self, project: RegProject, regset: RegisterDb):
        super().__init__(project, regset)
        self.scope = "spirit"
        self.schema = [
            'xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"'
        ]


EXPORTERS = [
    (
        ProjectType.REGSET,
        ExportInfo(
            IpXactWriter,
            ("XML", "IP-XACT Registers"),
            "IP-XACT files",
            ".xml",
            "ip-xact",
        ),
    ),
    (
        ProjectType.REGSET,
        ExportInfo(
            IpXactWriter,
            ("XML", "Spirit 1.4 Registers"),
            "Spirit files",
            ".spirit",
            "spirit",
        ),
    ),
]
