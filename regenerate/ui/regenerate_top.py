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

from typing import List, Union, Optional
from gi.repository import Gtk, GdkPixbuf, Gdk
from regenerate import PROGRAM_VERSION, PROGRAM_NAME
from regenerate.db import (
    RegProject,
    LOGGER,
    TYPES,
    remove_default_handler,
    ResetType,
    PRJ_EXT,
    OLD_PRJ_EXT,
)
from regenerate.importers import IMPORTERS
from regenerate.settings import ini
from regenerate.settings.paths import GLADE_TOP, INSTALL_PATH

from .addr_edit import AddrMapEdit
from .addrmap_list import AddrMapList
from .base_window import BaseWindow
from .block_tab import BlockTab
from .build import Build
from .error_dialogs import ErrorMsg, Question
from .help_window import HelpWindow
from .project_tab import ProjectTabs
from .register_tab import RegSetTab
from .status_logger import StatusHandler
from .top_level_tab import TopLevelTab


TYPE_ENB = {}
for data_type in TYPES:
    TYPE_ENB[data_type.type] = (data_type.input, data_type.control)

DEF_MIME = f"*{PRJ_EXT}"


class MainWindow(BaseWindow):
    """Main window of the Regenerate program"""

    def __init__(self):

        super().__init__()

        self.skip_changes = False
        self.filename = None
        self.loading_project = False
        self.active = None
        self.dbase = None
        self.bit_model = None
        self.modelsort = None
        self.prj = None
        self.dbmap = {}
        self.register = None

        self.builder = Gtk.Builder()
        self.builder.add_from_file(str(GLADE_TOP))

        self.setup_main_window()
        self.build_actions()

        self.top_notebook = self.find_obj("main_notebook")
        self.top_notebook.set_current_page(2)
        self.top_notebook.set_sensitive(False)

        autoload = bool(int(ini.get("user", "load_last_project", "0")))
        self.find_obj("autoload").set_active(autoload)
        
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

    def check_subsystem_addresses(self) -> bool:
        "Checks the address ranges"
        if check_address_ranges(self.prj):
            self.set_project_modified()
            return True
        return False

    def setup_main_window(self) -> None:
        "Sets up the main window and set up the status bar"

        self.top_window = self.find_obj("regenerate")
        self.configure(self.top_window)
        self.status_obj = self.find_obj("statusbar")
        remove_default_handler()
        LOGGER.addHandler(StatusHandler(self.status_obj))

    def setup_recent_menu(self) -> None:
        """Setup the recent files management system"""

        self.recent_manager = Gtk.RecentManager.get_default()
        self.find_obj("file_menu").insert(self.create_recent_menu_item(), 2)
        self.find_obj("open_btn").set_menu(self.create_recent_menu())

    def find_obj(self, name):
        "Convenience function to find an object"
        return self.builder.get_object(name)

    def on_addrmap_cursor_changed(self, obj: Gtk.TreeView) -> None:
        """Called when the row of the treeview changes."""

        mdl, node = obj.get_selection().get_selected()
        ebtn = self.find_obj("edit_map")
        rbtn = self.find_obj("remove_map")
        if node:
            path = mdl.get_path(node)
            ebtn.set_sensitive(len(path) == 1)
            rbtn.set_sensitive(len(path) == 1)
        else:
            ebtn.set_sensitive(False)
            rbtn.set_sensitive(False)

    def setup_project(self) -> None:
        "Sets up the project, register, and block tabs"

        self.project_tabs = ProjectTabs(
            self.builder, self.set_project_modified
        )

        self.regset_tab = RegSetTab(
            self.find_obj,
            self.set_project_modified,
            self.db_selected,
            self.reg_selected,
            self.field_selected,
        )

        self.block_tab = BlockTab(
            self.find_obj,
            self.delete_block_callback,
        )

        self.addr_map_list = AddrMapList(
            self.find_obj("address_tree"), self.set_project_modified
        )

    def set_parameters_modified(self) -> None:
        self.set_project_modified()
        self.regset_tab.reglist_obj.set_parameters(self.dbase.parameters.get())
        self.regset_tab.bitfield_obj.set_parameters(
            self.dbase.parameters.get()
        )

    def set_project_modified(self) -> None:
        "Sets the project modified flag"
        self.project_modified(True)

    def project_modified(self, value: bool) -> None:
        "Sets the modified flag and changes the title bar"
        self.set_title(value)
        self.prj.modified = value

    def load_project_tab(self) -> None:
        self.top_notebook.set_sensitive(True)
        self.block_tab.set_project(self.prj)
        self.project_tabs.change_db(self.prj)
        self.addr_map_list.set_project(self.prj)
        self.regset_tab.change_project(self.prj)
        self.project_modified(False)

    def on_edit_map_clicked(self, _obj):
        addr_map = self.addr_map_list.get_selected()
        if addr_map is None:
            return

        current = self.prj.address_maps[addr_map.uuid].blocks

        new_list = [
            (blk_inst, blk_inst.uuid in current)
            for blk_inst in self.prj.block_insts
        ]

        dialog = AddrMapEdit(
            addr_map.name,
            new_list,
            self.prj,
            self.top_window,
            self.set_project_modified,
        )

        new_list = dialog.get_list()
        if new_list is not None:
            self.prj.set_address_map_block_list(addr_map.uuid, new_list)
            self.addr_map_list.set_project(self.prj)
            self.set_project_modified()

    def on_block_select_changed(self, _obj: Gtk.TreeSelection) -> None:
        self.top_level_tab.update_buttons()

    def on_addr_map_help_clicked(self, _obj: Gtk.Button) -> None:
        "Display the address map help"
        HelpWindow(self.builder, "addr_map_help.rst", "Address Map Help")

    def on_param_help_clicked(self, _obj: Gtk.Button) -> None:
        """Display the parameter help"""
        HelpWindow(self.builder, "parameter_help.rst", "Parameter Help")

    def on_prj_param_help_clicked(self, _obj: Gtk.Button) -> None:
        """Display the project parameter help"""
        HelpWindow(self.builder, "prj_parameter_help.rst")

    def on_remove_map_clicked(self, _obj: Gtk.Button) -> None:
        """Remove the selected map with clicked"""
        self.project_modified(True)
        self.addr_map_list.remove_selected()

    def on_add_map_clicked(self, _obj: Gtk.Button) -> None:
        """Add a new map when clicked"""
        self.addr_map_list.add_new_map()

    def on_help_action_activate(self, _obj: Gtk.Action) -> None:
        """Display the help window"""
        HelpWindow(self.builder, "regenerate_help.rst", "Overview")

    def restore_position_and_size(self) -> None:
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

    def build_group(
        self, group_name: str, _action_names: List[str]
    ) -> Gtk.ActionGroup:
        return Gtk.ActionGroup(group_name)

    def build_actions(self) -> None:
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

    def on_build_action_activate(self, _obj: Gtk.Action) -> None:
        Build(self.prj)

    def on_autoload_toggled(self, _obj) -> None:
        ini.set("user", "load_last_project", int(bool(_obj.get_active())))

    def build_import_menu(self) -> None:
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

    def on_main_notebook_switch_page(
        self, _obj: Gtk.Notebook, _page: Gtk.Paned, page_num: int
    ) -> None:
        "Called when the Top/Block/Registers tab is changed"
        self.regset_tab.filter_visible(page_num == 0)
        if page_num == 0:
            self.regset_tab.update_display(True)
        elif page_num == 1:
            self.block_tab.redraw()
        else:
            self.top_level_tab.update()

    def on_notebook_switch_page(
        self, _obj: Gtk.Notebook, _page: Gtk.Box, page_num: int
    ) -> None:
        "Called when the notebook page on the register tab is changed"

        if page_num == 1:
            self.regset_tab.update_bit_count()
        if self.regset_tab.get_selected_register():
            self.reg_selected.set_sensitive(page_num == 0)
        else:
            self.reg_selected.set_sensitive(False)

    def create_file_selector(
        self,
        title: str,
        m_name: Optional[str],
        m_regex: Optional[Union[str, List[str]]],
        action: Gtk.FileChooserAction,
        icon: str,
    ) -> Gtk.FileChooserDialog:
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
        if m_name and m_regex:
            mime_filter = Gtk.FileFilter()
            mime_filter.set_name(m_name)
            if isinstance(m_regex, str):
                mime_filter.add_pattern(m_regex)
            else:
                for val in m_regex:
                    mime_filter.add_pattern(val)

            choose.add_filter(mime_filter)
        choose.show()
        return choose

    def create_save_selector(
        self, title: str, mime_name=None, mime_regex=None
    ) -> Gtk.FileChooserDialog:
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

    def create_open_selector(
        self, title: str, mime_name=None, mime_regex=None
    ) -> Gtk.FileChooserDialog:
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
            self.prj.name = ""
            self.prj.short_name = filename.stem
            self.prj.save()

            self.regset_tab.change_project(self.prj)
            self.block_tab.clear_flags()
            self.load_project_tab()

            self.project_modified(False)
            self.add_recent(str(filename.resolve()))
            self.find_obj("save_btn").set_sensitive(True)
            self.prj_loaded.set_sensitive(True)
        choose.destroy()

    def add_recent(self, path: str):
        "Adds the path th the recent manager. Must be an absolute path"

        if self.recent_manager:
            name = f"file://{path}"
            self.recent_manager.add_item(name)

    def on_open_action_activate(self, _obj):

        choose = self.create_open_selector(
            "Open Project", "Regenerate Project", [DEF_MIME, f"*{OLD_PRJ_EXT}"]
        )

        response = choose.run()
        filename = choose.get_filename()
        uri = choose.get_uri()
        choose.destroy()
        if response == Gtk.ResponseType.OK:
            self.open_project(filename, uri)
            self.add_recent(Path(filename).resolve())

    def open_project(self, filename, _uri):
        self.loading_project = True
        self.regset_tab.clear()

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

        filepath = Path(filename)
        if filepath.suffix != PRJ_EXT:
            filepath = filepath.with_suffix(PRJ_EXT)
            LOGGER.warning(
                "Converted the database to the new format - "
                " the new file name is %s",
                filepath,
            )
        else:
            LOGGER.info("Loaded %s", filepath)

        ini.set("user", "last_project", str(filepath.resolve()))

        self.regset_tab.change_project(self.prj)

        self.add_recent(str(filepath.resolve()))
        self.find_obj("save_btn").set_sensitive(True)

        self.set_title(False)

        self.load_project_tab()
        self.prj_loaded.set_sensitive(True)
        self.loading_project = False
        self.skip_changes = False

    def update_display(self):
        old_skip = self.skip_changes
        self.skip_changes = True
        self.redraw()
        self.regset_tab.redraw(False)
        self.block_tab.redraw()
        self.skip_changes = old_skip

    def on_save_clicked(self, _obj):
        """
        Called with the save button is clicked (gtk callback). Saves the
        database.
        """
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
            self.regset_tab.reg_set_model.update()
        except IOError as msg:
            os.rename(backup_path, current_path)
            ErrorMsg(
                f"Could not save {current_path}, restoring original",
                str(msg),
                self.top_window,
            )

        self.regset_tab.update_display(False)
        self.block_tab.redraw()

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
            self.set_project_modified()
        except IOError as msg:
            ErrorMsg("Could not create %s " % name, str(msg), self.top_window)

    def redraw(self):
        """Redraws the information in the register list."""
        self.regset_tab.parameter_list.set_db(self.dbase)
        self.regset_tab.reglist_obj.set_parameters(self.dbase.parameters.get())
        self.regset_tab.bitfield_obj.set_parameters(
            self.dbase.parameters.get()
        )
        self.regset_tab.update_display(False)
        self.set_description_warn_flag()

    def delete_block_callback(self):
        self.top_level_tab.blkinst_list.populate()

    def on_regenerate_delete_event(self, obj, _event):
        return self.on_quit_activate(obj)

    def on_quit_activate(self, *_obj):
        """
        Called when the quit button is clicked.  Checks to see if the
        data needs to be saved first.
        """
        need_save = False

        if self.prj:
            if self.prj.modified:
                need_save = True
            else:
                for blk in self.prj.blocks.values():
                    if blk.modified:
                        need_save = True
                for regset in self.prj.regsets.values():
                    if regset.modified:
                        need_save = True

        if need_save:

            dialog = Question(
                "Save Changes?",
                "Modifications have been made. Do you want to save your changes?",
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
        self.regset_tab.remove_register()

    def set_db_value(self, attr, val):
        if self.dbase:
            setattr(self.dbase, attr, val)
        self.regset_tab.set_modified()

    def on_array_changed(self, obj):
        self.regset_tab.array_changed(obj)

    def button_toggle(self, attr, obj):
        reg = self.regset_tab.get_selected_register()
        state = obj.get_active()
        if reg:
            setattr(reg.flags, attr, state)
            self.regset_tab.set_modified()

    def on_no_rtl_toggled(self, obj):
        self.button_toggle("do_not_generate_code", obj)

    def on_no_uvm_toggled(self, obj):
        self.button_toggle("do_not_use_uvm", obj)

    def on_no_test_toggled(self, obj):
        self.button_toggle("do_not_test", obj)

    def on_no_reset_test_toggled(self, obj):
        self.button_toggle("do_not_reset_test", obj)

    def on_no_cover_toggled(self, obj):
        self.button_toggle("do_not_cover", obj)

    def on_hide_doc_toggled(self, obj):
        self.button_toggle("hide", obj)

    def on_add_register_action_activate(self, _obj):
        """
        Adds a new register, seeding the address with the next available
        address
        """
        self.regset_tab.new_register()

    def cb_open_recent(self, chooser):
        """
        Called when a file is chosen from the open recent dialog
        """
        fname = chooser.get_current_uri()
        self.open_project(fname.replace("file://", ""), fname)

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
            with open(INSTALL_PATH / "LICENSE.txt") as ifile:
                data = ifile.read()
                box.set_license(data)
        except IOError:
            pass
        fname = INSTALL_PATH / "media" / "flop.svg"
        box.set_logo(GdkPixbuf.Pixbuf.new_from_file(str(fname)))
        box.run()
        box.destroy()

    def set_description_warn_flag(self):
        if not self.loading_project:
            self.find_obj("mod_descr_warn").set_property(
                "visible", self.dbase.overview_text == ""
            )

    def set_title(self, modified):
        name = self.prj.path.name
        if modified:
            self.top_window.set_title(
                f"{self.prj.name} ({name}*) - regenerate"
            )
        else:
            self.top_window.set_title(f"{self.prj.name} ({name}) - regenerate")


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


def check_address_ranges(project):

    glist = []

    for block_inst in project.block_insts:

        block = project.blocks[block_inst.blkid]

        for regset_inst in block.regset_insts:
            regset = block.regsets[regset_inst.regset_id]
            space = 1 << regset.ports.address_bus_width

            glist.append(
                (
                    regset_inst.offset,
                    regset_inst.offset
                    + (
                        regset_inst.repeat.resolve()
                        * regset_inst.repeat_offset
                    )
                    - 1,
                    regset_inst.name,
                    space,
                    block_inst.name,
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
