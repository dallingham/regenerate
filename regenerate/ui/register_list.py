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
from typing import List, Tuple, Optional

from gi.repository import Gtk
from regenerate.db import LOGGER, Register, ShareType
from regenerate.extras.regutils import build_define

from .columns import EditableColumn, ComboMapColumn, MenuEditColumn
from .error_dialogs import ErrorMsg
from .enums import RegCol, RegColType

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


class BitWidth:
    "Handles the bit with selection text/mappings"

    def __init__(self, size: int):
        self.bit2str = []
        self.str2bit = {}

        if size >= 8:
            self.bit2str.append(("8-bits", 8))
            self.str2bit[8] = "8-bits"
        if size >= 16:
            self.bit2str.append(("16-bits", 16))
            self.str2bit[16] = "16-bits"
        if size >= 32:
            self.bit2str.append(("32-bits", 32))
            self.str2bit[32] = "32-bits"
        if size == 64:
            self.bit2str.append(("64-bits", 64))
            self.str2bit[64] = "64-bits"

    def get_list(self) -> List[Tuple[str, int]]:
        "Returns the list of string/int mappings"

        return self.bit2str

    def get_text(self, size: int) -> str:
        "Returns the text associated with size"

        return self.str2bit[size]


class RegisterModel(Gtk.ListStore):
    """
    A derivation of the ListStore that defines the columns. The columsn are:

    Address, Name, Define, Width, Address Sort Value, Register Instance

    A couple of convenience functions are provided that allow a register to
    be added, to fetch the register at a particular path, and to set the
    address.
    """

    def __init__(self, size):
        super().__init__(str, str, str, str, str, str, int, str, object)
        self.reg2path = {}
        self.bit_width = BitWidth(size)

    def append_register(self, register: Register) -> str:
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
            register.name,
            register.token,
            register.dimension.int_str(),
            self.bit_width.get_text(register.width),
            register.address,
            None,
            register,
        )

        node = self.append(row=data)
        path = self.get_path(node)

        self.reg2path[register] = path
        return path

    def delete_register(self, register: Register) -> None:
        """
        Adds a new row in the ListStore for the specified register,
        filling in the data from the register into the appropriate
        column.

        After the register is deleted, we need to fix all the register
        to path operations by decrementing the corresponding path
        """
        old_path = self.reg2path[register]

        self.remove(self[old_path].iter)
        del self.reg2path[register]

        for reg in self.reg2path:
            if self.reg2path[reg] > old_path:
                self.reg2path[reg] = Gtk.TreePath(self.reg2path[reg][0] - 1)

    def set_tooltip(self, reg: Register, msg: str) -> None:
        """
        Sets the tooltip for the register.
        """
        try:
            path = self.get_path_from_register(reg)
            self[path][RegCol.TOOLTIP] = msg
        except IndexError:
            pass

    def get_register_at_path(self, path: str) -> Register:
        """
        Given a path (row) in the ListStore, we return the corresponding
        Register.
        """
        return self[path][RegCol.OBJ]

    def set_warning_for_register(self, register: Register, flag: bool) -> None:
        "Sets the warning icon for the register in the table"
        try:
            path = self.reg2path[register]
            self[path][RegCol.ICON] = (
                Gtk.STOCK_DIALOG_WARNING if flag else None
            )
        except IndexError:
            pass

    def get_path_from_register(self, register: Register) -> str:
        "Returns the path in the list associated with the register"
        return self.reg2path[register]

    def set_address_at_path(self, path: str, addr: int, length: int) -> None:
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
    "Provides the interface to the register table"

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
        self._addr_col = None
        self._selection = self._obj.get_selection()
        self._selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        self._selection.connect("changed", select_change_function)
        self._set_modified = mod_function
        self._update_addr = update_addr
        self._set_warn_flags = set_warn_flags
        self._build_columns()
        self._parameter_names = set()

    def update_bit_width(self, size: int):
        "Updates the bit width"

        self._model.bit_width = BitWidth(size)
        self._width_column.update_menu(self._model.bit_width.get_list())

    def set_parameters(self, parameters):
        "Sets the parameters"

        self._parameter_names = set({(p.name, p.uuid) for p in parameters})
        self._dim_column.update_menu(sorted(list(self._parameter_names)))

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
        if model and node:
            return model.get_path(node)
        return None

    def delete_selected_node(self):
        """
        Deletes the selected from from the table
        """
        for reg in self.get_selected_registers():
            self._model.delete_register(reg)

    def select_row(self, row):
        """
        Select the given row
        """
        self._selection.select_path(row)

    def _build_text_column(
        self, name: str, width: int, data_col: int, mono: bool
    ):
        "Builds a editable text column"

        col = EditableColumn(
            name,
            self._text_edited,
            data_col,
            mono,
            placeholder=name,
        )
        col.set_resizable(True)
        col.set_min_width(width)
        col.set_expand(False)
        return col

    def _build_dimension_col(self):
        "Builds the dimension column"

        col = MenuEditColumn(
            "Dimension",
            self._dimension_menu,
            self._dimension_text,
            [],
            RegCol.DIM,
        )
        col.set_resizable(True)
        col.set_min_width(125)
        col.set_expand(False)
        return col

    def _build_width_column(self):
        "Builds the width column"

        col = ComboMapColumn(
            "Width",
            self._combo_edited,
            [],
            RegCol.WIDTH,
        )
        col.set_resizable(True)
        col.set_min_width(150)
        col.set_expand(False)
        return col

    def _build_columns(self):
        """
        Builds the columns for the tree view. First, removes the old columns in
        the column list. The builds new columns and inserts them into the tree.
        """

        self._obj.append_column(_build_icon_col())

        self._addr_col = self._build_text_column("Address", 100, 1, True)
        self._obj.append_column(self._addr_col)

        self.name_col = self._build_text_column("Name", 350, 2, False)
        self._obj.append_column(self.name_col)

        self._token_col = self._build_text_column("Token", 300, 3, True)
        self._obj.append_column(self._token_col)

        self._dim_column = self._build_dimension_col()
        self._obj.append_column(self._dim_column)

        self._width_column = self._build_width_column()
        self._obj.append_column(self._width_column)

        self._obj.set_search_column(RegCol.NAME)
        self._obj.set_tooltip_column(RegCol.TOOLTIP)

    def set_model(self, model):
        "Sets the active model."

        self._obj.set_model(model)
        self._model = model.get_model() if model else None

    def clear(self):
        "Clears the associated model"
        self._model.clear()

    def load_reg_into_model(self, register: Register) -> None:
        "Loads the register into the model"
        self._model.append_register(register)

    def add_new_register(self, register: Register) -> str:
        """
        Addes a new register to the model and set it to edit the
        default column
        """
        path = self._model.append_register(register)
        self._obj.set_cursor(path, self._addr_col, start_editing=True)
        return path

    def get_selected_registers(self):
        """
        Returns the register associated with the selected row
        """
        registers = []
        store, path_list = self._selection.get_selected_rows()
        if path_list:
            for path in path_list:
                registers.append(store[path][RegCol.OBJ])
        return registers

    def get_selected_reg_iters(self):
        """
        Returns the register associated with the selected row
        """
        registers = []
        store, path_list = self._selection.get_selected_rows()
        if path_list:
            for path in reversed(path_list):
                registers.append((path, store[path][RegCol.OBJ]))
        return registers

    def find_row_by_register(self, register: Register):
        for row in self._model:
            if row[RegCol.OBJ].uuid == register.uuid:
                return row
        return 0

    def get_selected_reg_paths(self):
        """
        Returns the register associated with the selected row
        """
        registers = []
        _, path_list = self._selection.get_selected_rows()
        if path_list:
            for path in path_list:
                registers.append(int(str(path)))
        return registers

    def _ram_update_addr(self, reg: Register, path: str, text: str):
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
        self.rebuild_model(reg)

    def rebuild_model(self, selected: Optional[Register]) -> None:

        reglist = sorted(
            [row[RegCol.OBJ] for row in self._model], key=lambda x: x.address
        )
        self._model.clear()
        sel_row = 0
        for i, reg in enumerate(reglist):
            if selected and reg.uuid == selected.uuid:
                sel_row = i
            self._model.append_register(reg)
        self.select_row(sel_row)
        self._obj.scroll_to_cell(sel_row, None, True, 0.5, 0.0)

    def _reg_update_addr(self, reg: Register, path: str, text: str) -> None:
        """
        Updates the address associated with a register address
        """
        new_addr = int(text, 16)
        new_length = 0
        if new_addr != reg.address or new_length != reg.ram_size:
            self._update_addr(reg, new_addr, new_length)
            self._model.set_address_at_path(path, new_addr, new_length)
            self._set_modified()
        self.rebuild_model(reg)

    def _reg_update_name(self, reg: Register, path: str, text: str) -> None:
        """
        Updates the name associated with the register. Called after the text
        has been edited
        """
        if text != reg.name:
            reg.name = text
            self._set_modified()
        self._model[path][RegCol.NAME] = reg.name

        if reg.token == "":
            value = build_define(reg.name)
            self._model[path][RegCol.DEFINE] = value
            reg.token = value
            self._set_modified()

    def _reg_update_dim(self, reg: Register, path: str, text: str) -> None:
        """
        Updates the dimension associated with the register. Called after the text
        has been edited
        """
        if text != reg.dimension.int_str():
            reg.dimension.set_int(int(text, 0))
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
            stop = reg.address + (reg.dimension.resolve() * (reg.width >> 3))
            for i in range(start, stop):
                if reg.share == ShareType.READ:
                    ro_list.add(i)
                elif reg.share == ShareType.WRITE:
                    wo_list.add(i)
                else:
                    addr_list.add(i)

        data = new_text.split(":")

        length = 1 if len(data) == 1 else int(data[1], 16)
        start_address = int(data[0], 16)

        return not any(
            addr in addr_list or addr in wo_list and addr in ro_list
            for addr in range(start_address, start_address + length)
        )

    def _handle_edited_address(
        self, register: Register, path: str, text: str
    ) -> None:
        """
        Called when an address in the table has changed
        """
        try:
            if ":" in text:
                self._handle_ram_address(register, path, text)
            else:
                self._handle_reg_address(register, path, text)
        except ValueError:
            LOGGER.warning(
                'Address %0x was not changed: invalid value "%s"',
                register.address,
                text,
            )

    def _handle_ram_address(
        self, register: Register, path: str, text: str
    ) -> None:
        """
        Called when the RAM address in the table has changed
        """
        if self._new_address_is_not_used(text, path):
            self._ram_update_addr(register, path, text)
        else:
            ErrorMsg(
                "Address already used",
                "The address %0x is already used by another register"
                % int(text, 16),
            )

    def _handle_reg_address(
        self, register: Register, path: str, text: str
    ) -> None:
        "Called when the register address in the table has changed"

        address = int(text, 16)
        if not check_address_align(address, register.width):
            ErrorMsg(
                "Address does not match register width",
                "The address %04x is not aligned to a %d bit boundary"
                % (address, register.width),
            )
        elif not self._new_address_is_not_used(text, path):
            ErrorMsg(
                "Address already used",
                "%0x is already used by another register" % address,
            )
        else:
            self._reg_update_addr(register, path, text)

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
        # elif col == RegCol.DIM:
        #     self._reg_update_dim(register, path, new_text)
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
                    "integer greater than 0 or a defined parameter",
                    new_text,
                )

    def _dimension_menu(self, cell, path, node, _col):
        """
        Called when text has been edited. Selects the correct function
        depending on the edited column
        """
        model = cell.get_property("model")
        register = self._model.get_register_at_path(path)
        uuid = model.get_value(node, 1)
        name = model.get_value(node, 0)
        register.dimension.set_param(uuid)
        self._model[path][RegCol.DIM] = name
        self._set_modified()

    #        self._reg_update_dim(register, path, new_value)

    def _combo_edited(self, cell, path, node, col):
        "Called when the combo box in the table has been altered"

        model = cell.get_property("model")
        register = self._model.get_register_at_path(path)

        new_width = model.get_value(node, 1)
        if not check_address_align(register.address, new_width):
            ErrorMsg(
                "Address does not match register width",
                "The address %04x is not aligned to a %d bit boundary"
                % (register.address, new_width),
            )
        else:
            self._model[path][col] = model.get_value(node, 0)
            register.width = new_width
            self._set_modified()


def _build_icon_col():
    "Builds the icon column"

    renderer = Gtk.CellRendererPixbuf()
    col = Gtk.TreeViewColumn("", renderer, stock_id=RegColType.ICON)
    col.set_resizable(True)
    col.set_min_width(30)
    col.set_expand(False)
    return col


def check_address_align(address: int, width: int) -> bool:
    "Returns True if the address is aligned"

    align = width >> 3
    return address % align == 0
