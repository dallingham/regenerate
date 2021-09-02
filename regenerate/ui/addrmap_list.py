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

from typing import Callable, Optional, Tuple
from gi.repository import Gtk
from regenerate.db import LOGGER, AddressMap, RegProject
from regenerate.ui.columns import (
    EditableColumn,
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


class AddrMapList:
    "Container for the Address Map control logic."

    def __init__(self, obj: Gtk.TreeView, callback: Callable):
        self._obj = obj
        self._col: Optional[EditableColumn] = None
        self._prj: Optional[RegProject] = None
        self._model: Optional[AddrMapMdl] = None
        self._build_instance_table()
        self._obj.set_sensitive(False)
        self._callback = callback

    def set_project(self, project: RegProject) -> None:
        """
        Sets the project for the address map, and repopulates the list
        from the project.
        """
        self._prj = project
        self._obj.set_sensitive(True)
        self.populate()

    def populate(self) -> None:
        """
        Loads the data from the project
        """
        if self._prj is None or self._model is None:
            return

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

    def _name_changed(
        self,
        _cell: Gtk.CellRendererText,
        path: str,
        new_text: str,
        _col: AddrCol,
    ) -> None:
        """
        Called when the name field is changed.
        """

        if self._prj is None or self._model is None:
            return

        map_obj = self.get_obj(path)
        if map_obj.name == new_text:
            return

        current_maps = set({i.name for i in self._prj.get_address_maps()})
        if new_text in current_maps:
            LOGGER.error(
                '"%s" has already been used as an address map name', new_text
            )
        else:
            self._prj.change_address_map_name(map_obj.uuid, new_text)
            self._model[path][AddrCol.NAME] = new_text
            self._callback()

    def _base_changed(
        self,
        _cell: Gtk.CellRendererText,
        path: str,
        new_text: str,
        _col: AddrCol,
    ) -> None:
        """
        Called when the base address field is changed.
        """
        if self._prj is None or self._model is None:
            return

        try:
            _ = int(new_text, 0)
        except ValueError:
            LOGGER.error('Illegal address: "%s"', new_text)
            return

        if new_text:
            obj = self.get_obj(path)

            obj.base = int(new_text, 0)
            self._model[path][AddrCol.BASE] = f"0x{obj.base:08x}"
            self._callback()

    def _width_changed(
        self,
        cell: Gtk.CellRendererText,
        path: str,
        node: Gtk.TreeIter,
        col: AddrCol,
    ) -> None:
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """

        if self._model is None:
            return

        model = cell.get_property("model")
        self._model[path][col] = model.get_value(node, 0)
        width = model.get_value(node, 1)
        obj = self.get_obj(path)
        obj.width = width
        self._callback()

    def _build_instance_table(self) -> None:
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

    def clear(self) -> None:
        "Clears the data from the list"
        if self._model:
            self._model.clear()

    def get_selected(self) -> Optional[AddressMap]:
        "Removes the selected node from the list"
        (model, node) = self._obj.get_selection().get_selected()
        if node is None:
            return None

        if len(model.get_path(node)) > 1:
            return None
        return model.get_value(node, AddrCol.OBJ)

    def remove_selected(self) -> None:
        """
        Removes the selected node from the list
        """
        select_data = self._obj.get_selection().get_selected()
        if select_data is None or select_data[1] is None or self._prj is None:
            return

        (model, node) = select_data
        path = model.get_path(node)
        if len(path) > 1:
            # remove group from address map
            pass
        else:
            addr_map = model.get_value(node, AddrCol.OBJ)
            model.remove(node)
            self._callback()
            self._prj.remove_address_map(addr_map.uuid)

    def add_new_map(self) -> None:
        """
        Creates a new address map and adds it to the project. Uses default
        data, and sets the first field to start editing.
        """
        if self._col is None or self._prj is None or self._model is None:
            return

        name = self._create_new_map_name()
        obj = AddressMap(name, 0, 8, False, False)
        node = self._model.append(row=get_row_data(obj))

        path = self._model.get_path(node)
        self._callback()
        self._prj.add_or_replace_address_map(obj)
        self._obj.set_cursor(path, self._col, start_editing=True)

    def _create_new_map_name(self) -> str:
        """Creates a new map, finding an unused name"""
        if self._prj is None:
            return ""

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


def get_flags(map_obj: AddressMap) -> str:
    flag_str = []
    if map_obj.fixed:
        flag_str.append("fixed address")
    if map_obj.uvm:
        flag_str.append("exclude from UVM")
    return ", ".join(flag_str)


def get_row_data(map_obj: AddressMap) -> Tuple[str, str, str, str, AddressMap]:
    """Builds the data for the table row"""
    return (
        map_obj.name,
        f"0x{map_obj.base:08x}",
        get_flags(map_obj),
        INT2SIZE[map_obj.width],
        map_obj,
    )
