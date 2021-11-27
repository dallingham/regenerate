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

from typing import Type


class CorruptProjectFile(Exception):
    "Syntax error in the project file"

    def __init__(self, filename: str, text: str):
        super().__init__()
        self.filename = filename
        self.msg = text

    def __str__(self):
        return f"{self.filename} is corrupt\n{self.msg}"


class CorruptBlockFile(Exception):
    "Syntax error in the block file"

    def __init__(self, filename: str, text: str):
        super().__init__()
        self.filename = filename
        self.msg = text

    def __str__(self):
        return f"{self.filename} is corrupt\n{self.msg}"


class CorruptRegsetFile(Exception):
    "Syntax error in the register set file"

    def __init__(self, filename: str, text: str):
        super().__init__()
        self.filename = filename
        self.msg = text

    def __str__(self):
        return f"{self.filename} is corrupt\n{self.msg}"


class IoErrorProjectFile(Exception):
    "I/O Error accessing the project file"

    def __init__(self, filename: str, error: Type[OSError]):
        super().__init__()
        self.filename = filename
        self.error = error

    def __str__(self):
        return f"Error accessing {self.filename}: {self.error.strerror}"


class IoErrorBlockFile(Exception):
    "I/O Error accessing the block file"

    def __init__(self, filename: str, error: Type[OSError]):
        super().__init__()
        self.filename = filename
        self.error = error

    def __str__(self):
        return f"Error accessing {self.filename}: {self.error.strerror}"


class IoErrorRegsetFile(Exception):
    "I/O Error accessing the register set file"

    def __init__(self, filename: str, error: Type[OSError]):
        super().__init__()
        self.filename = filename
        self.error = error

    def __str__(self):
        return f"Error accessing {self.filename}: {self.error.strerror}"
