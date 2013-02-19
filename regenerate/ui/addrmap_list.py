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
Provides the Address List interface
"""

import gtk
from columns import EditableColumn, ToggleColumn, ComboMapColumn
from regenerate.db import LOGGER

SIZE2STR = (
    ("32-bits", 4),
    ("64-bits", 8))

INT2SIZE = {
    4: "32-bits",
    8: "64-bits",
    }

STR2SIZE = {
    "32-bits": 4,
    "64-bits": 8,
    }


class AddrMapModel(gtk.TreeStore):
    """
    Provides the list of instances for the module. Instances consist of the
    symbolic ID name and the base address.
    """

    (NAME_COL, BASE_COL, FIXED_COL, WIDTH_COL) = range(4)

    def __init__(self):
        gtk.TreeStore.__init__(self, str, str, bool, str)

    def new_instance(self):
        """
        Adds a new instance to the model. It is not added to the database until
        either the change_id or change_base is called.
        """
        node = self.append(None, row=('', '0', False, ""))
        return self.get_path(node)

    def append_instance(self, inst):
        """
        Adds the specified instance to the InstanceList
        """
        self.append(row=(inst[0], "%08x" % inst[1], False, ""))

    def get_values(self):
        """
        Returns the list of instance tuples from the model.
        """
        return [(val[0], int(val[1], 16)) for val in self if val[0]]


class AddrMapList(object):
    """
    Container for the Address Map control logic.
    """

    def __init__(self, obj):
        self.__obj = obj
        self.__col = None
        self.__project = None
        self.__model = None
        self.__build_instance_table()
        self.__enable_dnd()
        self.__obj.set_sensitive(False)

    def __enable_dnd(self):
        """
        Enables drag and drop
        """
        self.__obj.enable_model_drag_dest([('text/plain', 0, 0)],
                                          gtk.gdk.ACTION_DEFAULT |
                                          gtk.gdk.ACTION_MOVE)
        self.__obj.connect('drag-data-received',
                           self.__drag_data_received_data)

    def __drag_data_received_data(self, treeview, context, x, y, selection,
                                  info, etime):
        """
        Called when data is dropped.
        """
        model = treeview.get_model()
        data = selection.data
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            path, position = drop_info
            row_data = [data, "", "", ""]
            group_names = [n.name for n in self.__project.get_grouping_list()]
            if data not in group_names:
                return
            if len(path) == 1:
                parent_name = self.__model[path][0]
                if self.__project.add_address_map_group(parent_name, data):
                    node = self.__model.get_iter(path)
                    self.__model.append(node, row_data)
            else:
                parent = self.__model.get_iter((path[0],))
                parent_name = self.__model[path[0]][0]
                if self.__project.add_address_map_group(parent_name, data):
                    node = self.__model.get_iter(path)
                    if (position == gtk.TREE_VIEW_DROP_BEFORE
                        or position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                        self.__model.insert_before(parent, node, row_data)
                    else:
                        model.insert_after(parent, node, row_data)

    def set_project(self, project):
        """
        Sets the project for the address map, and repopulates the list
        from the project.
        """
        self.__project = project
        self.__obj.set_sensitive(True)
        self.populate()

    def populate(self):
        """
        Loads the data from the project
        """
        if self.__project is None:
            return

        self.__model.clear()
        for base in self.__project.get_address_maps():
            data = (base.name, "%x" % base.base, base.fixed,
                    INT2SIZE[base.width])
            node = self.__model.append(None, row=data)
            for name in self.__project.get_address_map_groups(base.name):
                self.__model.append(node, row=[name, "", False, ""])

    def _name_changed(self, cell, path, new_text, col):
        """
        Called when the name field is changed.
        """
        if len(path) != 1:
            return

        node = self.__model.get_iter(path)
        name = self.__model.get_value(node, AddrMapModel.NAME_COL)
        self.__project.change_address_map_name(name, new_text)
        self.__model[path][AddrMapModel.NAME_COL] = new_text
        self.__project.set_modified()

    def _base_changed(self, cell, path, new_text, col):
        """
        Called when the base address field is changed.
        """
        if len(path) != 1:
            return
        try:
            value = int(new_text, 16)
        except ValueError:
            LOGGER.error('Illegal address: "%s"' % new_text)
            return
        if new_text:
            node = self.__model.get_iter(path)
            name = self.__model.get_value(node, AddrMapModel.NAME_COL)
            fixed = self.__model.get_value(node, AddrMapModel.FIXED_COL)
            width = STR2SIZE[self.__model.get_value(node,
                                                    AddrMapModel.WIDTH_COL)]

            self.__project.set_address_map(name, value, width, fixed)
            self.__model[path][AddrMapModel.BASE_COL] = new_text
            self.__project.set_modified()

    def _width_changed(self, cell, path, node, col):
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """
        if len(path) != 1:
            return
        nde = self.__model.get_iter(path)
        name = self.__model.get_value(nde, AddrMapModel.NAME_COL)
        value = self.__model.get_value(nde, AddrMapModel.BASE_COL)
        fixed = self.__model.get_value(nde, AddrMapModel.FIXED_COL)

        model = cell.get_property('model')
        self.__model[path][col] = model.get_value(node, 0)
        width = model.get_value(node, 1)
        self.__project.set_address_map(name, int(value, 16), width, fixed)

    def _fixed_changed(self, cell, path, source):
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """
        if len(path) != 1:
            return
        node = self.__model.get_iter(path)
        name = self.__model.get_value(node, AddrMapModel.NAME_COL)
        value = self.__model.get_value(node, AddrMapModel.BASE_COL)
        fixed = self.__model.get_value(node, AddrMapModel.FIXED_COL)
        width = self.__model.get_value(node, AddrMapModel.WIDTH_COL)
        self.__model[path][AddrMapModel.FIXED_COL] = not fixed
        self.__project.set_address_map(name, int(value, 16),
                                       STR2SIZE[width], not fixed)

    def __build_instance_table(self):
        """
        Builds the columns, adding them to the address map list.
        """
        column = EditableColumn('Map Name', self._name_changed,
                                AddrMapModel.NAME_COL)
        column.set_min_width(240)
        column.set_sort_column_id(AddrMapModel.NAME_COL)
        self.__obj.append_column(column)
        self.__col = column

        column = EditableColumn('Address base (hex)', self._base_changed,
                                AddrMapModel.BASE_COL)
        column.set_sort_column_id(AddrMapModel.BASE_COL)
        self.__obj.append_column(column)

        column = ComboMapColumn('Access Width', self._width_changed,
                                SIZE2STR, AddrMapModel.WIDTH_COL)
        column.set_min_width(250)
        self.__obj.append_column(column)

        column = ToggleColumn('Fixed Address', self._fixed_changed,
                              AddrMapModel.FIXED_COL)
        column.set_max_width(200)
        self.__obj.append_column(column)

        self.__model = AddrMapModel()
        self.__obj.set_model(self.__model)

    def clear(self):
        """
        Clears the data from the list
        """
        self.__model.clear()

    def append(self, base, addr, fixed, width):
        """
        Add the data to the list.
        """
        data = (base, "%x" % addr, fixed, INT2SIZE[width])
        self.__model.append(row=(data))

    def remove_selected(self):
        """
        Removes the selected node from the list
        """
        (model, node) = self.__obj.get_selection().get_selected()
        if node is None:
            return

        path = model.get_path(node)
        if len(path) > 1:
            # remove group from address map
            pass
        else:
            name = model.get_value(node, AddrMapModel.NAME_COL)
            model.remove(node)
            self.__project.set_modified()
            self.__project.remove_address_map(name)

    def add_new_map(self):
        """
        Creates a new address map and adds it to the project. Uses default
        data, and sets the first field to start editing.
        """
        node = self.__model.append(None, row=("NewMap", 0,
                                              False, SIZE2STR[0][0]))
        path = self.__model.get_path(node)
        self.__project.set_modified()
        self.__project.set_address_map('NewMap', 0, False, SIZE2STR[0][1])
        self.__obj.set_cursor(path, focus_column=self.__col,
                              start_editing=True)
