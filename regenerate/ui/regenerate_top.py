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
regenerate

   regenerate is a program for managing the registers in the design. It allows
   you to build a database describing the registers, which can then be used
   to generate documentation, Verilog RTL descriptions, and support files.

"""

import xml
import os
from pathlib import Path

from gi.repository import Gtk, GdkPixbuf, Gdk
from regenerate import PROGRAM_VERSION, PROGRAM_NAME
from regenerate.db import (
    RegisterDb,
    RegProject,
    LOGGER,
    TYPES,
    remove_default_handler,
    ResetType,
    REG_EXT,
    PRJ_EXT,
    OLD_PRJ_EXT,
)
from regenerate.extras.regutils import duplicate_register
from regenerate.importers import IMPORTERS
from regenerate.settings import ini
from regenerate.settings.paths import GLADE_TOP, INSTALL_PATH
from regenerate.ui.addr_edit import AddrMapEdit
from regenerate.ui.addrmap_list import AddrMapList
from regenerate.ui.base_window import BaseWindow
from regenerate.ui.bit_list import BitModel
from regenerate.ui.build import Build
from regenerate.ui.error_dialogs import ErrorMsg, WarnMsg, Question
from regenerate.ui.help_window import HelpWindow
from regenerate.ui.param_overrides import OverridesList
from regenerate.ui.parameter_list import ParameterList
from regenerate.ui.preferences import Preferences
from regenerate.ui.prj_param_list import PrjParameterList

from regenerate.ui.module_tab import ProjectTabs
from regenerate.ui.block_tab import BlockTab
from regenerate.ui.top_level_tab import TopLevelTab
from regenerate.ui.register_tab import RegSetTab

from regenerate.ui.status_logger import StatusHandler


TYPE_ENB = {}
for data_type in TYPES:
    TYPE_ENB[data_type.type] = (data_type.input, data_type.control)

DEF_MIME = "*" + PRJ_EXT


class DbaseStatus:
    """
    Holds the state of a particular database. This includes the database model,
    the list models for the displays, the modified status, and the selected
    rows in the models.
    """

    def __init__(
        self,
        dbase,
        fname,
        name,
        rmodel,
        mdlsort,
        mdlfilter,
        bmodel,
    ):
        self.db = dbase
        self.path = fname
        self.reg_model = rmodel
        self.modelfilter = mdlfilter
        self.modelsort = mdlsort
        self.bit_field_list = bmodel
        self.name = name
        self.modified = False
        self.reg_select = None
        self.bit_select = None
        self.node = None


class MainWindow(BaseWindow):
    """Main window of the Regenerate program"""

    def __init__(self):

        super().__init__()

        self.skip_changes = False
        self.filename = None
        self.modified = False
        self.loading_project = False
        self.active = None
        self.dbase = None
        self.bit_model = None
        self.modelsort = None
        self.instance_model = None
        self.prj = None
        self.dbmap = {}
        self.register = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(GLADE_TOP)

        self.setup_main_window()
        self.build_actions()

        self.top_notebook = self.find_obj("main_notebook")
        self.top_notebook.set_current_page(2)
        self.prj_infobar = self.find_obj("register_infobar")
        self.prj_infobar_label = self.find_obj("register_infobar_label")

        self.setup_project()
        self.setup_recent_menu()

        self.top_level_tab = TopLevelTab(
            self.find_obj,
            self.check_subsystem_addresses,
            self.project_modified,
        )

        self.restore_position_and_size()
        self.top_window.show()
        self.builder.connect_signals(self)
        self.build_import_menu()

    def check_subsystem_addresses(self):
        if check_address_ranges(self.prj, self.dbmap):
            self.set_project_modified()
            return True
        return False

    def setup_main_window(self):
        self.top_window = self.find_obj("regenerate")
        self.configure(self.top_window)
        self.status_obj = self.find_obj("statusbar")
        remove_default_handler()
        LOGGER.addHandler(StatusHandler(self.status_obj))

    def setup_recent_menu(self):
        """Setup the recent files management system"""

        self.recent_manager = Gtk.RecentManager.get_default()
        self.find_obj("file_menu").insert(self.create_recent_menu_item(), 2)
        self.find_obj("open_btn").set_menu(self.create_recent_menu())

    def find_obj(self, name):
        return self.builder.get_object(name)

    def on_addrmap_cursor_changed(self, obj):
        """Called when the row of the treeview changes."""
        mdl, node = obj.get_selection().get_selected()
        btn = self.find_obj("edit_map")
        if node:
            path = mdl.get_path(node)
            btn.set_sensitive(len(path) == 1)
        else:
            btn.set_sensitive(False)

    def setup_project(self):
        self.project_tabs = ProjectTabs(
            self.builder, self.set_project_modified
        )

        self.reginst_tab = RegSetTab(
            self.find_obj,
            self.set_modified,
            self.db_selected,
            self.reg_selected,
            self.field_selected,
        )

        self.block_tab = BlockTab(
            self.find_obj("block_name"),
            self.find_obj("block_description"),
            self.find_obj("block_size"),
            self.find_obj("block_regsets"),
            self.find_obj("block_reg_add"),
            self.find_obj("block_reg_remove"),
            self.find_obj("block_doc_pages"),
            self.find_obj("block_select_list"),
        )

        self.addr_map_list = AddrMapList(
            self.find_obj("address_tree"), self.set_project_modified
        )

        self.parameter_list = ParameterList(
            self.find_obj("parameter_list"), self.set_parameters_modified
        )

        self.prj_parameter_list = PrjParameterList(
            self.find_obj("prj_param_list"), self.set_parameters_modified
        )

        self.overrides_list = OverridesList(
            self.find_obj("prj_subparam_list"), self.set_parameters_modified
        )

    def set_parameters_modified(self):
        self.set_modified()
        self.reglist_obj.set_parameters(self.dbase.get_parameters())
        self.bitfield_obj.set_parameters(self.dbase.get_parameters())

    def set_project_modified(self):
        self.project_modified(True)

    def project_modified(self, value):
        self.set_title(value)
        self.prj.modified = value

    def infobar_reveal(self, prop):
        try:
            self.prj_infobar.set_revealed(prop)
        except AttributeError:
            if prop:
                self.prj_infobar.show()
            else:
                self.prj_infobar.hide()

    def load_project_tab(self):
        self.block_tab.set_project(self.prj)
        self.project_tabs.change_db(self.prj)
        self.addr_map_list.set_project(self.prj)
        if len(self.prj.files) > 0:
            self.infobar_reveal(False)
        else:
            self.infobar_reveal(True)
        self.project_modified(False)

    def on_edit_map_clicked(self, _obj):
        map_name = self.addr_map_list.get_selected()
        if map_name is None:
            return

        current = self.prj.address_maps[map_name].blocks

        new_list = [
            (blk_inst, blk_inst.inst_name in current)
            for blk_inst in self.prj.block_insts
        ]

        dialog = AddrMapEdit(
            map_name,
            new_list,
            self.prj,
            self.top_window,
            self.set_project_modified,
        )

        new_list = dialog.get_list()
        if new_list is not None:
            self.prj.set_address_map_group_list(map_name, new_list)
            self.addr_map_list.set_project(self.prj)
            self.set_project_modified()

    def on_infobar_response(self, obj, _obj2):
        """Called to display the infobar"""
        try:
            obj.set_revealed(False)
        except AttributeError:
            obj.hide()

    def on_addr_map_help_clicked(self, _obj):
        "Display the address map help" ""
        HelpWindow(self.builder, "addr_map_help.rst")

    def on_param_help_clicked(self, _obj):
        """Display the parameter help"""
        HelpWindow(self.builder, "parameter_help.rst")

    def on_prj_param_help_clicked(self, _obj):
        """Display the project parameter help"""
        HelpWindow(self.builder, "prj_parameter_help.rst")

    def on_remove_map_clicked(self, _obj):
        """Remove the selected map with clicked"""
        self.project_modified(True)
        self.addr_map_list.remove_selected()

    def on_add_map_clicked(self, _obj):
        """Add a new map when clicked"""
        self.addr_map_list.add_new_map()

    def on_help_action_activate(self, _obj):
        """Display the help window"""
        HelpWindow(self.builder, "regenerate_help.rst")

    def restore_position_and_size(self):
        "Restore the desired position and size from the user's config file"

        height = int(ini.get("user", "height", 0))
        width = int(ini.get("user", "width", 0))
        vpos = int(ini.get("user", "vpos", 150))
        hpos = int(ini.get("user", "hpos", 140))
        block_hpos = int(ini.get("user", "block_hpos", 140))
        if height and width:
            self.top_window.resize(width, height)
        if vpos:
            self.find_obj("vpaned").set_position(vpos)
        if hpos:
            self.find_obj("hpaned").set_position(hpos)
        if block_hpos:
            self.find_obj("bpaned").set_position(block_hpos)

    def build_group(self, group_name, action_names):
        group = Gtk.ActionGroup(group_name)
        for name in action_names:
            group.add_action(self.find_obj(name))
        group.set_sensitive(False)
        return group

    def build_actions(self):
        """
        Builds the action groups. These groups are used to control which
        buttons/functions are active at any given time. The groups are:

        project_loaded - A project has been loaded.
        reg_selected   - A register is selected, so register operations are
                         valid
        db_selected    - A database is selected, so registers can be added,
                         checked, etc.
        field_selected - A bit field is selected, so a field can be removed
                         or edited.
        """

        prj_acn = [
            "save_project_action",
            "new_set_action",
            "add_set_action",
            "build_action",
            "reg_grouping_action",
            "project_prop_action",
        ]
        reg_acn = [
            "remove_register_action",
            "summary_action",
            "duplicate_register_action",
            "add_bit_action",
        ]
        db_acn = ["add_register_action", "remove_set_action", "import_action"]
        fld_acn = ["remove_bit_action", "edit_bit_action"]

        prj_acn.append("preview_action")

        self.prj_loaded = self.build_group("project_loaded", prj_acn)
        self.reg_selected = self.build_group("reg_selected", reg_acn)
        self.db_selected = self.build_group("database_selected", db_acn)
        self.field_selected = self.build_group("field_selected", fld_acn)

    def on_filter_icon_press(self, obj, icon, event):
        if icon == Gtk.EntryIconPosition.SECONDARY:
            if event.type == Gdk.EventType.BUTTON_PRESS:
                obj.set_text("")
        elif icon == Gtk.EntryIconPositon.PRIMARY:
            if event.type == Gdk.EventType.BUTTON_PRESS:
                menu = self.find_obj("filter_menu")
                menu.popup(
                    None, None, None, 1, 0, Gtk.get_current_event_time()
                )

    def set_search(self, values, obj):
        if obj.get_active():
            self.filter_manage.set_search_fields(values)

    def on_add_param_clicked(self, _obj):
        self.parameter_list.add_clicked()

    def on_add_prj_param_clicked(self, _obj):
        self.prj_parameter_list.add_clicked()

    def on_remove_param_clicked(self, _obj):
        self.parameter_list.remove_clicked()

    def on_prj_remove_param_clicked(self, _obj):
        self.prj_parameter_list.remove_clicked()

    def on_summary_action_activate(self, _obj):
        """Displays the summary window"""
        self.reginst_tab.show_summary()

    def on_build_action_activate(self, obj):

        Build(self.prj)

    def on_user_preferences_activate(self, _obj):
        Preferences(self.top_window)

    def on_delete_instance_clicked(self, _obj):
        self.top_level_tab.delete_blkinst()

    def on_add_instance_clicked(self, _obj):
        self.top_level_tab.blkinst_list.new_instance()
        self.project_modified(True)

    def build_import_menu(self):
        """
        Builds the export menu from the items in writers.IMPORTERS. The export
        menu is extracted from the glade description, the submenu is built,
        and added to the export menu.
        """
        menu = self.find_obj("import_menu")
        submenu = Gtk.Menu()
        menu.set_submenu(submenu)
        for item in IMPORTERS:
            menu_item = Gtk.MenuItem(label=item[1])
            menu_item.connect("activate", self.import_data, item)
            menu_item.show()
            submenu.append(menu_item)
        submenu.show()
        menu.set_submenu(submenu)

    def on_main_notebook_switch_page(self, _obj, _page, _page_num):
        self.block_tab.build_add_regset_menu()

    def on_notebook_switch_page(self, _obj, _page, page_num):
        if page_num == 1:
            self.reginst_tab.update_bit_count()
        if self.reginst_tab.get_selected_register():
            self.reg_selected.set_sensitive(page_num == 0)
        else:
            self.reg_selected.set_sensitive(False)

    def blk_selection_changed(self, obj):
        model, node = obj.get_selected()
        if node:
            block_name = model[node][1]
            self.block_tab.select_group(block_name)

    def selected_reg_changed(self, _obj):
        """
        GTK callback that checks the selected objects, and then enables the
        appropriate buttons on the interface.
        """
        self.reginst_tab.selected_reg_changed(_obj)

    def set_modified(self):
        """
        Indicates that the database has been modified. The modified
        value is set, and the status bar is updated with an appropriate
        message.
        """
        ...
        # if self.active and not self.active.modified and not self.skip_changes:
        #     self.active.modified = True
        #     self.file_modified.set_sensitive(True)

    def clear_modified(self, prj=None):
        """
        Clears the modified tag in the status bar.
        """
        self.modified = False
        # if prj is None:
        #     prj = self.active

    def on_no_sharing_toggled(self, obj):
        self.reginst_tab.on_no_sharing_toggled(obj)

    def on_read_access_toggled(self, obj):
        self.reginst_tab.on_read_access_toggled(obj)

    def on_write_access_toggled(self, obj):
        self.reginst_tab.on_write_access_toggled(obj)

    def on_add_bit_action_activate(self, _obj):
        self.reginst_tab.add_bit()

    def on_edit_field_clicked(self, _obj):
        self.reginst_tab.edit_bit()

    def on_remove_bit_action_activate(self, _obj):
        self.reginst_tab.remove_bit()

    def insert_new_register(self, register):
        if self.top_notebook.get_current_page() == 0:
            self.reglist_obj.add_new_register(register)
            self.dbase.add_register(register)
            self.set_register_warn_flags(register)
            self.set_modified()

    def on_duplicate_register_action_activate(self, _obj):
        """
        Makes a copy of the current register, modifying the address, and
        changing name and token
        """
        reg = self.reginst_tab.get_selected_register()
        if reg:
            reg_copy = duplicate_register(self.dbase, reg)
            self.insert_new_register(reg_copy)
            self.reginst_tab.set_register_warn_flags(reg_copy)

    def create_file_selector(self, title, m_name, m_regex, action, icon):
        """
        Creates a file save selector, using the mime type and regular
        expression to control the selector.
        """
        choose = Gtk.FileChooserDialog(
            title,
            self.top_window,
            action,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                icon,
                Gtk.ResponseType.OK,
            ),
        )

        choose.set_current_folder(os.curdir)
        if m_name:
            mime_filter = Gtk.FileFilter()
            mime_filter.set_name(m_name)
            mime_filter.add_pattern(m_regex)
            choose.add_filter(mime_filter)
        choose.show()
        return choose

    def create_save_selector(self, title, mime_name=None, mime_regex=None):
        """
        Creates a file save selector, using the mime type and regular
        expression to control the selector.
        """
        return self.create_file_selector(
            title,
            mime_name,
            mime_regex,
            Gtk.FileChooserAction.SAVE,
            Gtk.STOCK_SAVE,
        )

    def create_open_selector(self, title, mime_name=None, mime_regex=None):
        """
        Creates a file save selector, using the mime type and regular
        expression to control the selector.
        """
        return self.create_file_selector(
            title,
            mime_name,
            mime_regex,
            Gtk.FileChooserAction.OPEN,
            Gtk.STOCK_OPEN,
        )

    def on_add_register_set_activate(self, _obj):
        self.reginst_tab.add_register_set(_obj)

    def on_remove_register_set_activate(self, _obj):
        self.reginst_tab.on_remove_register_set_activate(_obj)

    def get_new_filename(self):
        """
        Opens up a file selector, and returns the selected file. The
        selected file is added to the recent manager.
        """
        name = None
        choose = Gtk.FileChooserDialog(
            "New",
            None,  # self.top_window,
            Gtk.FileChooserAction.SAVE,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.OK,
            ),
        )
        choose.set_current_folder(os.curdir)
        choose.show()

        response = choose.run()
        if response == Gtk.ResponseType.OK:
            name = choose.get_filename()
        choose.destroy()
        return name

    def on_new_project_clicked(self, _obj):

        choose = self.create_save_selector(
            "New Project", "Regenerate Project", DEF_MIME
        )

        response = choose.run()
        if response == Gtk.ResponseType.OK:
            filename = Path(choose.get_filename())

            if filename.suffix != PRJ_EXT:
                filename = filename.with_suffix(PRJ_EXT)

            self.prj = RegProject()
            self.prj.path = filename
            self.top_level_tab.change_project(self.prj)
            self.prj.name = filename.stem
            self.clear()
            self.prj.save()

            self.block_tab.clear_flags()

            self.project_modified(False)
            if self.recent_manager:
                self.recent_manager.add_item(f"file:///{str(filename)}")
            self.find_obj("save_btn").set_sensitive(True)
            self.prj_loaded.set_sensitive(True)
            self.load_project_tab()
        choose.destroy()

    def on_open_action_activate(self, _obj):

        choose = self.create_open_selector(
            "Open Project", "Regenerate Project", DEF_MIME
        )

        response = choose.run()
        filename = choose.get_filename()
        uri = choose.get_uri()
        choose.destroy()
        if response == Gtk.ResponseType.OK:
            self.open_project(filename, uri)

    def set_busy_cursor(self, value):
        """
        This seems to cause Windows to hang, so don't change the cursor
        to indicate busy under Windows.
        """
        if os.name == "posix":
            if value:
                cursor = Gdk.Cursor.new(Gdk.CursorType.WATCH)
                self.top_window.get_root_window().set_cursor(cursor)
            else:
                cursor = Gdk.Cursor.new(Gdk.CursorType.ARROW)
                self.top_window.get_root_window().set_cursor(cursor)
            while Gtk.events_pending():
                Gtk.main_iteration()

    def open_project(self, filename, uri):
        self.loading_project = True
        self.reginst_tab.clear()

        try:
            self.prj = RegProject(filename)
            self.project_tabs.change_db(self.prj)
            self.top_level_tab.change_project(self.prj)
        #            self.initialize_project_address_maps()
        except xml.parsers.expat.ExpatError as msg:
            ErrorMsg(
                f"{filename} was not a valid project file",
                str(msg),
                self.top_window,
            )
            return
        except IOError as msg:
            ErrorMsg(f"Could not open {filename}", str(msg), self.top_window)
            return

        self.prj_parameter_list.set_prj(self.prj)

        filepath = Path(filename)
        if filepath.suffix != PRJ_EXT:
            filepath = filepath.with_suffix(PRJ_EXT)
            LOGGER.warning(
                "Converted the database to the new format - "
                f" the new file name is {filepath}"
            )
        else:
            LOGGER.warning("Loaded %s", filepath)

        ini.set("user", "last_project", str(filepath.resolve()))

        self.reginst_tab.change_project(self.prj)

        if self.recent_manager and uri:
            self.recent_manager.add_item(uri)
        self.find_obj("save_btn").set_sensitive(True)

        self.set_title(False)

        self.load_project_tab()
        self.prj_loaded.set_sensitive(True)
        self.loading_project = False
        self.skip_changes = False

    def on_new_register_set_activate(self, _obj):
        self.reginst_tab.new_register_set(_obj)

    def input_xml(self, name, load=True):
        old_skip = self.skip_changes

        name_path = Path(name)
        if name_path.suffix == REG_EXT:
            self.skip_changes = True
        else:
            self.skip_changes = False
        self.dbase = RegisterDb()
        self.dbmap[self.dbase.set_name] = self.dbase
        self.load_database(name)
        if not os.access(name, os.W_OK):
            WarnMsg(
                "Read only file",
                "You will not be able to save this file unless\n"
                "you change permissions.",
                self.top_window,
            )

        mdl = self.reg_model.filter_new()
        self.filter_manage.change_filter(mdl, True)
        self.modelsort = Gtk.TreeModelSort(mdl)
        self.bit_model = BitModel()

        if load:
            self.reglist_obj.set_model(self.modelsort)
            self.bitfield_obj.set_model(self.bit_model)

        self.update_display()
        if name_path.suffix == REG_EXT:
            self.clear_modified()
        self.skip_changes = old_skip

    def update_display(self):
        old_skip = self.skip_changes
        self.skip_changes = True
        if self.reg_model:
            self.reg_model.clear()
            for key in self.dbase.get_keys():
                register = self.dbase.get_register(key)
                self.reg_model.append_register(register)
                self.reginst_tab.set_register_warn_flags(register)
        self.redraw()
        self.skip_changes = old_skip

    def open_xml(self, name, load=True):
        """
        Opens the specified XML file, parsing the data and building the
        internal RegisterDb data structure.
        """
        path = Path(name)
        converted = path.suffix == ".xml"

        if name:
            try:
                self.input_xml(name, load)
            except IOError as msg:
                ErrorMsg(
                    "Could not load existing register set",
                    str(msg),
                    self.top_window,
                )

            # self.active = DbaseStatus(
            #     self.dbase,
            #     name,
            #     str(path.stem),
            #     self.reg_model,
            #     self.modelsort,
            #     self.filter_manage.get_model(),
            #     self.bit_model,
            # )

        self.project_modified(True)

    def load_database(self, filename):
        """
        Reads the specified XML file, and redraws the screen.
        """
        self.filename = Path(filename)
        self.dbase.read_db(filename)
        self.dbmap[self.dbase.set_name] = self.dbase

    def on_save_clicked(self, _obj):
        """
        Called with the save button is clicked (gtk callback). Saves the
        database.
        """
        # change_suffix = False

        # self.top_level_tab.blkinst_list.get_groups()

        current_path = Path(self.prj.path)
        backup_path = Path(f"{current_path}.bak")

        if current_path.suffix != OLD_PRJ_EXT:
            if backup_path.is_file():
                backup_path.unlink()
            current_path.rename(backup_path)

        try:
            self.prj.save()
            self.project_modified(False)
            self.block_tab.clear_flags()
        except IOError as msg:
            os.rename(backup_path, current_path)
            ErrorMsg(
                f"Could not save {current_path}, restoring original",
                str(msg),
                self.top_window,
            )

    def exit(self):
        """
        Save the window size, along with the positions of the paned windows,
        then exit.
        """
        (width, height) = self.top_window.get_size()
        ini.set("user", "width", width)
        ini.set("user", "height", height)
        ini.set("user", "vpos", self.find_obj("vpaned").get_position())
        ini.set("user", "hpos", self.find_obj("hpaned").get_position())
        ini.set("user", "block_hpos", self.find_obj("bpaned").get_position())
        Gtk.main_quit()

    def save_and_quit(self):
        """
        Saves the database and quits. If the filename does not exist, prompt
        for a filename.
        """
        self.on_save_clicked(None)
        self.exit()

    def on_save_as_clicked(self, obj):
        """
        Called when the Save As button is clicked. Clears the filename first
        so that the user is prompted for a filename.
        """
        self.filename = None
        self.on_save_clicked(obj)

    def import_data(self, _obj, data):
        """Imports the data using the specified data importer."""
        choose = self.create_open_selector(data[1][1], data[2], "*" + data[3])

        response = choose.run()
        if response == Gtk.ResponseType.OK:
            choose.hide()
            while Gtk.events_pending():
                Gtk.main_iteration()

            filename = choose.get_filename()
            if filename:
                self.import_using_importer(filename, data[0])
        choose.destroy()

    def import_using_importer(self, name, importer_class):
        """Saves the file using the specified writer class."""
        importer = importer_class(self.dbase)
        try:
            importer.import_data(name)
            self.update_display()
            self.set_modified()
        except IOError as msg:
            ErrorMsg("Could not create %s " % name, str(msg), self.top_window)

    def redraw(self):
        """Redraws the information in the register list."""
        self.parameter_list.set_db(self.dbase)
        self.reglist_obj.set_parameters(self.dbase.get_parameters())
        self.bitfield_obj.set_parameters(self.dbase.get_parameters())

        if self.dbase.array_is_reg:
            self.find_obj("register_notation").set_active(True)
        else:
            self.find_obj("array_notation").set_active(True)

        self.update_bit_count()

        self.set_description_warn_flag()

    def on_regenerate_delete_event(self, obj, _event):
        return self.on_quit_activate(obj)

    def on_quit_activate(self, *_obj):
        """
        Called when the quit button is clicked.  Checks to see if the
        data needs to be saved first.
        """
        if self.modified or (self.prj and self.prj.modified):

            dialog = Question(
                "Save Changes?",
                "The file has been modified. Do you want to save your changes?",
                self.top_window,
            )

            status = dialog.run()
            if status == Question.DISCARD:
                self.exit()
                return False
            if status == Question.SAVE:
                self.save_and_quit()
                return False
            dialog.destroy()
            return True
        self.exit()
        return True

    def on_remove_register_action_activate(self, _obj):
        """
        Deletes the selected object (either a register or a bit range)
        """
        self.reginst_tab.remove_register()

    def set_db_value(self, attr, val):
        if self.dbase:
            setattr(self.dbase, attr, val)
        self.set_modified()

    def on_array_changed(self, obj):
        self.set_db_value("array_is_reg", not obj.get_active())

    def button_toggle(self, attr, obj):
        reg = self.reginst_tab.get_selected_register()
        if reg:
            setattr(reg.flags, attr, obj.get_active())
            self.set_modified()

    def on_no_rtl_toggled(self, obj):
        self.button_toggle("do_not_generate_code", obj)

    def on_no_uvm_toggled(self, obj):
        self.button_toggle("do_not_use_uvm", obj)

    def on_no_test_toggled(self, obj):
        self.button_toggle("do_not_test", obj)

    def on_no_cover_toggled(self, obj):
        self.button_toggle("do_not_cover", obj)

    def on_hide_doc_toggled(self, obj):
        self.button_toggle("hide", obj)

    def on_add_register_action_activate(self, _obj):
        """
        Adds a new register, seeding the address with the next available
        address
        """
        self.reginst_tab.new_register()

    def cb_open_recent(self, chooser):
        """
        Called when a file is chosen from the open recent dialog
        """
        recent_item = chooser.get_current_item()
        fname = recent_item.get_uri()
        if recent_item.exists():
            self.open_project(fname.replace("file:///", ""), fname)

    def create_recent_menu_item(self):
        """
        Builds the recent menu, applying the filter
        """
        recent_menu = Gtk.RecentChooserMenu()
        recent_menu.set_show_not_found(False)
        recent_menu.set_show_numbers(True)
        recent_menu.connect("item-activated", self.cb_open_recent)

        recent_menu_item = Gtk.MenuItem("Open Recent")
        recent_menu_item.set_submenu(recent_menu)

        filt = Gtk.RecentFilter()
        filt.add_pattern(DEF_MIME)
        recent_menu.set_filter(filt)
        recent_menu_item.show()
        return recent_menu_item

    def create_recent_menu(self):
        """
        Builds the recent menu, applying the filter
        """
        recent_menu = Gtk.RecentChooserMenu()
        recent_menu.set_show_not_found(False)
        recent_menu.set_show_numbers(True)
        recent_menu.connect("item-activated", self.cb_open_recent)

        filt = Gtk.RecentFilter()
        filt.add_pattern(DEF_MIME)
        recent_menu.set_filter(filt)
        return recent_menu

    def on_about_activate(self, _obj):
        """
        Displays the About box, describing the program
        """
        box = Gtk.AboutDialog()
        box.set_name(PROGRAM_NAME)
        box.set_version(PROGRAM_VERSION)
        box.set_comments(
            f"{PROGRAM_NAME} allows you to manage your\n"
            "registers for an ASIC or FPGA based design."
        )
        box.set_authors(["Donald N. Allingham"])
        try:
            with open(os.path.join(INSTALL_PATH, "LICENSE.txt")) as ifile:
                data = ifile.read()
                box.set_license(data)
        except IOError:
            pass
        fname = os.path.join(INSTALL_PATH, "media", "flop.svg")
        box.set_logo(GdkPixbuf.Pixbuf.new_from_file(fname))
        box.run()
        box.destroy()

    def set_description_warn_flag(self):
        if not self.loading_project:
            self.find_obj("mod_descr_warn").set_property(
                "visible", self.dbase.overview_text == ""
            )

    def set_title(self, modified):
        if modified:
            self.top_window.set_title(
                f"{self.prj.name} (modified) - regenerate"
            )
        else:
            self.top_window.set_title(f"{self.prj.name} - regenerate")


def check_field(field):
    if field.description.strip() == "":
        return Gtk.STOCK_DIALOG_WARNING
    return None


def check_reset(field):
    if (
        field.reset_type == ResetType.PARAMETER
        and field.reset_parameter.strip() == ""
    ):
        return Gtk.STOCK_DIALOG_WARNING
    return None


def sort_regset(rset):
    return os.path.basename(rset)


def check_address_ranges(project, dbmap):

    glist = []

    for group in project.get_grouping_list():

        for rset in group.register_sets:
            space = 1 << dbmap[rset.set].ports.address_bus_width
            if space > rset.repeat_offset:
                LOGGER.warning(
                    "%s.%s - %d bits specified for register set (size %x) which is greater than the repeat offset of %x",
                    group.name,
                    rset.inst,
                    dbmap[rset.set].address_bus_width,
                    space,
                    rset.repeat_offset,
                )
                return False

            glist.append(
                (
                    rset.offset,
                    rset.offset + (rset.repeat * rset.repeat_offset) - 1,
                    rset.inst,
                    1 << dbmap[rset.set].address_bus_width,
                    group.name,
                )
            )

    prev_start = 0
    prev_stop = 0
    prev_name = ""
    for (new_start, new_stop, new_name, _, new_group) in sorted(glist):
        if prev_stop > new_start:
            LOGGER.warning(
                "%s.%s (%x:%x) overlaps with %s.%s (%x:%x)",
                new_group,
                prev_name,
                prev_start,
                prev_stop,
                new_group,
                new_name,
                new_start,
                new_stop,
            )
            return False
        prev_name = new_name
        prev_start = new_start
        prev_stop = new_stop

    return True
