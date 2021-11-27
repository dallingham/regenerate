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

from pathlib import Path
from typing import Union, Dict, Any
from operator import methodcaller
import json

from .logger import LOGGER
from .name_base import NameBase


class BaseFile(NameBase):
    "Base class for file based data"

    def __init__(self, name: str = "", uuid: str = "", filename: str = ""):
        super().__init__(name, uuid)

        self.modified = False
        self._filename = Path(filename)

    def last_saved(self) -> int:
        "Returns the modified timestamp of the file"
        if self._filename:
            return self._filename.stat().st_mtime_ns
        return 0

    @property
    def filename(self) -> Path:
        "Returns the filename as a path"
        return self._filename

    @filename.setter
    def filename(self, value: Union[str, Path]) -> None:
        "Sets the filename, converting to a path, and fixing the suffix"

        self._filename = Path(value).with_suffix(BLK_EXT)

    def save_json(self, data: Dict[str, Any], path: Path):
        "Saves the data to the specifed file in JSON format"
        try:
            with path.open("w") as ofile:
                ofile.write(
                    json.dumps(
                        data, default=methodcaller("json"), sort_keys=True
                    )
                )
        except FileNotFoundError as msg:
            LOGGER.error(str(msg))

        self.modified = False
