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
Actual program. Parses the arguments, and initiates the main window
"""

import os
from jinja2 import Template
from regenerate.db.enums import BitType
from regenerate.writers.writer_base import WriterBase, ExportInfo

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


XML = [
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
    'xmlns:ipxact="http://www.accellera.org/XMLSchema/IPXACT/1685-2014"',
    'xsi:schemaLocation="http://www.accellera.org/XMLSchema/IPXACT/1685-2014 http://www.accellera.org/XMLSchema/IPXACT/1685-2014/index.xsd"',
]


class IpXactWriter(WriterBase):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(self, project, dbase):
        super().__init__(project, dbase)

    def write(self, filename):
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """

        dirpath = os.path.dirname(__file__)

        with open(os.path.join(dirpath, "templates", "ipxact.template")) as of:
            template = Template(
                of.read(), trim_blocks=True, lstrip_blocks=True
            )

        with open(filename, "w") as ofile:
            text = template.render(
                db=self._dbase,
                WRITE_MAP=WRITE_MAP,
                ACCESS_MAP=ACCESS_MAP,
                scope="ipxact",
                refs=XML,
            )
            ofile.write(text)


EXPORTERS = [
    (
        WriterBase.TYPE_BLOCK,
        ExportInfo(
            IpXactWriter,
            ("XML", "IP-XACT"),
            "IP-XACT files",
            ".xml",
            "ip-xact",
        ),
    )
]
