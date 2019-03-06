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
from regenerate.db import GroupInstData, GroupData, LOGGER
from regenerate.ui.enums import InstCol


class InstMdl(gtk.TreeStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    def __init__(self, project):

        super(InstMdl, self).__init__(
            str, str, str, gobject.TYPE_UINT64, str,
            str, str, bool, bool, bool, bool, object
        )

        self.callback = self.__null_callback()
        self.project = project

    def __null_callback(self):
        """Does nothing, should be overridden"""
        pass

    def change_id(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstCol.ID, text)
        self.callback()

    def change_inst(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """

        # get the previous value, bail if it is the same as the new value

        i2 = self.get_iter(path)
        old_value = self.get_value(i2, InstCol.INST)
        if old_value == text:
            return

        items = []

        node = self.get_iter_root()
        while node:
            items.append(self.get_value(node, InstCol.INST))
            node = self.iter_next(node)

        if text in set(items):
            LOGGER.error(
                '"{0}" has already been used as a group name'.format(text))
            return

        node = self.get_iter(path)
        self.set_value(node, InstCol.INST, text)
        self.callback()
        obj = self.get_value(node, InstCol.OBJ)
        if obj:
            obj.name = text

        if len(path.split(":")) == 1:
            self.project.change_subsystem_name(old_value, text)
        else:
            pnode = self.get_iter(path.split(":")[0])
            parent = self.get_value(pnode, InstCol.INST)
            self.project.change_instance_name(parent, old_value, text)

    def change_hdl(self, path, text):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        node = self.get_iter(path)
        self.set_value(node, InstCol.HDL, text)
        self.callback()
        obj = self.get_value(node, InstCol.OBJ)
        if obj:
            obj.hdl = text

    def change_uvm(self, cell, path):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        self[path][InstCol.UVM] = not self[path][InstCol.UVM]
        self.callback()

    def change_decode(self, cell, path):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        self[path][InstCol.DEC] = not self[path][InstCol.DEC]
        self.callback()

    def change_single_decode(self, cell, path):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        self[path][InstCol.SINGLE_DEC] = not self[path][InstCol.SINGLE_DEC]
        self.callback()

    def change_array(self, cell, path):
        """
        Called when the ID of an instance has been edited in the InstanceList
        """
        self[path][InstCol.ARRAY] = not self[path][InstCol.ARRAY]
        self.callback()

    def change_base(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """
        node = self.get_iter(path)
        try:
            self.set_value(node, InstCol.SORT, int(text, 16))
            self.set_value(node, InstCol.BASE, text)
            self.callback()
        except ValueError:
            LOGGER.error('Illegal base address: "{0}"'.format(text))
        obj = self.get_value(node, InstCol.OBJ)
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
            self.set_value(node, InstCol.RPT, text)
            self.callback()
        except ValueError:
            LOGGER.error('Illegal repeat count: "{0}"'.format(text))
        obj = self.get_value(node, InstCol.OBJ)
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
            self.set_value(node, InstCol.OFF, "{0:x}".format(value))
            self.callback()
        except ValueError:
            LOGGER.error('Illegal repeat offset column: "{0}"'.format(text))
        obj = self.get_value(node, InstCol.OBJ)
        if obj:
            obj.repeat_offset = int(text, 16)

    def new_instance(self):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        grps = set([row[0] for row in self])

        name = "new_group"
        for i in range(len(grps)+1):
            if name not in grps:
                break
            name = "new_group%d" % i

        new_grp = GroupData(name)
        row = build_row_data(
            new_grp.name,
            "",
            new_grp.base,
            new_grp.repeat,
            new_grp.repeat_offset,
            new_grp.hdl,
            False,
            False,
            False,
            False,
            new_grp
        )

        node = self.append(None, row=row)
        self.callback()
        return (self.get_path(node), new_grp)


class InstanceList(object):
    def __init__(self, obj):
        self.__obj = obj
        self.__col = None
        self.__project = None
        self.__model = None
        self.__build_instance_table()
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
        while tree_iter is not None:
            current_group = self.__model.get_value(tree_iter, InstCol.OBJ)
            current_group.register_sets = []

            child = self.__model.iter_children(tree_iter)
            while child:
                current_group.register_sets.append(
                    GroupInstData(
                        self.col_value(child, InstCol.ID),
                        self.col_value(child, InstCol.INST),
                        self.col_value(child, InstCol.SORT),
                        int(self.col_value(child, InstCol.RPT)),
                        int(self.col_value(child, InstCol.OFF), 16),
                        self.col_value(child, InstCol.HDL),
                        self.col_value(child, InstCol.UVM),
                        self.col_value(child, InstCol.DEC),
                        self.col_value(child, InstCol.ARRAY),
                        self.col_value(child, InstCol.SINGLE_DEC)
                    )
                )
                child = self.__model.iter_next(child)
            tree_iter = self.__model.iter_next(tree_iter)

    def col_value(self, node, col):
        return self.__model.get_value(node, col)

    def new_instance(self):
        pos, grp = self.__model.new_instance()
        self.__project.get_grouping_list().append(grp)
        self.__obj.set_cursor(
            pos,
            self.__col,
            start_editing=True
        )

    def get_selected_instance(self):
        return self.__obj.get_selection().get_selected()

    def __enable_dnd(self):
        self.__obj.enable_model_drag_dest([
            ('text/plain', 0, 0)
        ], gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
        self.__obj.connect('drag-data-received',
                           self.__drag_data_received_data)

    def __drag_data_received_data(self, treeview, context, x, y, selection,
                                  info, etime):
        model = treeview.get_model()

        try:
            data = selection.data
        except AttributeError:
            data = selection.get_text()

        drop_info = treeview.get_dest_row_at_pos(x, y)
        (name, width) = data.split(":")

        row_data = build_row_data(
            name,
            name,
            0,
            1,
            int(width, 16),
            "",
            False,
            False,
            False,
            False,
            None
        )
        if drop_info:
            path, position = drop_info
            self.modified_callback()
            if len(path) == 1:
                node = self.__model.get_iter(path)
                self.__model.append(node, row_data)
            else:
                parent = self.__model.get_iter((path[0], ))
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

            node = self.__model.append(
                None,
                row=build_row_data(
                    item.name,
                    "",
                    item.base,
                    item.repeat,
                    item.repeat_offset,
                    item.hdl,
                    False,
                    False,
                    False,
                    False,
                    item
                )
            )

            item_sets = item.register_sets
            for entry in sorted(item_sets, key=lambda x: x.offset):
                self.__model.append(
                    node,
                    row=build_row_data(
                        entry.inst,
                        entry.set,
                        entry.offset,
                        entry.repeat,
                        entry.repeat_offset,
                        entry.hdl,
                        entry.no_uvm,
                        entry.no_decode,
                        entry.array,
                        entry.single_decode,
                        None
                    )
                )

    def __build_instance_table(self):

        column = EditableColumn(
            'Instance',
            self.instance_inst_changed,
            InstCol.INST
        )
        column.set_sort_column_id(InstCol.INST)
        column.set_min_width(125)
        self.__obj.append_column(column)
        self.__col = column

        column = EditableColumn(
            'Subsystem',
            self.instance_id_changed,
            InstCol.ID,
            visible_callback=self.visible_callback
        )
        column.set_sort_column_id(InstCol.ID)
        column.set_min_width(125)
        self.__obj.append_column(column)

        column = EditableColumn(
            'Address base',
            self.instance_base_changed,
            InstCol.BASE,
            True
        )
        column.set_sort_column_id(InstCol.SORT)
        self.__obj.append_column(column)

        column = EditableColumn(
            'Repeat',
            self.instance_repeat_changed,
            InstCol.RPT,
            True
        )
        self.__obj.append_column(column)

        column = EditableColumn(
            'Repeat Offset',
            self.instance_repeat_offset_changed,
            InstCol.OFF,
            True
        )
        self.__obj.append_column(column)

        column = EditableColumn(
            'HDL Path',
            self.instance_hdl_changed,
            InstCol.HDL
        )
        column.set_min_width(250)
        column.set_sort_column_id(InstCol.HDL)
        self.__obj.append_column(column)

        column = ToggleColumn(
            'UVM Exclude',
            self.instance_uvm_changed,
            InstCol.UVM,
            self.visible_callback
        )
        column.set_min_width(80)
        self.__obj.append_column(column)

        column = ToggleColumn(
            'Decode Exclude',
            self.instance_decode_changed,
            InstCol.DEC,
            self.visible_callback
        )
        column.set_min_width(80)
        self.__obj.append_column(column)

        column = ToggleColumn(
            'Force arrays',
            self.instance_array_changed,
            InstCol.ARRAY,
            self.visible_callback
        )
        column.set_min_width(80)
        self.__obj.append_column(column)

        column = ToggleColumn(
            'Single decode',
            self.instance_single_decode_changed,
            InstCol.SINGLE_DEC,
            self.visible_callback
        )
        column.set_min_width(80)
        self.__obj.append_column(column)

    def visible_callback(self, column, cell, model, *obj):
        node = obj[0]
        if len(model.get_path(node)) == 1:
            cell.set_property('visible', False)
        else:
            cell.set_property('visible', True)

    def instance_id_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        LOGGER.error("Subsystem name cannot be changed")

    def inst_changed(self, attr, path, new_text):
        getattr(self.__model, attr)(path, new_text)
        self.modified_callback()

    def inst_bool_changed(self, attr, cell, path):
        getattr(self.__model, attr)(cell, path)
        self.modified_callback()

    def instance_inst_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_inst", path, new_text)

    def instance_base_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_base", path, new_text)

    def instance_format_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        if len(path) > 1:
            self.inst_changed("change_format", path, new_text)

    def instance_hdl_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_hdl", path, new_text)

    def instance_uvm_changed(self, cell, path, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_bool_changed("change_uvm", cell, path)

    def instance_decode_changed(self, cell, path, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_decode", cell, path)

    def instance_single_decode_changed(self, cell, path, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_single_decode", cell, path)

    def instance_array_changed(self, cell, path, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_array", cell, path)

    def instance_repeat_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_repeat", path, new_text)

    def instance_repeat_offset_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_repeat_offset", path, new_text)


def build_row_data(inst, name, offset, rpt, rpt_offset, hdl, uvm, dec, array,
                   single_decode, obj):
    row = (
        inst,
        name,
        "{0:x}".format(offset),
        offset,
        "{0:d}".format(rpt),
        "{0:x}".format(rpt_offset),
        hdl,
        uvm,
        dec,
        array,
        single_decode,
        obj
    )
    return row
