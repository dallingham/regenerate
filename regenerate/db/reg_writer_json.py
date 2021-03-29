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
Writes the XML file containing all the information in the register database
"""

from pathlib import Path
import json
from operator import methodcaller
from .const import REG_EXT
from .containers import Container


def create_backup_file(filename: Path):
    """
    Creates the backup file, renaming the existing file to a .bak extension,
    removing the original backup if it exists.
    """

    if filename.is_file() and filename.suffix == REG_EXT:
        backup = filename.with_suffix(f"{REG_EXT}.bak")
        if backup.is_file():
            backup.unlink()
        filename.rename(backup)


class RegWriterJSON:
    """Writes the XML file."""

    def __init__(self, dbase):
        self.dbase = dbase

    def save(self, filename: str):
        """Saves the data to the specified XML file."""

        new_path = Path(filename)

        with new_path.open("w") as ofile:
            ofile.write(
                json.dumps(self.dbase, default=methodcaller("json"), indent=4)
            )
        self.dbase.modified = False
