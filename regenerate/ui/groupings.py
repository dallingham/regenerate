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
import gobject
from regenerate.settings.paths import GLADE_GRP
from columns import EditableColumn


class Groupings(object):

    def __init__(self, project):
        self.__project = project
        self.__builder = gtk.Builder()
        self.__builder.add_from_file(GLADE_GRP)
        self.__builder.connect_signals(self)

        self.__list = self.__builder.get_object('list')
        self.__top = self.__builder.get_object('groupings')
        self.__model = gtk.ListStore(str, str, str, gobject.TYPE_UINT64,
                                     gobject.TYPE_UINT64)
        self.__list.set_model(self.__model)
        self.__build()
        self.__populate()
        self.__top.show()

    def __build(self):
        self.__column = EditableColumn("Group Name", self.__column_edited, 0)
        self.__column.set_min_width(150)
        self.__column.set_sort_column_id(0)
        self.__list.append_column(self.__column)

        column = EditableColumn("Starting Address",
                                self.__column_edited, 1)
        column.set_min_width(150)
        column.set_sort_column_id(3)
        self.__list.append_column(column)

        column = EditableColumn("Starting Address",
                                self.__column_edited, 2)
        column.set_min_width(150)
        column.set_sort_column_id(4)
        self.__list.append_column(column)

    def __populate(self):
        for item in self.__project.get_grouping_list():
            self.__model.append(row=[item[0], "%x" % item[1], "%x" % item[2],
                                     item[1], item[2]])

    def __column_edited(self, cell, path, text, col):
        if col == 0:
            self.__model[path][col] = text
            path = int(path)
            data = self.__project.get_grouping_list()[path]
            self.__project.set_grouping(path, text, data[1], data[2])
        elif col == 1:
            try:
                self.__model[path][col] = "%x" % int(text, 16)
                self.__model[path][3] = int(text, 16)
                path = int(path)
                data = self.__project.get_grouping_list()[path]
                self.__project.set_grouping(path, data[0], int(text, 16), data[2])
            except ValueError:
                return
        else:
            self.__model[path][col] = "%x" % int(text, 16)
            self.__model[path][4] = int(text, 16)
            path = int(path)
            data = self.__project.get_grouping_list()[path]
            self.__project.set_grouping(path, data[0], data[1], int(text, 16))

    def on_close_clicked(self, obj):
        self.__top.destroy()

    def on_add_clicked(self, obj):
        node = self.__model.append(("", "0", "0", 0, 0))
        path = self.__model.get_path(node)
        self.__project.add_to_grouping_list("", "0", "0")
        self.__list.set_cursor(path, focus_column=self.__column,
                               start_editing=True)

    def on_remove_clicked(self, obj):
        pass
