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

import os
from pathlib import Path

from gi.repository import Gtk, Gdk, GdkPixbuf, Pango
from regenerate.settings.paths import INSTALL_PATH
from regenerate.ui.enums import PrjCol, BlockCol
from regenerate.db import RegisterDb
from regenerate.db.containers import RegSetContainer


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
        return

        if modified:
            icon = Gtk.STOCK_EDIT
        else:
            icon = None
        self.set_value(node, BlockCol.ICON, icon)

    #        self.set_value(node, BlockCol.MODIFIED, modified)

    def is_not_saved(self):
        """True if the project is not saved"""

        for item in self:
            if item[BlockCol.ICON] != "":
                return True
        return False

    def load_icons(self):
        """Clear paths and the file list"""
        self.paths = set()
        self.file_list = {}

    def add_dbase(self, regset: RegSetContainer, modified=False):
        """Add the the database to the model"""

        base = regset.filename.stem
        if modified:
            node = self.append(row=[Gtk.STOCK_EDIT, base])
            print([Gtk.STOCK_EDIT, base])
        else:
            node = self.append(row=["", base])
            print(["", base])

        self.file_list[str(regset.filename)] = node
        self.paths.add(regset.filename.parent)
        return node
