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
from pathlib import Path

from gi.repository import Gtk
from regenerate.settings.paths import INSTALL_PATH
from regenerate.db.export import ExportData
from regenerate.ui.base_window import BaseWindow
from regenerate.ui.columns import EditableColumn, ToggleColumn
from regenerate.ui.error_dialogs import ErrorMsg
from regenerate.ui.export_assistant import ExportAssistant
from regenerate.ui.enums import (
    Level,
    BuildCol,
    MapOpt,
    OptMap,
    DbMap,
)
from regenerate.writers import EXPORTERS, PRJ_EXPORTERS, GRP_EXPORTERS


class Build(BaseWindow):
    """
    Builder interface. Allows the user to control exporters, building rules
    as to what should be built.
    """

    def __init__(self, project):
        super().__init__()

        self.__prj = project
        self.__modlist = []

        self.__base2path = {}
        for item in self.__prj.get_register_set():
            base_path = os.path.splitext(os.path.basename(item))
            self.__base2path[base_path[0]] = item

        self.__build_interface(None)
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
        for level, export_list in enumerate(
            [EXPORTERS, GRP_EXPORTERS, PRJ_EXPORTERS]
        ):
            for item in export_list:
                value = f"{item.type[0]} ({item.type[1]})"
                self.__optmap[item.id] = (value, item.obj_class, level)
                self.__mapopt[value] = (item.id, item.obj_class, level)

    def __build_interface(self, parent):
        """
        Builds the interface from the glade description, connects the signals,
        and creates the data models to load into the system.
        """
        self.__builder = Gtk.Builder()
        bfile = os.path.join(INSTALL_PATH, "ui", "build.ui")
        self.__builder.add_from_file(bfile)
        self.__build_top = self.__builder.get_object("build")
        self.__build_list = self.__builder.get_object("buildlist")
        self.__builder.connect_signals(self)
        self.__add_columns()
        self.__model = Gtk.ListStore(bool, str, str, str, object, object, int)
        self.__build_list.set_model(self.__model)
        self.configure(self.__build_top)
        self.__build_top.set_transient_for(parent)
        self.__build_top.show_all()

    def __add_item_to_list(self, full_path, exporter, dest):
        """
        Adds the item to the list view.
        """
        if self.__optmap[exporter][OptMap.REGISTER_SET] == Level.BLOCK:
            self.__add_dbase_item_to_list(full_path, exporter, dest)
        elif self.__optmap[exporter][OptMap.REGISTER_SET] == Level.GROUP:
            self.__add_group_item_to_list(full_path, exporter, dest)
        else:
            self.__add_prj_item_to_list(exporter, dest)

    def __add_prj_item_to_list(self, exporter, dest):
        """
        Adds a target to the list that is dependent on the entire project.
        This is similar to adding a target that is dependent on a single
        database, except we have to compare dates on all files in the project,
        not just a single file.
        """
        local_dest = os.path.join(os.path.dirname(self.__prj.path), dest)

        register_set = self.__prj.get_register_set()
        mod = file_needs_rebuilt(local_dest, self.__prj, register_set)
        self.__modlist.append(mod)
        (fmt, cls, _) = self.__optmap[exporter]
        self.__model.append(row=[mod, "<project>", fmt, dest, cls, None, 2])

    def __add_dbase_item_to_list(self, dbase_rel_path, exporter, dest):
        """
        Adds the specific item to the build list. We have to check to see
        if the file needs rebuilt, depending on modification flags a file
        timestamps.
        """

        dbase_full_path = os.path.join(
            os.path.dirname(self.__prj.path), dbase_rel_path
        )
        (base, _) = base_and_modtime(dbase_full_path)
        local_dest = os.path.join(os.path.dirname(self.__prj.path), dest)

        mod = file_needs_rebuilt(local_dest, self.__prj, [dbase_full_path])
        self.__modlist.append(mod)
        (fmt, cls, _) = self.__optmap[exporter]
        dbase = self.__prj.regsets[base]
        rel_dest = dest

        self.__model.append(row=(mod, base, fmt, rel_dest, cls, dbase, 0))

    def __add_group_item_to_list(self, group_name, exporter, dest):
        """
        Adds the specific item to the build list. We have to check to see
        if the file needs rebuilt, depending on modification flags a file
        timestamps.
        """
        # mod = file_needs_rebuilt(local_dest, self.__dbmap, [dbase_full_path])
        mod = True
        self.__modlist.append(mod)
        (fmt, cls, _) = self.__optmap[exporter]
        self.__model.append(row=(mod, group_name, fmt, dest, cls, None, 1))

    def __populate(self):
        """
        Populate the display with the items stored in the project's
        export list.
        """
        for item in self.__prj.get_register_set():
            directory = Path(self.__prj.path).parent.resolve()
            path = directory / item
            path_str = str(path.resolve())

            for export_data in self.__prj.get_exports(path_str):
                try:
                    self.__add_dbase_item_to_list(
                        path_str, export_data.exporter, str(export_data.target)
                    )
                except KeyError:
                    pass

        for group_data in self.__prj.block_insts:
            for export_data in self.__prj.get_group_exports(
                group_data.inst_name
            ):
                self.__add_group_item_to_list(
                    "%s (group)" % group_data.int_name,
                    export_data.exporter,
                    export_data.target,
                )

        for export_data in self.__prj.get_project_exports():
            try:
                self.__add_prj_item_to_list(
                    export_data.exporter, export_data.target
                )
            except KeyError:
                pass

    def toggle_callback(self, _cell, path, _source):
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """
        self.__model[path][BuildCol.MODIFIED] = not self.__model[path][
            BuildCol.MODIFIED
        ]

    def register_set_callback(self, cell, path, node, _col):
        """
        Called when the register set is changed. The combo_box_model is
        attached to the cell that caused the change (on the 'model'
        property). The data is then copied out of the combo_box_model and
        into the database.
        """
        combo_box_model = cell.get_property("model")
        self.__model[path][BuildCol.DBASE] = combo_box_model[node][1]
        self.__model[path][BuildCol.BASE] = combo_box_model[node][0]

    def format_callback(self, cell, path, node, _col):
        """
        Called when the format is changed. The combo_box_model is
        attached to the cell that caused the change (on the 'model'
        property). The data is then copied out of the combo_box_model and
        into the database.
        """
        combo_box_model = cell.get_property("model")
        self.__model[path][BuildCol.CLASS] = combo_box_model[node][1]
        self.__model[path][BuildCol.FORMAT] = combo_box_model[node][0]

    def __add_columns(self):
        """
        Adds the columns to the builder list.
        """
        column = ToggleColumn("Build", self.toggle_callback, BuildCol.MODIFIED)
        self.__build_list.append_column(column)

        column = EditableColumn("RegisterSet", None, BuildCol.BASE)
        column.set_min_width(125)
        column.set_sort_column_id(BuildCol.BASE)
        self.__build_list.append_column(column)

        column = EditableColumn("Format", None, BuildCol.FORMAT)
        column.set_min_width(175)
        column.set_sort_column_id(BuildCol.FORMAT)
        self.__build_list.append_column(column)

        column = EditableColumn("Destination", None, BuildCol.DEST)
        column.set_min_width(250)
        column.set_sort_column_id(BuildCol.DEST)
        self.__build_list.append_column(column)

    def on_buildlist_button_press_event(self, _obj, event):
        """
        Callback the pops open the menu if the right mouse button
        is clicked (event.button == 3, in GTK terms)
        """
        if event.button == 3:
            menu = self.__builder.get_object("menu")
            menu.popup(None, None, None, 1, 0, Gtk.get_current_event_time())

    def on_select_all_activate(self, _obj):
        """
        Called with the menu item has been selected to select all
        targets for rebuild. Simply sets all the modified flags to True.
        """
        for item in self.__model:
            item[BuildCol.MODIFIED] = True

    def on_unselect_all_activate(self, _obj):
        """
        Called with the menu item has been selected to unselect all
        targets for rebuild. Simply sets all the modified flags to False.
        """
        for item in self.__model:
            item[BuildCol.MODIFIED] = False

    def on_select_ood_activate(self, _obj):
        """
        Called when the menu item has been selected to select all out of
        data targets for rebuild. We have already determined this from
        the original load (we don't dynamically recalulate the ist). So
        we just march down the list and set the appropriate modified flags.
        """
        for (count, item) in enumerate(self.__model):
            item[BuildCol.MODIFIED] = self.__modlist[count]

    def on_run_build_clicked(self, _obj):
        """
        Called when the build button is pressed.
        """
        for item in [item for item in self.__model if item[BuildCol.MODIFIED]]:
            writer_class = item[BuildCol.CLASS]
            dbase = item[BuildCol.DBASE]
            rtype = item[BuildCol.TYPE]

            dest = str(Path(item[BuildCol.DEST]).resolve())

            try:
                if rtype == 0:
                    gen = writer_class(self.__prj, dbase)
                elif rtype == 1:
                    db_list = self.__prj.regsets.values()
                    grp = item[BuildCol.BASE].split()[0]
                    gen = writer_class(self.__prj, grp, db_list)
                else:
                    db_list = self.__prj.regsets.values()
                    gen = writer_class(self.__prj, db_list)
                gen.write(dest)
                item[BuildCol.MODIFIED] = False
            except IOError as msg:
                ErrorMsg("Error running exporter", str(msg))

    def on_add_build_clicked(self, _obj):
        """
        Brings up the export assistant, to help the user build a new rule
        to add to the builder.
        """
        optlist = (
            [
                (exp_type_fmt(item.type), 0, item.extension)
                for item in EXPORTERS
            ]
            + [
                (exp_type_fmt(item.type), 1, item.extension)
                for item in GRP_EXPORTERS
            ]
            + [
                (exp_type_fmt(item.type), 2, item.extension)
                for item in PRJ_EXPORTERS
            ]
        )

        reglist = [
            os.path.splitext(os.path.basename(i))[0]
            for i in self.__prj.get_register_set()
        ]

        groups = [group.inst_name for group in self.__prj.block_insts]

        ExportAssistant(
            self.__prj.short_name,
            optlist,
            reglist,
            groups,
            self.add_callback,
            self.__build_top,
        )

    def add_callback(self, filename, export_format, register_set, group):
        """
        Called when a item has been added to the builder, and is used
        to add the new item to the list view.
        """
        exporter = self.__mapopt[export_format][MapOpt.ID]

        if self.__mapopt[export_format][MapOpt.REGISTER_SET] == Level.BLOCK:
            register_path = self.__base2path[register_set]
            self.__prj.regsets[register_set].regset.exports.append(
                ExportData(exporter, filename)
            )
            self.__prj.regsets[register_set].modified = True
            self.__add_item_to_list(register_path, exporter, filename)
        elif self.__mapopt[export_format][MapOpt.REGISTER_SET] == Level.GROUP:
            self.__prj.add_to_group_export_list(group, exporter, filename)
            register_path = f"{group} (group)"
            self.__add_item_to_list(register_path, exporter, filename)
        else:
            register_path = "<project>"
            self.__prj.add_to_project_export_list(exporter, filename)
            self.__add_item_to_list(register_path, exporter, filename)

    def on_remove_build_clicked(self, _obj):
        """
        Called when the user had opted to delete an existing rule.
        Deletes the selected rule.
        """
        sel = self.__build_list.get_selection().get_selected()
        data = sel[0][sel[1]]

        exporter = self.__mapopt[data[BuildCol.FORMAT]][MapOpt.ID]
        filename = data[BuildCol.DEST]
        if data[BuildCol.DBASE]:
            register_path = self.__base2path[data[BuildCol.BASE]]
            self.__prj.remove_from_export_list(
                register_path, exporter, filename
            )
        else:
            self.__prj.remove_from_project_export_list(exporter, filename)
        self.__model.remove(sel[1])

    def on_close_clicked(self, _obj):
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


def file_needs_rebuilt(local_dest, prj, db_paths):
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
            if db_file_mtime > dest_mtime or prj.regsets[base].modified:
                mod = True
    return mod


def exp_type_fmt(item):
    return f"{item[0]} ({item[1]})"
