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
from regenerate.db import GroupMapData

class InstanceModel(gtk.TreeStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    (ID_COL, BASE_COL, SORT_COL, REPEAT_COL, REPEAT_OFF_COL) = range(5)

    def __init__(self):
        gtk.TreeStore.__init__(self, str, str, gobject.TYPE_UINT64, str, str)

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

    def change_repeat(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            a = int(text)
            self.set_value(node, InstanceModel.REPEAT_COL, text)
        except ValueError:
            return

    def change_repeat_offset(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            a = int(text, 16)
            self.set_value(node, InstanceModel.REPEAT_OFF_COL, "%x" % int(text,16))
        except ValueError:
            return

    def new_instance(self):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        node = self.append(None, row=('', '0', 0, "", ""))
        return self.get_path(node)

    def append_instance(self, inst):
        """
        Adds the specified instance to the InstanceList
        """
        self.append(row=(inst[0], "%08x" % inst[1], inst[1], "1", "0"))

    def get_values(self):
        """
        Returns the list of instance tuples from the model.
        """
        return [(val[0], int(val[1], 16)) for val in self if val[0]]


class InstanceList(object):

    def __init__(self, obj, id_changed, base_changed, repeat_changed, repeat_offset_changed):
        self.__obj = obj
        self.__col = None
        self.__project = None
        self.__model = None
        self.__build_instance_table(id_changed, base_changed, repeat_changed,
                                    repeat_offset_changed)
        self.__enable_dnd()
        self.__obj.set_sensitive(False)

    def __enable_dnd(self):
        self.__obj.enable_model_drag_dest([('text/plain', 0, 0)], gtk.gdk.ACTION_DEFAULT|
                                          gtk.gdk.ACTION_MOVE)
        self.__obj.connect('drag-data-received', self.__drag_data_received_data)

    def __drag_data_received_data(self, treeview, context, x, y, selection,
                                  info, etime):
        model = treeview.get_model()
        data = selection.data
        drop_info = treeview.get_dest_row_at_pos(x, y)
        row_data = [data, "0", 0, "1", "0"]
        if drop_info:
            path, position = drop_info
            if len(path) == 1:
                iter = self.__model.get_iter(path)
                self.__model.append(iter, row_data)
            else:
                parent = self.__model.get_iter((path[0],))
                iter = self.__model.get_iter(path)
                if (position == gtk.TREE_VIEW_DROP_BEFORE
                    or position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                    self.__model.insert_before(parent, iter, row_data)
                else:
                    model.insert_after(parent, iter, row_data)

    def set_project(self, project):
        self.__project = project
        self.__obj.set_sensitive(True)
        self.__populate()

    def __populate(self):
        if self.__project == None:
            return
        for item in self.__project.get_grouping_list():
            node = self.__model.append(None, row=(item[0], "%x" % item[1], item[1], "", ""))
            for entry in self.__project.get_group_map(item[0]):
                self.__model.append(node, (entry[0], "%x" % entry[1], entry[1],
                                    "%d" % entry[2], "%x" % entry[3]))


    def __build_instance_table(self, id_changed, base_changed, repeat_changed,
                               repeat_offset_changed):
        column = EditableColumn('Group/Instance', id_changed, InstanceModel.ID_COL)
        column.set_min_width(250)
        column.set_sort_column_id(InstanceModel.ID_COL)
        self.__obj.append_column(column)
        self.__col = column

        column = EditableColumn('Address base (hex)', base_changed,
                                InstanceModel.BASE_COL)
        column.set_sort_column_id(InstanceModel.SORT_COL)
        self.__obj.append_column(column)

        column = EditableColumn('Repeat', repeat_changed, InstanceModel.REPEAT_COL)
        self.__obj.append_column(column)

        column = EditableColumn('Repeat Offset (hex)', repeat_offset_changed,
                                InstanceModel.REPEAT_OFF_COL)
        self.__obj.append_column(column)

    def set_model(self, model):
        self.__obj.set_model(model)
        self.__model = model

    def get_groups(self):
        tree_iter = self.__model.get_iter_first()
        groups = []
        group_map = {}
        while tree_iter != None:
            data = self.__model.get(tree_iter, 0, 2)
            groups.append(data)
            group_map[data[0]] = []

            child = self.__model.iter_children(tree_iter)
            
            while child:
                group_map[data[0]].append(
                    GroupMapData(self.__model.get_value(child, 0),
                                 self.__model.get_value(child, 2),
                                 int(self.__model.get_value(child, 3)),
                                 int(self.__model.get_value(child, 4), 16)
                                 ))
                child = self.__model.iter_next(child)
            tree_iter = self.__model.iter_next(tree_iter)
        return (groups, group_map)

    def new_instance(self):
        self.__obj.set_cursor(self.__model.new_instance(),
                              focus_column=self.__col, start_editing=True)

    def get_selected_instance(self):
        return self.__obj.get_selection().get_selected()
