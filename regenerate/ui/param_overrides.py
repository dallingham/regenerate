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
from regenerate.ui.columns import EditableColumn, ComboMapColumn
from regenerate.db.parammap import ParameterData
from regenerate.ui.utils import check_hex


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

    def __init__(self, obj, find_obj, callback):
        self._obj = obj
        self._col = None
        self.prj = None
        self._model = None
        self._build_instance_table()
        self._obj.set_sensitive(True)
        self._callback = callback
        find_obj("override_add").connect("clicked", self.add_clicked)

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
        overrides = build_overrides_list(self.prj)
        self._col.update_menu(overrides)

    #        if self.prj is not None:
    #            self._model.clear()
    #            for data in build_possible_overrides(self.prj):
    #                new_data = (
    #                    f"{data[0]}.{data[1]}.{data[2].name}",
    #                    f"0x{data[2].value}",
    #                    data[2],
    #                )
    #                self._model.append(row=new_data)

    def remove_clicked(self):
        name = self.get_selected()
        self.prj.remove_parameter(name)
        self.remove_selected()
        self._callback()

    def add_clicked(self, obj):
        a = build_overrides_list(self.prj)
        if a:
            self._model.new_instance(a[0][0], "0x1", a[0][1])

    #        self._callback()

    def _name_changed(self, _combo, path, node, _param):
        """
        Called when the name field is changed.
        """
        name = self._model[path][0]
        new_text = self._col.model.get_value(node, 0)
        if name != new_text:
            self._model[path][0] = new_text
            self._callback(True)

    def _blk_changed(self, _cell, path, new_text, _col):
        """
        Called when the name field is changed.
        """
        current = set({p[0] for p in self.prj.get_parameters()})

        name = self._model[path][PrjParameterCol.BLK]
        if name != new_text and new_text not in current:
            self._model[path][PrjParameterCol.BLK] = new_text
            self.prj.remove_parameter(name)
            self.prj.add_parameter(
                new_text, int(self._model[path][PrjParameterCol.VALUE], 16)
            )
            self._callback()

    def _reg_changed(self, _cell, path, new_text, _col):
        """
        Called when the name field is changed.
        """
        current = set({p[0] for p in self.prj.get_parameters()})

        name = self._model[path][PrjParameterCol.REG]
        if name != new_text and new_text not in current:
            self._model[path][PrjParameterCol.REG] = new_text
            self.prj.remove_parameter(name)
            self.prj.add_parameter(
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
        self.prj.remove_parameter(name)
        self.prj.add_parameter(name, value)
        self._callback()

    def _build_instance_table(self):
        """
        Builds the columns, adding them to the address map list.
        """
        self.column = ComboMapColumn(
            "Parameter", self._name_changed, [], 0, dtype=object
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
    return (map_obj.name, hex(int(map_obj.value)), map_obj)


def build_possible_overrides(project):
    param_list = []
    for blkinst in project.block_insts:
        blkinst_name = blkinst.inst_name
        block = project.blocks[blkinst.block]
        for reginst in block.regset_insts:
            reginst_name = reginst.inst
            regset_name = reginst.set_name
            regset = project.regsets[regset_name]
            for param in regset.get_parameters():
                param_list.append((blkinst_name, reginst_name, param))
    return param_list


def build_overrides_list(project):
    param_list = []
    for blkinst in project.block_insts:
        blkinst_name = blkinst.inst_name
        block = project.blocks[blkinst.block]
        for reginst in block.regset_insts:
            reginst_name = reginst.inst
            regset_name = reginst.set_name
            regset = project.regsets[regset_name]
            for param in regset.get_parameters():
                param_list.append(
                    (f"{blkinst_name}.{reginst_name}.{param.name}", param)
                )
    return param_list
