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
Provides the editing interface to the register table
"""

from collections import namedtuple
from gi.repository import Gtk
from regenerate.ui.columns import (
    EditableColumn,
    ComboMapColumn,
    MyComboMapColumn,
)
from regenerate.ui.error_dialogs import ErrorMsg
from regenerate.db import LOGGER
from regenerate.db.enums import ShareType
from regenerate.extras.regutils import build_define
from regenerate.ui.enums import RegCol, RegColType

BAD_TOKENS = " /-@!#$%^&*()+=|{}[]:\"';\\,.?"

REPLACE = {
    "ADDRESS": "ADDR",
    "ALTERNATE": "ALT",
    "ARBITER": "ARB",
    "ARBITRATION": "ARB",
    "CLEAR": "CLR",
    "CLOCK": "CLK",
    "COMMAND": "CMD",
    "COMPARE": "CMP",
    "CONFIG": "CFG",
    "CONFIGURATION": "CFG",
    "CONTROL": "CTRL",
    "COUNT": "CNT",
    "COUNTER": "CNTR",
    "CURRENT": "CUR",
    "DEBUG": "DBG",
    "DELAY": "DLY",
    "DESTINATION": "DEST",
    "DIVIDER": "DIV",
    "ENABLE": "EN",
    "ERROR": "ERR",
    "ERRORS": "ERRS",
    "EXTERNAL": "EXT",
    "FABRIC": "FAB",
    "HARDWARE": "HW",
    "HEADER": "HDR",
    "INTERRUPT": "INT",
    "LOAD": "LD",
    "MAILBOX": "MBX",
    "MANAGEMENT": "MGMT",
    "MASTER": "MSTR",
    "MAXIMUM": "MAX",
    "MESSAGE": "MSG",
    "MINIMUM": "MIN",
    "NUMBER": "NUM",
    "PACKET": "PKT",
    "PARITY": "PAR",
    "POINTER": "PTR",
    "POWER": "PWR",
    "RANGE": "RNG",
    "READ": "RD",
    "RECEIVE": "RX",
    "REFERENCE": "REF",
    "REGISTER": "",
    "REQUEST": "REQ",
    "REQUESTER": "REQ",
    "RESET": "RST",
    "RESPONSE": "RSP",
    "SELECT": "SEL",
    "SLAVE": "SLV",
    "SOFTWARE": "SW",
    "SOURCE": "SRC",
    "SPACE": "SPC",
    "STATUS": "STAT",
    "SYSTEM": "SYS",
    "TRANSACTION": "TXN",
    "TRANSLATION": "TRANS",
    "TRANSMIT": "TX",
    "VALUE": "VAL",
    "VECTOR": "VECT",
    "WRITE": "WR",
}


class RegisterModel(Gtk.ListStore):
    """
    A derivation of the ListStore that defines the columns. The columsn are:

    Address, Name, Define, Width, Address Sort Value, Register Instance

    A couple of convenience functions are provided that allow a register to
    be added, to fetch the register at a particular path, and to set the
    address.
    """

    BIT2STR = (
        ("8 bits", 8),
        ("16 bits", 16),
        ("32 bits", 32),
        ("64 bits", 64),
    )

    STR2BIT = {8: "8 bits", 16: "16 bits", 32: "32 bits", 64: "64 bits"}

    def __init__(self):
        super().__init__(str, str, str, str, str, str, int, str, object)
        self.reg2path = {}

    def append_register(self, register):
        """
        Adds a new row in the ListStore for the specified register,
        filling in the data from the register into the appropriate
        column.
        """
        if register.ram_size:
            addr = "0x%04x:0x%x" % (register.address, register.ram_size)
        else:
            addr = "0x%04x" % register.address

        data = (
            None,
            addr,
            register.register_name,
            register.token,
            register.dimension_str,
            self.STR2BIT[register.width],
            register.address,
            None,
            register,
        )

        node = self.append(row=data)
        path = self.get_path(node)

        self.reg2path[register] = path
        return path

    def delete_register(self, register):
        """
        Adds a new row in the ListStore for the specified register,
        filling in the data from the register into the appropriate
        column.

        After the register is deleted, we need to fix all the register
        to path operations by decrementing the corresponding path
        """
        old_path = self.reg2path[register]

        del self[self.reg2path[register]]
        del self.reg2path[register]

        for reg in self.reg2path:
            if self.reg2path[reg] > old_path:
                self.reg2path[reg] = Gtk.TreePath(self.reg2path[reg][0] - 1)

    def set_tooltip(self, reg, msg):
        """
        Sets the tooltip for the register.
        """
        path = self.get_path_from_register(reg)
        self[path][RegCol.TOOLTIP] = msg

    def get_register_at_path(self, path):
        """
        Given a path (row) in the ListStore, we return the corresponding
        Register.
        """
        return self[path][RegCol.OBJ]

    def set_warning_for_register(self, register, flag):
        """
        Sets the warning icon for the register in the table
        """
        path = self.reg2path[register]
        if flag:
            self[path][RegCol.ICON] = Gtk.STOCK_DIALOG_WARNING
        else:
            self[path][RegCol.ICON] = None

    def get_path_from_register(self, register):
        """
        Given a path (row) in the ListStore, we return the corresponding
        Register.
        """
        return self.reg2path[register]

    def set_address_at_path(self, path, addr, length):
        """
        Sets the address for a register, but also sets the corresponding
        value for the sort columns.
        """
        node = self.get_iter(path)
        if length:
            self.set(node, RegCol.ADDR, "0x%04x:0x%x" % (addr, length))
        else:
            self.set(node, RegCol.ADDR, "0x%04x" % addr)
        self.set(node, RegCol.SORT, addr)


ColDef = namedtuple(
    "ColDef",
    ["title", "size", "sort_column", "expand", "type", "mono", "placeholder"],
)


class RegisterList:
    """
    Provides the interface to the register table
    """

    _COLS = (  # Title,   Size, Column, Expand, Type, Monospace
        ColDef("", 30, RegCol.ICON, False, RegColType.ICON, False, None),
        ColDef(
            "Address",
            100,
            RegCol.SORT,
            False,
            RegColType.TEXT,
            True,
            "Address",
        ),
        ColDef(
            "Name",
            200,
            RegCol.NAME,
            True,
            RegColType.TEXT,
            False,
            "Missing Register Descriptive Name",
        ),
        ColDef(
            "Token",
            150,
            RegCol.DEFINE,
            True,
            RegColType.TEXT,
            True,
            "Missing Register Token Name",
        ),
        ColDef(
            "Dimension", 150, RegCol.DIM, False, RegColType.COMBO, False, None
        ),
        ColDef("Width", 150, -1, False, RegColType.COMBO, False, None),
    )

    def __init__(
        self,
        obj,
        select_change_function,
        mod_function,
        update_addr,
        set_warn_flags,
    ):
        self._obj = obj
        self._model = None
        self._col = None
        self._icon_col = None
        self._icon_renderer = None
        self._selection = self._obj.get_selection()
        self._set_modified = mod_function
        self._update_addr = update_addr
        self._set_warn_flags = set_warn_flags
        self._selection.connect("changed", select_change_function)
        self._build_columns()
        self._parameter_names = set()

    def set_parameters(self, parameters):
        self._parameter_names = set({(p[0], p[0]) for p in parameters})
        self.dim_column.update_menu(sorted(list(self._parameter_names)))

    def get_selected_row(self):
        """
        Returns the selected row
        """
        return self._selection.get_selected_rows()[1]

    def get_selected_node(self):
        """
        Returns the node of the selected row
        """
        return self._selection.get_selected()[1]

    def get_selected_position(self):
        """
        Returns the node of the selected row
        """
        (model, node) = self._selection.get_selected()
        path = model.get_path(node)
        return path

    def delete_selected_node(self):
        """
        Deletes the selected from from the table
        """
        reg = self.get_selected_register()
        self._model.delete_register(reg)

    def select_row(self, row):
        """
        Select the given row
        """
        self._selection.select_path(row)

    def _build_columns(self):
        """
        Builds the columns for the tree view. First, removes the old columns in
        the column list. The builds new columns and inserts them into the tree.
        """
        for (i, col) in enumerate(self._COLS):
            if col.type == RegColType.COMBO:
                if col.title == "Dimension":
                    column = MyComboMapColumn(
                        col.title,
                        self._dimension_menu,
                        self._dimension_text,
                        [],
                        i,
                    )
                    column.set_resizable(True)
                    self.dim_column = column
                else:
                    column = ComboMapColumn(
                        col.title,
                        self._combo_edited,
                        RegisterModel.BIT2STR,
                        i,
                    )
                    column.set_resizable(True)
            elif col.type == RegColType.TEXT:
                column = EditableColumn(
                    col.title,
                    self._text_edited,
                    i,
                    col.mono,
                    placeholder=col.placeholder,
                )
                column.set_resizable(True)
            else:
                self._icon_renderer = Gtk.CellRendererPixbuf()
                column = Gtk.TreeViewColumn(
                    "", self._icon_renderer, stock_id=i
                )
                column.set_resizable(True)
                self._icon_col = column

            column.set_min_width(col.size)
            column.set_expand(col.expand)
            if i == 1:
                self._col = column
            if col.sort_column >= 0:
                column.set_sort_column_id(col.sort_column)
            self._obj.append_column(column)
        self._obj.set_search_column(3)
        self._obj.set_tooltip_column(RegCol.TOOLTIP)

    def set_model(self, model):
        """
        Sets the active model.
        """
        self._obj.set_model(model)
        if model:
            self._model = model.get_model().get_model()
        else:
            self._model = None

    def add_new_register(self, register):
        """
        Addes a new register to the model and set it to edit the
        default column
        """
        path = self._model.append_register(register)
        self._obj.set_cursor(path, self._col, start_editing=True)
        return path

    def get_selected_register(self):
        """
        Returns the register associated with the selected row
        """
        data = self._selection.get_selected()
        if data:
            (store, node) = data
            if node:
                return store.get_value(node, RegCol.OBJ)
        return None

    def _ram_update_addr(self, reg, path, text):
        """
        Updates the address associated with a RAM address
        """
        (addr_str, len_str) = text.split(":")
        try:
            new_addr = int(addr_str, 16)
            new_length = int(len_str, 16)
            if new_addr != reg.address or new_length != reg.ram_size:
                self._update_addr(reg, new_addr, new_length)
                self._model.set_address_at_path(path, new_addr, new_length)
                self._set_modified()
        except KeyError:
            ErrorMsg(
                "Internal Error",
                "Deleting the register caused an internal "
                "inconsistency.\nPlease exit without saving "
                "to prevent any corruption to\n"
                "your database and report this error.",
            )

    def _reg_update_addr(self, reg, path, text):
        """
        Updates the address associated with a register address
        """
        try:
            new_addr = int(text, 16)
            new_length = 0
            if new_addr != reg.address or new_length != reg.ram_size:
                self._update_addr(reg, new_addr, new_length)
                self._model.set_address_at_path(path, new_addr, new_length)
                self._set_modified()
        except KeyError:
            ErrorMsg(
                "Internal Error",
                "Deleting the register caused an internal "
                "inconsistency.\nPlease exit without saving to "
                "prevent any corruption to\n"
                "your database and report this error.",
            )

    def _reg_update_name(self, reg, path, text):
        """
        Updates the name associated with the register. Called after the text
        has been edited
        """
        if text != reg.register_name:
            reg.register_name = text
            self._set_modified()
        self._model[path][RegCol.NAME] = reg.register_name

        if reg.token == "":
            value = build_define(reg.register_name)
            self._model[path][RegCol.DEFINE] = value
            reg.token = value
            self._set_modified()

    def _reg_update_dim(self, reg, path, text):
        """
        Updates the name associated with the register. Called after the text
        has been edited
        """
        if text != reg.dimension_str:
            reg.dimension = text
            self._set_modified()
        self._model[path][RegCol.DIM] = text

    def _reg_update_define(self, reg, path, text, _cell):
        """
        Updates the token name associated with the register. Called after the
        text has been edited
        """
        for i in BAD_TOKENS:
            text = text.replace(i, "_")
        text = text.upper()
        if text != reg.token:
            reg.token = text
            self._set_warn_flags(reg)
            self._set_modified()
        self._model[path][RegCol.DEFINE] = reg.token

    def _new_address_is_not_used(self, new_text, path):
        """
        Verifies that the new address has not been previously used, or
        does not overlap with an existing address.
        """
        addr_list = set()
        ro_list = set()
        wo_list = set()

        for (index, data) in enumerate(self._model):
            if index == int(path):
                continue
            reg = data[-1]
            start = reg.address
            stop = reg.address + (reg.dimension * (reg.width >> 3))
            for i in range(start, stop):
                if reg.share == ShareType.READ:
                    ro_list.add(i)
                elif reg.share == ShareType.WRITE:
                    wo_list.add(i)
                else:
                    addr_list.add(i)

        data = new_text.split(":")

        if len(data) == 1:
            length = 1
        else:
            length = int(data[1], 16)
        start_address = int(data[0], 16)

        for addr in range(start_address, start_address + length):
            if addr in addr_list or addr in wo_list and addr in ro_list:
                return False
        return True

    def _handle_edited_address(self, register, path, new_text):
        """
        Called when an address in the table has changed
        """
        try:
            if ":" in new_text:
                self._handle_ram_address(register, path, new_text)
            else:
                self._handle_reg_address(register, path, new_text)
        except ValueError:
            LOGGER.warning(
                'Address %0x was not changed: invalid value "%s"',
                register.address,
                new_text,
            )

    def _handle_ram_address(self, register, path, new_text):
        """
        Called when the RAM address in the table has changed
        """
        if self._new_address_is_not_used(new_text, path):
            self._ram_update_addr(register, path, new_text)
        else:
            ErrorMsg(
                "Address already used",
                "The address %0x is already used by another register"
                % int(new_text, 16),
            )

    def _check_address_align(self, address, width):
        align = width >> 3
        return address % align == 0

    def _handle_reg_address(self, register, path, new_text):
        """
        Called when the register address in the table has changed
        """
        address = int(new_text, 16)
        if not self._check_address_align(address, register.width):
            ErrorMsg(
                "Address does not match register width",
                "The address %04x is not aligned to a %d bit boundary"
                % (address, register.width),
            )
        elif not self._new_address_is_not_used(new_text, path):
            ErrorMsg(
                "Address already used",
                "%0x is already used by another register" % address,
            )
        else:
            self._reg_update_addr(register, path, new_text)

    def _text_edited(self, cell, path, new_text, col):
        """
        Called when text has been edited. Selects the correct function
        depending on the edited column
        """
        register = self._model.get_register_at_path(path)
        new_text = new_text.strip()
        if col == RegCol.ADDR:
            self._handle_edited_address(register, path, new_text)
        elif col == RegCol.NAME:
            self._reg_update_name(register, path, new_text)
        elif col == RegCol.DIM:
            self._reg_update_dim(register, path, new_text)
        elif col == RegCol.DEFINE:
            self._reg_update_define(register, path, new_text, cell)

    def _dimension_text(self, _cell, path, new_text, _col):
        """
        Called when text has been edited. Selects the correct function
        depending on the edited column
        """
        register = self._model.get_register_at_path(path)
        new_text = new_text.strip()
        try:
            value = int(new_text, 16)
            if value < 1:
                LOGGER.warning(
                    "The dimension for a register must be 1 or greater"
                )
                return
            self._reg_update_dim(register, path, new_text)
        except ValueError:
            if new_text in self._parameter_names:
                self._reg_update_dim(register, path, new_text)
            else:
                LOGGER.warning(
                    '"%s" is not a valid dimension. It must be an '
                    "integer greater than 1 or a defined parameter",
                    new_text,
                )

    def _dimension_menu(self, cell, path, node, _col):
        """
        Called when text has been edited. Selects the correct function
        depending on the edited column
        """
        model = cell.get_property("model")
        register = self._model.get_register_at_path(path)
        new_value = model.get_value(node, 1)
        self._reg_update_dim(register, path, new_value)

    def _combo_edited(self, cell, path, node, col):
        """
        Called when the combo box in the table has been altered
        """
        model = cell.get_property("model")
        register = self._model.get_register_at_path(path)

        new_width = model.get_value(node, 1)
        if not self._check_address_align(register.address, new_width):
            ErrorMsg(
                "Address does not match register width",
                "The address %04x is not aligned to a %d bit boundary"
                % (register.address, new_width),
            )
        else:
            self._model[path][col] = model.get_value(node, 0)
            register.width = new_width
            self._set_modified()
