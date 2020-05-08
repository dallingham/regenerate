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
Provides the Address List interface
"""

from gi.repository import Gtk
from regenerate.db import LOGGER
from regenerate.ui.columns import EditableColumn
from regenerate.ui.enums import ParameterCol
from regenerate.db.parammap import ParameterData


class ParameterListMdl(Gtk.ListStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    def __init__(self):
        super().__init__(str, str)

    def new_instance(self, name, val):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        node = self.append((name, val))
        return self.get_path(node)

    def append_instance(self, inst):
        """Adds the specified instance to the InstanceList"""
        return self.append(row=get_row_data(inst))

    def get_values(self):
        """Returns the list of instance tuples from the model."""
        return [(val[0], int(val[1], 16)) for val in self if val[0]]


class ParameterList(object):
    """
    Container for the Address Map control logic.
    """

    def __init__(self, obj, callback):
        self._obj = obj
        self._col = None
        self._db = None
        self._model = None
        self._build_instance_table()
        self._obj.set_sensitive(True)
        self._callback = callback

    def set_db(self, db):
        """
        Sets the database for the paramter list, and repopulates the list
        from the database.
        """
        self._db = db
        self._obj.set_sensitive(True)
        self.populate()

    def populate(self):
        """
        Loads the data from the project
        """
        if self._db is not None:
            self._model.clear()
        for (name, value) in self._db.get_parameters():
            self.append(name, value)

    def remove_clicked(self):
        name = self.get_selected()
        self._db.remove_parameter(name)
        self.remove_selected()
        self._callback()

    def add_clicked(self):
        current = set([p[0] for p in self._db.get_parameters()])
        base = "pParameter"
        index = 0

        name = "{}{}".format(base, index)
        while name in current:
            index = index + 1
            name = "{}{}".format(base, index)

        self._model.new_instance(name, "1")
        self._db.add_parameter(name, "1")
        self._callback()

    def _name_changed(self, cell, path, new_text, col):
        """
        Called when the name field is changed.
        """
        current = set([p[0] for p in self._db.get_parameters()])

        name = self._model[path][ParameterCol.NAME]
        if name != new_text and name not in current:
            self._model[path][ParameterCol.NAME] = new_text
            self._db.remove_parameter(name)
            self._db.add_parameter(
                new_text, int(self._model[path][ParameterCol.VALUE], 16)
            )
            self._callback()

    def _value_changed(self, cell, path, new_text, col):
        """
        Called when the base address field is changed.
        """
        try:
            value = int(new_text, 16)
        except ValueError:
            LOGGER.error('Illegal address: "%s"', new_text)
            return

        if new_text != self._model[path][ParameterCol.VALUE]:
            self._model[path][ParameterCol.VALUE] = new_text
            name = self._model[path][ParameterCol.NAME]
            self._db.remove_parameter(name)
            self._db.add_parameter(name, value)
            self._callback()

    def _build_instance_table(self):
        """
        Builds the columns, adding them to the address map list.
        """
        column = EditableColumn(
            "Parameter Name", self._name_changed, ParameterCol.NAME
        )
        column.set_min_width(250)
        column.set_sort_column_id(ParameterCol.NAME)
        self._obj.append_column(column)
        self._col = column

        column = EditableColumn(
            "Default Value",
            self._value_changed,
            ParameterCol.VALUE,
            True,
            tooltip="Default value of the parameter if it is not overridden",
        )
        column.set_sort_column_id(ParameterCol.VALUE)
        column.set_min_width(150)
        self._obj.append_column(column)

        self._model = ParameterListMdl()
        self._obj.set_model(self._model)

    def clear(self):
        """
        Clears the data from the list
        """
        self._model.clear()

    def append(self, name, value):
        """
        Add the data to the list.
        """
        obj = ParameterData(name, value)
        self._model.append(row=get_row_data(obj))

    def get_selected(self):
        """
        Removes the selected node from the list
        """
        (model, node) = self._obj.get_selection().get_selected()
        if node is None:
            return None

        if len(model.get_path(node)) > 1:
            return None
        return model.get_value(node, ParameterCol.NAME)

    def remove_selected(self):
        """
        Removes the selected node from the list
        """
        select_data = self._obj.get_selection().get_selected()
        if select_data is None or select_data[1] is None:
            return

        (model, node) = select_data
        path = model.get_path(node)
        if len(path) > 1:
            # remove group from address map
            pass
        else:
            name = model.get_value(node, ParameterCol.NAME)
            model.remove(node)
            self._callback()

    def add_new_map(self):
        """
        Creates a new address map and adds it to the project. Uses default
        data, and sets the first field to start editing.
        """
        name = self._create_new_map_name()
        obj = ParameterData(name, 0)
        node = self._model.append(row=get_row_data(obj))

        path = self._model.get_path(node)
        self._callback()
        self._prj.add_or_replace_address_map(obj)
        self._obj.set_cursor(path, self._col, start_editing=True)

    def _create_new_map_name(self):
        template = "NewMap"
        index = 0
        current_maps = set([i.name for i in self._prj.get_address_maps()])

        name = template
        while name in current_maps:
            name = "{}{}".format(template, index)
            index += 1
        return name

    def get_obj(self, path):
        return self._model[path][ParameterCol.OBJ]


def get_row_data(map_obj):
    return (map_obj.name, "{0:x}".format(int(map_obj.value)))
