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

    def __init__(self, title, change_callback, source_column):
        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', change_callback, source_column)
        gtk.TreeViewColumn.__init__(self, title, renderer,
                                    active=source_column)


class EditableColumn(gtk.TreeViewColumn):
    """
    A TreeViewColumn that has editable cells. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(self, title, change_callback, source_column, 
                 monospace = False):
        renderer = gtk.CellRendererText()
        if change_callback:
            renderer.set_property('editable', True)
            renderer.connect('edited', change_callback, source_column)
        renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        if monospace:
            renderer.set_property('family', "Monospace")
        gtk.TreeViewColumn.__init__(self, title, renderer, text=source_column)


class ComboMapColumn(gtk.TreeViewColumn):
    """
    A TreeViewColumn that has a menu of options. The callback and listmodel
    columns are passed and used to create the CellRenderer.
    """

    def __init__(self, title, callback, data_list, source_column, dtype=int):
        renderer = gtk.CellRendererCombo()
        model = gtk.ListStore(str, dtype)
        for item in data_list:
            model.append(row=item)
        renderer.set_property("text-column", 0)
        renderer.set_property("model", model)
        renderer.set_property("has-entry", False)
        renderer.set_property('editable', True)
        renderer.connect('changed', callback, source_column)
        gtk.TreeViewColumn.__init__(self, title, renderer, text=source_column)
