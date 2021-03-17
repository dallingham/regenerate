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

import os

from gi.repository import Gtk, Gdk, GdkPixbuf, Pango
from regenerate.settings.paths import INSTALL_PATH
from regenerate.ui.enums import BlockCol
from regenerate.db.containers import RegSetContainer


class RegSetModel(Gtk.ListStore):
    """
    Provides the model for the project list
    """

    def __init__(self):
        super().__init__(str, str)

        Gdk.threads_init()
        self.file_list = {}
        self.paths = set()

    def set_markup(self, node, modified):
        """Sets the icon if the project has been modified"""
        return

        if modified:
            icon = Gtk.STOCK_EDIT
        else:
            icon = None
        self.set_value(node, BlockCol.ICON, icon)

    #        self.set_value(node, BlockCol.MODIFIED, modified)

    def is_not_saved(self):
        return False

    def load_icons(self):
        pass

    def add_dbase(self, regset: RegSetContainer, modified=False):
        """Add the the database to the model"""

        base = regset.filename.stem
        if modified:
            node = self.append(row=[Gtk.STOCK_EDIT, base])
        else:
            node = self.append(row=["", base])

        self.file_list[str(regset.filename)] = node
        self.paths.add(regset.filename.parent)
        return node


class RegSetList:
    """Project list"""

    def __init__(self, obj, selection_callback):
        self.__obj = obj
        self.__obj.get_selection().connect("changed", selection_callback)
        self.__obj.set_reorderable(True)
        self.__model = None
        self.__build_prj_window()

        #        self.__obj.set_tooltip_column(PrjCol.FILE)

        self.__obj.enable_model_drag_source(
            Gdk.ModifierType.BUTTON1_MASK,
            [("text/plain", 0, 0)],
            Gdk.DragAction.DEFAULT | Gdk.DragAction.MOVE,
        )
        self.__obj.connect("drag-data-get", self.drag_data_get)

        self.factory = Gtk.IconFactory()
        filename = os.path.join(INSTALL_PATH, "media", "ModifiedIcon.png")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        iconset = Gtk.IconSet(pixbuf)
        self.factory.add("out-of-date", iconset)
        self.factory.add_default()

    def drag_data_get(self, treeview, _context, selection, _target_id, _etime):
        """Get the data when a drag starts"""

        tselection = treeview.get_selection()
        model, tree_iter = tselection.get_selected()

        prj_name = model.get_value(tree_iter, PrjCol.NAME)
        prj_obj = model.get_value(tree_iter, PrjCol.OBJ)
        data = "{0}:{1:x}".format(prj_name, 1 << prj_obj.db.address_bus_width)

        try:
            selection.set(selection.target, 8, data)
        except AttributeError:
            selection.set_text(data, -1)

    def set_model(self, model):
        """Sets the model"""

        self.__model = model
        self.__obj.set_model(model)

    def __build_prj_window(self):
        """Build the project window"""

        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("", renderer, stock_id=0)
        column.set_min_width(20)
        self.__obj.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Register Sets", renderer, text=1)
        column.set_min_width(140)
        self.__obj.append_column(column)

    def get_selected(self):
        """Return the selected object"""
        return self.__obj.get_selection().get_selected()

    def select(self, node):
        """Select the specified row"""

        selection = self.__obj.get_selection()
        if node and selection:
            selection.select_iter(node)

    def select_path(self, path):
        """Select based on path"""

        selection = self.__obj.get_selection()
        selection.select_path(path)


class RegSetTab:
    def __init__(self, reg_set_list, reglist_obj, bitfield_obj):
        self.reg_set_model = None
        self.bitfield_obj = bitfield_obj

        self.reg_set_obj = RegSetList(reg_set_list, self.prj_selection_changed)
        self.reglist_obj = reglist_obj
        self.clear()
        self.active = None
        self.active_name = ""
        self.project = None

    def change_project(self, prj):

        self.project = prj
        for container_name in self.project.regsets:
            icon = (
                Gtk.STOCK_EDIT
                if self.project.regsets[container_name].modified
                else ""
            )

            self.reg_set_model.add_dbase(
                self.project.regsets[container_name],
            )

        self.reg_set_obj.select_path(0)

    def clear(self):
        self.reg_set_model = RegSetModel()
        self.reg_set_obj.set_model(self.reg_set_model)

    def prj_selection_changed(self, _obj):
        model, node = self.reg_set_obj.get_selected()
        if node:
            self.active_name = model[node][1]
            self.active = self.project.regsets[self.active_name]
        else:
            self.active = None
            self.active_name = ""
        print(self.active_name)

        # old_skip = self.skip_changes
        # self.skip_changes = True

        if self.active:
            self.active.reg_select = self.reglist_obj.get_selected_row()
            self.active.bit_select = self.bitfield_obj.get_selected_row()

            self.reg_model = self.active.reg_model
            self.reg_description.set_database(self.active.db)

            self.filter_manage.change_filter(self.active.modelfilter)
            self.modelsort = self.active.modelsort
            self.reglist_obj.set_model(self.modelsort)
            self.bit_model = self.active.bit_field_list
            self.bitfield_obj.set_model(self.bit_model)
            text = "<b>%s - %s</b>" % (
                self.dbase.module_name,
                self.dbase.descriptive_title,
            )
            self.selected_dbase.set_text(text)
            self.selected_dbase.set_use_markup(True)
            self.selected_dbase.set_ellipsize(Pango.EllipsizeMode.END)
            if self.active.reg_select:
                for row in self.active.reg_select:
                    self.reglist_obj.select_row(row)
            if self.active.bit_select:
                for row in self.active.bit_select:
                    self.bitfield_obj.select_row(row)
            self.redraw()
            self.enable_registers(True)
        else:
            self.active = None
            self.dbase = None
            self.selected_dbase.set_text("")
            self.reglist_obj.set_model(None)
            self.enable_registers(False)
        self.skip_changes = old_skip
