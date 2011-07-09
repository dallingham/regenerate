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
from columns import EditableColumn


class InstanceModel(gtk.ListStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    (ID_COL, BASE_COL, SORT_COL) = range(3)

    def __init__(self):
        gtk.ListStore.__init__(self, str, str, gobject.TYPE_UINT64)

    def change_id(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstanceModel.ID_COL, text)

    def change_base(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            self.set_value(node, InstanceModel.SORT_COL, int(text, 16))
            self.set_value(node, InstanceModel.BASE_COL, text)
        except ValueError:
            return

    def new_instance(self):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        node = self.append(row=('', '0', 0))
        return self.get_path(node)

    def append_instance(self, inst):
        """
        Adds the specified instance to the InstanceList
        """
        self.append(row=(inst[0], "%08x" % inst[1], inst[1]))

    def get_values(self):
        """
        Returns the list of instance tuples from the model.
        """
        return [(val[0], int(val[1], 16)) for val in self if val[0]]


class InstanceList(object):

    def __init__(self, obj, id_changed, base_changed):
        self.__obj = obj
        self.__col = None
        self.__model = None
        self.__build_instance_table(id_changed, base_changed)

    def __build_instance_table(self, id_changed, base_changed):
        column = EditableColumn('Instance ID', id_changed, 0)
        column.set_min_width(250)
        column.set_sort_column_id(0)
        self.__obj.append_column(column)
        self.__col = column

        column = EditableColumn('Address base (hex)', base_changed, 1)
        column.set_sort_column_id(2)
        self.__obj.append_column(column)

    def set_model(self, model):
        self.__obj.set_model(model)
        self.__model = model

    def new_instance(self):
        self.__obj.set_cursor(self.__model.new_instance(),
                              focus_column=self.__col, start_editing=True)

    def get_selected_instance(self):
        return self.__obj.get_selection().get_selected()
