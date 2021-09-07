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
Provides TreeView column to simplify usage.
"""

from gi.repository import Gtk, Pango


class BaseColumn(Gtk.TreeViewColumn):
    def __init__(self, title, cell_renderer, tooltip=None, **kwargs):

        super().__init__(cell_renderer=cell_renderer, **kwargs)

        header = Gtk.Label(title)
        header.show()
        self.set_widget(header)
        if tooltip:
            try:
                tooltips = Gtk.Tooltips()
                tooltips.set_tip(header, tooltip)
            except AttributeError:
                header.set_tooltip_text(tooltip)


class ToggleColumn(BaseColumn):
    """
    A TreeViewColumn that has editable cells. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(
        self,
        title,
        change_callback,
        source_column,
        tooltip=None,
        visible_callback=None,
    ):

        renderer = Gtk.CellRendererToggle()
        renderer.set_property("activatable", True)
        if change_callback:
            renderer.connect("toggled", change_callback, source_column)

        super().__init__(
            title,
            cell_renderer=renderer,
            active=source_column,
            tooltip=tooltip,
        )

        if visible_callback:
            self.set_cell_data_func(renderer, visible_callback)


class EditableColumn(BaseColumn):
    """
    A TreeViewColumn that has editable cells. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(
        self,
        title,
        change_callback,
        source_column,
        monospace=False,
        visible_callback=None,
        placeholder=None,
        tooltip=None,
    ):

        self.renderer = Gtk.CellRendererText()
        if change_callback:
            self.renderer.set_property("editable", True)
            self.renderer.connect("edited", change_callback, source_column)
        if placeholder:
            try:
                self.renderer.set_property("placeholder-text", placeholder)
            except TypeError:
                pass

        self.renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        if monospace:
            self.renderer.set_property("family", "Monospace")

        super().__init__(
            title, self.renderer, text=source_column, tooltip=tooltip
        )

        self.renderer.connect("editing-canceled", self.edit_canceled)
        self.renderer.connect("editing-started", self.edit_started)
        self.path = 0
        self.entry = None

        if visible_callback:
            self.set_cell_data_func(self.renderer, visible_callback)

    def edit_started(self, _cell, entry, path):
        """Called when editing of the cell begins"""
        self.path = path
        self.entry = entry

    def edit_canceled(self, _obj):
        """
        Called with editing of the cell is canceled, and we need
        to restore the original value.
        """
        val = self.entry.get_text()
        self.renderer.emit("edited", self.path, val)


class ReadOnlyColumn(BaseColumn):
    """
    A TreeViewColumn that has no editable cells. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(
        self,
        title,
        source_column,
        monospace=False,
        visible_callback=None,
        _placeholder=None,
        tooltip=None,
    ):

        self.renderer = Gtk.CellRendererText()
        super().__init__(
            title, self.renderer, text=source_column, tooltip=tooltip
        )

        self.renderer.set_property("editable", False)
        self.renderer.set_property("ellipsize", Pango.EllipsizeMode.END)

        if monospace:
            self.renderer.set_property("family", "Monospace")

        if visible_callback:
            self.set_cell_data_func(self.renderer, visible_callback)


class ComboMapColumn(BaseColumn):
    """
    A TreeViewColumn that has a menu of options. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(
        self,
        title,
        callback,
        data_list,
        source_column,
        dtype=int,
        visible_callback=None,
        tooltip=None,
    ):

        self.renderer = Gtk.CellRendererCombo()
        super().__init__(
            title, self.renderer, tooltip=tooltip, text=source_column
        )

        self.model = Gtk.ListStore(str, dtype)
        for item in data_list:
            self.model.append(row=item)

        self.renderer.set_property("text-column", 0)
        self.renderer.set_property("model", self.model)
        self.renderer.set_property("has-entry", False)
        self.renderer.set_property("editable", True)
        if callback:
            self.renderer.connect("changed", callback, source_column)

        if visible_callback:
            self.set_cell_data_func(self.renderer, visible_callback)

    def update_menu(self, item_list):
        """Update the menu with the supplied items."""
        self.item_list = item_list[:]
        self.model.clear()
        for item in item_list:
            self.model.append(row=item)


class MenuEditColumn(BaseColumn):
    """
    A TreeViewColumn that has a menu of options. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(
        self,
        title,
        menu_callback,
        text_callback,
        data_list,
        source_column,
        _dtype=str,
        visible_callback=None,
        tooltip=None,
    ):

        self.renderer = Gtk.CellRendererCombo()
        self._model = Gtk.ListStore(str, str)
        self.update_menu(data_list)
        self.renderer.set_property("text-column", 0)
        self.renderer.set_property("model", self._model)
        self.renderer.set_property("has-entry", True)
        self.renderer.set_property("editable", True)
        self.renderer.set_property("family", "Monospace")
        self.renderer.connect("changed", menu_callback, source_column)
        self.renderer.connect("edited", text_callback, source_column)

        super().__init__(
            title, self.renderer, tooltip=tooltip, text=source_column
        )

        if visible_callback:
            self.set_cell_data_func(self.renderer, visible_callback)

    def update_menu(self, item_list):
        """Update the menu with the supplied items."""
        self.item_list = item_list[:]
        self._model.clear()
        for item in item_list:
            self._model.append(row=item)


class EditComboMapColumn(BaseColumn):
    """
    A TreeViewColumn that has a menu of options. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(
        self,
        title,
        callback,
        data_list,
        source_column,
        dtype=str,
        visible_callback=None,
        tooltip=None,
    ):

        self.dtype = dtype
        self.renderer = Gtk.CellRendererText()
        self.renderer.set_property("editable", True)
        self.path = None
        self.update_menu(data_list)

        if callback:
            self.renderer.connect("edited", callback, source_column)

        super().__init__(
            title, self.renderer, tooltip=tooltip, text=source_column
        )

        self.renderer.connect(
            "editing-started", self.renderer_text_editing_started
        )

        if visible_callback:
            self.set_cell_data_func(self.renderer, visible_callback)

    def update_menu(self, item_list):
        """Update the menu from the passed list"""
        self.item_list = item_list[:]
        self.model = Gtk.ListStore(str, object)
        for item in item_list:
            self.model.append(row=item)

        self.completion = Gtk.EntryCompletion(model=self.model)
        self.completion.set_text_column(1)
        self.completion.connect("match-selected", self.renderer_match_selected)

    def renderer_match_selected(self, _completion, model, tree_iter):
        """
        The model and tree_iter passed in here are the model from the
        EntryCompletion, which may or may not be the same as the model of the
        Treeview
        """
        text_match = self.model[tree_iter][1]
        model[self.path][1] = text_match

    def renderer_text_editing_started(self, _renderer, editable, path):
        """since the editable widget gets created for every edit, we need to
        connect the completion to every editable upon creation"""
        editable.set_completion(self.completion)
        self.path = path  # save the path for later usage


class SwitchComboMapColumn(BaseColumn):
    """
    A TreeViewColumn that has a menu of options. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(
        self,
        title,
        callback,
        data_list0,
        data_list1,
        data_list2,
        source_column,
        dtype=int,
        tooltip=None,
    ):

        self.renderer = Gtk.CellRendererCombo()

        self.model = []

        self.model.append(Gtk.ListStore(str, dtype))
        for item in data_list0:
            self.model[0].append(row=item)

        self.model.append(Gtk.ListStore(str, dtype))
        for item in data_list1:
            self.model[1].append(row=item)

        self.model.append(Gtk.ListStore(str, dtype))
        for item in data_list2:
            self.model[2].append(row=item)

        self.renderer.set_property("text-column", 0)
        self.renderer.set_property("model", self.model[0])
        self.renderer.set_property("has-entry", False)
        self.renderer.set_property("editable", True)
        self.renderer.connect("changed", callback, source_column)

        super().__init__(
            title, self.renderer, tooltip=tooltip, text=source_column
        )

    def set_mode(self, i):
        """Set the model for the renderer"""
        self.renderer.set_property("model", self.model[i])
