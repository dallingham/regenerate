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
Manages the reading of the project file (.rprj)
"""
import json


class ProjectReaderJSON:
    """
    Reads the project information from the project file.
    """

    def __init__(self, project):
        self._prj = project

    def open(self, name):
        with open(name) as ofile:
            data = ofile.read()

        json_data = json.loads(data)
        self._prj.json_decode(json_data)
