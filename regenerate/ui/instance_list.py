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
from regenerate.ui.columns import EditableColumn, ToggleColumn
from regenerate.db import GroupMapData, GroupData, LOGGER


class InstMdl(gtk.TreeStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    (INST_COL, ID_COL, BASE_COL, SORT_COL, RPT_COL, OFF_COL,
     FMT_COL, HDL_COL, UVM_COL, OBJ_COL) = range(10)

    def __init__(self):
        gtk.TreeStore.__init__(self, str, str, str, gobject.TYPE_UINT64, str,
                               str, str, str, bool, object)
        self.callback = self.__null_callback()


    def __null_callback(self):
        """Does nothing, should be overridden"""
        pass

    def change_id(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstMdl.ID_COL, text)
        self.callback()

    def change_inst(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """

        items = []
        node = self.get_iter_root()
        while node:
            items.append(self.get_value(node, InstMdl.INST_COL))
            node = self.iter_next(node)

        if text in set(items):
            LOGGER.error('"{0}" has already been used as a group name'.format(text))
        else:
            node = self.get_iter(path)
            self.set_value(node, InstMdl.INST_COL, text)
            self.callback()
            obj = self.get_value(node, InstMdl.OBJ_COL)
            if obj:
                obj.name = text

    def change_format(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstMdl.FMT_COL, text)
        self.callback()

    def change_hdl(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstMdl.HDL_COL, text)
        self.callback()
        obj = self.get_value(node, InstMdl.OBJ_COL)
        if obj:
            obj.hdl = text

    def change_uvm(self, cell, path):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        self[path][InstMdl.UVM_COL] = not self[path][InstMdl.UVM_COL]
        self.callback()

    def change_base(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            self.set_value(node, InstMdl.SORT_COL, int(text, 16))
            self.set_value(node, InstMdl.BASE_COL, text)
            self.callback()
        except ValueError:
            LOGGER.error('Illegal base address: "{0}"'.format(text))
        obj = self.get_value(node, InstMdl.OBJ_COL)
        if obj:
            obj.base = int(text, 16)

    def change_repeat(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            int(text)
            self.set_value(node, InstMdl.RPT_COL, text)
            self.callback()
        except ValueError:
            LOGGER.error('Illegal repeat count: "{0}"'.format(text))
        obj = self.get_value(node, InstMdl.OBJ_COL)
        if obj:
            obj.repeat = int(text)

    def change_repeat_offset(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            value = int(text, 16)
            self.set_value(node, InstMdl.OFF_COL, "{0:x}".format(value))
            self.callback()
        except ValueError:
            LOGGER.error('Illegal repeat offset column: "{0}"'.format(text))
        obj = self.get_value(node, InstMdl.OBJ_COL)
        if obj:
            obj.repeat_offset = int(text, 16)

    def new_instance(self):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        new_grp = GroupData("new_group")
        row = build_row_data(new_grp.name, new_grp.name, new_grp.base, 
                             new_grp.repeat, new_grp.repeat_offset, "", 
                             new_grp.hdl, False, new_grp)

        node = self.append(None, row=row)
        self.callback()
        return (self.get_path(node), new_grp)


class InstanceList(object):

    def __init__(self, obj, id_changed, inst_changed, base_changed,
                 repeat_changed, repeat_offset_changed, format_changed,
                 hdl_changed, uvm_changed):
        self.__obj = obj
        self.__col = None
        self.__project = None
        self.__model = None
        self.__build_instance_table(id_changed, inst_changed, base_changed,
                                    repeat_changed, repeat_offset_changed,
                                    format_changed, hdl_changed, uvm_changed)
        self.__enable_dnd()
        self.__obj.set_sensitive(False)

    def modified_callback(self):
        if self.__project:
            self.__project.modified = True

    def set_project(self, project):
        self.__project = project
        self.__obj.set_sensitive(True)
        self.__populate()

    def set_model(self, model):
        self.__obj.set_model(model)
        self.__model = model
        self.__model.callback = self.modified_callback

    def get_groups(self):
        tree_iter = self.__model.get_iter_first()
        groups = []
        while tree_iter is not None:
            base = self.__model.get_value(tree_iter, InstMdl.SORT_COL)
            hdl = self.__model.get_value(tree_iter, InstMdl.HDL_COL)

            current_group = self.__model.get_value(tree_iter, InstMdl.OBJ_COL)
            current_group.register_sets = []

            child = self.__model.iter_children(tree_iter)
            while child:
                inst = self.__model.get_value(child, InstMdl.INST_COL)
                name = self.__model.get_value(child, InstMdl.ID_COL)
                base = self.__model.get_value(child, InstMdl.SORT_COL)
                rpt = int(self.__model.get_value(child, InstMdl.RPT_COL))
                offset_str = self.__model.get_value(child, InstMdl.OFF_COL)
                offset = int(offset_str, 16)
                fmt = self.__model.get_value(child, InstMdl.FMT_COL)
                hdl = self.__model.get_value(child, InstMdl.HDL_COL)
                uvm = self.__model.get_value(child, InstMdl.UVM_COL)
                current_group.register_sets.append(
                    GroupMapData(name, inst, base, rpt, offset, fmt, hdl, uvm))
                child = self.__model.iter_next(child)
            tree_iter = self.__model.iter_next(tree_iter)
        return groups

    def new_instance(self):
        pos, grp = self.__model.new_instance()
        self.__project.get_grouping_list().append(grp)
        self.__obj.set_cursor(pos, focus_column=self.__col, start_editing=True)

    def get_selected_instance(self):
        return self.__obj.get_selection().get_selected()

    def __enable_dnd(self):
        self.__obj.enable_model_drag_dest([('text/plain', 0, 0)],
                                          gtk.gdk.ACTION_DEFAULT |
                                          gtk.gdk.ACTION_MOVE)
        self.__obj.connect('drag-data-received',
                           self.__drag_data_received_data)

        self.__obj.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK, [('text/plain', 0, 0)],
            gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
        self.__obj.connect('drag-data-get', self.__drag_data_get)

    def __drag_data_get(self, treeview, context, selection, target_id, etime):
        tselection = treeview.get_selection()
        model, tree_iter = tselection.get_selected()
        data = model.get_value(tree_iter, 0)
        selection.set(selection.target, 8, data)

    def __drag_data_received_data(self, treeview, context, x, y, selection,
                                  info, etime):
        model = treeview.get_model()
        data = selection.data
        drop_info = treeview.get_dest_row_at_pos(x, y)
        (name, width) = data.split(":")
        row_data = build_row_data(name, name, 0, 1, int(width), "", "", False, None)
        if drop_info:
            path, position = drop_info
            self.modified_callback()
            if len(path) == 1:
                node = self.__model.get_iter(path)
                self.__model.append(node, row_data)
            else:
                parent = self.__model.get_iter((path[0],))
                node = self.__model.get_iter(path)
                if position in (gtk.TREE_VIEW_DROP_BEFORE,
                                gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                    self.__model.insert_before(parent, node, row_data)
                else:
                    model.insert_after(parent, node, row_data)

    def __populate(self):
        if self.__project is None:
            return
        group_list = sorted(self.__project.get_grouping_list(),
                            key=lambda x: x.base)
        for item in group_list:

            row = build_row_data(item.name, "", item.base, item.repeat,
                                 item.repeat_offset, "", item.hdl, 0, item)
            node = self.__model.append(None, row=row)

            entry_list = sorted(item.register_sets, key=lambda x: x.offset)
            for entry in entry_list:
                row = build_row_data(entry.inst, entry.set, entry.offset,
                                     entry.repeat, entry.repeat_offset, 
                                     entry.format, entry.hdl, entry.no_uvm,
                                     None)
                self.__model.append(node, row=row)

    def __build_instance_table(self, id_changed, inst_changed, base_changed,
                               repeat_changed, repeat_offset_changed,
                               format_changed, hdl_changed, uvm_changed):

        column = EditableColumn('Instance', inst_changed,
                                InstMdl.INST_COL)
        column.set_sort_column_id(InstMdl.INST_COL)
        column.set_min_width(125)
        self.__obj.append_column(column)
        self.__col = column

        column = EditableColumn('Subsystem', id_changed, InstMdl.ID_COL)
        column.set_sort_column_id(InstMdl.ID_COL)
        column.set_min_width(125)
        self.__obj.append_column(column)

        column = EditableColumn('Address base', base_changed,
                                InstMdl.BASE_COL, True)
        column.set_sort_column_id(InstMdl.SORT_COL)
        self.__obj.append_column(column)

        column = EditableColumn('Repeat', repeat_changed,
                                InstMdl.RPT_COL, True)
        self.__obj.append_column(column)

        column = EditableColumn('Repeat Offset', repeat_offset_changed,
                                InstMdl.OFF_COL, True)
        self.__obj.append_column(column)

        column = EditableColumn('ID Format', format_changed, InstMdl.FMT_COL)
        column.set_min_width(175)
        column.set_sort_column_id(InstMdl.FMT_COL)
        self.__obj.append_column(column)

        column = EditableColumn('HDL Path', hdl_changed, InstMdl.HDL_COL)
        column.set_min_width(250)
        column.set_sort_column_id(InstMdl.HDL_COL)
        self.__obj.append_column(column)
        self.__col = column

        column = ToggleColumn('UVM Exclude', uvm_changed, InstMdl.UVM_COL)
        column.set_min_width(100)
        self.__obj.append_column(column)


def build_row_data(inst, name, offset, rpt, rpt_offset, fmt, hdl, uvm, obj):
    row = (inst, name, "{0:x}".format(offset), offset, "{0:d}".format(rpt), 
           "{0:x}".format(rpt_offset), fmt, hdl, uvm, obj)
    return row
