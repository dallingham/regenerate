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
from regenerate.db import (
    RegProject,
    Overrides,
    ParameterFinder,
    ParamValue,
    LOGGER,
)
from regenerate.ui.columns import ReadOnlyColumn, MenuEditColumn
from regenerate.ui.utils import check_hex
from regenerate.ui.enums import ParameterCol, OverrideCol


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

    def append_instance(self, path, inst):
        """Adds the specified instance to the InstanceList"""
        return self.append(row=get_row_data(path, inst))

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
        self.finder = ParameterFinder()
        self._obj = obj
        self._col = None
        self.prj = None
        self.add = add
        self.remove = remove
        self._model = None
        self._used = set()

        self._build_table()
        self._obj.set_sensitive(True)
        self._callback = callback
        self.remove.connect("clicked", self.remove_clicked)
        self._obj.get_selection().connect("changed", self.selection_changed)

    def selection_changed(self, obj):
        _, node = obj.get_selected()
        if node:
            self.remove.set_sensitive(True)
        else:
            self.remove.set_sensitive(False)

    def set_project(self, prj):
        """
        Sets the database for the paramter list, and repopulates the list
        from the database.
        """
        self.prj = prj
        self._obj.set_sensitive(True)
        self.populate()

    def update_display(self):
        self.set_menu()
        for row in self._model:
            data = row[OverrideCol.OBJ]
            path = self.prj.reginst[data.path].name
            param = data.parameter.name
            new_name = f"{path}.{param}"
            if row[OverrideCol.NAME] != new_name:
                row[OverrideCol.NAME] = new_name

    def populate(self):
        """
        Loads the data from the project
        """
        self._model.clear()
        self._used = set()
        for override in self.prj.overrides:
            path = ""
            for inst in self.prj.regset_insts:
                if inst.uuid == override.path:
                    path = inst.name
            self._model.append_instance(path, override)
            self._used.add(override.parameter)
        self.set_menu()

    def build_used(self):
        self._used = set()
        for row in self._model:
            self._used.add(row[-1].uuid)

    def set_menu(self):
        count = 0
        menu = Gtk.Menu()
        override_list, total = self.build_overrides_list(self.prj)
        for override in override_list:
            count = count + 1
            menu_item = Gtk.MenuItem(override[0])
            menu_item.connect("activate", self.menu_selected, override)
            menu_item.show()
            menu.append(menu_item)

        self.add.set_sensitive(count)
        self.remove.set_sensitive(count)
        if count > 0:
            self.add.set_popup(menu)

        if total > 0:
            if count == 0:
                self._obj.set_tooltip_text(
                    "There are no additional lower level parameters that "
                    "can be overridden"
                )
            else:
                self._obj.set_tooltip_text(
                    "Lower level parameters can be overridding by selecting "
                    "the parameter from the Add button"
                )
        else:
            self._obj.set_tooltip_text(
                "There are no lower level parameters that can be overridden"
            )
        if self._model.iter_children():
            self.remove.set_sensitive(True)
        else:
            self.remove.set_sensitive(False)

    def remove_clicked(self, _obj):
        name = self.get_selected()
        self.prj.parameters.remove(name)
        self.remove_selected()
        self.set_menu()
        self._callback()

    def menu_selected(self, _obj, data):
        _, info = data
        override = Overrides()
        override.path = info[0].uuid
        override.parameter = info[1].uuid
        override.value = ParamValue()
        override.value.set_param(info[1].uuid)
        self._model.append(row=get_row_data(info[0].name, override))
        self._used.add(override.parameter)
        self.prj.overrides.append(override)
        self.set_menu()
        self._callback()

    def _value_changed(self, _cell, path, new_text, _col):
        """Called when the base address field is changed."""
        if check_hex(new_text) is False:
            return

        value = int(new_text, 0)

        self._model[path][OverrideCol.VALUE] = new_text
        self._model[path][OverrideCol.OBJ].value = value
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

        self.menu_column = MenuEditColumn(
            "Value",
            self._value_menu_callback,
            self._value_edit_callback,
            [],
            1,
            tooltip="Value of the parameter",
        )
        self.menu_column.set_min_width(150)
        self._obj.append_column(self.menu_column)

        self._model = OverridesListMdl()
        self._obj.set_model(self._model)

    def _value_menu_callback(
        self,
        cell: Gtk.CellRendererCombo,
        path: str,
        node: Gtk.TreeIter,
        col: int,
    ):

        model = cell.get_property("model")
        new_text = model.get_value(node, 0)
        new_uuid = model.get_value(node, 1)

        override = self._model[int(path)][OverrideCol.OBJ]
        override.value.set_param(new_uuid)
        self._model[int(path)][col] = new_text
        self._callback()

    def _value_edit_callback(self, _cell, path, new_text, col):

        try:
            value = int(new_text, 0)
        except ValueError:
            LOGGER.warning(
                '"%s" is not a valid parameter value. It must be an '
                "integer greater than 0 or a defined parameter",
                new_text,
            )
            return

        row = int(path)
        override = self._model[row][OverrideCol.OBJ]
        override.value.set_int(value)
        self._model[row][col] = f"0x{value:x}"
        self._callback()

    def clear(self):
        """
        Clears the data from the list
        """
        self._model.clear()

    # def append(self, name, value, max_val, min_val):
    #     """
    #     Add the data to the list.
    #     """
    #     obj = ParameterData(name, value, min_val, max_val)
    #     self._model.append(row=get_row_data(obj))

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
        obj = model.get_value(node, OverrideCol.OBJ)
        self._used.remove(obj.parameter.uuid)
        model.remove(node)

    def set_parameters(self, parameters):
        my_parameters = sorted([(p.name, p.uuid) for p in parameters])
        self.menu_column.update_menu(my_parameters)

    def build_overrides_list(self, project: RegProject):
        total = 0
        self.build_used()
        param_list = []
        for blkinst in project.block_insts:
            blkinst_name = blkinst.name
            block = project.blocks[blkinst.blkid]
            for param in block.parameters.get():
                total += 1
                name = f"{blkinst_name}.{param.name}"
                if param.uuid not in self._used:
                    param_list.append((name, (blkinst, param)))
        return param_list, total


class BlockOverridesList(OverridesList):
    def build_overrides_list(self, block):
        total = 0
        param_list = []
        if block is not None:
            for reginst in block.regset_insts:
                regset = block.regsets[reginst.regset_id]
                for param in regset.parameters.get():
                    total += 1
                    name = f"{reginst.name}.{param.name}"
                    if param.uuid not in self._used:
                        param_list.append((name, (reginst, param)))
        return param_list, total

    def update_display(self):
        self.set_menu()
        for row in self._model:
            data = row[OverrideCol.OBJ]
            path = ""
            for inst in self.prj.regset_insts:
                if inst.uuid == data.path:
                    path = inst.name

            param = data.parameter
            new_name = f"{path}.{self.finder.find(param).name}"
            if row[OverrideCol.NAME] != new_name:
                row[OverrideCol.NAME] = new_name


def get_row_data(path, map_obj):
    finder = ParameterFinder()
    data = (
        f"{path}.{finder.find(map_obj.parameter).name}",
        str(map_obj.value),
        map_obj,
    )
    return data
