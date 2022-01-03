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
Provides a base class for data access routines.

Allows abstractions other than simple file based reading.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple

from .const import REG_EXT


class DataReader(ABC):
    """
    Abtrace base class for reading data.

    Allows different sources to be used instead of just files. Allows for
    applications to provide their own custom data readers (e.g. git
    instead of files).
    """

    def __init__(self, top_path: Path):
        """
        Initialize the data reader.

        Parameters:
            top_path (Path): path to the source.

        """
        self.path = top_path

    def resolve_path(self, _name: Path) -> Tuple[Path, Path]:
        """
        Convert the path into a usable format.

        Converts into something that makes sense to the specific data reader.

        Parameters:
            _name (Path): unused in the base class

        Returns:
            Tuple[Path, Path]: returns the resolved path and the original path

        """
        return Path(self.path), Path(self.path)

    @abstractmethod
    def read(self, _filename: Path) -> str:
        """
        Read ASCII data from the source.

        Parameters:
            _filename (Path): unused in the base class

        Returns:
            str: Stream of characters from the source

        """
        return ""

    @abstractmethod
    def read_bytes(self, _filename: Path) -> bytes:
        """
        Read binary data from the source.

        Parameters:
            _filename (Path): unused in the base class

        Returns:
            bytes: Stream of bytes from the source

        """
        return b""


class FileReader(DataReader):
    """
    Provide the standard file based reader.

    The default reader, based on file system access. This is the only reader
    provided by the core regenerate system.
    """

    def resolve_path(self, name: Path) -> Tuple[Path, Path]:
        """
        Resolve the relative path into a full path.

        Parameters:
            _name (Path): unused in the base class

        Returns:
            Tuple[Path, Path]: returns the resolved path and the original path

        """
        filename = self.path.parent / name
        new_file_path = filename.with_suffix(REG_EXT).resolve()
        return filename, new_file_path

    def read(self, filename: Path) -> str:
        """
        Read ASCII data from the source.

        Parameters:
            filename (Path): filename to read

        Returns:
            str: Stream of characters from the source

        """
        fullpath = Path(self.path) / filename
        with fullpath.open() as ofile:
            data = ofile.read()
        return data

    def read_bytes(self, filename: Path) -> bytes:
        """
        Read binary data from the source.

        Parameters:
            filename (Path): filename to read

        Returns:
            bytes: Stream of bytes from the source

        """
        fullpath = self.path / filename
        with fullpath.open("rb") as ofile:
            data = ofile.read()
        return data
