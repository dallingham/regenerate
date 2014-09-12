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
from regenerate.db import LOGGER, AddrMapData

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


class AddrMapMdl(gtk.TreeStore):
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
        node = self.append(None, row=('', '0', False, "32-bits"))
        return self.get_path(node)

    def append_instance(self, inst):
        """
        Adds the specified instance to the InstanceList
        """
        self.append(row=(inst[0], "%08x" % inst[1], False, "32-bits"))

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
        self._obj = obj
        self._col = None
        self._prj = None
        self._model = None
        self._build_instance_table()
        self._enable_dnd()
        self._obj.set_sensitive(False)

    def _enable_dnd(self):
        """
        Enables drag and drop
        """
        self._obj.enable_model_drag_dest([('text/plain', 0, 0)],
                                         gtk.gdk.ACTION_DEFAULT |
                                         gtk.gdk.ACTION_MOVE)
        self._obj.connect('drag-data-received',
                          self._drag_data_received_data)

    def _drag_data_received_data(self, treeview, context, x, y, selection,
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
            group_names = [n.name for n in self._prj.get_grouping_list()]
            if data not in group_names:
                return
            if len(path) == 1:
                parent_name = self._model[path][0]
                if self._prj.add_address_map_group(parent_name, data):
                    node = self._model.get_iter(path)
                    self._model.append(node, row_data)
            else:
                parent = self._model.get_iter((path[0],))
                parent_name = self._model[path[0]][0]
                if self._prj.add_address_map_group(parent_name, data):
                    node = self._model.get_iter(path)
                    if (position == gtk.TREE_VIEW_DROP_BEFORE
                        or position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                        self._model.insert_before(parent, node, row_data)
                    else:
                        model.insert_after(parent, node, row_data)

    def set_project(self, project):
        """
        Sets the project for the address map, and repopulates the list
        from the project.
        """
        self._prj = project
        self._obj.set_sensitive(True)
        self.populate()

    def populate(self):
        """
        Loads the data from the project
        """
        if self._prj is None:
            return

        self._model.clear()
        for base in self._prj.get_address_maps():
            if base.width not in INT2SIZE:
                LOGGER.error('Illegal width (%d) for address map "%s"' %
                             (base.width, base.name))
                base = AddrMapData(base.name, base.base, 4, base.fixed)
            data = (base.name, "%x" % base.base, base.fixed,
                    INT2SIZE[base.width])
            node = self._model.append(None, row=data)
            for name in self._prj.get_address_map_groups(base.name):
                self._model.append(node, row=[name, "", False, ""])

    def _name_changed(self, cell, path, new_text, col):
        """
        Called when the name field is changed.
        """
        if len(path) != 1:
            return

        current_maps = set([i.name for i in self._prj.get_address_maps()])
        if new_text in current_maps:
            LOGGER.error('"%s" has already been used as an address map name'
                         % new_text)
        else:
            node = self._model.get_iter(path)
            name = self._model.get_value(node, AddrMapMdl.NAME_COL)
            self._prj.change_address_map_name(name, new_text)
            self._model[path][AddrMapMdl.NAME_COL] = new_text
            self._prj.modified = True

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
            node = self._model.get_iter(path)
            name = self._model.get_value(node, AddrMapMdl.NAME_COL)
            fixed = self._model.get_value(node, AddrMapMdl.FIXED_COL)
            width = STR2SIZE[self._model.get_value(node,
                                                   AddrMapMdl.WIDTH_COL)]

            self._prj.set_address_map(name, value, width, fixed)
            self._model[path][AddrMapMdl.BASE_COL] = new_text
            self._prj.modified = True

    def _width_changed(self, cell, path, node, col):
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """
        if len(path) != 1:
            return
        nde = self._model.get_iter(path)
        name = self._model.get_value(nde, AddrMapMdl.NAME_COL)
        value = self._model.get_value(nde, AddrMapMdl.BASE_COL)
        fixed = self._model.get_value(nde, AddrMapMdl.FIXED_COL)

        model = cell.get_property('model')
        self._model[path][col] = model.get_value(node, 0)
        width = model.get_value(node, 1)
        self._prj.set_address_map(name, int(value, 16), width, fixed)

    def _fixed_changed(self, cell, path, source):
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """
        if len(path) != 1:
            return
        node = self._model.get_iter(path)
        name = self._model.get_value(node, AddrMapMdl.NAME_COL)
        value = self._model.get_value(node, AddrMapMdl.BASE_COL)
        fixed = self._model.get_value(node, AddrMapMdl.FIXED_COL)
        width = self._model.get_value(node, AddrMapMdl.WIDTH_COL)
        self._model[path][AddrMapMdl.FIXED_COL] = not fixed
        self._prj.set_address_map(name, int(value, 16),
                                  STR2SIZE[width], not fixed)

    def _build_instance_table(self):
        """
        Builds the columns, adding them to the address map list.
        """
        column = EditableColumn('Map Name', self._name_changed,
                                AddrMapMdl.NAME_COL)
        column.set_min_width(240)
        column.set_sort_column_id(AddrMapMdl.NAME_COL)
        self._obj.append_column(column)
        self._col = column

        column = EditableColumn('Address base (hex)', self._base_changed,
                                AddrMapMdl.BASE_COL, True)
        column.set_sort_column_id(AddrMapMdl.BASE_COL)
        self._obj.append_column(column)

        column = ComboMapColumn('Access Width', self._width_changed,
                                SIZE2STR, AddrMapMdl.WIDTH_COL)
        column.set_min_width(250)
        self._obj.append_column(column)

        column = ToggleColumn('Fixed Address', self._fixed_changed,
                              AddrMapMdl.FIXED_COL)
        column.set_max_width(200)
        self._obj.append_column(column)

        self._model = AddrMapMdl()
        self._obj.set_model(self._model)

    def clear(self):
        """
        Clears the data from the list
        """
        self._model.clear()

    def append(self, base, addr, fixed, width):
        """
        Add the data to the list.
        """
        data = (base, "%x" % addr, fixed, INT2SIZE[width])
        self._model.append(row=(data))

    def remove_selected(self):
        """
        Removes the selected node from the list
        """
        (model, node) = self._obj.get_selection().get_selected()
        if node is None:
            return

        path = model.get_path(node)
        if len(path) > 1:
            # remove group from address map
            pass
        else:
            name = model.get_value(node, AddrMapMdl.NAME_COL)
            model.remove(node)
            self._prj.modified = True
            self._prj.remove_address_map(name)

    def add_new_map(self):
        """
        Creates a new address map and adds it to the project. Uses default
        data, and sets the first field to start editing.
        """
        name = self._create_new_map_name()
        node = self._model.append(None, row=(name, 0, False,
                                             SIZE2STR[0][0]))
        path = self._model.get_path(node)
        self._prj.modified = True
        self._prj.set_address_map(name, 0, False, SIZE2STR[0][1])
        self._obj.set_cursor(path, focus_column=self._col,
                             start_editing=True)

    def _create_new_map_name(self):
        template = "NewMap"
        index = 0
        current_maps = set([i.name for i in self._prj.get_address_maps()])

        name = template
        while name in current_maps:
            name = "%s%d" % (template, index)
            index = index + 1
        return name
