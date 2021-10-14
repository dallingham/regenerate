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
from typing import Tuple, Dict, List, NamedTuple
from pathlib import Path

from gi.repository import Gtk, Pango
from regenerate.settings.paths import INSTALL_PATH
from regenerate.db import RegProject, RegisterDb, ExportData
from regenerate.writers import (
    ExportInfo,
    BaseWriter,
    EXPORTERS,
    PRJ_EXPORTERS,
    GRP_EXPORTERS,
    ProjectType,
)

from .base_window import BaseWindow
from .columns import EditableColumn, ToggleColumn
from .error_dialogs import ErrorMsg
from .rule_builder import RuleBuilder

from .enums import (
    Level,
    BuildCol,
)


class LocalExportData(NamedTuple):
    "Holds the information for exporters"

    name: str
    cls: BaseWriter
    level: Level


class Build(BaseWindow):
    """
    Builder interface. Allows the user to control exporters, building rules
    as to what should be built.
    """

    def __init__(self, project: RegProject):
        super().__init__()

        self.__prj = project
        self.__modlist: List[bool] = []
        self.__mapopt: Dict[str, LocalExportData] = {}
        self.__optmap: Dict[str, LocalExportData] = {}

        self.__base2path = {}
        for item in self.__prj.get_register_set():
            base_path = os.path.splitext(os.path.basename(item))
            self.__base2path[base_path[0]] = item

        self.__build_interface(None)
        self.__build_export_maps()
        self.__populate()

    def __build_export_maps(self) -> None:
        """
        Builds the maps used to map options. The __optmap maps an internal
        Type Identifier to:

        (Document Description, Exporter Class, Register/Block/Project)

        The __mapopt maps the Document Description to:

        (Type Identifier, Exporter Class, Register/Block/Project)

        """
        self.__optmap = {}
        for level, export_list in [
            (Level.REGSET, EXPORTERS),
            (Level.BLOCK, GRP_EXPORTERS),
            (Level.PROJECT, PRJ_EXPORTERS),
        ]:
            for item in export_list:
                value = item.description
                self.__optmap[item.writer_id] = LocalExportData(
                    value, item.obj_class, level
                )
                self.__mapopt[value] = LocalExportData(
                    item.writer_id, item.obj_class, level
                )

    def __build_interface(self, parent: Gtk.Window) -> None:
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
        self.__model = Gtk.ListStore(
            bool, str, str, str, str, object, object, int
        )
        self.__build_list.set_model(self.__model)
        self.configure(self.__build_top)
        self.__build_top.set_transient_for(parent)
        self.__build_top.show_all()

    def __add_item_to_list(
        self, full_path: str, exporter: str, dest: str
    ) -> None:
        """
        Adds the item to the list view.
        """
        if self.__optmap[exporter].level == Level.REGSET:
            self.__add_dbase_item_to_list(full_path, exporter, dest)
        elif self.__optmap[exporter].level == Level.BLOCK:
            self.__add_group_item_to_list(full_path, exporter, dest)
        else:
            self.__add_prj_item_to_list(exporter, dest)

    def __add_prj_item_to_list(self, exporter: str, dest: str) -> None:
        """
        Adds a target to the list that is dependent on the entire project.
        This is similar to adding a target that is dependent on a single
        database, except we have to compare dates on all files in the project,
        not just a single file.
        """
        local_dest = os.path.join(os.path.dirname(self.__prj.path), dest)

        mod = file_needs_rebuilt(local_dest, self.__prj, self.__prj.regsets)
        self.__modlist.append(mod)
        info = self.__optmap[exporter]
        self.__model.append(
            row=[
                mod,
                "Project",
                "",
                info.name,
                dest,
                info.cls,
                None,
                ProjectType.PROJECT,
            ]
        )

    def __add_dbase_item_to_list(
        self, regset_name: str, exporter: str, dest: str
    ) -> None:
        """
        Adds the specific item to the build list. We have to check to see
        if the file needs rebuilt, depending on modification flags a file
        timestamps.
        """
        regset = self.__prj.regsets[regset_name]
        local_dest = os.path.join(os.path.dirname(self.__prj.path), dest)
        mod = file_needs_rebuilt(local_dest, self.__prj, self.__prj.regsets)
        self.__modlist.append(mod)
        info = self.__optmap[exporter]
        rel_dest = dest

        self.__model.append(
            row=(
                mod,
                "Register Set",
                regset.name,
                info.name,
                rel_dest,
                info.cls,
                regset,
                ProjectType.REGSET,
            )
        )

    def __add_group_item_to_list(
        self, blkid: str, exporter: str, dest: str
    ) -> None:
        """
        Adds the specific item to the build list. We have to check to see
        if the file needs rebuilt, depending on modification flags a file
        timestamps.
        """
        # mod = file_needs_rebuilt(local_dest, self.__dbmap, [dbase_full_path])
        mod = True
        self.__modlist.append(mod)
        info = self.__optmap[exporter]
        block = self.__prj.blocks[blkid]
        self.__model.append(
            row=(
                mod,
                "Block",
                block.name,
                info.name,
                dest,
                info.cls,
                block,
                ProjectType.BLOCK,
            )
        )

    def __populate(self) -> None:
        """
        Populate the display with the items stored in the project's
        export list.
        """
        for item in self.__prj.regsets:
            path_str = str(self.__prj.regsets[item].filename)

            for export_data in self.__prj.get_exports(path_str):
                try:
                    self.__add_dbase_item_to_list(
                        item,
                        export_data.exporter,
                        str(export_data.target),
                    )
                except KeyError:
                    pass

        for block in self.__prj.blocks.values():
            for i, export_data in enumerate(block.exports):
                self.__add_group_item_to_list(
                    block.uuid,
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

    def toggle_callback(
        self, _cell: Gtk.CellRendererToggle, path: str, _source: BuildCol
    ) -> None:
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """
        self.__model[path][BuildCol.MODIFIED] = not self.__model[path][
            BuildCol.MODIFIED
        ]

    # def register_set_callback(self, cell, path, node, _col):
    #     """
    #     Called when the register set is changed. The combo_box_model is
    #     attached to the cell that caused the change (on the 'model'
    #     property). The data is then copied out of the combo_box_model and
    #     into the database.
    #     """
    #     print(type(cell), type(path), type(node), type(_col))

    #     combo_box_model = cell.get_property("model")
    #     self.__model[path][BuildCol.DBASE] = combo_box_model[node][1]
    #     self.__model[path][BuildCol.BASE] = combo_box_model[node][0]

    # def format_callback(self, cell, path, node, _col):
    #     """
    #     Called when the format is changed. The combo_box_model is
    #     attached to the cell that caused the change (on the 'model'
    #     property). The data is then copied out of the combo_box_model and
    #     into the database.
    #     """
    #     print(type(cell), type(path), type(node), type(_col))
    #     combo_box_model = cell.get_property("model")
    #     self.__model[path][BuildCol.CLASS] = combo_box_model[node][1]
    #     self.__model[path][BuildCol.FORMAT] = combo_box_model[node][0]

    def __add_columns(self) -> None:
        """
        Adds the columns to the builder list.
        """
        column = ToggleColumn("Build", self.toggle_callback, BuildCol.MODIFIED)
        self.__build_list.append_column(column)

        column = EditableColumn("Type", None, BuildCol.TYPE_STR)
        column.set_min_width(120)
        column.set_sort_column_id(BuildCol.TYPE_STR)
        self.__build_list.append_column(column)

        column = EditableColumn("Source", None, BuildCol.BASE)
        column.set_min_width(150)
        column.set_sort_column_id(BuildCol.BASE)
        self.__build_list.append_column(column)

        column = EditableColumn("Format", None, BuildCol.FORMAT)
        column.set_min_width(200)
        column.set_sort_column_id(BuildCol.FORMAT)
        self.__build_list.append_column(column)

        column = EditableColumn(
            "Destination",
            None,
            BuildCol.DEST,
            ellipsize=Pango.EllipsizeMode.START,
        )
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

    def on_select_all_activate(self, _obj) -> None:
        """
        Called with the menu item has been selected to select all
        targets for rebuild. Simply sets all the modified flags to True.
        """
        for item in self.__model:
            item[BuildCol.MODIFIED] = True

    def on_unselect_all_activate(self, _obj) -> None:
        """
        Called with the menu item has been selected to unselect all
        targets for rebuild. Simply sets all the modified flags to False.
        """
        for item in self.__model:
            item[BuildCol.MODIFIED] = False

    def on_select_ood_activate(self, _obj) -> None:
        """
        Called when the menu item has been selected to select all out of
        data targets for rebuild. We have already determined this from
        the original load (we don't dynamically recalulate the ist). So
        we just march down the list and set the appropriate modified flags.
        """
        for (count, item) in enumerate(self.__model):
            item[BuildCol.MODIFIED] = self.__modlist[count]

    def on_run_build_clicked(self, _obj) -> None:
        """
        Called when the build button is pressed.
        """
        for item in [item for item in self.__model if item[BuildCol.MODIFIED]]:
            writer_class = item[BuildCol.CLASS]
            dbase = item[BuildCol.DBASE]
            rtype = item[BuildCol.TYPE]

            dest = Path(item[BuildCol.DEST]).resolve()

            try:
                if rtype == ProjectType.REGSET:
                    gen = writer_class(self.__prj, dbase)
                elif rtype == ProjectType.BLOCK:
                    db_list = self.__prj.regsets.values()
                    gen = writer_class(self.__prj, dbase)
                else:
                    db_list = self.__prj.regsets.values()
                    gen = writer_class(self.__prj)
                gen.write(dest)
                item[BuildCol.MODIFIED] = False
            except IOError as msg:
                ErrorMsg("Error running exporter", str(msg))

    def on_add_build_clicked(self, _obj: Gtk.Button) -> None:
        """
        Brings up the export assistant, to help the user build a new rule
        to add to the builder.
        """

        rlist = [
            (item.description, ProjectType.REGSET, item.file_extension)
            for item in EXPORTERS
        ]
        blist = [
            (item.description, ProjectType.BLOCK, item.file_extension)
            for item in GRP_EXPORTERS
        ]
        plist = [
            (item.description, ProjectType.PROJECT, item.file_extension)
            for item in PRJ_EXPORTERS
        ]

        optlist = rlist + blist + plist

        # reglist = [(i.name, i.uuid) for i in self.__prj.regsets.values()]

        # groups = [
        #     (group.name, group.uuid) for group in self.__prj.blocks.values()
        # ]

        assistant = RuleBuilder(
            self.__prj,
            self.add_callback,
            # self.__build_top,
        )
        assistant.show_all()

    def add_callback(
        self, filename: str, export_info: ExportInfo, uuid: str, project_type: ProjectType
    ) -> None:
        """
        Called when a item has been added to the builder, and is used
        to add the new item to the list view.
        """

        exporter = export_info.writer_id
        if project_type == ProjectType.REGSET:
            self.__prj.regsets[uuid].exports.append(
                ExportData(exporter, filename)
            )
            self.__prj.regsets[uuid].modified = True
            self.__add_item_to_list(uuid, exporter, filename)
        elif project_type == ProjectType.BLOCK:
            block = self.__prj.blocks[uuid]
            self.__add_item_to_list(uuid, exporter, filename)
            block.exports.append(ExportData(exporter, filename))
            block.modified = True
        else:
            self.__prj.add_to_project_export_list(exporter, filename)
            self.__add_item_to_list(uuid, exporter, filename)

    def on_remove_build_clicked(self, _obj: Gtk.Button):
        """
        Called when the user had opted to delete an existing rule.
        Deletes the selected rule.
        """
        store, node = self.__build_list.get_selection().get_selected()
        if node is None:
            return

        data = store[node]

        fmt = data[BuildCol.FORMAT]
        exporter = self.__mapopt[fmt].name
        filename = data[BuildCol.DEST]
        dbase = data[BuildCol.DBASE]
        if dbase:
            dbase.exports = [
                export
                for export in dbase.exports
                if export.exporter != exporter and export.target != filename
            ]
        else:
            self.__prj.remove_from_project_export_list(exporter, filename)
        self.__model.remove(node)

    def on_close_clicked(self, _obj: Gtk.Button):
        """
        Closes the builder.
        """
        self.__build_top.destroy()


def base_and_modtime(dbase_full_path: Path):
    """
    Returns the base name of the register set, along with the modification
    time of the associated file.
    """
    base = dbase_full_path.stem
    try:
        db_file_mtime = os.path.getmtime(dbase_full_path)
        return (base, db_file_mtime)
    except OSError:
        return (base, 0)


def file_needs_rebuilt(
    local_dest: str, prj: RegProject, db_paths: Dict[str, RegisterDb]
) -> bool:
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
        for regset_name in db_paths:
            regset = prj.regsets[regset_name]
            (_, db_file_mtime) = base_and_modtime(regset.filename)
            dest_mtime = os.path.getmtime(local_dest)
            try:
                if (
                    db_file_mtime > dest_mtime
                    or prj.regsets[regset.name].modified
                ):
                    mod = True
            except:
                pass
    return mod


def exp_type_fmt(item: Tuple[str, str]) -> str:
    "Export format type"

    return f"{item[1]}"
