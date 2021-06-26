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
Provides both the GTK ListStore and ListView for the bit fields.
"""

import re
from gi.repository import Gtk

from regenerate.db import TYPES, LOGGER, ResetType
from regenerate.ui.columns import (
    EditableColumn,
    MyComboMapColumn,
    SwitchComboMapColumn,
)
from regenerate.ui.enums import BitCol

#
# Types conversions
#
TYPE2STR = [(t.description, t.type) for t in sorted(TYPES)]
RO2STR = [
    (t.description, t.type) for t in sorted(TYPES) if t.simple_type == "RO"
]
WO2STR = [
    (t.description, t.type) for t in sorted(TYPES) if t.simple_type == "WO"
]

TYPE_ENB = {}
for data_type in TYPES:
    TYPE_ENB[data_type.type] = (data_type.input, data_type.control)


(BIT_TITLE, BIT_SIZE, BIT_SORT, BIT_EXPAND, BIT_MONO) = range(5)


class BitModel(Gtk.ListStore):
    """
    The GTK list store model for the bit fields. This model is added to the
    ListView to provide the data for the bitfields.
    """

    def __init__(self):
        """
        Initialize the base class with the object types that we are going to
        be adding to the model.
        """
        super().__init__(str, str, str, str, str, str, int, object)
        self.register = None

    def append_field(self, field):
        "Adds the field to the model, filling out the fields in the model."

        node = self.append(
            row=[
                None,
                field.msb.int_str(),
                str(field.lsb),
                field.name,
                TYPE2STR[field.field_type][0],
                get_field_reset_data(field),
                field.lsb,
                field,
            ]
        )
        return self.get_path(node)

    def get_bitfield_at_path(self, path):
        """
        Returns the field object associated with a ListModel path.
        """
        return self[path][-1]


class BitList:
    """
    Bit Field display representation. We can't inherit from the ListModel,
    since it is generated by glade. So this object connects to the list
    model through the list model parameter passed into the constructor.
    """

    # Title, Size, Sort, Expand, Monospace
    BIT_COLS = (
        ("", 20, -1, False, False),
        ("MSB", 120, -1, False, True),
        ("LSB", 80, BitCol.SORT, False, True),
        ("Name", 60, BitCol.NAME, True, True),
        ("Type", 300, -1, True, False),
        ("Reset", 130, -1, False, True),
    )

    def __init__(self, obj, selection_changed, modified):
        """
        Creates the object, connecting it to the ListView (obj). Three
        callbacks are associated with the object.

        text_edit - called when a text field is edited
        selection_changed - called when the selected field is changed
        """
        self.__obj = obj
        self.__col = None
        self.__model = None
        self.__modified = modified
        self.__build_bitfield_columns()
        self.__obj.get_selection().connect(
            "changed", self.my_selection_changed
        )
        self.selection_changed = selection_changed

    def my_selection_changed(self, obj):
        self.clear_msg()
        self.selection_changed(obj)

    def set_parameters(self, parameters):
        my_parameters = sorted([(p.name, p.name) for p in parameters])
        self.reset_column.update_menu(my_parameters)

        msb_parameters = sorted([(f"{p.name}-1", p.uuid) for p in parameters])
        self.msb_column.update_menu(msb_parameters)

    def set_model(self, model):
        "Associates a List Model with the list view."
        self.__model = model
        self.__obj.set_model(model)

    def set_mode(self, mode):
        self.type_column.set_mode(mode)

    def __build_bitfield_columns(self):
        """
        Builds the columns for the tree view. First, removes the old columns in
        the column list. The builds new columns and inserts them into the tree.
        """
        for (i, col) in enumerate(self.BIT_COLS):
            if i == BitCol.TYPE:
                column = SwitchComboMapColumn(
                    col[BIT_TITLE],
                    self.field_type_edit,
                    TYPE2STR,
                    RO2STR,
                    WO2STR,
                    i,
                )
                self.type_column = column
            elif i == BitCol.ICON:
                column = Gtk.TreeViewColumn(
                    "", Gtk.CellRendererPixbuf(), stock_id=i
                )
            elif i == BitCol.RESET:
                column = MyComboMapColumn(
                    col[BIT_TITLE],
                    self.reset_menu_edit,
                    self.reset_text_edit,
                    [],
                    i,
                )
                self.reset_column = column
            elif i == BitCol.NAME:
                column = EditableColumn(
                    col[BIT_TITLE], self.field_name_edit, i, col[BIT_MONO]
                )
            elif i == BitCol.MSB:
                column = MyComboMapColumn(
                    col[BIT_TITLE],
                    self._msb_menu,
                    self._msb_text,
                    [],
                    i,
                    col[BIT_MONO],
                )
                self.msb_column = column
            elif i == BitCol.LSB:
                column = EditableColumn(
                    col[BIT_TITLE], self.update_lsb, i, col[BIT_MONO]
                )
                self.__col = column

            if col[BIT_SORT] >= 0:
                column.set_sort_column_id(col[BIT_SORT])
            column.set_min_width(col[BIT_SIZE])
            column.set_expand(col[BIT_EXPAND])
            column.set_resizable(True)
            self.__obj.append_column(column)

    def get_selected_row(self):
        "Returns the path of the selected row"
        value = self.__obj.get_selection().get_selected_rows()
        if value:
            return value[1]
        return None

    def select_row(self, path):
        "Selectes the row associated with the path"
        if path:
            self.__obj.get_selection().select_path(path)

    def select_field(self):
        "Returns the field object associated with selected row."

        data = self.__obj.get_selection().get_selected()
        if data:
            (store, node) = data
            if node:
                return store.get_value(node, BitCol.FIELD)
        return None

    def add_new_field(self, field):
        "Adds a new field to the model, and sets editing to begin"
        path = self.__model.append_field(field)
        self.__obj.set_cursor(path, self.__col, start_editing=True)

    def field_name_edit(self, _cell, path, new_text, _col):
        """
        Primary callback when a text field is edited in the BitList. Based off
        the column, we pass it to a function to handle the data.
        """

        field = self.__model.get_bitfield_at_path(path)
        if new_text != field.name:
            new_text = new_text.upper().replace(" ", "_")
            new_text = new_text.replace("/", "_").replace("-", "_")

            register = self.__model.register

            current_names = [
                f.name for f in register.get_bit_fields() if f != field
            ]

            if new_text not in current_names:
                self.__model[path][BitCol.NAME] = new_text
                field.name = new_text
                self.__modified()
                self.clear_msg()
            else:
                self.show_msg(
                    '"%s" has already been used as a field name' % new_text
                )

    def reset_text_edit(self, _cell, path, new_val, col):
        field = self.__model.get_bitfield_at_path(path)

        if re.match(r"^(0x)?[a-fA-F0-9]+$", new_val):
            if self.check_reset(field, int(new_val, 0)) is False:
                return
            field.reset_value = int(new_val, 0)
            field.reset_type = ResetType.NUMERIC
            self.__model[path][col] = reset_value(field)
            self.__modified()
        elif re.match(r"""^[A-Za-z]\w*$""", new_val):
            field.reset_input = new_val
            field.reset_type = ResetType.INPUT
            self.__model[path][BitCol.RESET] = new_val
            self.__modified()
        else:
            self.show_msg(
                f'"{new_val}" is not a valid constant, parameter, or signal name'
            )

    def reset_menu_edit(self, cell, path, node, _col):
        model = cell.get_property("model")
        field = self.__model.get_bitfield_at_path(path)
        field.reset_type = ResetType.PARAMETER
        new_val = model.get_value(node, 0)
        field.reset_parameter = new_val
        self.__model[path][BitCol.RESET] = new_val
        self.__modified()

    def field_type_edit(self, cell, path, node, col):
        """
        The callback function that occurs whenever a combo entry is altered
        in the BitList. The 'col' value tells us which column was selected,
        and the path tells us the row. So [path][col] is the index into the
        table.
        """
        model = cell.get_property("model")
        field = self.__model.get_bitfield_at_path(path)
        self.__model[path][col] = model.get_value(node, 0)
        self.update_type_info(field, model, path, node)
        self.__modified()

    def update_type_info(self, field, model, _path, node):
        field.field_type = model.get_value(node, 1)

        if not field.output_signal:
            field.output_signal = "%s_%s_OUT" % (
                self.__model.register.token,
                field.name,
            )

        if TYPE_ENB[field.field_type][0] and not field.input_signal:
            field.input_signal = "%s_%s_IN" % (
                self.__model.register.token,
                field.name,
            )

        if TYPE_ENB[field.field_type][1] and not field.control_signal:
            field.control_signal = "%s_%s_LD" % (
                self.__model.register.token,
                field.name,
            )

    def update_msb(self, _cell, path, new_text, _col):
        """
        Called when the bits column of the BitList is edited. If the new text
        does not match a valid bit combination (determined by the VALID_BITS
        regular expression, then we do not modifiy the ListStore, which
        prevents the display from being altered. If it does match, we extract
        the start or start and stop positions, and alter the model and the
        corresponding field.
        """

        field = self.__model.get_bitfield_at_path(path)
        try:
            stop = int(new_text, 0)
        except ValueError:
            return

        if self.check_for_overlaps(field, field.lsb, stop) is False:
            return

        if self.check_for_width(field.lsb, stop) is False:
            return

        if stop != field.msb.resolve():
            field.msb.set_int(stop)
            self.__model.register.change_bit_field(field)
            self.__modified()

        self.__model[path][BitCol.MSB] = f"{field.msb.int_str()}"

    def update_lsb(self, _cell, path, new_text, _col):
        """
        Called when the bits column of the BitList is edited. If the new text
        does not match a valid bit combination (determined by the VALID_BITS
        regular expression, then we do not modifiy the ListStore, which
        prevents the display from being altered. If it does match, we extract
        the start or start and stop positions, and alter the model and the
        corresponding field.
        """

        field = self.__model.get_bitfield_at_path(path)
        start = int(new_text, 0)

        if self.check_for_overlaps(field, start, field.msb.resolve()) is False:
            return

        if self.check_for_width(start, field.msb.resolve()) is False:
            return

        if start != field.lsb:
            field.lsb = start
            self.__model.register.change_bit_field(field)
            self.__modified()

        self.__model[path][BitCol.LSB] = f"{field.lsb}"
        self.__model[path][BitCol.SORT] = field.start_position

    def show_msg(self, text):
        LOGGER.warning(text)

    def clear_msg(self):
        pass

    def check_for_width(self, _start, stop):
        register = self.__model.register
        if stop >= register.width:
            self.show_msg(
                f"Bit position ({stop}) is greater than register width ({register.width})"
            )
            return False
        return True

    def check_reset(self, field, value):
        maxval = (1 << ((field.msb.resolve() - field.lsb) + 1)) - 1
        if value > maxval:
            self.show_msg(
                "Reset value (0x%x) is greater than the maximum value (0x%x)"
                % (value, maxval)
            )
            return False
        return True

    def check_for_overlaps(self, field, start, stop):
        register = self.__model.register

        used = set()
        for fld in register.get_bit_fields():
            if fld != field:
                for bit in range(fld.lsb, fld.msb.resolve() + 1):
                    used.add(bit)

        for bit in range(start, stop + 1):
            if bit in used:
                self.show_msg(
                    f"Bit {bit} overlaps with the bits in another register"
                )
                return False
        return True

    def _msb_menu(self, cell, path, node, _col):
        """
        Called when text has been edited. Selects the correct function
        depending on the edited column
        """
        model = cell.get_property("model")
        field = self.__model[path][-1]
        descript = model.get_value(node, 0)
        uuid = model.get_value(node, 1)
        field.msb.set_param(uuid, -1)
        self.__model[path][BitCol.MSB] = descript
        self.__modified()

    def _msb_text(self, _cell, path, new_text, _col):
        """
        Called when text has been edited. Selects the correct function
        depending on the edited column
        """
        field = self.__model[path][-1]
        new_text = new_text.strip()
        try:
            value = int(new_text, 0)
            if value < 1:
                LOGGER.warning(
                    "The dimension for a register must be 1 or greater"
                )
                return
            field.msb.is_parameter = False
            field.msb.offset = 0
            field.msb.value = int(new_text, 0)
            self.__model[path][BitCol.MSB] = f"{field.msb.value}"
        except ValueError:
            ...


def reset_value(field):
    "Returns a string representation of the reset value."

    return f"0x{field.reset_value:04x}"


def get_field_reset_data(field):
    "Converts the fields reset value/type into a displayable value."

    if field.reset_type == ResetType.NUMERIC:
        reset = reset_value(field)
    elif field.reset_type == ResetType.INPUT:
        reset = field.reset_input
    else:
        reset = field.reset_parameter
    return reset
