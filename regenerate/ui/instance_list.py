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
Instance List and Model
"""

import re
from gi.repository import Gtk, GObject
from regenerate.ui.columns import EditableColumn
from regenerate.db import RegisterInst, LOGGER
from regenerate.ui.enums import InstCol


class InstMdl(Gtk.TreeStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    def __init__(self, project):

        super().__init__(str, str, str, GObject.TYPE_UINT64, str, str, object)

        self.callback = self.__null_callback
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

        iter2 = self.get_iter(path)
        old_value = self.get_value(iter2, InstCol.INST)
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
                "Array notation not valid. "
                "Use the repeat/repeat count to create arrays"
            )
            return

        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]+$", text):
            LOGGER.warning("{text} is not a valid subsystem name")
            return

        node = self.get_iter(path)
        self.set_value(node, InstCol.INST, text)
        self.callback()

        if len(path.split(":")) == 1:
            obj = self.get_value(node, InstCol.OBJ)
            obj.inst_name = text
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
            obj.hdl_path = text

    def change_base(self, path, text):
        """
        Called when the base address of an instance has been edited in the
        InstanceList
        """

        node = self.get_iter(path)
        try:
            self.set_value(node, InstCol.SORT, int(text, 0))
            self.set_value(node, InstCol.BASE, "0x{:08x}".format(int(text, 0)))
            self.callback()
        except AttributeError:
            LOGGER.warning('Illegal base address: "%s"', text)
        obj = self.get_value(node, InstCol.OBJ)
        if obj:
            obj.address_base = int(text, 16)

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

    def add_instance(self, new_inst):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        row = build_row_data(
            new_inst.block,
            new_inst.inst_name,
            new_inst.address_base,
            new_inst.repeat,
            new_inst.hdl_path,
            new_inst,
        )

        node = self.append(None, row=row)
        self.callback()
        return (self.get_path(node), new_inst)


class InstanceList:
    """Instance list"""

    def __init__(self, obj, callback):
        self.__obj = obj
        self.__col = None
        self.__project = None
        self.__model = None
        self.__build_instance_table()
        self.__obj.set_sensitive(False)
        self.modified_callback = callback
        self.need_subsystem = True
        self.need_regset = True

    def set_project(self, project):
        """Set the project object for the instance list"""

        self.__project = project
        self.__obj.set_sensitive(True)
        self.__populate()

    def set_model(self, model):
        """Set the model object for the instance list"""

        self.__obj.set_model(model)
        self.__model = model
        self.__model.callback = self.modified_callback

    def get_groups(self):
        """Get the groups that are currently in the list"""

        tree_iter = self.__model.get_iter_first()
        while tree_iter is not None:
            current_group = self.__model.get_value(tree_iter, InstCol.OBJ)

            child = self.__model.iter_children(tree_iter)
            while child:
                cobj = self.col_value(child, InstCol.OBJ)
                current_group.regset_insts.append(
                    RegisterInst(
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
        """Get the value at the particular node and column"""

        return self.__model.get_value(node, col)

    def new_instance(self):
        """Create a new empty instance in the list/model"""

        pos, grp = self.__model.new_instance()
        self.__project.get_grouping_list().append(grp)
        self.__obj.set_cursor(pos, self.__col, start_editing=True)
        self.need_subsystem = False

    def get_selected_instance(self):
        """Get the selected instance"""

        return self.__obj.get_selection().get_selected()

    # def __drag_data_received_data(
    #     self, treeview, _context, xpos, ypos, selection, _info, _etime
    # ):
    #     """Called with drag data is recieved"""

    #     model = treeview.get_model()

    #     try:
    #         data = selection.data
    #     except AttributeError:
    #         data = selection.get_text()

    #     drop_info = treeview.get_dest_row_at_pos(xpos, ypos)
    #     (name, width) = data.split(":")

    #     inst = RegisterInst(
    #         name, name, 0, 1, int(width, 16), "", False, False, False, False
    #     )

    #     row_data = build_row_data(
    #         inst.set_name,
    #         inst.inst,
    #         inst.offset,
    #         inst.repeat,
    #         inst.repeat_offset,
    #         inst.hdl,
    #         inst,
    #     )
    #     if drop_info:
    #         path, position = drop_info
    #         self.modified_callback()
    #         if len(path) == 1:
    #             node = self.__model.get_iter(path)
    #             self.__model.append(node, row_data)
    #         else:
    #             parent = self.__model.get_iter((path[0],))
    #             node = self.__model.get_iter(path)
    #             if position in (
    #                 Gtk.TreeViewDropPosition.BEFORE,
    #                 Gtk.TreeViewDropPosition.INTO_OR_BEFORE,
    #             ):
    #                 self.__model.insert_before(parent, node, row_data)
    #             else:
    #                 model.insert_after(parent, node, row_data)
    #     self.need_regset = False

    def __populate(self):
        """Fill the list from the project"""

        if self.__project is None:
            return
        blocks = sorted(
            self.__project.block_insts, key=lambda x: x.address_base
        )

        for item in blocks:
            self.need_subsystem = False
            node = self.__model.append(
                None,
                row=build_row_data(
                    item.inst_name,
                    item.block,
                    item.address_base,
                    item.repeat,
                    item.hdl_path,
                    item,
                ),
            )

    def __build_instance_table(self):
        """Build the table, adding the columns"""

        column = EditableColumn(
            "Block Name",
            self.instance_id_changed,
            InstCol.ID,
        )
        column.set_sort_column_id(InstCol.ID)
        column.set_min_width(150)
        column.set_resizable(True)
        self.__obj.append_column(column)

        column = EditableColumn(
            "Block Instance", self.instance_inst_changed, InstCol.INST
        )
        column.set_sort_column_id(InstCol.INST)
        column.set_min_width(200)
        column.set_resizable(True)
        self.__obj.append_column(column)
        self.__col = column

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
            "HDL Path", self.instance_hdl_changed, InstCol.HDL
        )
        column.set_min_width(250)
        column.set_sort_column_id(InstCol.HDL)
        column.set_resizable(True)
        self.__obj.append_column(column)

    def instance_id_changed(self, _cell, _path, _new_text, _col):
        """
        Updates the data model when the text value is changed in the model.
        """
        LOGGER.warning("Subsystem name cannot be changed")

    def inst_changed(self, attr, path, new_text):
        """Called with the instance name changed"""

        getattr(self.__model, attr)(path, new_text)

    def instance_inst_changed(self, _cell, path, new_text, _col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_inst", path, new_text)

    def instance_base_changed(self, _cell, path, new_text, _col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_base", path, new_text)

    def instance_format_changed(self, _cell, path, new_text, _col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_format", path, new_text)

    def instance_hdl_changed(self, _cell, path, new_text, _col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_hdl", path, new_text)

    def instance_repeat_changed(self, _cell, path, new_text, _col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.inst_changed("change_repeat", path, new_text)


def build_row_data(inst, name, offset, rpt, hdl, obj):
    """Build row data from the data"""

    row = (
        inst,
        name,
        "0x{:08x}".format(offset),
        offset,
        "{:d}".format(rpt),
        hdl,
        obj,
    )
    return row
