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

from regenerate.db import BitField, TYPES, LOGGER
from regenerate.writers.writer_base import WriterBase
import time
import os
from jinja2 import Template

#
# Map regenerate types to UVM type strings
#
ACCESS_MAP = {
    BitField.TYPE_READ_ONLY: "read-only",
    BitField.TYPE_READ_ONLY_LOAD: "read-only",
    BitField.TYPE_READ_ONLY_VALUE: "read-only",
    BitField.TYPE_READ_ONLY_CLEAR_LOAD: "read-only",
    BitField.TYPE_READ_ONLY_VALUE_1S: "read-only",
    BitField.TYPE_READ_WRITE: "read-write",
    BitField.TYPE_READ_WRITE_1S: "read-write",
    BitField.TYPE_READ_WRITE_1S_1: "read-write",
    BitField.TYPE_READ_WRITE_LOAD: "read-write",
    BitField.TYPE_READ_WRITE_LOAD_1S: "read-write",
    BitField.TYPE_READ_WRITE_LOAD_1S_1: "read-write",
    BitField.TYPE_READ_WRITE_SET: "read-write",
    BitField.TYPE_READ_WRITE_SET_1S: "read-write",
    BitField.TYPE_READ_WRITE_SET_1S_1: "read-write",
    BitField.TYPE_READ_WRITE_CLR: "read-write",
    BitField.TYPE_READ_WRITE_CLR_1S: "read-write",
    BitField.TYPE_READ_WRITE_CLR_1S_1: "read-write",
    BitField.TYPE_WRITE_1_TO_CLEAR_SET: "read-write",
    BitField.TYPE_WRITE_1_TO_CLEAR_SET_CLR: "read-write",
    BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S: "read-write",
    BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S_1: "read-write",
    BitField.TYPE_WRITE_1_TO_CLEAR_LOAD: "read-write",
    BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S: "read-write",
    BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1: "read-write",
    BitField.TYPE_WRITE_1_TO_SET: "read-write",
    BitField.TYPE_WRITE_ONLY: "write-only",
    BitField.TYPE_READ_WRITE_PROTECT: "read-write",
    BitField.TYPE_READ_WRITE_PROTECT_1S:  "read-write",
    }

WRITE_MAP = {
    BitField.TYPE_WRITE_1_TO_CLEAR_SET: "oneToClear",
    BitField.TYPE_WRITE_1_TO_CLEAR_SET_CLR: "oneToClear",
    BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S: "oneToClear",
    BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S_1: "oneToClear",
    BitField.TYPE_WRITE_1_TO_CLEAR_LOAD: "oneToClear",
    BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S: "oneToClear",
    BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1: "oneToClear",
    BitField.TYPE_WRITE_1_TO_SET: "oneToSet"
    }


class SpiritWriter(WriterBase):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    def __init__(self, project, dbase):
        WriterBase.__init__(self, project, dbase)

    def write(self, filename):
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """
        
        dirpath = os.path.dirname(__file__)

        template = Template(file(os.path.join(dirpath, "templates", "ipxact.templ")).read(), 
                            trim_blocks=True,
                            lstrip_blocks=True)

        with open(filename, "w") as of:
            of.write(template.render(db = self._dbase,
                                     WRITE_MAP=WRITE_MAP,
                                     ACCESS_MAP=ACCESS_MAP,
                                     scope="spirit",
                                     refs=['xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"']
                                     ))

