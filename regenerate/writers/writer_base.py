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
WriterBase - base class for objects that product output from the
             register database.
"""

import os
import pwd
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import List, Tuple, Callable, Dict, Any, Optional
from enum import IntEnum
from jinja2 import FileSystemLoader, Environment

from regenerate.db import RegisterDb, RegProject, Block


class ProjectType(IntEnum):
    "Project type enumeration"

    REGSET = 0
    BLOCK = 1
    PROJECT = 2


def get_username():
    "Returns the POSIX password name"
    return pwd.getpwnam(os.environ["USER"])[4].split(",")[0]


def find_template(
    template_name: str,
    filters: Optional[List[Tuple[str, Callable]]] = None,
):
    "Find the JINJA template"

    template_dir = Path(__file__).parent / "templates"

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    if filters:
        for (name, func) in filters:
            env.filters[name] = func

    return env.get_template(template_name)


class BaseWriter(metaclass=ABCMeta):
    "Common base function for all the writers"

    def __init__(self, project: RegProject, options: Dict[str, Any]) -> None:
        self._project = project
        self.options = options

    @abstractmethod
    def write(self, filename: Path):
        "The child class must override this to provide an implementation."
        ...


class ProjectWriter(BaseWriter):
    """
    Writes the register information to the output file determined
    by the derived class.
    """

    @abstractmethod
    def write(self, filename: Path):
        "The child class must override this to provide an implementation."
        ...


class RegsetWriter(BaseWriter):
    """
    Writes the register information to the output file determined
    by the derived class.
    """

    def __init__(
        self,
        project: RegProject,
        regset: RegisterDb,
        options: Dict[str, Any],
    ) -> None:
        super().__init__(project, options)
        self._regset = regset

    @abstractmethod
    def write(self, filename: Path):
        "The child class must override this to provide an implementation."
        ...


class BlockWriter(BaseWriter):
    """
    Writes the register information to the output file determined
    by the derived class.
    """

    def __init__(
        self,
        project: RegProject,
        block: Block,
        options: Dict[str, Any],
    ) -> None:
        super().__init__(project, options)
        self._block = block

    @abstractmethod
    def write(self, filename: Path):
        "The child class must override this to provide an implementation."
        ...
