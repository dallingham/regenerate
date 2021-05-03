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
Project model and list
"""

from gi.repository import Gtk, Gdk
from regenerate.ui.enums import SelectCol
from regenerate.db import RegisterDb


class ProjectModel(Gtk.ListStore):
    """
    Provides the model for the project list
    """

    def __init__(self):
        super().__init__(str, str)

        Gdk.threads_init()
        self.file_list = {}
        self.paths = set()

    def set_markup(self, node, modified):
        """Sets the icon if the project has been modified"""
        if modified:
            icon = Gtk.STOCK_EDIT
        else:
            icon = None
        self.set_value(node, SelectCol.ICON, icon)

    def is_not_saved(self):
        """True if the project is not saved"""

        for item in self:
            if item[SelectCol.ICON] != "":
                return True
        return False

    def load_icons(self):
        """Clear paths and the file list"""
        self.paths = set()
        self.file_list = {}

    def add_dbase(self, regset: RegisterDb, modified=False):
        """Add the the database to the model"""

        base = regset.filename.stem
        if modified:
            node = self.append(row=[Gtk.STOCK_EDIT, base])
        else:
            node = self.append(row=["", base])

        self.file_list[str(regset.filename)] = node
        self.paths.add(regset.filename.parent)
        return node
