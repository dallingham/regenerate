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
from typing import Optional
from operator import methodcaller
import json

from .block import Block
from .register_db import RegisterDb


class Container:
    def __init__(self):
        self.filename = Path("")
        self.modified = False

    def _save_data(self, data):
        with self.filename.open("w") as ofile:
            ofile.write(
                json.dumps(data, default=methodcaller("json"), indent=4)
            )

    def save(self):
        ...


class BlockContainer(Container):
    def __init__(self):
        super().__init__()
        self.block: Optional[Block, None] = None

    def save(self):
        if self.block:
            self._save_data(self.block)


class RegSetContainer(Container):
    def __init__(self):
        super().__init__()
        self.regset: Optional[RegisterDb, None] = None

    def save(self):
        if self.regset:
            self._save_data(self.regset)
