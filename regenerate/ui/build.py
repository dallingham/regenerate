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
"""
Provides the builder, which allows the user to construct rules that
keeps track of when an output file should be rebuilt.
"""

import os
import gtk
from regenerate.settings.paths import INSTALL_PATH
from regenerate.ui.base_window import BaseWindow
from regenerate.ui.columns import EditableColumn, ToggleColumn
from regenerate.ui.error_dialogs import ErrorMsg
from regenerate.ui.export_assistant import ExportAssistant
from regenerate.writers import EXPORTERS, PRJ_EXPORTERS, GRP_EXPORTERS

(MDL_MOD, MDL_BASE, MDL_FMT, MDL_DEST, MDL_CLASS, MDL_DBASE, MDL_TYPE) = range(7)
(OPTMAP_DESCRIPTION, OPTMAP_CLASS, OPTMAP_REGISTER_SET) = range(3)
(MAPOPT_ID, MAPOPT_CLASS, MAPOPT_REGISTER_SET) = range(3)
(DB_MAP_DBASE, DB_MAP_MODIFIED) = range(2)

(LEVEL_BLOCK, LEVEL_GROUP, LEVEL_PROJECT) = range(3)


class Build(BaseWindow):
    """
    Builder interface. Allows the user to control exporters, building rules
    as to what should be built.
    """

    def __init__(self, project, dbmap):
        BaseWindow.__init__(self)

        self.__dbmap = dbmap
        self.__prj = project
        self.__modlist = []

        self.__base2path = {}
        for item in self.__prj.get_register_set():
            base_path = os.path.splitext(os.path.basename(item))
            self.__base2path[base_path[0]] = item

        self.__build_interface()
        self.__build_export_maps()
        self.__populate()

    def __build_export_maps(self):
        """
        Builds the maps used to map options. The __optmap maps an internal
        Type Identifier to:

        (Document Description, Exporter Class, Register/Group/Project)

        The __mapopt maps the Document Description to:

        (Type Identifier, Exporter Class, Register/Group/Project)

        """
        self.__optmap = {}
        self.__mapopt = {}
        for level, export_list in enumerate([EXPORTERS, GRP_EXPORTERS, PRJ_EXPORTERS]):
            for item in export_list:
                value = "{0} ({1})".format(item.type[0], item.type[1])
                self.__optmap[item.id] = (value, item.obj_class, level)
                self.__mapopt[value] = (item.id, item.obj_class, level)

    def __build_interface(self):
        """
        Builds the interface from the glade description, connects the signals,
        and creates the data models to load into the system.
        """
        self.__builder = gtk.Builder()
        bfile = os.path.join(INSTALL_PATH, "ui", "build.ui")
        self.__builder.add_from_file(bfile)
        self.__build_top = self.__builder.get_object('build')
        self.__build_list = self.__builder.get_object('buildlist')
        self.__builder.connect_signals(self)
        self.__add_columns()
        self.__model = gtk.ListStore(bool, str, str, str, object, object, int)
        self.__build_list.set_model(self.__model)
        self.configure(self.__build_top)
        self.__build_top.show_all()

    def __add_item_to_list(self, full_path, option, dest):
        """
        Adds the item to the list view.
        """
        if self.__optmap[option][OPTMAP_REGISTER_SET] == LEVEL_BLOCK:
            self.__add_dbase_item_to_list(full_path, option, dest)
        elif self.__optmap[option][OPTMAP_REGISTER_SET] == LEVEL_GROUP:
            self.__add_group_item_to_list(full_path, option, dest)
        else:
            self.__add_prj_item_to_list(option, dest)

    def __add_prj_item_to_list(self, option, dest):
        """
        Adds a target to the list that is dependent on the entire project.
        This is similar to adding a target that is dependent on a single
        database, except we have to compare dates on all files in the project,
        not just a single file.
        """
        local_dest = os.path.join(os.path.dirname(self.__prj.path), dest)

        register_set = self.__prj.get_register_set()
        mod = file_needs_rebuilt(local_dest, self.__dbmap, register_set)
        self.__modlist.append(mod)
        (fmt, cls, dbtype) = self.__optmap[option]
        self.__model.append(row=[mod, "<project>", fmt, dest, cls, None, 2])

    def __add_dbase_item_to_list(self, dbase_rel_path, option, dest):
        """
        Adds the specific item to the build list. We have to check to see
        if the file needs rebuilt, depending on modification flags a file
        timestamps.
        """
        dbase_full_path = os.path.join(os.path.dirname(self.__prj.path),
                                       dbase_rel_path)
        (base, db_file_mtime) = base_and_modtime(dbase_full_path)
        local_dest = os.path.join(os.path.dirname(self.__prj.path), dest)

        mod = file_needs_rebuilt(local_dest, self.__dbmap, [dbase_full_path])
        self.__modlist.append(mod)
        (fmt, cls, rpttype) = self.__optmap[option]
        dbase = self.__dbmap[base][DB_MAP_DBASE].db
        self.__model.append(row=(mod, base, fmt, dest, cls, dbase, 0))

    def __add_group_item_to_list(self, group_name, option, dest):
        """
        Adds the specific item to the build list. We have to check to see
        if the file needs rebuilt, depending on modification flags a file
        timestamps.
        """
        #mod = file_needs_rebuilt(local_dest, self.__dbmap, [dbase_full_path])
        mod = True
        self.__modlist.append(mod)
        (fmt, cls, rpttype) = self.__optmap[option]
        self.__model.append(row=(mod, group_name, fmt, dest, cls, None, 1))

    def __populate(self):
        """
        Populate the display with the items stored in the project's
        export list.
        """
        for item in self.__prj.get_register_set():
            path = os.path.relpath(item, os.path.dirname(self.__prj.path))
            for (option, dest) in self.__prj.get_exports(path):
                try:
                    self.__add_dbase_item_to_list(path, option, dest)
                except KeyError:
                    pass

        for group_data in self.__prj.get_grouping_list():
            for grp_type, grp_dest in self.__prj.get_group_exports(group_data.name):
                self.__add_group_item_to_list("%s (group)" % group_data.name,
                                              grp_type, grp_dest)

        for (option, dest) in self.__prj.get_project_exports():
            try:
                self.__add_prj_item_to_list(option, dest)
            except KeyError as msg:
                print str(msg)
                pass

    def toggle_callback(self, cell, path, source):
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """
        self.__model[path][MDL_MOD] = not self.__model[path][MDL_MOD]

    def register_set_callback(self, cell, path, node, col):
        """
        Called when the register set is changed. The combo_box_model is
        attached to the cell that caused the change (on the 'model'
        property). The data is then copied out of the combo_box_model and
        into the database.
        """
        combo_box_model = cell.get_property('model')
        self.__model[path][MDL_DBASE] = combo_box_model[node][1]
        self.__model[path][MDL_BASE] = combo_box_model[node][0]

    def format_callback(self, cell, path, node, col):
        """
        Called when the format is changed. The combo_box_model is
        attached to the cell that caused the change (on the 'model'
        property). The data is then copied out of the combo_box_model and
        into the database.
        """
        combo_box_model = cell.get_property('model')
        self.__model[path][MDL_CLASS] = combo_box_model[node][1]
        self.__model[path][MDL_FMT] = combo_box_model[node][0]

    def __add_columns(self):
        """
        Adds the columns to the builder list.
        """
        column = ToggleColumn("Build", self.toggle_callback, MDL_MOD)
        self.__build_list.append_column(column)

        column = EditableColumn("RegisterSet", None, MDL_BASE)
        column.set_min_width(125)
        column.set_sort_column_id(MDL_BASE)
        self.__build_list.append_column(column)

        column = EditableColumn("Format", None, MDL_FMT)
        column.set_min_width(175)
        column.set_sort_column_id(MDL_FMT)
        self.__build_list.append_column(column)

        column = EditableColumn("Destination", None, MDL_DEST)
        column.set_min_width(250)
        column.set_sort_column_id(MDL_DEST)
        self.__build_list.append_column(column)

    def on_buildlist_button_press_event(self, obj, event):
        """
        Callback the pops open the menu if the right mouse button
        is clicked (event.button == 3, in GTK terms)
        """
        if event.button == 3:
            menu = self.__builder.get_object("menu")
            menu.popup(None, None, None, 1, 0)

    def on_select_all_activate(self, obj):
        """
        Called with the menu item has been selected to select all
        targets for rebuild. Simply sets all the modified flags to True.
        """
        for item in self.__model:
            item[MDL_MOD] = True

    def on_unselect_all_activate(self, obj):
        """
        Called with the menu item has been selected to unselect all
        targets for rebuild. Simply sets all the modified flags to False.
        """
        for item in self.__model:
            item[MDL_MOD] = False

    def on_select_ood_activate(self, obj):
        """
        Called when the menu item has been selected to select all out of
        data targets for rebuild. We have already determined this from
        the original load (we don't dynamically recalulate the ist). So
        we just march down the list and set the appropriate modified flags.
        """
        for (count, item) in enumerate(self.__model):
            item[MDL_MOD] = self.__modlist[count]

    def on_run_build_clicked(self, obj):
        """
        Called when the build button is pressed.
        """
        for item in [item for item in self.__model if item[MDL_MOD]]:
            writer_class = item[MDL_CLASS]
            dbase = item[MDL_DBASE]
            rtype = item[MDL_TYPE]
            dest = os.path.abspath(
                os.path.join(os.path.dirname(self.__prj.path), item[MDL_DEST]))

            try:
                if rtype == 0:
                    gen = writer_class(self.__prj, dbase)
                elif rtype == 1:
                    db_list = [i[DB_MAP_DBASE].db
                               for i in self.__dbmap.values()]
                    grp = item[MDL_BASE].split()[0]
                    gen = writer_class(self.__prj, grp, db_list)
                else:
                    db_list = [i[DB_MAP_DBASE].db
                               for i in self.__dbmap.values()]
                    gen = writer_class(self.__prj, db_list)
                gen.write(dest)
                item[MDL_MOD] = False
            except IOError as msg:
                ErrorMsg("Error running exporter", str(msg))

    def on_add_build_clicked(self, obj):
        """
        Brings up the export assistant, to help the user build a new rule
        to add to the builder.
        """
        optlist = [(exp_type_fmt(item.type), 0, item.extension) for item in EXPORTERS] + \
            [(exp_type_fmt(item.type), 1, item.extension) for item in GRP_EXPORTERS] + \
            [(exp_type_fmt(item.type), 2, item.extension) for item in PRJ_EXPORTERS]
        reglist = [os.path.splitext(os.path.basename(i))[0]
                   for i in self.__prj.get_register_set()]
        groups = [group.name for group in self.__prj.get_grouping_list()]
        ExportAssistant(self.__prj.short_name, optlist, reglist, groups,
                        self.add_callback)

    def add_callback(self, filename, export_format, register_set, group):
        """
        Called when a item has been added to the builder, and is used
        to add the new item to the list view.
        """
        option = self.__mapopt[export_format][MAPOPT_ID]

        if self.__mapopt[export_format][MAPOPT_REGISTER_SET] == LEVEL_BLOCK:
            register_path = self.__base2path[register_set]
            self.__prj.add_to_export_list(register_path, option, filename)
            self.__add_item_to_list(register_path, option, filename)
        elif self.__mapopt[export_format][MAPOPT_REGISTER_SET] == LEVEL_GROUP:
            self.__prj.add_to_group_export_list(group, option, filename)
            register_path = "%s (group)" % group
            self.__add_item_to_list(register_path, option, filename)
        else:
            register_path = '<project>'
            self.__prj.add_to_project_export_list(option, filename)
            self.__add_item_to_list(register_path, option, filename)

    def on_remove_build_clicked(self, obj):
        """
        Called when the user had opted to delete an existing rule.
        Deletes the selected rule.
        """
        sel = self.__build_list.get_selection().get_selected()
        data = sel[0][sel[1]]

        option = self.__mapopt[data[MDL_FMT]][MAPOPT_ID]
        filename = data[MDL_DEST]
        if data[MDL_DBASE]:
            register_path = self.__base2path[data[MDL_BASE]]
            self.__prj.remove_from_export_list(register_path, option, filename)
        else:
            self.__prj.remove_from_project_export_list(option, filename)
        self.__model.remove(sel[1])

    def on_close_clicked(self, obj):
        """
        Closes the builder.
        """
        self.__build_top.destroy()


def base_and_modtime(dbase_full_path):
    """
    Returns the base name of the register set, along with the modification
    time of the associated file.
    """
    base = os.path.splitext(os.path.basename(dbase_full_path))[0]
    try:
        db_file_mtime = os.path.getmtime(dbase_full_path)
        return (base, db_file_mtime)
    except OSError as msg:
        ErrorMsg("Error accessing file", str(msg))
        db_file_mtime = os.path.getmtime(dbase_full_path)
        return (base, 0)

def file_needs_rebuilt(local_dest, dbmap, db_paths):
    """
    Returns True if the associated database has been modified since the
    local_dest file has been last modified. If the destination file does
    not exist, the destination file is older than the saved database file,
    or if the database has been modified in internal memory, we consider
    it to need to be rebuilt.
    """
    mod = False
    if not os.path.exists(local_dest):
        mod = True
    else:
        for full_path in db_paths:
            (base, db_file_mtime) = base_and_modtime(full_path)
            dest_mtime = os.path.getmtime(local_dest)
            if db_file_mtime > dest_mtime or dbmap[base][DB_MAP_MODIFIED]:
                mod = True
    return mod

def exp_type_fmt(item):
    return "{0} ({1})".format(item[0], item[1])
