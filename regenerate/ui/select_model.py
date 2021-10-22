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
Provides a common Gtk.TreeModel for the register and block tabs
"""

from typing import Union

from gi.repository import Gtk
from regenerate.db import Block, RegisterDb

from .enums import SelectCol


class SelectModel(Gtk.ListStore):
    "Provides the model for the select lists"

    def __init__(self):
        "Model consists of ICON, DISPLAY, OBJECT"

        super().__init__(bool, str, object)

        self.file_list = {}
        self.paths = set()

    def update(self):
        "Update the EDIT flag"

        for row in self:
            if row[SelectCol.OBJ].modified:
                row[SelectCol.ICON] = True
            else:
                row[SelectCol.ICON] = False

    def set_markup(self, node, modified: bool) -> None:
        """Sets the icon if the project has been modified"""

        self.set_value(node, SelectCol.ICON, modified)

    def add(self, obj: Union[Block, RegisterDb], modified=False):
        """Add the database to the model"""

        if modified or obj.modified:
            node = self.append(row=[True, obj.name, obj])
        else:
            node = self.append(row=[False, obj.name, obj])

        self.file_list[str(obj.filename)] = node
        self.paths.add(obj.filename.parent)
        return node
