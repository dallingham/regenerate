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
RegProject is the container object for a regenerate project
"""
from typing import Union
from pathlib import Path
from operator import methodcaller
import json

from .block import BlockContainer
from .containers import Container


class ProjectWriterJSON:
    """
    ProjectWriter writes the data in the project to the XML file.
    """

    def __init__(self, project):
        self._prj = project

    def save(self, path: Union[str, Path]):
        """Save the JSON data to the specified file"""

        new_path = Path(path)
        Container.block_data_path = new_path.parent

        with new_path.open("w") as ofile:
            ofile.write(
                json.dumps(self._prj, default=methodcaller("json"), indent=4)
            )
        self._prj.modified = False