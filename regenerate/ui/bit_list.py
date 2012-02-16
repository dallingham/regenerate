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
from regenerate.db import BitField, TYPES, BFT_TYPE, BFT_DESC
from columns import EditableColumn, ComboMapColumn

TYPE2STR = [(i[BFT_DESC], i[BFT_TYPE]) for i in sorted(TYPES)]

class BitModel(gtk.ListStore):

    RESET2STR = (
        ("Constant", BitField.RESET_NUMERIC),
        ("Input Port", BitField.RESET_INPUT),
        ("Parameter", BitField.RESET_PARAMETER),
        )

    (ICON_COL, BIT_COL, NAME_COL, TYPE_COL, RESET_COL,
     RESET_TYPE_COL, SORT_COL, FIELD_COL) = range(8)

    def __init__(self):
        gtk.ListStore.__init__(self, str, str, str, str, str, str, int, object)

    def append_field(self, field):
        if field.reset_type == 0:
            reset = reset_value(field)
        elif field.reset_type == 1:
            reset = field.reset_input
        else:
            reset = field.reset_parameter

        node = self.append(row=[
            None,
            bits(field),
            field.field_name,
            TYPE2STR[field.field_type][0],
            reset,
            self.RESET2STR[field.reset_type][0],
            field.start_position,
            field
            ])
        return self.get_path(node)

    def get_bitfield_at_path(self, path):
        return self[path][-1]


class BitList(object):

    BIT_COLS = (
        # Title, Size, Sort, Expand
        ('', 20, -1, False, False),
        ('Bits', 60, BitModel.SORT_COL, False, False),
        ('Name', 125, BitModel.NAME_COL, True, False),
        ('Type', 350, -1, False, True),
        ('Reset', 125, -1, False, False),
        ('Reset Type', 75, -1, False, False),
        )

    def __init__(self, obj, combo_edit, text_edit, selection_changed):
        self.__obj = obj
        self.__col = None
        self.__model = None
        self.__build_bitfield_columns(combo_edit, text_edit)
        self.__obj.get_selection().connect('changed', selection_changed)

    def set_model(self, model):
        self.__model = model
        self.__obj.set_model(model)

    def __build_bitfield_columns(self, combo_edit, text_edit):
        """
        Builds the columns for the tree view. First, removes the old columns in
        the column list. The builds new columns and inserts them into the tree.
        """
        for (i, col) in enumerate(self.BIT_COLS):
            if i == BitModel.TYPE_COL:
                column = ComboMapColumn(col[0], combo_edit,
                                        TYPE2STR, i)
            elif i == BitModel.RESET_TYPE_COL:
                column = ComboMapColumn(col[0], combo_edit,
                                        BitModel.RESET2STR, i)
            elif i == BitModel.ICON_COL:
                renderer = gtk.CellRendererPixbuf()
                column = gtk.TreeViewColumn("", renderer, stock_id=i)
            else:
                column = EditableColumn(col[0], text_edit, i)
            if i == BitModel.BIT_COL:
                self.__col = column
            if col[2] >= 0:
                column.set_sort_column_id(col[2])
            column.set_min_width(col[1])
            column.set_expand(col[3])
            self.__obj.append_column(column)

    def get_selected_row(self):
        value = self.__obj.get_selection().get_selected_rows()
        if value:
            return value[1]
        else:
            return None

    def select_row(self, path):
        if path:
            self.__obj.get_selection().select_path(path)

    def select_field(self):
        data = self.__obj.get_selection().get_selected()
        if data:
            (store, node) = data
            if node:
                return store.get_value(node, BitModel.FIELD_COL)
        return None

    def add_new_field(self, field):
        path = self.__model.append_field(field)
        self.__obj.set_cursor(path, focus_column=self.__col,
                              start_editing=True)


def bits(field):
    if field.start_position == field.stop_position:
        return "%d" % field.start_position
    else:
        return "%d:%d" % (field.stop_position, field.start_position)


def reset_value(field):
    width = (field.stop_position - field.start_position) + 1
    strval = "%x" % field.reset_value
    return strval.zfill(width / 4)
