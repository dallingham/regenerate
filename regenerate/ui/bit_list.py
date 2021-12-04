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
from enum import IntEnum
from typing import Optional, Callable, List, Union
from gi.repository import Gtk

from regenerate.db import TYPES, LOGGER, ResetType, BitField
from regenerate.ui.columns import (
    EditableColumn,
    MenuEditColumn,
    SwitchComboMapColumn,
)
from regenerate.ui.enums import BitCol
from regenerate.db import ParameterFinder, ShareType, ParameterData

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


class BitModelCol(IntEnum):
    "Model column IDs"

    TITLE = 0
    SIZE = 1
    SORT = 2
    EXPAND = 3
    MONO = 4


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

    def append_field(self, field: BitField) -> Gtk.TreePath:
        """
        Add the field to the model.

        Fills out the fields of the model from the field parameters.

        Parameters:
           field (BitField): Bit field to add to the model

        Returns:
           Gtk.TreePath: Path of the row that was added

        """
        node = self.append(
            row=[
                None,
                field.msb.int_decimal_str(),
                str(field.lsb),
                field.name,
                TYPE2STR[field.field_type][0],
                get_field_reset_data(field),
                field.lsb,
                field,
            ]
        )
        return self.get_path(node)

    def update_fields(self) -> None:
        """
        Add the field to the model.

        Fills out the fields of the model from the field parameters.

        Parameters:
           field (BitField): Bit field to add to the model

        Returns:
           Gtk.TreePath: Path of the row that was added

        """
        for row in self:
            field = row[BitCol.FIELD]
            row[BitCol.MSB] = field.msb.int_decimal_str()
            row[BitCol.LSB] = str(field.lsb)
            row[BitCol.NAME] = field.name
            row[BitCol.TYPE] = TYPE2STR[field.field_type][0]
            row[BitCol.RESET] = get_field_reset_data(field)
            row[BitCol.SORT] = field.lsb

    def get_bitfield_at_path(self, path: Union[Gtk.TreePath, str]) -> BitField:
        """
        Return the field object associated with a ListModel path.

        Parameters:
           path: The path in the model that holds the field

        Returns:
           BitField: Bit field associated with the row

        """
        return self[path][BitCol.FIELD]


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

    def __init__(
        self,
        treeview: Gtk.TreeView,
        selection_changed: Callable,
        modified: Callable,
    ):
        """
        Initializes the object.

        Creates the object, connecting it to the ListView (obj).

        Parameters:
           treeview (Gtk.TreeView): treeview interface object
           selection_changed (Callable): function that is called when the
                selection changed
           modified (Callable): function that is called when the data has
                been modified

        """
        self._treeview = treeview
        self._lsb_col = None
        self._model: Optional[BitModel] = None
        self._modified = modified
        self._build_bitfield_columns()
        self.selection_changed = selection_changed
        self._treeview.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self._treeview.get_selection().connect(
            "changed", self.selection_changed
        )
        self._treeview.connect(
            "button-press-event", self.on_button_press_event
        )
        self._menu = self._build_menu()

    def _build_menu(self) -> Gtk.Menu:
        menu = Gtk.Menu()

        item = Gtk.MenuItem("Compact selected fields")
        item.connect("activate", self.compact_selected_fields)
        item.show()
        menu.add(item)

        item = Gtk.MenuItem("Push fields down")
        item.connect("activate", self.push_fields_down)
        item.show()
        menu.add(item)
        return menu

    def push_fields_down(self, _menuitem: Gtk.MenuItem) -> None:
        rows = self.get_selected_rows()
        if len(rows) != 1:
            LOGGER.error(
                "Only a single field can be selected to push fields down"
            )
            return

        selected_field = self._model[rows[0]][BitCol.FIELD]
        reg_width = self._model.register.width

        next_list = []
        field_list = self._model.register.get_bit_fields()

        field = field_list.pop(0)
        while field != selected_field:
            next_list.append((field.msb.resolve(), field.lsb))
            field = field_list.pop(0)

        next_expected = field.msb.resolve() + 1

        if field.msb.resolve() + 1 >= reg_width:
            LOGGER.error("Pushing down would exceed register size")
            return

        next_list.append((field.msb.resolve() + 1, field.lsb + 1))

        while len(field_list):
            field = field_list.pop(0)
            if next_expected + field.width >= reg_width:
                LOGGER.error("Pushing down would exceed register size")
                return

            if field.lsb == next_expected:
                next_list.append(
                    (next_expected + field.width, next_expected + 1)
                )
                next_expected = next_expected + field.width
            else:
                next_expected = -1
                next_list.append((field.msb.resolve(), field.lsb))

        for field in self._model.register.get_bit_fields():
            new_msb, new_lsb = next_list.pop(0)
            field.lsb = new_lsb
            field.msb.set_int(new_msb)

        self._modified()
        self._model.update_fields()

    def compact_selected_fields(self, _menuitem: Gtk.MenuItem) -> None:
        rows = self.get_selected_rows()
        if len(rows) < 2:
            return

        rowlist = [int(str(row)) for row in rows]
        if rowlist != list(range(rowlist[0], rowlist[0] + len(rowlist))):
            LOGGER.error("Fields must be contiguous to be compacted")
            return

        fields = [self._model[row][BitCol.FIELD] for row in rows]

        for field in fields:
            if field.msb.is_parameter:
                LOGGER.error(
                    "Fields with a parameterized MSB cannot be compacted"
                )
                return

        next_lsb = fields[0].lsb + fields[0].width

        for field in fields[1:]:
            width = field.width
            field.lsb = next_lsb
            field.msb.set_int(next_lsb + width - 1)
            next_lsb = next_lsb + width

        self.update_display()
        self._modified()

    def redraw(self) -> None:
        if self._model:
            self._model.clear()
            for field in self._model.register.get_bit_fields():
                self._model.append_field(field)

    def update_display(self) -> None:
        if self._model:
            self._model.update_fields()

    def set_parameters(self, parameters: List[ParameterData]) -> None:
        """
        Set the parameters for the bitlist.

        Updates the menus for the reset column and the msb column - the two
        columns that use parameters.

        Parameters:
           parameters (List[ParameterData]): parameter data list

        """
        self.reset_column.update_menu(
            sorted([(p.name, p.uuid) for p in parameters])
        )

        self.msb_column.update_menu(
            sorted([(f"{p.name}-1", p.uuid) for p in parameters])
        )

    def set_model(self, model):
        "Associates a List Model with the list view."
        self._model = model
        self._treeview.set_model(model)

    def set_mode(self, mode: ShareType) -> None:
        """
        Sets the mode of the type column

        Parameters:
           mode (ShareType): sets the share type of the column

        """
        self.type_column.set_mode(mode)

    def _build_bitfield_columns(self):
        """
        Builds the columns for the tree view. First, removes the old columns in
        the column list. The builds new columns and inserts them into the tree.
        """
        for (i, col) in enumerate(self.BIT_COLS):
            if i == BitCol.TYPE:
                column = SwitchComboMapColumn(
                    col[BitModelCol.TITLE],
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
                column = MenuEditColumn(
                    col[BitModelCol.TITLE],
                    self.reset_menu_edit,
                    self.reset_text_edit,
                    [],
                    i,
                )
                self.reset_column = column
            elif i == BitCol.NAME:
                column = EditableColumn(
                    col[BitModelCol.TITLE],
                    self.field_name_edit,
                    i,
                    monospace=False,
                )
            elif i == BitCol.MSB:
                column = MenuEditColumn(
                    col[BitModelCol.TITLE],
                    self._msb_menu,
                    self._msb_text,
                    [],
                    i,
                )
                self.msb_column = column
            elif i == BitCol.LSB:
                column = EditableColumn(
                    col[BitModelCol.TITLE],
                    self.update_lsb,
                    i,
                    monospace=True,
                )
                self._lsb_col = column

            if col[BitModelCol.SORT] >= 0:
                column.set_sort_column_id(col[BitModelCol.SORT])
            column.set_min_width(col[BitModelCol.SIZE])
            column.set_expand(col[BitModelCol.EXPAND])
            column.set_resizable(True)
            self._treeview.append_column(column)

    def get_selected_row(self):
        "Returns the path of the selected row"
        value = self._treeview.get_selection().get_selected_rows()
        if value:
            return value[1]
        return None

    def get_selected_rows(self) -> List[Gtk.TreePath]:
        "Returns the path of the selected row"
        return self._treeview.get_selection().get_selected_rows()[1]

    def select_row(self, path):
        "Selectes the row associated with the path"
        if path:
            self._treeview.get_selection().select_path(path)

    def selected_fields(self) -> List[BitField]:
        """
        Return the field object associated with selected row.

        Returns:
           Optional[BitField]: selected object, or None if no object

        """
        data = self._treeview.get_selection().get_selected_rows()
        if data:
            (store, row_list) = data
            return [
                store.get_value(store.get_iter(row), BitCol.FIELD)
                for row in row_list
            ]
        return []

    def add_new_field(self, field: BitField) -> None:
        """
        Add a new field to the model.

        Appends the field to the model, set start editing the LSB column.

        Parameters:
           field (BitField): New bitfield to add

        """
        if self._model:
            path = self._model.append_field(field)
            self._treeview.set_cursor(path, self._lsb_col, start_editing=True)

    def field_name_edit(
        self,
        _cell: Gtk.CellRendererText,
        path: Gtk.TreePath,
        new_text: str,
        _col: int,
    ) -> None:
        """
        Update the field name when edited.

        Primary callback when a text field is edited in the BitList. Based off
        the column, we pass it to a function to handle the data.

        Parameters:
           _cell (Gtk.CellRendererText): cell renderer, unused
           path (Gtk.TreePath): path of the edited row
           new_text (str): new text value
           _col: column number, unused

        """
        if self._model is None:
            return

        field = self._model.get_bitfield_at_path(path)
        if new_text != field.name:
            new_text = new_text.upper().replace(" ", "_")
            new_text = new_text.replace("/", "_").replace("-", "_")

            register = self._model.register

            current_names = [
                f.name for f in register.get_bit_fields() if f != field
            ]

            if new_text not in current_names:
                self._model[path][BitCol.NAME] = new_text
                field.name = new_text
                self._modified()
            else:
                LOGGER.warning(
                    '"%s" has already been used as a field name', new_text
                )

    def reset_text_edit(self, _cell, path, new_val, col) -> None:
        "Called when the text of the reset field has been altered"

        if self._model is None:
            return

        field = self._model.get_bitfield_at_path(path)

        if re.match(r"^(0x)?[a-fA-F0-9]+$", new_val):
            if _check_reset(field, int(new_val, 0)) is False:
                return
            field.reset_value = int(new_val, 0)
            field.reset_type = ResetType.NUMERIC
            self._model[path][col] = reset_value(field)
            self._modified()
        elif re.match(r"""^[A-Za-z]\w*$""", new_val):
            field.reset_input = new_val
            field.reset_type = ResetType.INPUT
            self._model[path][BitCol.RESET] = new_val
            self._modified()
        else:
            LOGGER.warning(
                '"%s" is not a valid constant, parameter, or signal name',
                new_val,
            )

    def reset_menu_edit(self, cell, path, node, _col) -> None:
        "Called with the reset field has been altered by the menu"

        if self._model is None:
            return

        model = cell.get_property("model")
        field = self._model.get_bitfield_at_path(path)
        field.reset_type = ResetType.PARAMETER
        new_val = model.get_value(node, 1)
        new_text = model.get_value(node, 0)
        field.reset_parameter = new_val

        if self._model:
            self._model[path][BitCol.RESET] = new_text
            self._modified()

    def field_type_edit(self, cell, path, node, col) -> None:
        """
        The callback function that occurs whenever a combo entry is altered
        in the BitList. The 'col' value tells us which column was selected,
        and the path tells us the row. So [path][col] is the index into the
        table.
        """
        if self._model:
            model = cell.get_property("model")
            field = self._model.get_bitfield_at_path(path)
            self._model[path][col] = model.get_value(node, 0)
            self.update_type_info(field, model, path, node)
            self._modified()

    def update_type_info(self, field: BitField, model, _path, node):
        "Updates the bit field type info"

        if self._model is None:
            return

        field.field_type = model.get_value(node, 1)

        if not field.output_signal:
            field.output_signal = "%s_%s_OUT" % (
                self._model.register.token,
                field.name,
            )

        if TYPE_ENB[field.field_type][0] and not field.input_signal:
            field.input_signal = "%s_%s_IN" % (
                self._model.register.token,
                field.name,
            )

        if TYPE_ENB[field.field_type][1] and not field.control_signal:
            field.control_signal = "%s_%s_LD" % (
                self._model.register.token,
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

        if self._model is None:
            return

        field = self._model.get_bitfield_at_path(path)
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
            self._model.register.change_bit_field(field)
            self._modified()

        self._model[path][BitCol.MSB] = f"{field.msb.int_str()}"

    def update_lsb(self, _cell, path, new_text, _col):
        """
        Called when the bits column of the BitList is edited. If the new text
        does not match a valid bit combination (determined by the VALID_BITS
        regular expression, then we do not modifiy the ListStore, which
        prevents the display from being altered. If it does match, we extract
        the start or start and stop positions, and alter the model and the
        corresponding field.
        """

        if self._model is None:
            return

        field = self._model.get_bitfield_at_path(path)
        start = int(new_text, 0)

        if self.check_for_overlaps(field, start, field.msb.resolve()) is False:
            return

        if self.check_for_width(start, field.msb.resolve()) is False:
            return

        if start != field.lsb:
            field.lsb = start
            self._model.register.change_bit_field(field)
            self._modified()

        self._model[path][BitCol.LSB] = f"{field.lsb}"
        self._model[path][BitCol.SORT] = field.lsb

    def check_for_width(self, _start: int, stop: int) -> bool:
        "Checks to make sure the bit position is with the valid range"

        if self._model is None:
            return False

        reg = self._model.register
        if stop >= reg.width:
            LOGGER.warning(
                "Bit position (%d) is greater than register width (%d)",
                stop,
                reg.width,
            )
            return False
        return True

    def check_for_overlaps(
        self, field: BitField, start: int, stop: int
    ) -> bool:
        "Checks for overlapping bit fields"

        if self._model is None:
            return False

        register = self._model.register

        used = set()
        for fld in register.get_bit_fields():
            if fld.uuid != field.uuid:
                for bit in range(fld.lsb, fld.msb.resolve() + 1):
                    used.add(bit)

        for bit in range(start, stop + 1):
            if bit in used:
                LOGGER.warning(
                    "Bit %d overlaps with the bits in another register", bit
                )
                return False
        return True

    def _msb_menu(self, cell, path, node, _col) -> None:
        """
        Called when text has been edited. Selects the correct function
        depending on the edited column
        """
        if self._model is None:
            return

        model = cell.get_property("model")
        field = self._model[path][-1]
        descript = model.get_value(node, 0)
        uuid = model.get_value(node, 1)
        field.msb.set_param(uuid, -1)
        self._model[path][BitCol.MSB] = descript
        self._modified()

    def _msb_text(self, _cell, path, new_text, _col) -> None:
        """
        Called when text has been edited. Selects the correct function
        depending on the edited column
        """
        if self._model is None:
            return

        field = self._model[path][-1]
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

            field.msb.set_int(int(new_text, 0))
            self._model[path][BitCol.MSB] = f"{field.msb.int_decimal_str()}"
            self._modified()
        except ValueError:
            ...

    def on_button_press_event(self, _obj, event):
        "Callback for a button press on the register list. Display the menu"

        if event.button == 3:
            self._menu.popup(
                None, None, None, 1, 0, Gtk.get_current_event_time()
            )
            return True
        return False


def _check_reset(field: BitField, value: int) -> bool:
    "Checks the reset value for validity"

    maxval = (1 << ((field.msb.resolve() - field.lsb) + 1)) - 1
    if value > maxval:
        LOGGER.warning(
            "Reset value (0x%x) is greater than the maximum value (0x%x)",
            value,
            maxval,
        )
        return False
    return True


def reset_value(field: BitField) -> str:
    "Returns a string representation of the reset value."

    return f"0x{field.reset_value:04x}"


def get_field_reset_data(field: BitField) -> str:
    "Converts the fields reset value/type into a displayable value."

    if field.reset_type == ResetType.NUMERIC:
        reset = reset_value(field)
    elif field.reset_type == ResetType.INPUT:
        reset = field.reset_input
    else:
        finder = ParameterFinder()
        param = finder.find(field.reset_parameter)
        reset = param.name
    return reset
