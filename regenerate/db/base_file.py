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
Provides the base class for JSON based data.

The base class inherits from NameBase, adding the modified flag and the
file path.
"""

from pathlib import Path
from typing import Union, Dict, Any
from operator import methodcaller
import json

from .logger import LOGGER
from .const import BLK_EXT
from .name_base import NameBase, Uuid


class BaseFile(NameBase):
    """
    Base class for file based data.

    Contains the modified flag and the filename, along with the information
    contained in the parent NameBase class.
    """

    def __init__(
        self, name: str = "", uuid: Uuid = Uuid(""), filename: str = ""
    ):
        """
        Initialize the class.

        Parameters:
           name: Name of the object
           uuid: Unique ID, should either be loaded from a save file, or generated
                 by the object itself.

        """
        super().__init__(name, uuid)

        self._modified = False
        self._filename = Path(filename)

    def last_saved(self) -> int:
        """
        Return the modified timestamp of the file.

        Return:
           int: modified time of the file in nanoseconds

        """
        if self._filename:
            return self._filename.stat().st_mtime_ns
        return 0

    @property
    def filename(self) -> Path:
        """
        Return the filename as a path.

        Returns:
           Path: path associated with the object

        """
        return self._filename

    @filename.setter
    def filename(self, value: Union[str, Path]) -> None:
        """
        Set the filename, converting to a path, and fixing the suffix.

        Parameters:
           Union[str, Path]: Path of the file object

        """
        self._filename = Path(value).with_suffix(BLK_EXT)

    @property
    def modified(self):
        """
        Set the flag that indicates that the file has been modified.

        Returns:
           bool: Modification status

        """
        return self._modified

    @modified.setter
    def modified(self, value: bool) -> None:
        """
        Set the value of the modified flag.

        Parameters:
           value (bool): New value of the modified flag

        """
        self._modified = bool(value)

    def save_json(self, data: Dict[str, Any], path: Path) -> None:
        """
        Save the data in JSON format to the specifed file.

        Parameters:
           data (Dict[str, Any]): data to save

           path (Path): Path to save the file

        """
        try:
            with path.open("w") as ofile:
                ofile.write(
                    json.dumps(
                        data, default=methodcaller("json"), sort_keys=True
                    )
                )
        except FileNotFoundError as msg:
            LOGGER.error(str(msg))

        self._modified = False
