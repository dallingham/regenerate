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

from typing import Dict
from pathlib import Path

from gi.repository import Gtk, Gdk, GdkPixbuf, Pango
from regenerate.settings.paths import INSTALL_PATH
from regenerate.db import Register, BitField, LOGGER, RegisterDb
from regenerate.db.enums import ShareType, ResetType
from regenerate.db.const import REG_EXT, OLD_REG_EXT
from regenerate.ui.bit_list import BitModel, BitList
from regenerate.ui.bitfield_editor import BitFieldEditor
from regenerate.ui.columns import ReadOnlyColumn
from regenerate.ui.enums import SelectCol, BitCol, RegCol
from regenerate.ui.module_tab import ModuleTabs
from regenerate.ui.parameter_list import ParameterList
from regenerate.ui.reg_description import RegisterDescription
from regenerate.ui.register_list import RegisterModel, RegisterList
from regenerate.ui.summary_window import SummaryWindow
from regenerate.extras.remap import REMAP_NAME
from regenerate.extras.regutils import (
    calculate_next_address,
    duplicate_register,
)
from regenerate.ui.filter_mgr import FilterManager


class RegSetWidgets:
    def __init__(self, find_obj):
        self.reglist = find_obj("register_list")
        self.regset_list = find_obj("project_list")
        self.notebook = find_obj("module_notebook")
        self.descript = find_obj("register_description")
        self.regset_preview = find_obj("scroll_reg_webkit")
        self.descript_warn = find_obj("reg_descr_warn")
        self.bit_warn = find_obj("reg_bit_warn")
        self.reg_notebook = find_obj("reg_notebook")
        self.no_rtl = find_obj("no_rtl")
        self.no_uvm = find_obj("no_uvm")
        self.no_test = find_obj("no_test")
        self.no_cover = find_obj("no_cover")
        self.hide_doc = find_obj("hide_doc")
        self.no_sharing = find_obj("no_sharing")
        self.read_access = find_obj("read_access")
        self.write_access = find_obj("write_access")
        self.selected_regset = find_obj("selected_dbase")
        self.filter_obj = find_obj("filter")
        self.reg_count = find_obj("reg_count")
        self.mod_descr_warn = find_obj("mod_descr_warn")
        self.bitfield_list = find_obj("bitfield_list")
        self.parameter_list = find_obj("parameter_list")
        self.summary_window = find_obj("summary_window")
        self.summary_scroll = find_obj("summary_scroll")
        self.summary_button = find_obj("summary_button")
        self.register_notation = find_obj("register_notation")
        self.array_notation = find_obj("array_notation")
        self.add_regset_param = find_obj("add_regset_param")
        self.remove_regset_param = find_obj("remove_regset_param")


class RegSetStatus:
    """
    Holds the state of a particular database. This includes the database model,
    the list models for the displays, the modified status, and the selected
    rows in the models.
    """

    def __init__(self, container, reg_model, mdlsort, mdlfilter, bmodel, node):
        self.container = container
        self.reg_model = reg_model
        self.modelfilter = mdlfilter
        self.modelsort = mdlsort
        self.bit_model = bmodel
        self.reg_select = None
        self.bit_select = None
        self.node = node


class RegSetModel(Gtk.ListStore):
    """
    Provides the model for the project list
    """

    def __init__(self):
        super().__init__(str, str, object)

        Gdk.threads_init()
        self.file_list = {}
        self.paths = set()

    def set_markup(self, node, modified):
        """Sets the icon if the project has been modified"""
        if modified:
            icon = Gtk.STOCK_EDIT
        else:
            icon = None
        self.set_value(node, SelectCol.ICON, icon)

    def add_dbase(self, regset: RegisterDb, modified=False):
        """Add the the database to the model"""
        base = regset.filename.stem
        if regset.modified:
            node = self.append(row=[Gtk.STOCK_EDIT, base, regset])
        else:
            node = self.append(row=["", base, regset])

        self.file_list[str(regset.filename)] = node
        self.paths.add(regset.filename.parent)
        return node

    def update(self):
        for row in self:
            if row[2].modified:
                row[0] = Gtk.STOCK_EDIT
            else:
                row[0] = ""


class RegSetList:
    """Project list"""

    def __init__(self, obj, selection_callback):
        self.__obj = obj
        self.__obj.get_selection().connect("changed", selection_callback)
        self.__obj.set_reorderable(True)
        self.__model = None
        self.__build_prj_window()

        self.factory = Gtk.IconFactory()
        filename = os.path.join(INSTALL_PATH, "media", "ModifiedIcon.png")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(filename)
        iconset = Gtk.IconSet(pixbuf)
        self.factory.add("out-of-date", iconset)
        self.factory.add_default()
        self.prj = None

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

        column = ReadOnlyColumn("Register Sets", 1)
        column.renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column.set_min_width(140)
        self.__obj.append_column(column)

    def highlight(self, col, renderer, model, node, ptr):
        if self.prj:
            regset = model.get_value(node, 2)
            for block in self.prj.blocks:
                for setname in self.prj.blocks[block].regsets:
                    if setname == regset.name:
                        renderer.set_property("weight", Pango.Weight.NORMAL)
                        return
            renderer.set_property("weight", Pango.Weight.BOLD)

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

    def change_project(self, prj):
        self.prj = prj


class RegSetTab:
    def __init__(
        self,
        find_obj,
        modified,
        db_selected_action,
        reg_selected_action,
        field_selected_action,
    ):
        self.modified_callback = modified
        self.db_selected_action = db_selected_action
        self.reg_selected_action = reg_selected_action
        self.field_selected_action = field_selected_action

        self.skip_changes = False
        self.reg_set_model = None
        self.widgets = RegSetWidgets(find_obj)

        self.widgets.reg_notebook.set_sensitive(False)
        self.widgets.reg_notebook.hide()
        self.reg_selected_action.set_sensitive(False)

        self.widgets.notebook.connect("switch-page", self.reg_page_changed)

        self.reg_set_obj = RegSetList(
            self.widgets.regset_list, self.regset_sel_changed
        )
        self.module_tabs = ModuleTabs(find_obj, self.set_modified)

        self.parameter_list = ParameterList(
            self.widgets.parameter_list,
            self.widgets.add_regset_param,
            self.widgets.remove_regset_param,
            self.set_parameters_modified,
        )

        self.reglist_obj = RegisterList(
            self.widgets.reglist,
            self.selected_reg_changed,
            self.set_modified,
            self.update_register_addr,
            self.set_register_warn_flags,
        )

        self.bitfield_obj = BitList(
            self.widgets.bitfield_list,
            self.bit_changed,
            self.set_modified,
        )

        self.reg_description = RegisterDescription(
            self.widgets.descript,
            self.widgets.regset_preview,
            self.reg_descript_callback,
        )

        self.active = None
        self.active_name = ""
        self.project = None
        self.name2status: Dict[str, RegSetStatus] = {}

        self.widgets.filter_obj.set_placeholder_text("Signal Filter")
        self.filter_manage = FilterManager(self.widgets.filter_obj)

        self.clear()

    def reg_page_changed(self, obj, page, page_num):
        """When the notebook page changes, update any fields that are
        out of date due to parameter name changes"""

        self.update_size_parameters()
        self.update_field_parameters()

    def update_field_parameters(self):
        "Update any displayed parameter names if they have changed"
        for row in self.bit_model:
            field = row[BitCol.FIELD]
            if field.reset_type == ResetType.PARAMETER:
                if field.reset_parameter != row[BitCol.RESET]:
                    row[BitCol.RESET] = field.reset_parameter

    def update_size_parameters(self):
        "Change the reset parameters, updating for any name changes"
        for row in self.reg_model:
            reg = row[-1]
            if (
                reg.dimension_is_param()
                and reg.dimension_str != row[RegCol.DIM]
            ):
                row[RegCol.DIM] = reg.dimension_str

    def set_parameters_modified(self):
        self.set_modified()
        self.reglist_obj.set_parameters(self.active.parameters.get())
        self.bitfield_obj.set_parameters(self.active.parameters.get())
        self.selected_reg_changed(None)

    def set_modified(self):
        if not self.skip_changes:
            self.active.modified = True
            self.reg_set_model.set_markup(self.node, True)
            self.modified_callback()

    def enable_registers(self, value):
        """
        Enables UI items when a database has been loaded. This includes
        enabling the register window, the register related buttons, and
        the export menu.
        """
        self.widgets.notebook.set_sensitive(value)
        self.db_selected_action.set_sensitive(value)
        if value:
            self.widgets.reg_notebook.show()
        else:
            self.widgets.reg_notebook.hide()

    def new_regset(self, regset):

        node = self.reg_set_model.add_dbase(regset)
        self.reg_model = RegisterModel()
        mdl = self.reg_model.filter_new()
        self.filter_manage.change_filter(mdl, True)
        self.modelsort = Gtk.TreeModelSort(mdl)
        self.reglist_obj.set_model(self.modelsort)

        for key in regset.get_keys():
            register = regset.get_register(key)
            self.reg_model.append_register(register)

        bit_model = BitModel()

        status = RegSetStatus(
            regset,
            self.reg_model,
            self.modelsort,
            self.filter_manage.get_model(),
            bit_model,
            node,
        )

        self.name2status[regset.uuid] = status
        return node

    def array_changed(self, obj):
        self.active.array_is_reg = obj.get_active()
        self.set_modified()

    def change_project(self, prj):

        self.reg_set_obj.change_project(prj)
        self.project = prj
        self.name2status = {}
        self.rebuild_model()
        self.update_display()
        self.reg_set_obj.select_path(0)

    def rebuild_model(self):
        if len(self.project.regsets) != len(self.reg_set_model):
            self.reg_set_model.clear()

            sorted_dict = {
                key: value
                for key, value in sorted(
                    self.project.regsets.items(), key=lambda item: item[1].name
                )
            }

            for rsid in sorted_dict:
                regset = self.project.regsets[rsid]
                self.new_regset(regset)

    def reg_descript_callback(self, reg):
        self.set_modified()
        self.set_register_warn_flags(reg)

    def update_display(self):
        old_skip = self.skip_changes
        self.skip_changes = True
        self.redraw()
        self.skip_changes = old_skip

    def redraw(self):
        """Redraws the information in the register list."""
        if self.active:
            self.module_tabs.change_db(self.active)
            self.parameter_list.set_db(self.active)
            self.reglist_obj.set_parameters(self.active.parameters.get())
            self.bitfield_obj.set_parameters(self.active.parameters.get())
            if self.active.array_is_reg:
                self.widgets.register_notation.set_active(True)
            else:
                self.widgets.array_notation.set_active(True)
        self.rebuild_model()

        self.update_bit_count()
        self.set_description_warn_flag()

    def get_selected_register(self):
        return self.reglist_obj.get_selected_register()

    def clear(self):
        self.reg_set_model = RegSetModel()
        self.reg_set_obj.set_model(self.reg_set_model)

    def regset_sel_changed(self, _obj):
        model, node = self.reg_set_obj.get_selected()
        if node:
            self.active_name = model[node][SelectCol.OBJ].uuid
            self.active = model[node][SelectCol.OBJ]
        else:
            self.active = None
            self.active_name = ""

        old_skip = self.skip_changes
        self.skip_changes = True

        if self.active:
            self.active.reg_select = self.reglist_obj.get_selected_row()
            self.active.bit_select = self.bitfield_obj.get_selected_row()

            status = self.name2status[self.active.uuid]
            self.reg_model = status.reg_model
            self.filter_manage.change_filter(status.modelfilter)
            self.modelsort = status.modelsort
            self.node = status.node

            # self.reg_description.set_database(self.active)

            status = self.name2status[self.active.uuid]
            self.filter_manage.change_filter(status.modelfilter)
            self.reglist_obj.set_model(status.modelsort)

            self.bit_model = status.bit_model
            self.bitfield_obj.set_model(self.bit_model)

            text = "<b>%s - %s</b>" % (
                self.active.module_name,
                self.active.descriptive_title,
            )
            self.widgets.selected_regset.set_text(text)
            self.widgets.selected_regset.set_use_markup(True)
            self.widgets.selected_regset.set_ellipsize(Pango.EllipsizeMode.END)
            # if self.active.reg_select:
            #     for row in self.active.reg_select:
            #         self.reglist_obj.select_row(row)
            # if self.active.bit_select:
            #     for row in self.active.bit_select:
            #         self.bitfield_obj.select_row(row)
            self.redraw()
            self.enable_registers(True)
        else:
            self.active = None
            self.dbase = None
            self.widgets.selected_regset.set_text("")
            self.reglist_obj.set_model(None)
            self.enable_registers(False)
        self.skip_changes = old_skip

    def set_register_warn_flags(self, reg, mark=True):
        warn_reg = warn_bit = False
        msg = []
        if not reg.description:
            warn_reg = True
            msg.append("Missing register description")
        if reg.token.lower() in REMAP_NAME:
            warn_reg = True
            msg.append("Register name is a SystemVerilog reserved word")
        if not reg.get_bit_fields():
            warn_bit = True
            msg.append("No bit fields exist for the register")
        else:
            for field in reg.get_bit_fields():
                if field.name.lower() in REMAP_NAME:
                    txt = f"Field name ({field.name}) is a SystemVerilog reserved word"
                    msg.append(txt)
                if check_field(field):
                    txt = "Missing field description for '{field.name}'"
                    msg.append(txt)
                    warn_bit = True
                if check_reset(field):
                    txt = "Missing reset parameter name for '{field.name}'"
                    msg.append(txt)
                    warn_bit = True
        # if mark and not self.loading_project:
        if mark:
            self.widgets.descript_warn.set_property("visible", warn_reg)
            self.widgets.bit_warn.set_property("visible", warn_bit)
        self.reg_model.set_warning_for_register(reg, warn_reg or warn_bit)
        if msg:
            tip = "\n".join(msg)
        else:
            tip = None
        self.reg_model.set_tooltip(reg, tip)

    def selected_reg_changed(self, _obj):
        """
        GTK callback that checks the selected objects, and then enables the
        appropriate buttons on the interface.
        """
        old_skip = self.skip_changes
        self.skip_changes = True
        reg = self.get_selected_register()
        self.reg_description.set_register(reg)
        if reg:
            self.widgets.reg_notebook.show()
            self.widgets.reg_notebook.set_sensitive(True)
            self.reg_selected_action.set_sensitive(True)
            self.bit_model.clear()
            self.bit_model.register = reg
            self.bitfield_obj.set_mode(reg.share)
            for key in reg.get_bit_field_keys():
                field = reg.get_bit_field(key)
                self.bit_model.append_field(field)

            self.widgets.no_rtl.set_active(reg.flags.do_not_generate_code)
            self.widgets.no_uvm.set_active(reg.flags.do_not_use_uvm)
            self.widgets.no_test.set_active(reg.flags.do_not_test)
            self.widgets.no_cover.set_active(reg.flags.do_not_cover)
            self.widgets.hide_doc.set_active(reg.flags.hide)

            self.set_register_warn_flags(reg)
            self.set_bits_warn_flag()
            self.set_share(reg)
        else:
            self.widgets.reg_notebook.hide()
            self.widgets.reg_notebook.set_sensitive(False)
            self.reg_selected_action.set_sensitive(False)
        self.skip_changes = old_skip

    def set_share(self, reg):
        if reg.share == ShareType.NONE:
            self.widgets.no_sharing.set_active(True)
        elif reg.share == ShareType.READ:
            self.widgets.read_access.set_active(True)
        else:
            self.widgets.write_access.set_active(True)

    def remove_register(self):
        row = self.reglist_obj.get_selected_position()
        reg = self.get_selected_register()
        if reg:
            self.reglist_obj.delete_selected_node()
            self.active.delete_register(reg)
            self.reglist_obj.select_row(row)
            self.set_modified()

    def new_register(self):
        register = Register()
        dbase = self.active
        register.width = dbase.ports.data_bus_width
        register.address = calculate_next_address(dbase, register.width)
        self.insert_new_register(register)

    def insert_new_register(self, register):
        if self.widgets.notebook.get_current_page() == 0:
            self.reglist_obj.add_new_register(register)
            self.active.add_register(register)
            self.set_register_warn_flags(register)
            self.set_modified()

    def add_bit(self):
        register = self.get_selected_register()
        next_pos = register.find_next_unused_bit()

        if next_pos == -1:
            LOGGER.error("All bits are used in this register")
            return

        field = BitField()
        field.lsb = next_pos

        field.msb.set_int(field.lsb)
        field.name = "BIT%d" % field.lsb
        field.output_signal = ""
        if register.share == ShareType.WRITE:
            field.field_type = BitType.WRITE_ONLY

        register.add_bit_field(field)

        self.bitfield_obj.add_new_field(field)
        self.set_modified()
        self.set_register_warn_flags(register)

    def remove_bit(self):
        register = self.get_selected_register()
        row = self.bitfield_obj.get_selected_row()
        field = self.bit_model.get_bitfield_at_path(row[0])
        register.delete_bit_field(field)
        node = self.bit_model.get_iter(row[0])
        self.bit_model.remove(node)
        self.set_register_warn_flags(register)
        self.set_modified()

    def edit_bit(self):
        register = self.get_selected_register()
        field = self.bitfield_obj.select_field()
        if field:
            BitFieldEditor(
                self.active,
                register,
                field,
                self.set_field_modified,
                None,  # self.builder,
                None,  # self.top_window,
            )

    def update_register_addr(self, register, new_addr, new_length=0):
        self.active.delete_register(register)
        register.address = new_addr
        register.ram_size = new_length
        share_reg = self.find_shared_address(register)
        if share_reg:
            if share_reg.share == ShareType.READ:
                register.share = ShareType.WRITE
            else:
                register.share = ShareType.READ
            self.set_share(register)
        self.active.add_register(register)

    def find_shared_address(self, reg):
        for shared_reg in self.active.get_all_registers():
            if shared_reg != reg and shared_reg.address == reg.address:
                return shared_reg
        return None

    def set_field_modified(self):
        reg = self.get_selected_register()
        self.set_register_warn_flags(reg)
        self.set_bits_warn_flag()
        self.set_modified()

    def set_bits_warn_flag(self):
        warn = False
        for row in self.bit_model:
            field = row[BitCol.FIELD]
            icon = check_field(field)
            row[BitCol.ICON] = icon
            if icon:
                warn = True
        return warn

    def update_bit_count(self):
        if self.active:
            text = "%d" % self.active.total_bits()
        else:
            text = ""
        self.widgets.reg_count.set_text(text)

    def set_description_warn_flag(self):
        if self.active:
            warn = self.active.overview_text == ""
        else:
            warn = False
        self.widgets.mod_descr_warn.set_property("visible", warn)
        #    if not self.loading_project:

    def on_no_sharing_toggled(self, obj):
        if obj.get_active():
            register = self.get_selected_register()

            if self.duplicate_address(register.address):
                self.set_share(register)
                LOGGER.error(
                    "Register cannot be set to non-sharing "
                    "if it shares an address with another"
                )
            else:
                register.share = ShareType.NONE
                self.set_modified()
            self.bitfield_obj.set_mode(register.share)

    def on_read_access_toggled(self, obj):
        if obj.get_active():
            register = self.get_selected_register()

            other = self.find_shared_address(register)
            if other and other.share != ShareType.WRITE:
                self.set_share(register)
                LOGGER.error("The shared register is not of Write Access type")
            elif register.is_completely_read_only():
                register.share = ShareType.READ
                self.set_modified()
            else:
                self.set_share(register)
                LOGGER.error("All bits in the register must be read only")
            self.bitfield_obj.set_mode(register.share)

    def on_write_access_toggled(self, obj):
        if obj.get_active():
            register = self.get_selected_register()

            other = self.find_shared_address(register)
            if other and other.share != ShareType.READ:
                self.set_share(register)
                LOGGER.error("The shared register is not of Read Access type")
            elif register.is_completely_write_only():
                register.share = ShareType.WRITE
                self.set_modified()
            else:
                self.set_share(register)
                LOGGER.error("All bits in the register must be write only")
            self.bitfield_obj.set_mode(register.share)

    def duplicate_address(self, reg_addr):
        cnt = 0
        for reg in self.active.get_all_registers():
            if reg.address == reg_addr:
                cnt += 1
        return cnt > 1

    def duplicate_register(self):
        reg = self.get_selected_register()
        if reg:
            reg_copy = duplicate_register(self.active, reg)
            self.reglist_obj.add_new_register(reg_copy)
            self.active.add_register(reg_copy)
            self.set_register_warn_flags(reg_copy)
            self.set_modified()

    def bit_changed(self, _obj):
        self.field_selected_action.set_sensitive(True)

    def on_remove_register_set_activate(self, _obj):
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        data = self.reg_set_obj.get_selected()
        if not data:
            return
        old_skip = self.skip_changes
        self.skip_changes = True

        (store, node) = data
        base = store.get_value(node, SelectCol.OBJ)
        store.remove(node)
        self.remove_regset_from_project(base.uuid)
        self.remove_regset_from_groups(base.uuid)
        self.set_modified()
        self.skip_changes = old_skip
        self.reg_set_obj.select_path(0)

    def remove_regset_from_project(self, uuid):
        regset = self.project.regsets[uuid]
        self.project.remove_register_set(regset.filename)
        del self.project.regsets[uuid]

    def remove_regset_from_groups(self, uuid):
        for key, block in self.project.blocks.items():
            new_reglist = [
                reglist
                for reglist in block.regset_insts
                if reglist.uuid != uuid
            ]
            block.regset_insts = new_reglist

    def new_register_set(self, _obj):
        """
        Creates a new database, and initializes the interface.
        """
        name = self.get_new_filename()
        if not name:
            return

        name = Path(name).with_suffix(REG_EXT)

        dbase = RegisterDb()
        dbase.module_name = name.stem
        dbase.set_name = name.stem
        dbase.filename = name
        dbase.modified = True

        self.project.regsets[dbase.set_name] = container
        node = self.new_regset(dbase, name.stem)
        self.reg_set_obj.select(node)

        # self.set_project_modified()
        return

    def get_new_filename(self):
        """
        Opens up a file selector, and returns the selected file. The
        selected file is added to the recent manager.
        """
        name = None
        choose = Gtk.FileChooserDialog(
            "New",
            None,
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

    def add_register_set(self, obj):
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        choose = self.create_open_selector(
            "Open Register Database",
            "Register files",
            [f"*{REG_EXT}", f"*{OLD_REG_EXT}"],
        )
        choose.set_select_multiple(True)
        response = choose.run()
        if response == Gtk.ResponseType.OK:
            for filename in choose.get_filenames():

                name = Path(filename)
                dbase = RegisterDb(name)
                dbase.filename = name
                dbase.modified = True

                self.project.regsets[dbase.set_name] = dbase
                node = self.new_regset(dbase, name.stem)
                self.reg_set_obj.select(node)
                # self.set_project_modified()
                # self.infobar_reveal(False)
            # self.reginst_model.load_icons()
        choose.destroy()

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

    def create_file_selector(self, title, name, mime_types, action, icon):
        """
        Creates a file save selector, using the mime type and regular
        expression to control the selector.
        """
        choose = Gtk.FileChooserDialog(
            title,
            None,
            action,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                icon,
                Gtk.ResponseType.OK,
            ),
        )
        choose.set_current_folder(os.curdir)
        mime_filter = Gtk.FileFilter()
        mime_filter.set_name(name)

        for m_regex in mime_types:
            mime_filter.add_pattern(m_regex)

        choose.add_filter(mime_filter)
        choose.show()
        return choose

    def show_summary(self):
        reg = self.get_selected_register()

        if reg:
            SummaryWindow(
                self.widgets, reg, self.active.set_name, self.project
            )


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
