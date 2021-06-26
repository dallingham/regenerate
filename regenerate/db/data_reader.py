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
from .const import REG_EXT

class DataReader:

    def __init__(self, top_path):
        self.path = top_path

    def resolve_path(self):
        return path

    def read(self, path) -> str:
        return ""
    
    def read_bytes(self, path) -> bytes:
        return bytes("")


class FileReader(DataReader):

    def __init__(self, top_path):
        super(FileReader, self).__init__(top_path)


    def resolve_path(self, name: str):
        filename = Path(self.path).parent / name
        new_file_path = Path(filename).with_suffix(REG_EXT).resolve()
        return filename, new_file_path;

    def read(self, filename):
        fullpath = Path(self.path) / filename
        with fullpath.open() as ofile:
            data = ofile.read()
        return data

    def read_bytes(self, filename):
        fullpath = Path(self.path) / filename
        with fullpath.open("rb") as ofile:
            data = ofile.read()
        return data
    
    
