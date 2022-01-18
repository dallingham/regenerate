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
Bit reorder dialog.

Allows the user to reorder the bit fields within a register.

"""
from typing import Callable
from enum import IntEnum
from gi.repository import Gtk, Gdk

from regenerate.settings.paths import GLADE_REORDER
from regenerate.db import Register

from .base_window import BaseWindow
from .columns import ReadOnlyColumn
from .error_dialogs import ErrorMsg


class SrcCol(IntEnum):

    BITPOS = 0
    NAME = 1
    FIELD = 2


class DestCol(IntEnum):

    BITPOS = 0
    NAME = 1
    INDEX = 2
    FIELD = 3


class ReorderFields(BaseWindow):

    TARGETS = [
        ("text/plain", Gtk.TargetFlags.OTHER_WIDGET, 0),
    ]

    ENTER = Gdk.keyval_from_name("Return")
    BACKSPACE = Gdk.keyval_from_name("BackSpace")
    DELETE = Gdk.keyval_from_name("Delete")

    def __init__(self, register: Register, callback: Callable):

        super().__init__()
        self._register = register
        self.callback = callback

        if self._uses_parameters():
            ErrorMsg(
                "Cannot reorder register",
                "Registers that contain bit fields whose width is controlled by a parameter cannot be reordered",
            )
        else:
            self._builder = Gtk.Builder()
            self._builder.add_from_file(str(GLADE_REORDER))
            self._top_window = self._builder.get_object("reorder")
            self._builder.connect_signals(self)
            self.configure(self._top_window)

            self._build()
            self._populate()
            self._top_window.show()

    def _uses_parameters(self) -> bool:
        """
        Checks the bits to see if any of the MSBs' use parameters.

        Returns:
            bool: True if parameters are used

        """
        for field in self._register.get_bit_fields():
            if field.msb.is_parameter:
                return True
        return False

    def _build(self) -> None:
        """
        Build the source and destination tables.

        Add the read-only columns to both tables.

        """
        self._src_table = self._builder.get_object("src_table")
        self._src_model = Gtk.ListStore(str, str, object)
        self._src_table.set_model(self._src_model)

        self._dest_table = self._builder.get_object("dest_table")
        self._dest_model = Gtk.ListStore(str, str, int, object)
        self._dest_table.set_model(self._dest_model)

        column = ReadOnlyColumn("Current Index", 0)
        column.set_min_width(150)
        column.set_resizable(True)

        self._src_table.append_column(column)

        column = ReadOnlyColumn("Field Name", 1)
        column.set_resizable(True)
        self._src_table.append_column(column)

        column = ReadOnlyColumn("Index", 0)
        column.set_min_width(150)
        column.set_resizable(True)
        self._dest_table.append_column(column)

        column = ReadOnlyColumn("Field Name", 1)
        column.set_resizable(True)
        self._dest_table.append_column(column)

        self._src_table.enable_model_drag_source(
            Gdk.ModifierType.BUTTON1_MASK,
            self.TARGETS,
            Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE,
        )

        self._dest_table.enable_model_drag_dest(
            self.TARGETS, Gdk.DragAction.DEFAULT
        )

        self._src_table.connect("drag_data_get", self._drag_data_get)
        self._dest_table.connect(
            "drag_data_received", self._drag_data_received
        )

    def _populate(self) -> None:
        """
        Populate the source and destination tables.

        Fill the source table with the field information, and the destination
        table with bit positions.

        """
        for field in self._register.get_bit_fields():

            if field.msb.resolve() == field.lsb:
                index = f"{field.lsb}"
            else:
                index = f"[{field.msb.resolve()}:{field.lsb}]"

            self._src_model.append(row=(index, field.name, field))

        for index in range(0, self._register.width):
            self._dest_model.append(row=(f"{index}", "", index, None))

    def _last_index(self) -> int:
        for index in range(self._register.width, 0, -1):
            row = self._dest_model[index - 1]
            field = row[DestCol.FIELD]
            if field and index + field.width - 1 < self._register.width:
                return index + field.width - 1
        return 0

    def on_src_table_key_press_event(
        self, treeview: Gtk.TreeView, event: Gdk.EventKey
    ) -> bool:
        if event.state == Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == self.ENTER:
                self._move_selected_to_bottom(treeview)
        return False

    def on_dest_table_key_press_event(
        self, treeview: Gtk.TreeView, event: Gdk.EventKey
    ) -> bool:
        if event.state == 0 and event.keyval in (self.DELETE, self.BACKSPACE):
            _, node = treeview.get_selection().get_selected()
            treeview.get_selection().unselect_all()
            if node:
                dest_path = self._dest_model.get_path(node)
                field = self._dest_model[dest_path][DestCol.FIELD]
                if field is None:
                    return False

                start_bit = self._dest_model[dest_path][DestCol.INDEX]
                self._dest_model[dest_path][DestCol.BITPOS] = f"{start_bit}"
                self._dest_model[dest_path][DestCol.NAME] = ""
                self._dest_model[dest_path][DestCol.INDEX] = start_bit
                self._dest_model[dest_path][DestCol.FIELD] = None

                if field.width > 1:
                    for bitpos in range(field.width - 1, 0, -1):
                        self._dest_model.insert_after(
                            node,
                            row=(
                                f"{bitpos + start_bit}",
                                "",
                                bitpos + start_bit,
                                None,
                            ),
                        )

                if field.msb.resolve() == field.lsb:
                    val = f"{field.lsb}"
                else:
                    val = f"[{field.msb.resolve()}:{field.lsb}]"
                data = [val, field.name, field]

                for index, row in enumerate(self._src_model):
                    pos = row[SrcCol.FIELD].lsb
                    if pos > field.lsb:
                        self._src_model.insert_before(
                            self._src_model.get_iter(index), row=data
                        )
                        break
                else:
                    self._src_model.insert_after(
                        self._src_model.get_iter(index), row=data
                    )

        return False

    def _move_selected_to_bottom(self, treeview: Gtk.TreeView) -> None:
        _, node = treeview.get_selection().get_selected()
        field = self._src_model[self._src_model.get_path(node)][SrcCol.FIELD]
        width = field.width

        max_val = self._last_index()
        if max_val + width > self._register.width:
            return

        start = max_val
        if field.width > 1:
            self._dest_model[max_val][
                DestCol.BITPOS
            ] = f"[{start + field.width -1}:{start}]"
        else:
            self._dest_model[max_val][DestCol.BITPOS] = f"{start}"
        self._dest_model[max_val][DestCol.NAME] = field.name
        self._dest_model[max_val][DestCol.FIELD] = field

        for val in reversed(range(max_val + 1, max_val + width)):
            self._dest_model.remove(self._dest_model.get_iter(val))

        _, node = self._src_table.get_selection().get_selected()
        self._src_model.remove(node)

    def _build_row_map(self):
        row_map = {}
        for row in self._dest_model:  # pylint: disable=E1133
            row_map[row[DestCol.INDEX]] = row
        return row_map

    def on_row_activated(
        self,
        _treeview: Gtk.TreeView,
        path: Gtk.TreePath,
        _column: ReadOnlyColumn,
    ):
        field = self._src_model[path][SrcCol.FIELD]
        width = field.width

        row_map = self._build_row_map()
        for index in range(field.lsb, field.lsb + width):
            if row_map[index][DestCol.FIELD]:
                return

        start = field.lsb
        if field.width > 1:
            row_map[start][
                DestCol.BITPOS
            ] = f"[{start + field.width -1}:{start}]"
        else:
            row_map[start][DestCol.BITPOS] = f"{start}"
        row_map[start][DestCol.NAME] = field.name
        row_map[start][DestCol.INDEX] = start
        row_map[start][DestCol.FIELD] = field

        for val in reversed(range(field.lsb + 1, field.lsb + field.width)):
            self._dest_model.remove(row_map[val].iter)

        _, node = self._src_table.get_selection().get_selected()
        self._src_model.remove(node)

    def _drag_data_get(
        self, treeview, _drag_context, selection, _target_id, _etime
    ) -> None:
        tree_selection = treeview.get_selection()
        model, selected_paths = tree_selection.get_selected_rows()
        selected_iter = model.get_iter(selected_paths[0])

        obj = self._src_model.get_value(selected_iter, SrcCol.FIELD)
        uuid = obj.uuid
        selection.set_text(uuid, -1)

    def _drag_data_received(
        self, treeview, _context, xpos, ypos, selection, _info, _etime
    ) -> None:
        data = selection.get_data()
        dest_path, _ = treeview.get_dest_row_at_pos(xpos, ypos)

        uuid = str(data, "ascii")
        field = self._register.get_bit_field_from_uuid(uuid)
        if field:
            width = field.width

            index = dest_path.get_indices()[0]
            for val in range(index, index + width):
                if self._dest_model[val][DestCol.FIELD]:
                    return

            if field.width > 1:
                start = int(self._dest_model[index][DestCol.BITPOS])
                self._dest_model[index][
                    DestCol.BITPOS
                ] = f"[{start + field.width -1}:{start}]"
            self._dest_model[index][DestCol.NAME] = field.name
            self._dest_model[index][DestCol.FIELD] = field

        for val in reversed(range(index + 1, index + width)):
            self._dest_model.remove(self._dest_model.get_iter(val))

        _, node = self._src_table.get_selection().get_selected()
        self._src_model.remove(node)

    def on_save_clicked(self, _button: Gtk.Button) -> None:
        """
        Saves the new order.

        Parameters:
            _button (Gtk.Button): unused

        """
        self._register.remove_all_fields()
        for row in self._dest_model:  # pylint: disable=E1133
            if row[DestCol.FIELD] is not None:
                lsb = row[DestCol.INDEX]
                field = row[DestCol.FIELD]
                width = field.width
                field.lsb = lsb
                field.msb.set_int(lsb + width - 1)
                self._register.add_bit_field(field)
        self.callback(self._register)
        self._top_window.destroy()

    def on_cancel_clicked(self, _button: Gtk.Button) -> None:
        """
        Closes the dialog.

        Parameters:
            _button (Gtk.Button): unused

        """
        self._top_window.destroy()
