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
Containers for data groups, modified flags, and file paths
"""

from pathlib import Path
from operator import methodcaller
import json

from .logger import LOGGER


class Container:

    block_data_path = ""
    regset_data_path = ""

    def __init__(self):
        self._filename = Path("")
        self.modified = False

    def _save_data(self, data):
        try:
            with self._filename.open("w") as ofile:
                ofile.write(
                    json.dumps(data, default=methodcaller("json"), indent=4)
                )
        except FileNotFoundError as msg:
            LOGGER.error(str(msg))

    def save(self):
        ...