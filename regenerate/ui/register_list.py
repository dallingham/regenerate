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

import gtk
from columns import EditableColumn, ComboMapColumn

REPLACE = {
    'ENABLE'    : 'EN',    'TRANSLATION'   : 'TRANS',
    'ADDRESS'   : 'ADDR',  'CONFIGURATION' : 'CFG',
    'CONFIG'    : 'CFG',   'SYSTEM'        : 'SYS',
    'CONTROL'   : 'CTRL',  'STATUS'        : 'STAT',
    'DEBUG'     : 'DBG',   'COMMAND'       : 'CMD',
    'HEADER'    : 'HDR',   'PACKET'        : 'PKT',
    'ERROR'     : 'ERR',   'INTERRUPT'     : 'INT',
    'WRITE'     : 'WR',    'READ'          : 'RD',
    'TRANSMIT'  : 'TX',    'RECEIVE'       : 'RX',
    'SOFTWARE'  : 'SW',    'HARDWARE'      : 'HW',
    'SOURCE'    : 'SRC',   'DESTINATION'   : 'DEST',
    'REGISTER'  : '',      'LOAD'          : 'LD',
    'CLEAR'     : 'CLR',   'CURRENT'       : 'CUR',
    'RANGE'     : 'RNG',   'DELAY'         : 'DLY',
    'ERROR'     : 'ERR',   'LOAD'          : 'LD',
    'PARITY'    : 'PAR',   'COMPARE'       : 'CMP',
    'POINTER'   : 'PTR',   'SELECT'        : 'SEL',
    'COUNT'     : 'CNT',   'COUNTER'       : 'CNTR',
    'VALUE'     : 'VAL',   'MESSAGE'       : 'MSG',
    'ERRORS'    : 'ERRS',  'POWER'         : 'PWR',
    'MAILBOX'   : 'MBX',   'VECTOR'        : 'VECT',
    'RESPONSE'  : 'RSP',   'NUMBER'        : 'NUM',
    'CLOCK'     : 'CLK',   'EXTERNAL'      : 'EXT',
    'FABRIC'    : 'FAB',   'SPACE'         : 'SPC',
    'MAXIMUM'   : 'MAX',   'MINIMUM'       : 'MIN', 
    'RESET'     : 'RST',   'MANAGEMENT'    : 'MGMT',
    'REQUESTER' : 'REQ',   'REQUEST'       : 'REQ',
    'ALTERNATE' : 'ALT',   'DIVIDER'       : 'DIV',
    'REFERENCE' : 'REF',   'ARBITRATION'   : 'ARB',
    'ARBITER'   : 'ARB',   'TRANSACTION'   : 'TXN',
    'MASTER'    : 'MSTR',  'SLAVE'         : 'SLV',
    }


Class registermodel(gtk.ListStore):
    """
    A derivation of the ListStore that defines the columns. The columsn are:

    Address, Name, Define, Width, Address Sort Value, Register Instance

    A couple of convenience functions are provided that allow a register to
    be added, to fetch the register at a particular path, and to set the
    address.
    """

    (ICON_COL, ADDR_COL, NAME_COL, DEFINE_COL, WIDTH_COL, SORT_COL,
     TOOLTIP_COL, OBJ_COL) = range(8)

    BIT2STR = (
        ("8 bits", 8),
        ("16 bits", 16),
        ("32 bits", 32),
        ("64 bits", 64),
        )

    STR2BIT = {
        8: "8 bits",
        16: "16 bits",
        32: "32 bits",
        64: "64 bits",
        }

    def __init__(self):
        gtk.ListStore.__init__(self, str, str, str, str, str, int, str, object)
        self.reg2path = {}

    def append_register(self, register):
        """
        Adds a new row in the ListStore for the specified register,
        filling in the data from the register into the appropriate
        column.
        """
        icon = None
        data = [icon, "%04x" % register.address, register.register_name,
                register.token, self.STR2BIT[register.width],
                register.address, None, register]
        path = self.get_path(self.append(row=data))
        self.reg2path[register] = path
        return path

    def delete_register(self, register):
        """
        Adds a new row in the ListStore for the specified register,
        filling in the data from the register into the appropriate
        column.
        """
        del self[self.reg2path[register]]

    def set_tooltip(self, reg, msg):
        path = self.get_path_from_register(reg)
        self[path][self.TOOLTIP_COL] = msg

    def get_register_at_path(self, path):
        """
        Given a path (row) in the ListStore, we return the corresponding
        Register.
        """
        return self[path][self.OBJ_COL]

    def set_warning_for_register(self, register, flag):
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

    def set_address_at_path(self, path, addr):
        """
        Sets the address for a register, but also sets the corresponding
        value for the sort columns.
        """
        node = self.get_iter(path)
        self.set(node, self.ADDR_COL, "%04x" % addr)
        self.set(node, self.SORT_COL, addr)


class RegisterList(object):

    (COL_TEXT, COL_COMBO, COL_ICON) = range(3)

    _COLS = (
        # Title,   Size, Column,                   Expand
        ('',         20, RegisterModel.ICON_COL,   False,  COL_ICON),
        ('Address',  75, RegisterModel.SORT_COL,   False,  COL_TEXT),
        ('Name',    175, RegisterModel.NAME_COL,   True,   COL_TEXT),
        ('Token',   175, RegisterModel.DEFINE_COL, True,   COL_TEXT),
        ('Width',    75, -1,                       False,  COL_COMBO),
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
        return self.__selection.get_selected_rows()[1]

    def get_selected_node(self):
        return self.__selection.get_selected()[1]

    def delete_selected_node(self):
        reg = self.get_selected_register()
        self.__model.delete_register(reg)

    def select_row(self, row):
        self.__selection.select_path(row)

    def __build_columns(self):
        """
        Builds the columns for the tree view. First, removes the old columns in
        the column list. The builds new columns and inserts them into the tree.
        """
        for (i, col) in enumerate(self._COLS):
            if col[4] == self.COL_COMBO:
                column = ComboMapColumn(col[0], self.__combo_edited,
                                        RegisterModel.BIT2STR, i)
            elif col[4] == self.COL_TEXT:
                column = EditableColumn(col[0], self.__text_edited, i)
            else:
                self.__icon_renderer = gtk.CellRendererPixbuf()
                column = gtk.TreeViewColumn("", self.__icon_renderer,
                                            stock_id=i)
                self.__icon_col = column
            column.set_min_width(col[1])
            column.set_expand(col[3])
            if i == 1:
                self.__col = column
            if col[2] >= 0:
                column.set_sort_column_id(col[2])
            self.__obj.append_column(column)
        self.__obj.set_search_column(3)
        self.__obj.set_tooltip_column(RegisterModel.TOOLTIP_COL)

    def set_model(self, model):
        self.__obj.set_model(model)
        if model:
            self.__model = model.get_model().get_model()
        else:
            self.__model = None

    def add_new_register(self, register):
        path = self.__model.append_register(register)
        self.__obj.set_cursor(path, focus_column=self.__col,
                              start_editing=True)
        return path

    def get_selected_register(self):
        data = self.__selection.get_selected()
        if data:
            (store, node) = data
            if node:
                return store.get_value(node, RegisterModel.OBJ_COL)
        return None

    def __reg_update_addr(self, reg, path, text):
        try:
            new_addr = int(text, 16)
            if new_addr != reg.address:
                self.__update_addr(reg, new_addr)
                self.__model.set_address_at_path(path, new_addr)
                self.__set_modified()
        except ValueError:
            return

    def __reg_update_name(self, reg, path, text):
        if text != reg.register_name:
            reg.register_name = text
            self.__set_modified()
        self.__model[path][RegisterModel.NAME_COL] = reg.register_name
        if reg.token == "":
            value = build_define(reg.register_name)
            self.__model[path][RegisterModel.DEFINE_COL] = value
            reg.token = value
            self.__set_modified()

    def __reg_update_define(self, reg, path, text):
        text = text.upper().replace(' ', '_')
        text = text.replace('/', '_')
        text = text.replace('-', '_')
        if text != reg.token:
            reg.token = text
            self.__set_modified()
        self.__model[path][RegisterModel.DEFINE_COL] = reg.token

    def __text_edited(self, cell, path, new_text, col):
        register = self.__model.get_register_at_path(path)
        new_text = new_text.strip()
        if col == RegisterModel.ADDR_COL:
            self.__reg_update_addr(register, path, new_text)
        elif col == RegisterModel.NAME_COL:
            self.__reg_update_name(register, path, new_text)
        elif col == RegisterModel.DEFINE_COL:
            self.__reg_update_define(register, path, new_text)

    def __combo_edited(self, cell, path, node, col):
        model = cell.get_property('model')
        register = self.__model.get_register_at_path(path)
        self.__model[path][col] = model.get_value(node, 0)
        register.width = model.get_value(node, 1)
        self.__set_modified()


def build_define(text):
    text = text.replace('/', ' ')
    text = text.replace('-', ' ')
    return "_".join([REPLACE.get(i.upper(), i.upper())
                     for i in text.split()
                     if REPLACE.get(i.upper(), i.upper()) != ""])
