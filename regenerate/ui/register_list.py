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
import gtk
from regenerate.ui.columns import EditableColumn, ComboMapColumn
from regenerate.ui.error_dialogs import ErrorMsg
from regenerate.db import LOGGER, Register

BAD_TOKENS = ' /-@!#$%^&*()+=|{}[]:"\';\\,.?'

REPLACE = {
    'ADDRESS': 'ADDR',
    'ALTERNATE': 'ALT',
    'ARBITER': 'ARB',
    'ARBITRATION': 'ARB',
    'CLEAR': 'CLR',
    'CLOCK': 'CLK',
    'COMMAND': 'CMD',
    'COMPARE': 'CMP',
    'CONFIG': 'CFG',
    'CONFIGURATION': 'CFG',
    'CONTROL': 'CTRL',
    'COUNT': 'CNT',
    'COUNTER': 'CNTR',
    'CURRENT': 'CUR',
    'DEBUG': 'DBG',
    'DELAY': 'DLY',
    'DESTINATION': 'DEST',
    'DIVIDER': 'DIV',
    'ENABLE': 'EN',
    'ERROR': 'ERR',
    'ERRORS': 'ERRS',
    'EXTERNAL': 'EXT',
    'FABRIC': 'FAB',
    'HARDWARE': 'HW',
    'HEADER': 'HDR',
    'INTERRUPT': 'INT',
    'LOAD': 'LD',
    'MAILBOX': 'MBX',
    'MANAGEMENT': 'MGMT',
    'MASTER': 'MSTR',
    'MAXIMUM': 'MAX',
    'MESSAGE': 'MSG',
    'MINIMUM': 'MIN',
    'NUMBER': 'NUM',
    'PACKET': 'PKT',
    'PARITY': 'PAR',
    'POINTER': 'PTR',
    'POWER': 'PWR',
    'RANGE': 'RNG',
    'READ': 'RD',
    'RECEIVE': 'RX',
    'REFERENCE': 'REF',
    'REGISTER': '',
    'REQUEST': 'REQ',
    'REQUESTER': 'REQ',
    'RESET': 'RST',
    'RESPONSE': 'RSP',
    'SELECT': 'SEL',
    'SLAVE': 'SLV',
    'SOFTWARE': 'SW',
    'SOURCE': 'SRC',
    'SPACE': 'SPC',
    'STATUS': 'STAT',
    'SYSTEM': 'SYS',
    'TRANSACTION': 'TXN',
    'TRANSLATION': 'TRANS',
    'TRANSMIT': 'TX',
    'VALUE': 'VAL',
    'VECTOR': 'VECT',
    'WRITE': 'WR',
}


class RegisterModel(gtk.ListStore):
    """
    A derivation of the ListStore that defines the columns. The columsn are:

    Address, Name, Define, Width, Address Sort Value, Register Instance

    A couple of convenience functions are provided that allow a register to
    be added, to fetch the register at a particular path, and to set the
    address.
    """

    (ICON_COL, ADDR_COL, NAME_COL, DEFINE_COL, DIM_COL, WIDTH_COL, SORT_COL,
     TOOLTIP_COL, OBJ_COL) = range(9)

    BIT2STR = (("8 bits", 8), ("16 bits", 16), ("32 bits", 32),
               ("64 bits", 64), )

    STR2BIT = {8: "8 bits", 16: "16 bits", 32: "32 bits", 64: "64 bits", }

    def __init__(self):
        gtk.ListStore.__init__(self, str, str, str, str, str, str, int, str, object)
        self.reg2path = {}

    def append_register(self, register):
        """
        Adds a new row in the ListStore for the specified register,
        filling in the data from the register into the appropriate
        column.
        """
        icon = None
        if register.ram_size:
            addr = "%04x:%x" % (register.address, register.ram_size)
        else:
            addr = "%04x" % register.address
        data = (icon, addr, register.register_name, register.token, register.dimension,
                self.STR2BIT[register.width], register.address, None, register)
        path = self.get_path(self.append(row=data))
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
                self.reg2path[reg] = (self.reg2path[reg][0] - 1, )

    def set_tooltip(self, reg, msg):
        """
        Sets the tooltip for the register.
        """
        path = self.get_path_from_register(reg)
        self[path][self.TOOLTIP_COL] = msg

    def get_register_at_path(self, path):
        """
        Given a path (row) in the ListStore, we return the corresponding
        Register.
        """
        return self[path][self.OBJ_COL]

    def set_warning_for_register(self, register, flag):
        """
        Sets the warning icon for the register in the table
        """
        path = self.reg2path[register]
        if flag:
            self[path][self.ICON_COL] = gtk.STOCK_DIALOG_WARNING
        else:
            self[path][self.ICON_COL] = None

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
            self.set(node, self.ADDR_COL, "%04x:%x" % (addr, length))
        else:
            self.set(node, self.ADDR_COL, "%04x" % addr)
        self.set(node, self.SORT_COL, addr)



ColDef = namedtuple("ColDef", ["title", "size", "sort_column", "expand", "type"])

class RegisterList(object):
    """
    Provides the interface to the register table
    """

    (COL_TEXT, COL_COMBO, COL_ICON) = range(3)

    _COLS = (  # Title,   Size, Column, Expand, Type
        ColDef('', 20, RegisterModel.ICON_COL, False, COL_ICON), 
        ColDef('Address', 100, RegisterModel.SORT_COL, False, COL_TEXT),
        ColDef('Name', 175, RegisterModel.NAME_COL, True, COL_TEXT),
        ColDef('Token', 150, RegisterModel.DEFINE_COL, True, COL_TEXT),
        ColDef('Dimension', 75, RegisterModel.DIM_COL, True, COL_TEXT),
        ColDef('Width', 75, -1, False, COL_COMBO), 
        )

    def __init__(self, obj, select_change_function, mod_function, update_addr):
        self.__obj = obj
        self.__model = None
        self.__col = None
        self.__icon_col = None
        self.__icon_renderer = None
        self.__selection = self.__obj.get_selection()
        self.__set_modified = mod_function
        self.__update_addr = update_addr
        self.__selection.connect('changed', select_change_function)
        self.__build_columns()

    def get_selected_row(self):
        """
        Returns the selected row
        """
        return self.__selection.get_selected_rows()[1]

    def get_selected_node(self):
        """
        Returns the node of the selected row
        """
        return self.__selection.get_selected()[1]

    def delete_selected_node(self):
        """
        Deletes the selected from from the table
        """
        reg = self.get_selected_register()
        self.__model.delete_register(reg)

    def select_row(self, row):
        """
        Select the given row
        """
        self.__selection.select_path(row)

    def __build_columns(self):
        """
        Builds the columns for the tree view. First, removes the old columns in
        the column list. The builds new columns and inserts them into the tree.
        """
        for (i, col) in enumerate(self._COLS):
            if col.type == self.COL_COMBO:
                column = ComboMapColumn(col.title, self.__combo_edited,
                                        RegisterModel.BIT2STR, i)
            elif col.type == self.COL_TEXT:
                column = EditableColumn(col.title, self.__text_edited, i)
            else:
                self.__icon_renderer = gtk.CellRendererPixbuf()
                column = gtk.TreeViewColumn("", self.__icon_renderer,
                                            stock_id=i)
                self.__icon_col = column

            column.set_min_width(col.size)
            column.set_expand(col.expand)
            if i == 1:
                self.__col = column
            if col.sort_column >= 0:
                column.set_sort_column_id(col.sort_column)
            self.__obj.append_column(column)
        self.__obj.set_search_column(3)
        self.__obj.set_tooltip_column(RegisterModel.TOOLTIP_COL)

    def set_model(self, model):
        """
        Sets the active model.
        """
        self.__obj.set_model(model)
        if model:
            self.__model = model.get_model().get_model()
        else:
            self.__model = None

    def add_new_register(self, register):
        """
        Addes a new register to the model and set it to edit the
        default column
        """
        path = self.__model.append_register(register)
        self.__obj.set_cursor(path,
                              focus_column=self.__col,
                              start_editing=True)
        return path

    def get_selected_register(self):
        """
        Returns the register associated with the selected row
        """
        data = self.__selection.get_selected()
        if data:
            (store, node) = data
            if node:
                return store.get_value(node, RegisterModel.OBJ_COL)
        return None

    def __ram_update_addr(self, reg, path, text):
        """
        Updates the address associated with a RAM address
        """
        (addr_str, len_str) = text.split(':')
        try:
            new_addr = int(addr_str, 16)
            new_length = int(len_str, 16)
            if new_addr != reg.address or new_length != reg.ram_size:
                self.__update_addr(reg, new_addr, new_length)
                self.__model.set_address_at_path(path, new_addr, new_length)
                self.__set_modified()
        except KeyError:
            ErrorMsg("Internal Error",
                     "Deleting the register caused an internal "
                     "inconsistency.\nPlease exit without saving "
                     "to prevent any corruption to\n"
                     "your database and report this error.")

    def __reg_update_addr(self, reg, path, text):
        """
        Updates the address associated with a register address
        """
        print "REG UPDATE ADDR"
        try:
            new_addr = int(text, 16)
            new_length = 0
            if new_addr != reg.address or new_length != reg.ram_size:
                self.__update_addr(reg, new_addr, new_length)
                self.__model.set_address_at_path(path, new_addr, new_length)
                self.__set_modified()
        except KeyError:
            ErrorMsg("Internal Error",
                     "Deleting the register caused an internal "
                     "inconsistency.\nPlease exit without saving to "
                     "prevent any corruption to\n"
                     "your database and report this error.")

    def __reg_update_name(self, reg, path, text):
        """
        Updates the name associated with the register. Called after the text
        has been edited
        """
        if text != reg.register_name:
            reg.register_name = text
            self.__set_modified()
        self.__model[path][RegisterModel.NAME_COL] = reg.register_name
        if reg.token == "":
            value = build_define(reg.register_name)
            self.__model[path][RegisterModel.DEFINE_COL] = value
            reg.token = value
            self.__set_modified()

    def __reg_update_dim(self, reg, path, text):
        """
        Updates the name associated with the register. Called after the text
        has been edited
        """
        try:
            value = int(text)
        except ValueError:
            return

        if value != reg.dimension:
            reg.dimension = value
            self.__set_modified()
        self.__model[path][RegisterModel.DIM_COL] = "%d" % value

    def __reg_update_define(self, reg, path, text):
        """
        Updates the token name associated with the register. Called after the
        text has been edited
        """
        for i in BAD_TOKENS:
            text = text.replace(i, '_')
        text = text.upper()
        if text != reg.token:
            reg.token = text
            self.__set_modified()
        self.__model[path][RegisterModel.DEFINE_COL] = reg.token

    def __new_address_is_not_used(self, new_text, path):
        """
        Verifies that the new address has not been previously used, or
        does not overlap with an existing address.
        """
        addr_list = set()
        ro_list = set()
        wo_list = set()

        for (index, data) in enumerate(self.__model):
            if index == int(path):
                continue
            reg = data[-1]
            for i in range(reg.address, reg.address + (reg.dimension * (reg.width / 8))):
                if reg.share == Register.SHARE_READ:
                    ro_list.add(i)
                elif reg.share == Register.SHARE_WRITE:
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

    def __handle_edited_address(self, register, path, new_text):
        """
        Called when an address in the table has changed
        """
        try:
            if ":" in new_text:
                self.__handle_ram_address(register, path, new_text)
            else:
                self.__handle_reg_address(register, path, new_text)
        except ValueError:
            LOGGER.warning('Address %0x was not changed: invalid value "%s"' %
                           (register.address, new_text))

    def __handle_ram_address(self, register, path, new_text):
        """
        Called when the RAM address in the table has changed
        """
        if self.__new_address_is_not_used(new_text, path):
            self.__ram_update_addr(register, path, new_text)
        else:
            ErrorMsg("Address already used",
                     "The address %0x is already used by another register" %
                     int(new_text, 16))

    def __check_address_align(self, address, width):
        align = width / 8
        return address % align == 0

    def __handle_reg_address(self, register, path, new_text):
        """
        Called when the register address in the table has changed
        """
        address = int(new_text, 16)
        if not self.__check_address_align(address, register.width):
            ErrorMsg("Address does not match register width",
                     "The address %04x is not aligned to a %d bit boundary" %
                     (address, register.width))
        elif not self.__new_address_is_not_used(new_text, path):
            ErrorMsg(
                "Address already used",
                "The address %0x is already used by another register" % address)
        else:
            self.__reg_update_addr(register, path, new_text)

    def __text_edited(self, cell, path, new_text, col):
        """
        Called when text has been edited. Selects the correct function
        depending on the edited column
        """
        register = self.__model.get_register_at_path(path)
        new_text = new_text.strip()
        if col == RegisterModel.ADDR_COL:
            self.__handle_edited_address(register, path, new_text)
        elif col == RegisterModel.NAME_COL:
            self.__reg_update_name(register, path, new_text)
        elif col == RegisterModel.DIM_COL:
            self.__reg_update_dim(register, path, new_text)
        elif col == RegisterModel.DEFINE_COL:
            self.__reg_update_define(register, path, new_text)

    def __combo_edited(self, cell, path, node, col):
        """
        Called when the combo box in the table has been altered
        """
        model = cell.get_property('model')
        register = self.__model.get_register_at_path(path)

        new_width = model.get_value(node, 1)
        if not self.__check_address_align(register.address, new_width):
            ErrorMsg("Address does not match register width",
                     "The address %04x is not aligned to a %d bit boundary" %
                     (register.address, new_width))
        else:
            self.__model[path][col] = model.get_value(node, 0)
            register.width = new_width
            self.__set_modified()


def build_define(text):
    """
    Converts a register name into a define token
    """
    for i in BAD_TOKENS:
        text = text.replace(i, '_')
    return "_".join([REPLACE.get(i.upper(), i.upper()) for i in text.split('_')
                     if REPLACE.get(i.upper(), i.upper()) != ""])
