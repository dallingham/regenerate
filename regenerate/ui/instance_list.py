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

import re
from gi.repository import Gtk, Gdk, GObject
from regenerate.ui.columns import EditableColumn
from regenerate.db import GroupInstData, GroupData, LOGGER
from regenerate.ui.enums import InstCol


class InstMdl(Gtk.TreeStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    def __init__(self, project):

        super().__init__(
            str, str, str, GObject.TYPE_UINT64, str, str, str, object
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

        items = set([])
        for row in self:
            items.add(row[InstCol.INST])

        if text in items:
            LOGGER.warning(
                '"%s" has already been used as a subsystem name', text
            )
            return

        if re.match(r"^[A-Za-z_][A-Za-z0-9_]\[.*\]+$", text):
            LOGGER.warning(
                "Array notation not valid. Use the repeat/repeat count to create arrays"
            )
            return

        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]+$", text):
            LOGGER.warning("%s is not a valid subsystem name", text)
            return

        node = self.get_iter(path)
        self.set_value(node, InstCol.INST, text)
        self.callback()

        if len(path.split(":")) == 1:
            obj = self.get_value(node, InstCol.OBJ)
            obj.name = text
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

    def change_base(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """

        node = self.get_iter(path)
        try:
            self.set_value(node, InstCol.SORT, int(text, 0))
            self.set_value(node, InstCol.BASE, "0x{:04x}".format(int(text, 0)))
            self.callback()
        except AttributeError:
            LOGGER.warning('Illegal base address: "%s"', text)
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
            value = int(text)
            self.set_value(node, InstCol.RPT, text)
            self.callback()
        except ValueError:
            LOGGER.warning(
                '"%s" is not a valid repeat count. '
                "The repeat count must be an integer equal or greater than 1.",
                text,
            )
            return

        if value < 1:
            LOGGER.warning(
                '"%s" is not a valid repeat count. '
                "The repeat count must be an integer equal or greater than 1.",
                text,
            )
            return

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
        except ValueError:
            LOGGER.warning(
                '"%s" is not a valid repeat offset. '
                "The repeat offset must be a valid hexidecimal number",
                text,
            )
            return

        obj = self.get_value(node, InstCol.OBJ)
        if obj is None:
            return

        original = obj.repeat_offset
        obj.repeat_offset = value
        if not self.callback():
            obj.repeat_offset = original
        else:
            self.set_value(node, InstCol.OFF, "0x{:04x}".format(value))

    def new_instance(self):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        grps = set([row[0] for row in self])

        name = "new_group"
        for i in range(len(grps) + 1):
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
            new_grp,
        )

        node = self.append(None, row=row)
        self.callback()
        return (self.get_path(node), new_grp)


# class MessageHelp(Gtk.Popover):
#     def __init__(self):
#         super().__init__()
#         self.__label = Gtk.Label()
#         vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
#         vbox.pack_start(self.__label, False, True, 10)
#         self.add(vbox)
#         self.set_position(Gtk.PositionType.BOTTOM)

#     def set_text(self, obj, msg):
#         self.__label.set_text(msg)
#         self.set_relative_to(obj)
#         self.show_all()
#         self.popup()


class InstanceList(object):
    def __init__(self, obj, infobar, infolabel, callback):
        self.__obj = obj
        self.__infobar = infobar
        self.__infolabel = infolabel
        self.__col = None
        self.__project = None
        self.__model = None
        self.__build_instance_table()
        self.__enable_dnd()
        self.__obj.set_sensitive(False)
        self.modified_callback = callback
        self.need_subsystem = True
        self.need_regset = True

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
                cobj = self.col_value(child, InstCol.OBJ)
                current_group.register_sets.append(
                    GroupInstData(
                        self.col_value(child, InstCol.ID),
                        self.col_value(child, InstCol.INST),
                        self.col_value(child, InstCol.SORT),
                        int(self.col_value(child, InstCol.RPT)),
                        int(self.col_value(child, InstCol.OFF), 16),
                        self.col_value(child, InstCol.HDL),
                        cobj.no_uvm,
                        cobj.no_decode,
                        cobj.array,
                        cobj.single_decode,
                    )
                )
                child = self.__model.iter_next(child)
            tree_iter = self.__model.iter_next(tree_iter)

    def col_value(self, node, col):
        return self.__model.get_value(node, col)

    def new_instance(self):
        pos, grp = self.__model.new_instance()
        self.__project.get_grouping_list().append(grp)
        self.__obj.set_cursor(pos, self.__col, start_editing=True)
        self.need_subsystem = False
        self.infobar_update()

    def get_selected_instance(self):
        return self.__obj.get_selection().get_selected()

    def __enable_dnd(self):
        self.__obj.enable_model_drag_dest(
            [("text/plain", 0, 0)],
            Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE,
        )
        self.__obj.connect(
            "drag-data-received", self.__drag_data_received_data
        )

    def __drag_data_received_data(
        self, treeview, context, x, y, selection, info, etime
    ):
        model = treeview.get_model()

        try:
            data = selection.data
        except AttributeError:
            data = selection.get_text()

        drop_info = treeview.get_dest_row_at_pos(x, y)
        (name, width) = data.split(":")

        inst = GroupInstData(
            name, name, 0, 1, int(width, 16), "", False, False, False, False
        )

        row_data = build_row_data(
            inst.set,
            inst.inst,
            inst.offset,
            inst.repeat,
            inst.repeat_offset,
            inst.hdl,
            inst,
        )
        if drop_info:
            path, position = drop_info
            self.modified_callback()
            if len(path) == 1:
                node = self.__model.get_iter(path)
                self.__model.append(node, row_data)
            else:
                parent = self.__model.get_iter((path[0],))
                node = self.__model.get_iter(path)
                if position in (
                    Gtk.TreeViewDropPosition.BEFORE,
                    Gtk.TreeViewDropPosition.INTO_OR_BEFORE,
                ):
                    self.__model.insert_before(parent, node, row_data)
                else:
                    model.insert_after(parent, node, row_data)
        self.need_regset = False
        self.infobar_update()

    def __populate(self):
        if self.__project is None:
            return
        group_list = sorted(
            self.__project.get_grouping_list(), key=lambda x: x.base
        )

        for item in group_list:

            self.need_subsystem = False
            node = self.__model.append(
                None,
                row=build_row_data(
                    item.name,
                    "",
                    item.base,
                    item.repeat,
                    item.repeat_offset,
                    item.hdl,
                    item,
                ),
            )

            item_sets = item.register_sets
            for entry in sorted(item_sets, key=lambda x: x.offset):
                self.need_regset = False
                self.__model.append(
                    node,
                    row=build_row_data(
                        entry.inst,
                        entry.set,
                        entry.offset,
                        entry.repeat,
                        entry.repeat_offset,
                        entry.hdl,
                        entry,
                    ),
                )
        self.infobar_update()

    def _infobar_reveal(self, prop):
        try:
            self.__infobar.set_revealed(prop)
        except AttributeError:
            if prop:
                self.__infobar.show()
            else:
                self.__infobar.hide()

    def infobar_update(self):
        if self.need_subsystem:
            self.__infolabel.set_text(
                "Add a subsystem instance by clicking on the Add button next to the subsystem table."
            )
            self._infobar_reveal(True)
        elif self.need_regset:
            self.__infolabel.set_text(
                "Add a register set to a subsystem by dragging it from the sidebar and "
                "dropping it on the instance in the subsystem table."
            )
            self._infobar_reveal(True)
        else:
            self._infobar_reveal(False)

    def __build_instance_table(self):

        column = EditableColumn(
            "Instance", self.instance_inst_changed, InstCol.INST
        )
        column.set_sort_column_id(InstCol.INST)
        column.set_min_width(200)
        column.set_resizable(True)
        self.__obj.append_column(column)
        self.__col = column

        column = EditableColumn(
            "Subsystem",
            self.instance_id_changed,
            InstCol.ID,
            visible_callback=self.visible_callback,
        )
        column.set_sort_column_id(InstCol.ID)
        column.set_min_width(150)
        column.set_resizable(True)
        self.__obj.append_column(column)

        column = EditableColumn(
            "Address base", self.instance_base_changed, InstCol.BASE, True
        )
        column.set_sort_column_id(InstCol.SORT)
        column.set_min_width(150)
        column.set_resizable(True)
        self.__obj.append_column(column)

        column = EditableColumn(
            "Repeat", self.instance_repeat_changed, InstCol.RPT, True
        )
        column.set_min_width(125)
        column.set_resizable(True)
        self.__obj.append_column(column)

        column = EditableColumn(
            "Repeat Offset",
            self.instance_repeat_offset_changed,
            InstCol.OFF,
            True,
        )
        column.set_min_width(150)
        column.set_resizable(True)
        self.__obj.append_column(column)

        column = EditableColumn(
            "HDL Path", self.instance_hdl_changed, InstCol.HDL
        )
        column.set_min_width(250)
        column.set_sort_column_id(InstCol.HDL)
        column.set_resizable(True)
        self.__obj.append_column(column)

    def visible_callback(self, column, cell, model, *obj):
        node = obj[0]
        if len(model.get_path(node)) == 1:
            cell.set_property("visible", False)
        else:
            cell.set_property("visible", True)

    def instance_id_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        LOGGER.warning("Subsystem name cannot be changed")

    def inst_changed(self, attr, path, new_text):
        getattr(self.__model, attr)(path, new_text)

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


def build_row_data(inst, name, offset, rpt, rpt_offset, hdl, obj):
    row = (
        inst,
        name,
        "0x{:04x}".format(offset),
        offset,
        "{:d}".format(rpt),
        "0x{:04x}".format(rpt_offset),
        hdl,
        obj,
    )
    return row
