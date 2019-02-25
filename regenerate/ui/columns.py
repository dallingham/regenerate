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

import gtk
import pango


class ToggleColumn(gtk.TreeViewColumn):
    """
    A TreeViewColumn that has editable cells. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(self, title, change_callback, source_column,
                 visible_callback=None):

        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        if change_callback:
            renderer.connect('toggled', change_callback, source_column)

        super(ToggleColumn, self).__init__(
            title, renderer,
            active=source_column
        )

        if visible_callback:
            self.set_cell_data_func(renderer, visible_callback)


class EditableColumn(gtk.TreeViewColumn):
    """
    A TreeViewColumn that has editable cells. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(self, title, change_callback, source_column, monospace=False,
                 visible_callback=None):

        self.renderer = gtk.CellRendererText()
        if change_callback:
            self.renderer.set_property('editable', True)
            self.renderer.connect('edited', change_callback, source_column)
        self.renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        if monospace:
            self.renderer.set_property('family', "Monospace")

        super(EditableColumn, self).__init__(
            title,
            self.renderer,
            text=source_column
        )

        self.renderer.connect('editing-canceled', self.edit_canceled)
        self.renderer.connect('editing-started', self.edit_started)
        self.path = 0
        self.entry = None

        if visible_callback:
            self.set_cell_data_func(self.renderer, visible_callback)

    def edit_started(self, cell, entry, path):
        self.path = path
        self.entry = entry

    def edit_canceled(self, obj):
        val = self.entry.get_text()
        self.renderer.emit('edited', self.path, val)


class ComboMapColumn(gtk.TreeViewColumn):
    """
    A TreeViewColumn that has a menu of options. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(self, title, callback, data_list, source_column, dtype=int,
                 visible_callback=None):

        renderer = gtk.CellRendererCombo()
        model = gtk.ListStore(str, dtype)
        for item in data_list:
            model.append(row=item)
        renderer.set_property("text-column", 0)
        renderer.set_property("model", model)
        renderer.set_property("has-entry", False)
        renderer.set_property('editable', True)
        if callback:
            renderer.connect('changed', callback, source_column)

        super(ComboMapColumn, self).__init__(
            title,
            renderer,
            text=source_column
        )

        if visible_callback:
            self.set_cell_data_func(renderer, visible_callback)


class SwitchComboMapColumn(gtk.TreeViewColumn):
    """
    A TreeViewColumn that has a menu of options. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(self, title, callback, data_list0, data_list1, data_list2,
                 source_column, dtype=int):

        self.renderer = gtk.CellRendererCombo()

        self.model = []

        self.model.append(gtk.ListStore(str, dtype))
        for item in data_list0:
            self.model[0].append(row=item)

        self.model.append(gtk.ListStore(str, dtype))
        for item in data_list1:
            self.model[1].append(row=item)

        self.model.append(gtk.ListStore(str, dtype))
        for item in data_list2:
            self.model[2].append(row=item)

        self.renderer.set_property("text-column", 0)
        self.renderer.set_property("model", self.model[0])
        self.renderer.set_property("has-entry", False)
        self.renderer.set_property('editable', True)
        self.renderer.connect('changed', callback, source_column)

        super(SwitchComboMapColumn, self).__init__(
            title,
            self.renderer,
            text=source_column
        )

    def set_mode(self, i):
        self.renderer.set_property("model", self.model[i])
