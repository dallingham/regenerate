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
from regenerate.db import LOGGER, AddressMap
from regenerate.ui.columns import (
    EditableColumn,
    ToggleColumn,
    ComboMapColumn,
    ReadOnlyColumn,
)
from regenerate.ui.enums import AddrCol

_BITS8 = "8 bits"
_BITS16 = "16 bits"
_BITS32 = "32 bits"
_BITS64 = "64 bits"

SIZE2STR = ((_BITS8, 1), (_BITS16, 2), (_BITS32, 4), (_BITS64, 8))

ACCESS2STR = (
    ("Full Access", 0),
    ("Read Only", 1),
    ("Write Only", 2),
    ("No Access", 3),
)

INT2SIZE = dict((_i[1], _i[0]) for _i in SIZE2STR)
STR2SIZE = dict((_i[0], _i[1]) for _i in SIZE2STR)

INT2ACCESS = dict((_i[1], _i[0]) for _i in ACCESS2STR)
STR2ACCESS = dict((_i[0], _i[1]) for _i in ACCESS2STR)


class AddrMapMdl(Gtk.ListStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    def __init__(self):
        super().__init__(str, str, str, str, object)

    def new_instance(self):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        new_obj = AddressMap("new_map", 0, 8, False, False)
        node = self.append(None, row=get_row_data(new_obj))
        return self.get_path(node)

    def append_instance(self, inst):
        """Adds the specified instance to the InstanceList"""
        self.append(None, row=get_row_data(inst))

    def get_values(self):
        """Returns the list of instance tuples from the model."""
        return [(val[0], int(val[1], 16)) for val in self if val[0]]


class AddrMapList:
    """
    Container for the Address Map control logic.
    """

    def __init__(self, obj, callback):
        self._obj = obj
        self._col = None
        self._prj = None
        self._model = None
        self._build_instance_table()
        self._obj.set_sensitive(False)
        self._callback = callback

    def set_project(self, project):
        """
        Sets the project for the address map, and repopulates the list
        from the project.
        """
        self._prj = project
        self._obj.set_sensitive(True)
        self.populate()

    def populate(self):
        """
        Loads the data from the project
        """
        if self._prj is not None:
            self._model.clear()
            for base in self._prj.get_address_maps():
                if base.width not in INT2SIZE:
                    LOGGER.error(
                        'Illegal width (%0d) for address map "%s"',
                        base.width,
                        base.name,
                    )
                    base.width = 4
                self._model.append(row=get_row_data(base))

    def _name_changed(self, _cell, path, new_text, _col):
        """
        Called when the name field is changed.
        """

        map_obj = self.get_obj(path)
        if map_obj.name == new_text:
            return

        current_maps = set({i.name for i in self._prj.get_address_maps()})
        if new_text in current_maps:
            LOGGER.error(
                '"%s" has already been used as an address map name', new_text
            )
        else:
            name = self._model[path][AddrCol.NAME]
            self._prj.change_address_map_name(name, new_text)
            self._model[path][AddrCol.NAME] = new_text
            self._callback()

    def _base_changed(self, _cell, path, new_text, _col):
        """
        Called when the base address field is changed.
        """
        try:
            _ = int(new_text, 16)
        except ValueError:
            LOGGER.error('Illegal address: "%s"', new_text)
            return

        if new_text:
            obj = self.get_obj(path)
            base = self._model[path][AddrCol.BASE]

            obj.base = int(base, 16)
            self._model[path][AddrCol.BASE] = new_text
            self._callback()

    def _width_changed(self, cell, path, node, col):
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """

        model = cell.get_property("model")
        self._model[path][col] = model.get_value(node, 0)
        width = model.get_value(node, 1)
        obj = self.get_obj(path)
        obj.width = width
        self._callback()

    def _build_instance_table(self):
        """
        Builds the columns, adding them to the address map list.
        """
        column = EditableColumn("Map Name", self._name_changed, AddrCol.NAME)
        column.set_min_width(175)
        column.set_sort_column_id(AddrCol.NAME)
        column.set_resizable(True)
        self._obj.append_column(column)
        self._col = column

        column = EditableColumn(
            "Address base",
            self._base_changed,
            AddrCol.BASE,
            True,
            tooltip="Base address in hex format",
        )
        column.set_sort_column_id(AddrCol.BASE)
        column.set_min_width(200)
        column.set_resizable(True)
        self._obj.append_column(column)

        column = ComboMapColumn(
            "Access Width", self._width_changed, SIZE2STR, AddrCol.WIDTH
        )
        column.set_min_width(150)
        column.set_resizable(True)
        self._obj.append_column(column)

        column = ReadOnlyColumn(
            "Flags",
            AddrCol.FLAGS,
        )
        column.set_max_width(250)
        column.set_resizable(True)
        self._obj.append_column(column)

        self._model = AddrMapMdl()
        self._obj.set_model(self._model)

    def clear(self):
        """
        Clears the data from the list
        """
        self._model.clear()

    def append(self, base, addr, fixed, uvm, width, _access):
        """
        Add the data to the list.
        """
        obj = AddressMap(base, addr, width, fixed, uvm)
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
        return model.get_value(node, AddrCol.NAME)

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
            _ = model.get_value(node, AddrCol.NAME)
            model.remove(node)
            self._callback()
            # self._prj.remove_address_map(name)

    def add_new_map(self):
        """
        Creates a new address map and adds it to the project. Uses default
        data, and sets the first field to start editing.
        """
        name = self._create_new_map_name()
        obj = AddressMap(name, 0, 8, False, False)
        node = self._model.append(row=get_row_data(obj))

        path = self._model.get_path(node)
        self._callback()
        self._prj.add_or_replace_address_map(obj)
        self._obj.set_cursor(path, self._col, start_editing=True)

    def _create_new_map_name(self):
        """Creates a new map, finding an unused name"""
        template = "NewMap"
        index = 0
        current_maps = set({i.name for i in self._prj.get_address_maps()})

        name = template
        while name in current_maps:
            name = f"{template}{index}"
            index += 1
        return name

    def get_obj(self, row):
        """Returns the object at the specified row"""
        return self._model[row][AddrCol.OBJ]


def get_flags(map_obj):
    flag_str = []
    if map_obj.fixed:
        flag_str.append("fixed address")
    if map_obj.uvm:
        flag_str.append("exclude from UVM")
    return ", ".join(flag_str)


def get_row_data(map_obj):
    """Builds the data for the table row"""
    return (
        map_obj.name,
        "0x{:08x}".format(map_obj.base),
        get_flags(map_obj),
        INT2SIZE[map_obj.width],
        map_obj,
    )
