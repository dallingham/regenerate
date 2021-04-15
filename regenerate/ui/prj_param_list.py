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
from regenerate.db import PrjParameterData
from regenerate.ui.columns import EditableColumn
from regenerate.ui.enums import PrjParameterCol
from regenerate.ui.utils import find_next_free, check_hex


class PrjParameterListMdl(Gtk.ListStore):
    """
    Provides the list of parameters for the module. The parameter information
    consists of name, default value, and the minimum and maximum values.
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
        val_list = []
        for val in self:
            if val[0]:
                try:
                    def_val = int(val[1], 16)
                except ValueError:
                    def_val = 1

                val_list.append((val[0], def_val))


class PrjParameterList:
    """
    Container for the Parameter List control logic.
    """

    def __init__(self, obj, callback):
        self._obj = obj
        self._col = None
        self._prj = None
        self._model = None
        self._build_instance_table()
        self._obj.set_sensitive(True)
        self._callback = callback

    def set_prj(self, prj):
        """
        Sets the database for the paramter list, and repopulates the list
        from the database.
        """
        self._prj = prj
        self._obj.set_sensitive(True)
        self.populate()

    def populate(self):
        """
        Loads the data from the project
        """
        if self._prj is not None:
            self._model.clear()
        for param in self._prj.parameters.get():
            self.append(param.name, param.value)

    def remove_clicked(self):
        """Remove parameter"""
        name = self.get_selected()
        self._prj.remove_parameter(name)
        self.remove_selected()
        self._callback()

    def add_clicked(self):
        """Add a new parameter, creating an unused name"""
        current = set({p[0] for p in self._prj.parameters.get()})
        name = find_next_free("pParameter", current)
        self._model.new_instance(name, hex(1))
        self._prj.add_parameter(name, hex(1))
        self._callback()

    def _name_changed(self, _cell, path, new_text, _col):
        """
        Called when the name field is changed.
        """
        current = set({p[0] for p in self._prj.parameters.get()})

        name = self._model[path][PrjParameterCol.NAME]
        if name != new_text and new_text not in current:
            self._model[path][PrjParameterCol.NAME] = new_text
            self._prj.remove_parameter(name)
            self._prj.add_parameter(
                new_text, int(self._model[path][PrjParameterCol.VALUE], 16)
            )
            self._callback()

    def _value_changed(self, _cell, path, new_text, _col):
        """Called when the base address field is changed."""
        if check_hex(new_text) is False:
            return

        name = self._model[path][PrjParameterCol.NAME]
        value = int(new_text, 16)

        self._model[path][PrjParameterCol.VALUE] = new_text
        self._prj.remove_parameter(name)
        self._prj.add_parameter(name, value)
        self._callback()

    def _build_instance_table(self):
        """
        Builds the columns, adding them to the address map list.
        """
        column = EditableColumn(
            "Parameter Name", self._name_changed, PrjParameterCol.NAME
        )
        column.set_min_width(300)
        column.set_sort_column_id(PrjParameterCol.NAME)
        self._obj.append_column(column)
        self._col = column

        column = EditableColumn(
            "Value",
            self._value_changed,
            PrjParameterCol.VALUE,
            True,
            tooltip="Value of the parameter",
        )
        column.set_sort_column_id(PrjParameterCol.VALUE)
        column.set_min_width(150)
        self._obj.append_column(column)

        self._model = PrjParameterListMdl()
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
        obj = PrjParameterData(name, value)
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
        return model.get_value(node, PrjParameterCol.NAME)

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
            _ = model.get_value(node, PrjParameterCol.NAME)
            model.remove(node)
            self._callback()


def get_row_data(map_obj):
    """Get the data from the row"""
    return (map_obj.name, hex(int(map_obj.value)))
