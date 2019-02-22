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
import pango
import os
from regenerate.settings.paths import INSTALL_PATH

try:
    import pysvn
    __client = pysvn.Client()

    def __ood(path):
        files = []
        for svn_status in __client.status(path,
                                          recurse=False,
                                          get_all=True,
                                          update=True):
            if (svn_status.repos_text_status != pysvn.wc_status_kind.none or
                    svn_status.repos_prop_status != pysvn.wc_status_kind.none):
                files.append(svn_status.path)
        return files

    def get_out_of_date(path):
        try:
            files = __ood(path)
        except:
            files = []
        return files

    def update_file(path):
        __client.update(path)

except ImportError:

    def get_out_of_date(filename):
        return []

    def update_file(path):
        pass


class ProjectModel(gtk.ListStore):

    (NAME, ICON, FILE, MODIFIED, OOD, OBJ) = range(6)

    def __init__(self, use_svn=False):
        gtk.gdk.threads_init()
        gtk.ListStore.__init__(self, str, str, str, bool, bool, object)
        self.file_list = {}
        self.paths = set()
        self.__use_svn = use_svn

    def set_markup(self, node, modified):
        if modified:
            icon = gtk.STOCK_EDIT
        else:
            icon = None
        self.set_value(node, self.ICON, icon)
        self.set_value(node, self.MODIFIED, modified)

    def is_not_saved(self):
        for item in self:
            if item[self.MODIFIED]:
                return True
        return False

    def load_icons(self):
        if self.__use_svn:
            for path in self.paths:
                for ood_file in get_out_of_date(path):
                    try:
                        node = self.file_list[ood_file]
                        self.set_value(node, self.ICON, 'out-of-date')
                        self.set_value(node, self.OOD, True)
                    except KeyError:
                        pass
        self.paths = set()
        self.file_list = {}

    def add_dbase(self, filename, dbase):
        base = os.path.splitext(os.path.basename(filename))[0]
        node = self.append(row=[base, "", filename, False, False, dbase])
        self.file_list[filename] = node
        self.paths.add(os.path.dirname(filename))
        return node


class ProjectList(object):
    def __init__(self, obj, selection_callback):
        self.__obj = obj
        self.__obj.get_selection().connect('changed', selection_callback)
        self.__obj.set_reorderable(True)
        self.__model = None
        self.__build_prj_window()

        self.__obj.enable_model_drag_source(
            gtk.gdk.BUTTON1_MASK,
            [('text/plain', 0, 0)],
            gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE
        )
        self.__obj.connect('drag-data-get', self.drag_data_get)

        self.factory = gtk.IconFactory()
        filename = os.path.join(INSTALL_PATH, "media", "ModifiedIcon.png")
        pixbuf = gtk.gdk.pixbuf_new_from_file(filename)
        iconset = gtk.IconSet(pixbuf)
        self.factory.add('out-of-date', iconset)
        self.factory.add_default()

    def drag_data_get(self, treeview, context, selection, target_id, etime):

        tselection = treeview.get_selection()
        model, tree_iter = tselection.get_selected()

        prj_name = model.get_value(tree_iter, ProjectModel.NAME)
        prj_obj = model.get_value(tree_iter, ProjectModel.OBJ)
        data = "{0}:{1:x}".format(prj_name, 1 << prj_obj.db.address_bus_width)

        try:
            selection.set(selection.target, 8, data)
        except AttributeError:
            selection.set_text(data, -1)

    def set_model(self, model):
        self.__model = model
        self.__obj.set_model(model)

    def __build_prj_window(self):
        renderer = gtk.CellRendererPixbuf()
        column = gtk.TreeViewColumn("", renderer, stock_id=1)
        column.set_min_width(20)
        self.__obj.append_column(column)

        renderer = gtk.CellRendererText()
        renderer.set_property('ellipsize', pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn("Register Sets", renderer, text=0)
        column.set_min_width(140)
        self.__obj.append_column(column)

    def get_selected(self):
        return self.__obj.get_selection().get_selected()

    def select(self, node):
        selection = self.__obj.get_selection()
        if node and selection:
            selection.select_iter(node)

    def select_path(self, path):
        selection = self.__obj.get_selection()
        selection.select_path(path)
