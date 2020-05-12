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
from regenerate.db import TYPES, LOGGER
from regenerate.db.enums import ResetType
from regenerate.ui.columns import (
    EditableColumn,
    MyComboMapColumn,
    SwitchComboMapColumn,
    ReadOnlyColumn,
)
from regenerate.ui.enums import BitCol

VALID_BITS = re.compile(r"""^\s*[\(\[]?(\d+)(\s*[-:]\s*(\d+))?[\)\]]?\s*$""")


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

    RESET2STR = ("Constant", "Input Port", "Parameter")

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
                bits(field),
                field.field_name,
                TYPE2STR[field.field_type][0],
                get_field_reset_data(field),
                self.RESET2STR[field.reset_type],
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


class BitList(object):
    """
    Bit Field display representation. We can't inherit from the ListModel,
    since it is generated by glade. So this object connects to the list
    model through the list model parameter passed into the constructor.
    """

    # Title, Size, Sort, Expand, Monospace
    BIT_COLS = (
        ("", 20, -1, False, False),
        ("Bits", 60, BitCol.SORT, False, True),
        ("Name", 60, BitCol.NAME, True, True),
        ("Type", 325, -1, True, False),
        ("Reset", 160, -1, False, True),
        ("Reset Type", 105, -1, False, False),
    )

    def __init__(
        self,
        obj,
        reset_text_edit,
        reset_menu_edit,
        selection_changed,
        modified,
    ):
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
        self.__build_bitfield_columns(reset_text_edit, reset_menu_edit)
        self.__obj.get_selection().connect("changed", selection_changed)

    def set_parameters(self, parameters):
        my_parameters = sorted([(p[0], p[0]) for p in parameters])
        self.reset_column.update_menu(my_parameters)

    def set_model(self, model):
        "Associates a List Model with the list view."
        self.__model = model
        self.__obj.set_model(model)

    def set_mode(self, mode):
        self.type_column.set_mode(mode)

    def __build_bitfield_columns(self, reset_text_edit, reset_menu_edit):
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
            elif i == BitCol.RESET_TYPE:
                column = ReadOnlyColumn(col[BIT_TITLE], i, col[BIT_MONO])
            elif i == BitCol.ICON:
                column = Gtk.TreeViewColumn(
                    "", Gtk.CellRendererPixbuf(), stock_id=i
                )
            elif i == BitCol.RESET:
                column = MyComboMapColumn(
                    col[BIT_TITLE], reset_menu_edit, reset_text_edit, [], i
                )
                self.reset_column = column
            elif i == BitCol.NAME:
                column = EditableColumn(
                    col[BIT_TITLE], self.field_name_edit, i, col[BIT_MONO]
                )
            elif i == BitCol.BIT:
                column = EditableColumn(
                    col[BIT_TITLE], self.update_bits, i, col[BIT_MONO]
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

    def field_name_edit(self, cell, path, new_text, col):
        """
        Primary callback when a text field is edited in the BitList. Based off
        the column, we pass it to a function to handle the data.
        """

        field = self.__model.get_bitfield_at_path(path)
        if new_text != field.field_name:
            new_text = new_text.upper().replace(" ", "_")
            new_text = new_text.replace("/", "_").replace("-", "_")

            register = self.__model.register

            current_names = [
                f.field_name for f in register.get_bit_fields() if f != field
            ]

            if new_text not in current_names:
                self.__model[path][BitCol.NAME] = new_text
                field.field_name = new_text
                self.__modified()
            else:
                LOGGER.error(
                    '"%s" has already been used as a field name', new_text
                )

    def field_type_edit(self, cell, path, node, col):
        """
        The callback function that occurs whenever a combo entry is altered
        in the BitList. The 'col' value tells us which column was selected,
        and the path tells us the row. So [path][col] is the index into the
        table.
        """
        field = self.__model.get_bitfield_at_path(path)
        model = cell.get_property("model")
        self.__model[path][col] = model.get_value(node, 0)
        self.update_type_info(field, model, path, node)
        self.__modified()

    def update_type_info(self, field, model, path, node):
        field.field_type = model.get_value(node, 1)

        if not field.output_signal:
            field.output_signal = "%s_%s_OUT" % (
                self.__model.register.token,
                field.field_name,
            )

        if TYPE_ENB[field.field_type][0] and not field.input_signal:
            field.input_signal = "%s_%s_IN" % (
                self.__model.register.token,
                field.field_name,
            )

        if TYPE_ENB[field.field_type][1] and not field.control_signal:
            field.control_signal = "%s_%s_LD" % (
                self.__model.register.token,
                field.field_name,
            )

    def update_bits(self, cell, path, new_text, col):
        """
        Called when the bits column of the BitList is edited. If the new text
        does not match a valid bit combination (determined by the VALID_BITS
        regular expression, then we do not modifiy the ListStore, which
        prevents the display from being altered. If it does match, we extract
        the start or start and stop positions, and alter the model and the
        corresponding field.
        """

        field = self.__model.get_bitfield_at_path(path)
        match = VALID_BITS.match(new_text)
        if match:
            groups = match.groups()
            stop = int(groups[0])

            if groups[2]:
                start = int(groups[2])
            else:
                start = stop

            # TODO: check for overlapping bits
            register = self.__model.register
            if stop >= register.width:
                LOGGER.error("Bit position is greater than register width")
                return

            if stop != field.msb or start != field.lsb:
                field.msb, field.lsb = stop, start
                register.change_bit_field(field)
                self.__modified()

            self.__model[path][BitCol.BIT] = bits(field)
            self.__model[path][BitCol.SORT] = field.start_position


def bits(field):
    "Returns a text representation of the bit field range"

    if field.lsb == field.msb:
        return "{:d}".format(field.lsb)
    return "{:d}:{:d}".format(field.msb, field.lsb)


def reset_value(field):
    "Returns a string representation of the reset value."

    strval = "{:x}".format(field.reset_value)
    return "0x" + strval.zfill(int(field.width / 4))


def get_field_reset_data(field):
    "Converts the fields reset value/type into a displayable value."

    if field.reset_type == ResetType.NUMERIC:
        reset = reset_value(field)
    elif field.reset_type == ResetType.INPUT:
        reset = field.reset_input
    else:
        reset = field.reset_parameter
    return reset
