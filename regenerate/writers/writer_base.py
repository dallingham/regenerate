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
import time
import pwd
from pathlib import Path
from typing import List, Tuple, Callable
from enum import IntEnum
from typing import Optional
from collections import namedtuple
from jinja2 import FileSystemLoader, Environment

from regenerate.db import RegisterDb, RegProject, Block
from ..settings.paths import INSTALL_PATH


class ProjectType(IntEnum):
    REGSET = 0
    BLOCK = 1
    PROJECT = 2


ExportInfo = namedtuple(
    "ExportInfo",
    [
        "obj_class",
        "type",
        "description",
        "full_description",
        "extension",
        "id",
    ],
)


def get_username():
    return pwd.getpwnam(os.environ["USER"])[4].split(",")[0]


class WriterBase:
    """
    Writes the register information to the output file determined
    by the derived class.
    """

    def __init__(
        self, project: RegProject, dbase: Optional[RegisterDb]
    ) -> None:
        self._dbase = dbase
        self._project = project
        self._project_name = ""
        if dbase:
            self._set_values_init(dbase)

    def set_project(self, obj: RegProject) -> None:
        self._project = obj
        self._project_name = obj.short_name

    def _set_values_init(self, dbase: RegisterDb, _instance_name=None) -> None:
        self._comments = dbase.overview_text
        self._module = dbase.name
        self._clock = dbase.ports.clock_name
        self._addr = dbase.ports.address_bus_name
        self._addr_width = dbase.ports.address_bus_width

        self._data_width = dbase.ports.data_bus_width
        self._reset = dbase.ports.reset_name
        self._reset_level = dbase.ports.reset_active_level
        self._byte_enables = dbase.ports.byte_strobe_name
        self._be_level = dbase.ports.byte_strobe_active_level
        self._data_in = dbase.ports.write_data_name
        self._data_out = dbase.ports.read_data_name
        self._write_strobe = dbase.ports.write_strobe_name
        self._read_strobe = dbase.ports.read_strobe_name
        self._filename = "UNKNOWN"
        self._project_name = "UNKNOWN"
        self._local_path = os.path.join(INSTALL_PATH, "site_local")
        self._data_path = os.path.join(INSTALL_PATH, "data")

        self._prefix = ""

    def _write_header_comment(self, ofile, default_path, comment_char="#"):
        """
        Looks for the header include file to allow users to define their own
        header. If not, default to the built in header.
        """
        try:
            cfile = os.path.join(self._data_path, default_path)
            with open(cfile) as ifile:
                data = "".join(ifile.readlines())
        except IOError:
            try:
                cfile = os.path.join(self._data_path, "site_comment.txt")
                with open(cfile) as ifile:
                    data = comment_char.join(ifile.readlines())
            except IOError:
                try:
                    cfile = os.path.join(INSTALL_PATH, "comment.txt")
                    with open(cfile) as ifile:
                        data = comment_char.join(ifile.readlines())
                except IOError:
                    data = "\n"
            data = comment_char + data

        self.write_header(ofile, data)

    def write_header(self, ofile, line):
        """
        Goes through the specified text, substituting information if needed.
        """
        current_time = time.time()
        year = str(time.localtime(current_time)[0])
        date = time.asctime(time.localtime(current_time))

        user = get_username()

        module = self._dbase.name

        fixed = self._filename.upper().replace(".", "_")
        line = line.replace("$M$", module)
        line = line.replace("$Y$", year)
        line = line.replace("$f$", self._filename)
        line = line.replace("$F$", fixed)
        line = line.replace("$D$", date)
        line = line.replace("$U$", user)
        ofile.write(line)

    def write(self, filename: Path):
        """
        The child class must override this to provide an implementation.
        """
        raise NotImplementedError


class ProjectWriter:
    """
    Writes the register information to the output file determined
    by the derived class.
    """

    def __init__(self, project: RegProject) -> None:
        self._project = project
        self._project_name = project.short_name

    def set_project(self, obj: RegProject) -> None:
        self._project = obj
        self._project_name = obj.short_name

    def write(self, filename: Path):
        """
        The child class must override this to provide an implementation.
        """
        raise NotImplementedError


def find_template(
    template_name: str,
    filters: Optional[List[Tuple[str, Callable]]] = None,
):

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


class RegsetWriter:
    """
    Writes the register information to the output file determined
    by the derived class.
    """

    def __init__(self, project: RegProject, regset: RegisterDb) -> None:
        self._project = project
        self._regset = regset

    def set_project(self, obj: RegProject) -> None:
        self._project = obj
        self._project_name = obj.short_name

    def write(self, filename: Path):
        """
        The child class must override this to provide an implementation.
        """
        raise NotImplementedError


class BlockWriter:
    """
    Writes the register information to the output file determined
    by the derived class.
    """

    def __init__(self, project: RegProject, block: Block) -> None:
        self._project = project
        self._block = block
        self._project_name = project.short_name

    def set_project(self, project: RegProject) -> None:
        self._project = project
        self._project_name = project.short_name

    def write(self, filename: Path):
        """
        The child class must override this to provide an implementation.
        """
        raise NotImplementedError
