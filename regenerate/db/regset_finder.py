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

from typing import Dict


class RegsetFinder:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(RegsetFinder, cls).__new__(cls)
        return cls.instance

    idmap: Dict[str, Dict[str, "RegisterDb"]] = {}
    filemap: Dict[str, Dict[str, "RegisterDb"]] = {}

    def __init__(self):
        ...

    def clear(self):
        self.idmap = {}
        self.filemap = {}

    def __repr__(self):
        return "RegsetFinder()"

    def find_by_id(self, uuid: str):
        return self.idmap.get(uuid)

    def find_by_file(self, filename: str):
        return self.filemap.get(str(filename))

    def register(self, db: "RegisterDb") -> None:
        self.filemap[str(db.filename)] = db
        self.idmap[db.uuid] = db
