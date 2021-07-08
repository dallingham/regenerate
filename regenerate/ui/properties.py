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

from gi.repository import GObject, Gtk
from regenerate.settings.paths import GLADE_PROP
from .columns import EditableColumn


class Properties:
    """
    Properties dialog interface.
    """

    def __init__(self, project):
        self.__project = project
        self.__builder = Gtk.Builder()
        self.__builder.add_from_file(str(GLADE_PROP))
        self.__properties = self.__builder.get_object("properties")

        self.__builder.get_object("short_name").set_text(project.short_name)
        self.__builder.get_object("project_name").set_text(project.name)
        self.__builder.get_object("company_name").set_text(
            project.company_name
        )
        self.__builder.connect_signals(self)

        self.__tree = self.__builder.get_object("address_tree")
        self.__model = Gtk.ListStore(str, str, GObject.TYPE_UINT64)
        self.__tree.set_model(self.__model)

        column = EditableColumn("Map Name", self.map_name_changed, 0)
        column.set_min_width(200)
        self.__tree.append_column(column)

        column = EditableColumn("Base Address", self.map_address_changed, 1)
        self.__tree.append_column(column)

        for base in project.get_address_maps():
            addr = project.get_address_base(base)
            self.__model.append(row=(base, f"{addr:x}", addr))

        self.__properties.show()

    def map_name_changed(self, _cell, path, new_text, _col):
        """Called when the map name changes"""

        node = self.__model.get_iter(path)
        name = self.__model.get_value(node, 0)
        value = self.__model.get_value(node, 2)
        try:
            self.__project.remove_address_map(name)
        except:
            pass
        self.__project.set_address_map(new_text, value)
        self.__model[path][0] = new_text

    def map_address_changed(self, _cell, path, new_text, _col):
        """Called with the address changes"""

        try:
            value = int(new_text, 16)
        except ValueError:
            pass
        if new_text:
            self.__project.set_address_map(new_text, value)
            self.__model[path][1] = f"{value:x}"
            self.__model[path][2] = value

    def on_remove_map_clicked(self, _obj):
        """Remove the selected map"""

        (model, node) = self.__tree.get_selection().get_selected()
        name = model.get_value(node, 0)
        model.remove(node)
        self.__project.remove_address_map(name)

    def on_add_map_clicked(self, _obj):
        """Add a new map"""

        self.__model.append(row=("<new name>", 0, 0))
        self.__project.set_address_map("<new name>", 0)

    def on_project_name_changed(self, obj):
        """
        Callback function from glade to handle changes in the project name.
        When the name is changed, it is immediately updated in the project
        object.
        """
        self.__project.name = obj.get_text()

    def on_company_name_changed(self, obj):
        """
        Callback function from glade to handle changes in the company name.
        When the name is changed, it is immediately updated in the project
        object.
        """
        self.__project.company_name = obj.get_text()

    def on_offset_insert_text(self, obj, new_text, _pos, *_extra):
        """Called when text is inserted into the offset field"""

        try:
            int(new_text, 16)
        except ValueError:
            obj.stop_emission("insert-text")

    def on_short_name_changed(self, obj):
        """
        Callback function from glade to handle changes in the short name.
        When the name is changed, it is immediately updated in the project
        object. The name must not have spaces, so we immediately replace any
        spaces.
        """
        self.__project.short_name = obj.get_text().replace(" ", "").strip()
        obj.set_text(self.__project.short_name)

    def on_close_button_clicked(self, _obj):
        """
        Closes the window
        """
        self.__properties.destroy()
