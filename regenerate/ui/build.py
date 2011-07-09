#
# Manage registers in a hardware design
#
# Copyright (C) 2010  Donald N. Allingham
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
import gtk
from export_assistant import ExportAssistant
from regenerate.settings.paths import INSTALL_PATH
from regenerate.writers import EXPORTERS, PRJ_EXPORTERS
from columns import EditableColumn, ToggleColumn, ComboMapColumn


class Build(object):

    (MOD, BASE, FMT, DEST, CLS, DBASE) = range(6)
    (COL_MOD, COL_BASE, COL_FMT, COL_DEST, COL_CLASS, COL_DBASE) = range(6)

    def __init__(self, project, dbmap):
        self.__dbmap = dbmap
        self.__project = project
        self.__builder = gtk.Builder()
        self.__builder.add_from_file(os.path.join(INSTALL_PATH, "ui/build.ui"))
        self.__build_top = self.__builder.get_object('build')
        self.__build_list = self.__builder.get_object('buildlist')
        self.__builder.connect_signals(self)
        self.__add_columns()
        self.__model = gtk.ListStore(bool, str, str, str, object, object)
        self.__build_list.set_model(self.__model)
        self.__build_top.show_all()
        self.__modlist = []

        self.__base2path = {}
        for item in self.__project.get_register_set():
            self.__base2path[os.path.splitext(os.path.basename(item))[0]] = item
        self.__optmap = {}
        self.__mapopt = {}
        for item in EXPORTERS:
            value = "%s (%s)" % item[1]
            self.__optmap[item[4]] = (value, item[0], True)
            self.__mapopt[value] = (item[4], item[0], True)
        for item in PRJ_EXPORTERS:
            value = "%s (%s)" % item[1]
            self.__optmap[item[4]] = (value, item[0], False)
            self.__mapopt[value] = (item[4], item[0], False)

        self.__populate()

    def __add_item_to_list(self, full_path, option, dest):
        if  self.__optmap[option][2]:
            self.__add_dbase_item_to_list(full_path, option, dest)
        else:
            self.__add_prj_item_to_list(option, dest)

    def __add_prj_item_to_list(self, option, dest):
        local_dest = os.path.join(os.path.dirname(self.__project.path), dest)
        mod = False
        if not os.path.exists(local_dest):
            mod = True
        else:
            dest_mtime = os.path.getmtime(local_dest)

            for full_path in self.__project.get_register_set():
                db_file_mtime = os.path.getmtime(full_path)
                base = os.path.splitext(os.path.basename(full_path))[0]
                if db_file_mtime > dest_mtime or self.__dbmap[base][1]:
                    mod = True
        self.__modlist.append(mod)
        (fmt, cls, dbtype) = self.__optmap[option]
        self.__model.append(row=[mod, "<project>", fmt, dest, cls, None])

    def __add_dbase_item_to_list(self, full_path, option, dest):
        base = os.path.splitext(os.path.basename(full_path))[0]
        db_file_mtime = os.path.getmtime(full_path)
        local_dest = os.path.join(os.path.dirname(self.__project.path), dest)
        mod = False
        if not os.path.exists(local_dest):
            mod = True
        else:
            dest_mtime = os.path.getmtime(local_dest)
            if db_file_mtime > dest_mtime or self.__dbmap[base][1]:
                mod = True
        self.__modlist.append(mod)
        (fmt, cls, rpttype) = self.__optmap[option]
        dbase = self.__dbmap[base][0].db
        self.__model.append(row=[mod, base, fmt, dest, cls, dbase])

    def __populate(self):
        for item in self.__project.get_register_set():
            try:
                for (option, dest) in self.__project.get_export_list(item):
                    self.__add_dbase_item_to_list(item, option, dest)
            except KeyError:
                pass
        for (option, dest) in self.__project.get_project_export_list():
            try:
                self.__add_prj_item_to_list(option, dest)
            except KeyError:
                pass

    def toggle_callback(self, cell, path, source):
        self.__model[path][0] = not self.__model[path][0]

    def register_set_callback(self, cell, path, node, col):
        model = cell.get_property('model')
        self.__model[path][self.DBASE] = model[node][1]
        self.__model[path][self.BASE] = model[node][0]

    def format_callback(self, cell, path, node, col):
        model = cell.get_property('model')
        self.__model[path][self.CLS] = model[node][1]
        self.__model[path][self.FMT] = model[node][0]

    def __add_columns(self):
        column = ToggleColumn("Build", self.toggle_callback, self.MOD)
        self.__build_list.append_column(column)

        column = EditableColumn("RegisterSet", None, self.BASE)
        column.set_min_width(125)
        column.set_sort_column_id(self.BASE)
        self.__build_list.append_column(column)

        column = EditableColumn("Format", None, self.FMT)
        column.set_min_width(175)
        column.set_sort_column_id(self.FMT)
        self.__build_list.append_column(column)

        column = EditableColumn("Destination", None, self.DEST)
        column.set_min_width(250)
        column.set_sort_column_id(self.DEST)
        self.__build_list.append_column(column)

    def on_buildlist_button_press_event(self, obj, event):
        if event.button == 3:
            menu = self.__builder.get_object("menu")
            menu.popup(None, None, None, 1, 0)

    def on_select_all_activate(self, obj):
        for item in self.__model:
            item[0] = True

    def on_unselect_all_activate(self, obj):
        for item in self.__model:
            item[0] = False

    def on_select_ood_activate(self, obj):
        for (count, item) in enumerate(self.__model):
            item[0] = self.__modlist[count]

    def on_run_build_clicked(self, obj):
        for item in [item for item in self.__model if item[0]]:
            wrclass = item[self.CLS]
            dbase = item[self.DBASE]
            dest = os.path.abspath(
                os.path.join(os.path.dirname(self.__project.path),
                             item[self.DEST]))
            try:
                if dbase:
                    gen = wrclass(dbase)
                else:
                    db_list = [i[0].db for i in self.__dbmap.values()]
                    gen = wrclass(self.__project, db_list)
                gen.set_project(self.__project)
                gen.write(dest)
                item[self.MOD] = False
            except IOError, msg:
                from error_dialogs import ErrorMsg
                ErrorMsg("Error running exporter",
                         str(msg))

    def on_add_build_clicked(self, obj):
        optlist = [("%s (%s)" % item[1], True, item[3]) for item in EXPORTERS] + \
            [("%s (%s)" % item[1], False, item[3]) for item in PRJ_EXPORTERS]
        reglist = [os.path.splitext(os.path.basename(i))[0]
                   for i in self.__project.get_register_set()]
        ExportAssistant(self.__project.short_name, optlist, reglist,
                        self.add_callback, self.run_callback)

    def add_callback(self, filename, export_format, register_set):
        option = self.__mapopt[export_format][0]
        if self.__mapopt[export_format][2]:
            register_path = self.__base2path[register_set]
            self.__project.add_to_export_list(register_path, option, filename)
        else:
            register_path = '<project>'
            self.__project.add_to_project_export_list(option, filename)
        self.__add_item_to_list(register_path, option, filename)

    def run_callback(self, filename, export_format, register_set):
        base = os.path.splitext(os.path.basename(register_set))[0]
        dbase = self.__dbmap[base][0].db
        wrclass = self.__mapopt[export_format][1]
        if self.__mapopt[export_format][2]:
            gen = wrclass(dbase)
        else:
            db_list = [i[0].db for i in self.__dbmap.values()]
            gen = wrclass(self.__project, db_list)
        gen.set_project(self.__project)
        gen.write(filename)

    def on_remove_build_clicked(self, obj):
        sel = self.__build_list.get_selection().get_selected()
        data = sel[0][sel[1]]

        option = self.__mapopt[data[self.COL_FMT]][0]
        filename = data[self.COL_DEST]
        if data[self.COL_DBASE]:
            register_path = self.__base2path[data[self.COL_BASE]]
            self.__project.remove_from_export_list(register_path, option,
                                                   filename)
        else:
            self.__project.remove_from_project_export_list(option, filename)
        self.__model.remove(sel[1])

    def on_close_clicked(self, obj):
        self.__build_top.destroy()
