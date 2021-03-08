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
from regenerate.ui.enums import PrjCol
from regenerate.db import RegisterDb

class ProjectModel(Gtk.ListStore):
    """
    Provides the model for the project list
    """

    def __init__(self):
        super().__init__(str, str, str, bool, bool, object)

        Gdk.threads_init()
        self.file_list = {}
        self.paths = set()

    def set_markup(self, node, modified):
        """Sets the icon if the project has been modified"""

        if modified:
            icon = Gtk.STOCK_EDIT
        else:
            icon = None
        self.set_value(node, PrjCol.ICON, icon)
        self.set_value(node, PrjCol.MODIFIED, modified)

    def is_not_saved(self):
        """True if the project is not saved"""

        for item in self:
            if item[PrjCol.MODIFIED]:
                return True
        return False

    def load_icons(self):
        """Clear paths and the file list"""
        self.paths = set()
        self.file_list = {}

    def add_dbase(self, filename: Path, dbase: RegisterDb, modified=False):
        """Add the the database to the model"""

        filename = Path(filename)
        
        base = filename.stem
        if modified:
            node = self.append(
                row=[base, Gtk.STOCK_EDIT, str(filename), True, False, dbase]
            )
        else:
            node = self.append(row=[base, "", str(filename), False, False, dbase])
        self.file_list[str(filename)] = node
        self.paths.add(filename.parent)
        return node


class ProjectList:
    """Project list"""

    def __init__(self, obj, selection_callback):
        self.__obj = obj
        self.__obj.get_selection().connect("changed", selection_callback)
        self.__obj.set_reorderable(True)
        self.__model = None
        self.__build_prj_window()

        self.__obj.set_tooltip_column(PrjCol.FILE)

        self.__obj.enable_model_drag_source(
            Gdk.ModifierType.BUTTON1_MASK,
            [("text/plain", 0, 0)],
            Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE,
        )
        self.__obj.connect("drag-data-get", self.drag_data_get)

        self.factory = Gtk.IconFactory()
        filename = os.path.join(INSTALL_PATH, "media", "ModifiedIcon.png")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        iconset = Gtk.IconSet(pixbuf)
        self.factory.add("out-of-date", iconset)
        self.factory.add_default()

    def drag_data_get(self, treeview, _context, selection, _target_id, _etime):
        """Get the data when a drag starts"""

        tselection = treeview.get_selection()
        model, tree_iter = tselection.get_selected()

        prj_name = model.get_value(tree_iter, PrjCol.NAME)
        prj_obj = model.get_value(tree_iter, PrjCol.OBJ)
        data = "{0}:{1:x}".format(prj_name, 1 << prj_obj.db.address_bus_width)

        try:
            selection.set(selection.target, 8, data)
        except AttributeError:
            selection.set_text(data, -1)

    def set_model(self, model):
        """Sets the model"""

        self.__model = model
        self.__obj.set_model(model)

    def __build_prj_window(self):
        """Build the project window"""

        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("", renderer, stock_id=1)
        column.set_min_width(20)
        self.__obj.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Register Sets", renderer, text=0)
        column.set_min_width(140)
        self.__obj.append_column(column)

    def get_selected(self):
        """Return the selected object"""
        return self.__obj.get_selection().get_selected()

    def select(self, node):
        """Select the specified row"""

        selection = self.__obj.get_selection()
        if node and selection:
            selection.select_iter(node)

    def select_path(self, path):
        """Select based on path"""

        selection = self.__obj.get_selection()
        selection.select_path(path)
