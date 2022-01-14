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
from gi.repository import Gtk, Gdk

from regenerate.settings.paths import GLADE_REORDER
from regenerate.db import Register

from .base_window import BaseWindow
from .columns import ReadOnlyColumn
from .error_dialogs import ErrorMsg


class ReorderFields(BaseWindow):

    TARGETS = [
        ("text/plain", Gtk.TargetFlags.OTHER_WIDGET, 0),
    ]

    ENTER_KEY = Gdk.keyval_from_name("Return")

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
            field = row[-1]
            if field and index + field.width - 1 < self._register.width:
                return index + field.width - 1
        return 0

    def on_src_table_key_press_event(
        self, treeview: Gtk.TreeView, event: Gdk.EventKey
    ) -> bool:
        if event.state == Gdk.ModifierType.CONTROL_MASK:
            if event.keyval == self.ENTER_KEY:
                _, node = treeview.get_selection().get_selected()
                field = self._src_model[self._src_model.get_path(node)][-1]
                width = field.width

                max_val = self._last_index()
                if max_val + width > self._register.width:
                    return False

                start = max_val
                if field.width > 1:
                    self._dest_model[max_val][
                        0
                    ] = f"[{start + field.width -1}:{start}]"
                else:
                    self._dest_model[max_val][0] = f"{start}"
                self._dest_model[max_val][1] = field.name
                self._dest_model[max_val][-1] = field

                for val in reversed(range(max_val + 1, max_val + width)):
                    self._dest_model.remove(self._dest_model.get_iter(val))

                _, node = self._src_table.get_selection().get_selected()
                self._src_model.remove(node)
        return False

    def on_row_activated(
        self,
        _treeview: Gtk.TreeView,
        path: Gtk.TreePath,
        _column: ReadOnlyColumn,
    ):
        field = self._src_model[path][-1]
        width = field.width

        for index in range(field.lsb, field.lsb + width):
            row = self._dest_model[index]
            if row[-1]:
                return

        start = field.lsb
        if field.width > 1:
            self._dest_model[index][0] = f"[{start + field.width -1}:{start}]"
        else:
            self._dest_model[index][0] = f"{start}"
        self._dest_model[index][1] = field.name
        self._dest_model[index][-1] = field

        for val in reversed(range(index + 1, index + width)):
            self._dest_model.remove(self._dest_model.get_iter(val))

        _, node = self._src_table.get_selection().get_selected()
        self._src_model.remove(node)

    def _drag_data_get(
        self, treeview, _drag_context, selection, _target_id, _etime
    ) -> None:
        tree_selection = treeview.get_selection()
        model, selected_paths = tree_selection.get_selected_rows()
        selected_iter = model.get_iter(selected_paths[0])

        obj = self._src_model.get_value(selected_iter, 2)
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
                if self._dest_model[val][-1]:
                    return

            if field.width > 1:
                start = int(self._dest_model[index][0])
                self._dest_model[index][
                    0
                ] = f"[{start + field.width -1}:{start}]"
            self._dest_model[index][1] = field.name
            self._dest_model[index][-1] = field

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
        for row in self._dest_model:
            if row[-1] is not None:
                lsb = row[2]
                field = row[-1]
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
