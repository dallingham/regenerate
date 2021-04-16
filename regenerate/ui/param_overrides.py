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
from regenerate.ui.columns import ReadOnlyColumn, EditableColumn
from regenerate.db.parammap import ParameterData
from regenerate.ui.utils import check_hex
from regenerate.ui.enums import ParameterCol


class OverridesListMdl(Gtk.ListStore):
    """
    Provides the list of parameters for the module. The parameter information
    consists of name, default value, and the minimum and maximum values.
    """

    def __init__(self):
        super().__init__(str, str, object)

    def new_instance(self, name, value, obj):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        node = self.append((name, value, obj))
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
                    def_val = int(val[1], 0)
                except ValueError:
                    def_val = 1
                val_list.append((val[0], def_val, val[2]))
        return val_list


class OverridesList:
    """
    Container for the Parameter List control logic.
    """

    def __init__(self, obj, add, remove, callback):
        self._obj = obj
        self._col = None
        self.prj = None
        self.add = add
        self.remove = remove
        self._model = None

        self._build_table()
        self._obj.set_sensitive(True)
        self._callback = callback
        self.remove.connect("clicked", self.remove_clicked)

    def set_project(self, prj):
        """
        Sets the database for the paramter list, and repopulates the list
        from the database.
        """
        self.prj = prj
        self._obj.set_sensitive(True)
        self.populate()

    def populate(self):
        """
        Loads the data from the project
        """
        self.set_menu()

    def set_menu(self):
        self.menu = Gtk.Menu()
        for override in self.build_overrides_list(self.prj):
            menu_item = Gtk.MenuItem(override[0])
            menu_item.connect("activate", self.menu_selected, override)
            menu_item.show()
            self.menu.append(menu_item)
        self.add.set_popup(self.menu)

    def remove_clicked(self, _obj):
        name = self.get_selected()
        self.prj.parameters.remove(name)
        self.remove_selected()
        self._callback()

    def menu_selected(self, _obj, data):
        label, info = data
        self._model.new_instance(label, hex(info[1].value), info)
        self._callback()

    def _value_changed(self, _cell, path, new_text, _col):
        """Called when the base address field is changed."""
        if check_hex(new_text) is False:
            return

        name = self._model[path][ParameterCol.NAME]
        value = int(new_text, 16)

        self._model[path][ParameterCol.VALUE] = new_text
        self.prj.parameters.remove(name)
        self.prj.add_parameter(name, value)
        self._callback()

    def _build_table(self):
        """
        Builds the columns, adding them to the address map list.
        """
        self.column = ReadOnlyColumn(
            "Parameter",
            0,
        )
        self.column.set_min_width(300)
        self.column.set_sort_column_id(0)
        self._obj.append_column(self.column)
        self._col = self.column

        column = EditableColumn(
            "Value",
            self._value_changed,
            1,
            True,
            tooltip="Value of the parameter",
        )
        column.set_min_width(150)
        self._obj.append_column(column)

        self._model = OverridesListMdl()
        self._obj.set_model(self._model)

    def clear(self):
        """
        Clears the data from the list
        """
        self._model.clear()

    def append(self, name, value, max_val, min_val):
        """
        Add the data to the list.
        """
        obj = ParameterData(name, value, min_val, max_val)
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
            _ = model.get_value(node, ParameterCol.NAME)
            model.remove(node)
            self._callback()

    def build_overrides_list(self, project):
        param_list = []
        for blkinst in project.block_insts:
            blkinst_name = blkinst.inst_name
            block = project.blocks[blkinst.block]
            for param in block.parameters.get():
                param_list.append(
                    (f"{blkinst_name}.{param.name}", (blkinst, param))
                )
        return param_list


class BlockOverridesList(OverridesList):
    def build_overrides_list(self, block):
        param_list = []
        for reginst in block.regset_insts:
            regset = block.regsets[reginst.set_name]
            for param in regset.parameters.get():
                param_list.append(
                    (f"{reginst.inst}.{param.name}", (reginst.inst, param))
                )
        return param_list


def get_row_data(map_obj):
    return (map_obj.name, hex(int(map_obj.value)), map_obj)
