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
Provides the common base for the register and block sidebars
"""

from typing import Callable, List, Type, Optional
from pathlib import Path
from gi.repository import Gtk, Pango

from regenerate.db import NameBase
from regenerate.settings.paths import HELP_PATH

from .enums import SelectCol


class SelectModel(Gtk.ListStore):
    "Provides the model for the select lists"

    def __init__(self, add_callback: Optional[Callable] = None):
        "Model consists of ICON, DISPLAY, OBJECT"

        super().__init__(bool, str, object)

        self.file_list = {}
        self.paths = set()
        self.callback = add_callback

    def update(self):
        "Update the EDIT flag"
        # pylint: disable=E1133

        for row in self:
            row[SelectCol.NAME] = row[SelectCol.OBJ].name
            if row[SelectCol.OBJ].modified:
                row[SelectCol.ICON] = True
            else:
                row[SelectCol.ICON] = False

    def set_markup(self, node, modified: bool) -> None:
        """Sets the icon if the project has been modified"""

        self.set_value(node, SelectCol.ICON, modified)

    def add(self, obj: Type[NameBase], modified=False):
        """Add the database to the model"""
        if modified or obj.modified:
            node = self.append(row=[True, obj.name, obj])
        else:
            node = self.append(row=[False, obj.name, obj])

        self.file_list[str(obj.filename)] = node
        self.paths.add(obj.filename.parent)
        if self.callback:
            self.callback(obj, node)
        return node


class SelectList:
    "List for the sidebar"

    def __init__(self, obj: Gtk.TreeView, title: str):
        self._obj = obj
        self._obj.set_reorderable(True)
        self._model = None
        self._build_window(title)

    def set_selection_callback(self, selection_callback: Callable):
        "Called with the selection is changed"
        self._obj.get_selection().connect("changed", selection_callback)

    def update_data(self):
        "Refreshes the data in the model after the block has been changed"

        if self._model:
            for row in self._model:
                row[SelectCol.NAME] = row[SelectCol.OBJ].name

    def set_items(self, name_list: List[NameBase]):
        "Updates after a change in the project"

        if self._model:
            self._model.clear()
            for item in sorted(name_list, key=lambda item: item.name):
                self._model.add(item)

    def set_model(self, model):
        """Sets the model"""

        self._model = model
        self._obj.set_model(model)

    def _build_window(self, title: str):
        """Build the block window"""

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        renderer.set_padding(6, 3)
        column = Gtk.TreeViewColumn(title, renderer, text=1)
        column.set_min_width(140)
        column.set_cell_data_func(renderer, _set_format)
        self._obj.append_column(column)

    def get_selected(self):
        """Return the selected object"""
        return self._obj.get_selection().get_selected()

    def get_selected_object(self) -> Optional[Type[NameBase]]:
        """Return the selected object"""
        model, node = self._obj.get_selection().get_selected()
        if node:
            return model[node][SelectCol.OBJ]
        return None

    def select(self, node) -> None:
        """Select the specified row"""

        selection = self._obj.get_selection()
        if node and selection:
            selection.select_iter(node)

    def select_path(self, path: int) -> None:
        """Select based on path"""

        selection = self._obj.get_selection()
        selection.select_path(path)


class SelectSidebar:
    "Provides the sidebar for the block and register set tabs"

    def __init__(
        self,
        sidebar_obj: Gtk.Box,
        title: str,
        help_html: str,
        new_callback: Callable,
        add_callback: Callable,
        remove_callback: Callable,
        add_model_callback: Callable = None,
    ):
        self._model = SelectModel(add_model_callback)

        widget_list = sidebar_obj.get_children()

        select_notebook = widget_list[0]
        button_box = widget_list[1]
        buttons = button_box.get_children()
        buttons[0].connect("clicked", new_callback)
        buttons[1].connect("clicked", add_callback)
        buttons[2].connect("clicked", remove_callback)

        self.notebook = select_notebook
        self.notebook.set_show_tabs(False)
        children = select_notebook.get_children()

        tree = children[0].get_children()[0]
        self._list = SelectList(tree, title)
        self._list.set_model(self._model)

        help_win = children[1]
        _load_help(help_win, help_html)

    def set_selection_changed_callback(self, callback: Callable):
        "Sets the callback for the list"
        self._list.set_selection_callback(callback)

    def set_items(self, name_list: List[NameBase]) -> None:
        "Sets the items in the sidebar"
        self._list.set_items(name_list)

    def clear(self) -> None:
        "Clear the model"
        self._model.clear()

    def size(self) -> int:
        "Returns the number of entries in the list"
        return len(self._model)

    def add(self, item: NameBase) -> Gtk.TreeIter:
        "Adds a new item to the list"
        return self._model.add(item)

    def get_selected(self):
        """Return the selected object"""
        return self._list.get_selected()

    def get_selected_object(self) -> Optional[Type[NameBase]]:
        """Return the selected object"""
        return self._list.get_selected_object()

    def select_path(self, path: int) -> None:
        "Select an item in the list by the path"
        self._list.select_path(path)

    def select(self, node: Gtk.TreeIter) -> None:
        "Select an item based on the TreeIter"
        self._list.select(node)

    def update(self) -> None:
        "Update the model"
        self._model.update()

    def remove_selected(self) -> str:
        "Remove the selected item, returning the UUID of the object removed"

        model, node = self.get_selected()
        obj = self.get_selected_object()
        model.remove(node)
        return obj.uuid


def _load_help(help_win, help_html: str) -> None:
    "Load the help HTML file"

    help_path = Path(HELP_PATH) / help_html
    try:
        with help_path.open() as ifile:
            help_win.load_html(ifile.read(), "text/html")
    except IOError:
        pass


def _set_format(_col, renderer, model, node, _data):
    "Sets the format based on if the item has been modfied"

    if model.get_value(node, 0):
        renderer.set_property("weight", Pango.Weight.BOLD)
        renderer.set_property("style", Pango.Style.ITALIC)
    else:
        renderer.set_property("weight", Pango.Weight.NORMAL)
        renderer.set_property("style", Pango.Style.NORMAL)
