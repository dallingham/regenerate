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
from regenerate.db import LOGGER, ParameterData, Block
from regenerate.ui.columns import EditableColumn
from regenerate.ui.enums import ParameterCol
from regenerate.db.enums import ResetType
from regenerate.ui.utils import check_hex


class ParameterListMdl(Gtk.ListStore):
    """
    Provides the list of parameters for the module. The parameter information
    consists of name, default value, and the minimum and maximum values.
    """

    def __init__(self):
        super().__init__(str, str, str, str, object)

    def new_instance(self, obj):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        node = self.append(
            (obj.name, hex(obj.value), hex(obj.min_val), hex(obj.max_val), obj)
        )
        return self.get_path(node)

    # def get_values(self):
    #     """Returns the list of instance tuples from the model."""
    #     return [val[-1] for row in self]


class ParameterList:
    """Container for the Parameter List control logic."""

    def __init__(self, obj, add, remove, callback):
        self._obj = obj
        self._col = None
        self._db = None
        self._model = None
        self._build_instance_table()
        self._obj.set_sensitive(True)
        self._callback = callback
        self.remove = remove
        add.connect("clicked", self.add_clicked)
        remove.connect("clicked", self.remove_clicked)
        obj.get_selection().connect("changed", self.selection_changed)

    def selection_changed(self, obj):
        _, node = obj.get_selected()
        if node:
            self.remove.set_sensitive(True)
        else:
            self.remove.set_sensitive(False)

    def set_db(self, dbase):
        """
        Sets the database for the paramter list, and repopulates the list
        from the database.
        """
        self._db = dbase
        self._obj.set_sensitive(True)
        self.populate()

    def populate(self):
        """Loads the data from the project"""

        if self._db is not None:
            self._model.clear()
        for param in self._db.parameters.get():
            self.append(param)
        self.remove.set_sensitive(False)

    def remove_clicked(self, _obj):
        """Remove the entry"""

        name = self.get_selected()
        self._db.parameters.remove(name)
        self.remove_selected()
        self._callback()

    def add_clicked(self, _obj):
        """Add a new entry, after picking a new name"""
        current = set({p.name for p in self._db.parameters.get()})
        base = "pParameter"
        index = 0

        name = f"{base}{index}"
        while name in current:
            index = index + 1
            name = f"{base}{index}"

        new_item = ParameterData(name, 1, 0, 0xFFFFFFFF)

        self._model.new_instance(new_item)
        self._db.parameters.add(new_item)
        self._callback()

    def _name_changed(self, _cell, path, new_text, _col):
        """Called when the name field is changed."""

        current = set({p.name for p in self._db.parameters.get()})

        name = self._model[path][ParameterCol.NAME]
        if name != new_text and new_text not in current:
            self._model[path][ParameterCol.NAME] = new_text
            self._model[path][ParameterCol.OBJ].name = new_text
            self._callback()
        self.update_db(name, new_text)

    def _value_changed(self, _cell, path, new_text, _col):
        """Called when the base address field is changed."""
        if check_hex(new_text) is False:
            return

        name = self._model[path][ParameterCol.NAME]
        value = int(new_text, 0)
        min_val = int(self._model[path][ParameterCol.MIN], 0)
        max_val = int(self._model[path][ParameterCol.MAX], 0)

        if not (min_val <= value <= max_val):
            LOGGER.warning(
                "Default value (0x%x) for %s must be between the "
                "minimum (0x%x) and the maximum (0x%x)",
                value,
                name,
                min_val,
                max_val,
            )
        else:
            self._model[path][ParameterCol.VALUE] = f"0x{value:x}"
            self._model[path][ParameterCol.OBJ].value = value
            self._callback()

    def _min_changed(self, _cell, path, new_text, _col):
        if check_hex(new_text) is False:
            return

        name = self._model[path][ParameterCol.NAME]
        min_val = int(new_text, 16)
        value = int(self._model[path][ParameterCol.VALUE], 0)
        max_val = int(self._model[path][ParameterCol.MAX], 0)

        if min_val > value:
            LOGGER.warning(
                "Minimum value (0x%x) for %s must be less than or  "
                "equal default value (0x%x)",
                min_val,
                name,
                value,
            )
        else:
            self._model[path][ParameterCol.MIN] = hex(int(new_text, 0))
            self._model[path][ParameterCol.OBJ].min_val = int(new_text, 0)
            self._callback()

    def _max_changed(self, _cell, path, new_text, _col):
        if check_hex(new_text) is False:
            return

        name = self._model[path][ParameterCol.NAME]
        max_val = int(new_text, 0)
        min_val = int(self._model[path][ParameterCol.MIN], 0)
        value = int(self._model[path][ParameterCol.VALUE], 0)

        if max_val < value:
            LOGGER.warning(
                "Maximum value (0x%x) for %s must be greater than or  "
                "equal default value (0x%x)",
                max_val,
                name,
                value,
            )
        else:
            self._model[path][ParameterCol.MAX] = hex(int(new_text, 0))
            self._model[path][ParameterCol.OBJ].max_val = int(new_text, 0)
            self._callback()

    def _build_instance_table(self):
        """
        Builds the columns, adding them to the address map list.
        """
        column = EditableColumn(
            "Parameter Name", self._name_changed, ParameterCol.NAME
        )
        column.set_min_width(300)
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
        column.set_min_width(150)
        self._obj.append_column(column)

        column = EditableColumn(
            "Minimum Value",
            self._min_changed,
            ParameterCol.MIN,
            True,
            tooltip="Minimum value of the parameter",
        )
        column.set_min_width(150)
        self._obj.append_column(column)

        column = EditableColumn(
            "Maximum Value",
            self._max_changed,
            ParameterCol.MAX,
            True,
            tooltip="Maximum value of the parameter",
        )
        column.set_min_width(150)
        self._obj.append_column(column)

        self._model = ParameterListMdl()
        self._obj.set_model(self._model)

    def clear(self):
        """Clears the data from the list"""

        self._model.clear()

    def append(self, param):
        """Add the data to the list."""

        self._model.append(row=get_row_data(param))

    def get_selected(self):
        """Removes the selected node from the list"""

        (model, node) = self._obj.get_selection().get_selected()
        if node is None:
            return None

        if len(model.get_path(node)) > 1:
            return None
        return model.get_value(node, ParameterCol.NAME)

    def remove_selected(self):
        """Removes the selected node from the list"""

        select_data = self._obj.get_selection().get_selected()
        if select_data is None or select_data[1] is None:
            return

        (model, node) = select_data
        path = model.get_path(node)
        if len(path) > 1:
            # remove group from address map
            pass
        else:
            _ = model.get_value(node, ParameterCol.NAME)
            model.remove(node)
            self._callback()

    def update_db(self, name, new_text):
        if type(self._db) != Block:
            for reg in self._db.get_all_registers():
                if reg.dimension_is_param():
                    if reg.dimension_str == name:
                        reg.dimension = new_text
                for field in reg.get_bit_fields():
                    if field.reset_type == ResetType.PARAMETER:
                        if name == field.reset_parameter:
                            field.reset_parameter = new_text


def get_row_data(map_obj):
    """Return row data from the object"""
    return (
        map_obj.name,
        f"0x{map_obj.value:x}",
        f"0x{map_obj.min_val:x}",
        f"0x{map_obj.max_val:x}",
        map_obj,
    )
