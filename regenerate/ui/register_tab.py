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

from typing import Dict, Optional, Callable
from pathlib import Path

from gi.repository import Gtk, Gdk
from regenerate.db import (
    Register,
    BitField,
    LOGGER,
    RegisterDb,
    ShareType,
    ResetType,
    RegProject,
    BitType,
    REG_EXT,
    OLD_REG_EXT,
)
from regenerate.extras.remap import REMAP_NAME
from regenerate.extras.regutils import (
    calculate_next_address,
    duplicate_register,
)
from .bit_list import BitModel, BitList
from .bitfield_editor import BitFieldEditor
from .enums import BitCol, RegCol
from .module_tab import ModuleTabs
from .parameter_list import ParameterList
from .reg_description import RegisterDescription
from .register_list import RegisterModel, RegisterList
from .summary_window import SummaryWindow
from .filter_mgr import FilterManager
from .file_dialogs import get_new_filename
from .select_sidebar import SelectSidebar


class RegSetWidgets:
    "Track the widgets uses in the register tab"

    def __init__(self, find_obj):
        self.reglist = find_obj("register_list")
        self.regset_list = find_obj("project_list")
        self.notebook = find_obj("module_notebook")
        self.descript = find_obj("scroll_reg_text")
        self.regset_preview = find_obj("scroll_reg_webkit")
        self.descript_warn = find_obj("reg_descr_warn")
        self.bit_warn = find_obj("reg_bit_warn")
        self.reg_notebook = find_obj("reg_notebook")
        self.no_rtl = find_obj("no_rtl")
        self.no_uvm = find_obj("no_uvm")
        self.no_test = find_obj("no_test")
        self.no_reset_test = find_obj("no_reset_test")
        self.no_cover = find_obj("no_cover")
        self.hide_doc = find_obj("hide_doc")
        self.no_sharing = find_obj("no_sharing")
        self.read_access = find_obj("read_access")
        self.write_access = find_obj("write_access")
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
        self.new_regset_button = find_obj("new_regset_button")
        self.add_regset_button = find_obj("add_regset_button")
        self.remove_regset_button = find_obj("remove_regset_button")
        self.add_field_button = find_obj("add_field")
        self.remove_field_button = find_obj("delete_field")
        self.edit_field_button = find_obj("edit_field")
        self.copy_reg_button = find_obj("copy_reg_button")
        self.preview_button = find_obj("preview_button")
        self.add_reg_button = find_obj("add_register_button")
        self.remove_reg_button = find_obj("remove_register_button")


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


class RegSetTab:
    "Register set tab"

    def __init__(
        self,
        find_obj: Callable,
        modified: Callable,
        db_selected_action: Gtk.ActionGroup,
        reg_selected_action: Gtk.ActionGroup,
        field_selected_action: Gtk.ActionGroup,
    ):
        self._modified_callback = modified
        self._db_selected_action = db_selected_action
        self._reg_selected_action = reg_selected_action
        self._field_selected_action = field_selected_action

        self._reg_model: Optional[RegisterModel] = None
        self._modelsort: Optional[Gtk.TreeModelSort] = None

        self._skip_changes = False
        self._widgets = RegSetWidgets(find_obj)

        self._regset_select_notebook = find_obj("regset_select_notebook")

        self._sidebar = SelectSidebar(
            find_obj("regset_sidebar"),
            "Register Sets",
            "regset_select_help.html",
            self.new_regset_callback,
            self.add_regset_callback,
            self.remove_regset_callback,
            self.add_model_callback,
        )
        self._sidebar.set_selection_changed_callback(self._regset_sel_changed)

        self._widgets.reg_notebook.set_sensitive(False)
        self._widgets.reg_notebook.hide()
        self._reg_selected_action.set_sensitive(False)

        self._connect_signals()

        self._module_tabs = ModuleTabs(find_obj, self.set_modified)

        self._parameter_list = ParameterList(
            self._widgets.parameter_list,
            self._widgets.add_regset_param,
            self._widgets.remove_regset_param,
            self.set_parameters_modified,
        )

        self._reglist_obj = RegisterList(
            self._widgets.reglist,
            self._selected_reg_changed,
            self.set_modified,
            self.update_register_addr,
            self.set_register_warn_flags,
        )

        self._bitfield_obj = BitList(
            self._widgets.bitfield_list,
            self.bit_changed,
            self.set_modified,
        )

        self.reg_description = RegisterDescription(
            self._widgets.descript,
            self._widgets.regset_preview,
            self.reg_descript_callback,
        )

        self._regset: Optional[RegisterDb] = None
        self._project: Optional[RegProject] = None
        self._name2status: Dict[str, RegSetStatus] = {}

        self._widgets.filter_obj.set_placeholder_text("Signal Filter")
        self._filter_manage = FilterManager(self._widgets.filter_obj)

        self.clear()

    def _connect_signals(self) -> None:
        "Connect signals to the elements"

        self._widgets.notebook.connect("switch-page", self.reg_page_changed)
        self._widgets.add_field_button.connect(
            "clicked",
            self.add_bit_callback,
        )
        self._widgets.remove_field_button.connect(
            "clicked",
            self.remove_bit_callback,
        )
        self._widgets.edit_field_button.connect(
            "clicked",
            self.edit_bit_callback,
        )
        self._widgets.copy_reg_button.connect(
            "clicked", self.duplicate_register_callback
        )
        self._widgets.no_sharing.connect(
            "toggled", self.no_sharing_toggle_callback
        )
        self._widgets.read_access.connect(
            "toggled", self.read_access_toggle_callback
        )
        self._widgets.write_access.connect(
            "toggled", self.write_access_toggle_callback
        )
        self._widgets.preview_button.connect(
            "clicked",
            self.show_preview_callback,
        )
        self._widgets.add_reg_button.connect(
            "clicked",
            self.add_register_callback,
        )
        self._widgets.remove_reg_button.connect(
            "clicked",
            self.remove_register_callback,
        )

    def filter_visible(self, visible: bool) -> None:
        "Shows or hides the filter object"
        if visible:
            self._widgets.filter_obj.show()
        else:
            self._widgets.filter_obj.hide()

    def reg_page_changed(self, _obj, _page, _page_num: int) -> None:
        """When the notebook page changes, update any fields that are
        out of date due to parameter name changes"""

        self.update_size_parameters()
        self.update_field_parameters()

    def update_field_parameters(self):
        "Update any displayed parameter names if they have changed"
        for row in self._bit_model:
            field = row[BitCol.FIELD]
            if field.reset_type == ResetType.PARAMETER:
                if field.reset_parameter != row[BitCol.RESET]:
                    row[BitCol.RESET] = field.reset_parameter

    def update_size_parameters(self):
        "Change the reset parameters, updating for any name changes"
        if self._reg_model is None:
            return

        for row in self._reg_model:
            reg = row[-1]
            if (
                reg.dimension.is_parameter
                and reg.dimension.int_str() != row[RegCol.DIM]
            ):
                row[RegCol.DIM] = reg.dimension.int_str()

    def set_parameters_modified(self):
        self.set_modified()
        self._reglist_obj.set_parameters(self._regset.parameters.get())
        self._bitfield_obj.set_parameters(self._regset.parameters.get())
        self._selected_reg_changed(None)

    def force_reglist_rebuild(self):
        self._reglist_obj.clear()
        for reg in self._regset.get_all_registers():
            self._reglist_obj.load_reg_into_model(reg)

    def set_modified(self):
        "Sets the modified flag"

        if not self._skip_changes:
            self._regset.modified = True
            self._sidebar.update()
            self._modified_callback()

    def _enable_registers(self, value: bool) -> None:
        """
        Enables UI items when a database has been loaded. This includes
        enabling the register window, the register related buttons, and
        the export menu.
        """
        self._widgets.notebook.set_sensitive(value)
        self._db_selected_action.set_sensitive(value)
        if value:
            self._widgets.reg_notebook.show()
        else:
            self._widgets.reg_notebook.hide()

    def new_regset(self, regset: RegisterDb) -> Optional[Gtk.TreeIter]:
        "Inserts the register set into the tree"

        self._reg_model = RegisterModel()
        filter_model = self._reg_model.filter_new()
        self._modelsort = Gtk.TreeModelSort(filter_model)
        self._filter_manage.change_filter(filter_model, True)

        self._reglist_obj.set_model(self._modelsort)

        for key in regset.get_keys():
            reg = regset.get_register(key)
            if reg:
                self._reg_model.append_register(reg)

        bit_model = BitModel()

        node = self._sidebar.add(regset)
        status = RegSetStatus(
            regset,
            self._reg_model,
            self._modelsort,
            self._filter_manage.get_model(),
            bit_model,
            node,
        )

        self._name2status[regset.uuid] = status
        return node

    def array_changed(self, obj):
        "Callback for the array_is_reg value"
        if self._regset:
            self._regset.array_is_reg = obj.get_active()
            self.set_modified()

    def change_project(self, prj: RegProject) -> None:
        "Change the project"

        self._project = prj
        self._sidebar.set_items(prj.regsets.values())
        self.rebuild_model()
        self.update_display(False)
        self._sidebar.select_path(0)

    def update_sidebar(self):
        self._sidebar.update()

    def rebuild_model(self) -> None:
        "Rebuild the model in the register set"
        if (
            len(self._project.regsets) != self._sidebar.size()
            or len(self._project.regsets) == 0
        ):
            self._sidebar.clear()

            sorted_dict = {
                key: value
                for key, value in sorted(
                    self._project.regsets.items(),
                    key=lambda item: item[1].name,
                )
            }

            for rsid in sorted_dict:
                regset = self._project.regsets[rsid]
                self.new_regset(regset)

    def reg_descript_callback(self, reg: Register):
        self.set_modified()
        self.set_register_warn_flags(reg)

    def update_display(self, show_msg=False):
        old_skip = self._skip_changes
        self._skip_changes = True
        self.redraw(show_msg)
        self._skip_changes = old_skip

    def redraw(self, _show_msg=False):
        """Redraws the information in the register list."""
        if self._regset:
            self._module_tabs.change_db(self._regset, self._project)
            self._parameter_list.set_db(self._regset)
            self._reglist_obj.set_parameters(self._regset.parameters.get())
            self._bitfield_obj.set_parameters(self._regset.parameters.get())
            if self._regset.array_is_reg:
                self._widgets.register_notation.set_active(True)
            else:
                self._widgets.array_notation.set_active(True)
        else:
            self._module_tabs.change_db(None, None)

        if self._project.regsets:
            self._regset_select_notebook.set_current_page(0)
        else:
            self._regset_select_notebook.set_current_page(1)

        self.update_bit_count()
        self.set_description_warn_flag()

    def get_selected_registers(self):
        return self._reglist_obj.get_selected_registers()

    def get_selected_reg_paths(self):
        return self._reglist_obj.get_selected_reg_paths()

    def add_model_callback(self, regset: RegisterDb, node: Gtk.TreeIter):
        if regset.uuid not in self._name2status:

            self._reg_model = RegisterModel()
            filter_model = self._reg_model.filter_new()
            self._modelsort = Gtk.TreeModelSort(filter_model)
            self._filter_manage.change_filter(filter_model, True)

            for key in regset.get_keys():
                reg = regset.get_register(key)
                if reg:
                    self._reg_model.append_register(reg)

            bit_model = BitModel()

            status = RegSetStatus(
                regset,
                self._reg_model,
                self._modelsort,
                self._filter_manage.get_model(),
                bit_model,
                node,
            )

            self._name2status[regset.uuid] = status

    def clear(self):
        self._sidebar.clear()

    def current_regset(self) -> Optional[RegisterDb]:
        return self._regset

    def _regset_sel_changed(self, _obj: Gtk.TreeSelection) -> None:

        self._regset = self._sidebar.get_selected_object()

        old_skip = self._skip_changes
        self._skip_changes = True

        if self._regset:
            status = self._name2status[self._regset.uuid]
            self._reg_model = status.reg_model
            self._filter_manage.change_filter(status.modelfilter)
            self._modelsort = status.modelsort
            self.node = status.node

            self.reg_description.set_project(self._project)

            status = self._name2status[self._regset.uuid]
            self._filter_manage.change_filter(status.modelfilter)
            self._reglist_obj.set_model(status.modelsort)

            self._bit_model = status.bit_model
            self._bitfield_obj.set_model(self._bit_model)

            self.update_display()
            self._enable_registers(True)
        else:
            self._regset = None
            self._reglist_obj.set_model(None)
            self._enable_registers(False)
        self._skip_changes = old_skip

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
                    txt = (
                        f"Missing field description for '{field.name}' "
                        "field of this register. Select the field in the "
                        "Bit Fields table and click on the Edit button "
                        "to add a description."
                    )
                    msg.append(txt)
                    warn_bit = True
                if check_reset(field):
                    txt = f"Missing reset parameter name for '{field.name}'"
                    msg.append(txt)
                    warn_bit = True
        if mark:
            self._widgets.descript_warn.set_property("visible", warn_reg)
            self._widgets.bit_warn.set_property("visible", warn_bit)
        self._reg_model.set_warning_for_register(reg, warn_reg or warn_bit)
        if msg:
            tip = "\n".join(msg)
        else:
            tip = None
        self._reg_model.set_tooltip(reg, tip)

    def _selected_reg_changed(self, _obj):
        """
        GTK callback that checks the selected objects, and then enables the
        appropriate buttons on the interface.
        """
        old_skip = self._skip_changes
        self._skip_changes = True
        reglist = self.get_selected_registers()
        if len(reglist) != 1:
            reg = None
        else:
            reg = reglist[0]

        self.reg_description.set_register(reg)
        if reg:
            self._widgets.reg_notebook.show()
            self._widgets.reg_notebook.set_sensitive(True)
            self._reg_selected_action.set_sensitive(True)
            self._bit_model.clear()
            self._bit_model.register = reg
            self._bitfield_obj.set_mode(reg.share)
            for key in reg.get_bit_field_keys():
                field = reg.get_bit_field(key)
                self._bit_model.append_field(field)

            self._widgets.no_rtl.set_active(reg.flags.do_not_generate_code)
            self._widgets.no_uvm.set_active(reg.flags.do_not_use_uvm)
            self._widgets.no_test.set_active(reg.flags.do_not_test)
            self._widgets.no_reset_test.set_active(reg.flags.do_not_reset_test)
            self._widgets.no_cover.set_active(reg.flags.do_not_cover)
            self._widgets.hide_doc.set_active(reg.flags.hide)

            self.set_register_warn_flags(reg)
            self.set_bits_warn_flag()
            self.set_share(reg)
        else:
            self._widgets.reg_notebook.hide()
            self._widgets.reg_notebook.set_sensitive(False)
            self._reg_selected_action.set_sensitive(False)
        self._skip_changes = old_skip

    def set_share(self, reg):
        if reg.share == ShareType.NONE:
            self._widgets.no_sharing.set_active(True)
        elif reg.share == ShareType.READ:
            self._widgets.read_access.set_active(True)
        else:
            self._widgets.write_access.set_active(True)

    def remove_register_callback(self, _obj: Gtk.Button) -> None:
        self.remove_register()

    def remove_register(self) -> None:
        if self._regset:
            reglist = self._reglist_obj.get_selected_registers()
            self._reglist_obj.delete_selected_node()
            for reg in reglist:
                self._regset.delete_register(reg)
            self.set_modified()

    def add_register_callback(self, _obj: Gtk.Button) -> None:
        self.new_register()

    def new_register(self) -> None:
        dbase = self._regset
        if dbase:
            register = Register()
            register.width = dbase.ports.data_bus_width
            register.address = calculate_next_address(dbase, register.width)
            self.insert_new_register(register)

    def insert_new_register(self, register):
        if self._widgets.notebook.get_current_page() == 0:
            self._reglist_obj.add_new_register(register)
            self._regset.add_register(register)
            self.set_register_warn_flags(register)
            self.set_modified()

    def add_bit_callback(self, _obj: Gtk.Button):
        register = self.get_selected_registers()[0]
        next_pos = register.find_next_unused_bit()

        if next_pos == -1:
            LOGGER.error("All bits are used in this register")
            return

        field = BitField()
        field.lsb = next_pos

        field.msb.set_int(field.lsb)
        field.name = f"BIT{field.lsb}"
        field.output_signal = ""
        if register.share == ShareType.WRITE:
            field.field_type = BitType.WRITE_ONLY

        register.add_bit_field(field)

        self._bitfield_obj.add_new_field(field)
        self.set_modified()
        self.set_register_warn_flags(register)

    def remove_bit_callback(self, _obj: Gtk.Button):
        register = self.get_selected_registers()[0]
        row = self._bitfield_obj.get_selected_row()
        field = self._bit_model.get_bitfield_at_path(row[0])
        register.delete_bit_field(field)
        node = self._bit_model.get_iter(row[0])
        self._bit_model.remove(node)
        self.set_register_warn_flags(register)
        self.set_modified()

    def edit_bit_callback(self, _obj: Gtk.Button):
        register = self.get_selected_registers()[0]
        field = self._bitfield_obj.select_field()
        if field and self._regset:
            BitFieldEditor(
                self._regset,
                register,
                field,
                self.set_field_modified,
                None,  # self.builder,
                None,  # self.top_window,
            )

    def update_register_addr(self, register, new_addr, new_length=0):
        self._regset.delete_register(register)
        register.address = new_addr
        register.ram_size = new_length
        share_reg = self.find_shared_address(register)
        if share_reg:
            if share_reg.share == ShareType.READ:
                register.share = ShareType.WRITE
            else:
                register.share = ShareType.READ
            self.set_share(register)
        self._regset.add_register(register)

    def find_shared_address(self, reg):
        for shared_reg in self._regset.get_all_registers():
            if shared_reg != reg and shared_reg.address == reg.address:
                return shared_reg
        return None

    def set_field_modified(self):
        reg = self.get_selected_registers()[0]
        self.set_register_warn_flags(reg)
        self.set_bits_warn_flag()
        self.set_modified()

    def set_bits_warn_flag(self):
        warn = False
        for row in self._bit_model:
            field = row[BitCol.FIELD]
            icon = check_field(field)
            row[BitCol.ICON] = icon
            if icon:
                warn = True
        return warn

    def update_bit_count(self):
        if self._regset:
            text = f"{self._regset.total_bits()}"
        else:
            text = ""
        self._widgets.reg_count.set_text(text)

    def set_description_warn_flag(self):
        if self._regset:
            warn = self._regset.overview_text == ""
        else:
            warn = False
        self._widgets.mod_descr_warn.set_property("visible", warn)

    def no_sharing_toggle_callback(self, obj):
        if obj.get_active():
            register = self.get_selected_registers()[0]

            if self.duplicate_address(register.address):
                self.set_share(register)
                LOGGER.error(
                    "Register cannot be set to non-sharing "
                    "if it shares an address with another"
                )
            else:
                register.share = ShareType.NONE
                self.set_modified()
            self._bitfield_obj.set_mode(register.share)

    def read_access_toggle_callback(self, obj):
        if obj.get_active():
            register = self.get_selected_registers()[0]

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
            self._bitfield_obj.set_mode(register.share)

    def write_access_toggle_callback(self, obj):
        if obj.get_active():
            register = self.get_selected_registers()[0]

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
            self._bitfield_obj.set_mode(register.share)

    def duplicate_address(self, reg_addr):
        cnt = 0
        for reg in self._regset.get_all_registers():
            if reg.address == reg_addr:
                cnt += 1
        return cnt > 1

    def duplicate_register_callback(self, _obj: Gtk.Button):
        reg = self.get_selected_registers()[0]
        if reg and self._regset:
            reg_copy = duplicate_register(self._regset, reg)
            self._reglist_obj.add_new_register(reg_copy)
            self._regset.add_register(reg_copy)
            self.set_register_warn_flags(reg_copy)
            self.set_modified()

    def bit_changed(self, _obj):
        self._field_selected_action.set_sensitive(True)

    def remove_regset_callback(self, _obj: Gtk.Button):
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        old_skip = self._skip_changes
        self._skip_changes = True

        uuid = self._sidebar.remove_selected()
        self.remove_regset_from_project(uuid)
        self.remove_regset_from_groups(uuid)
        self.set_modified()
        self._skip_changes = old_skip
        self._sidebar.select(0)

    def remove_regset_from_project(self, uuid: str):
        if self._project:
            self._project.remove_register_set(uuid)

    def remove_regset_from_groups(self, uuid: str):
        if self._project:
            for block in self._project.blocks.values():
                block.remove_register_set(uuid)

    def new_regset_callback(self, _obj: Gtk.Button):
        """
        Creates a new database, and initializes the interface.
        """
        name_str = get_new_filename()
        if not name_str or not self._project:
            return

        name = Path(name_str).with_suffix(REG_EXT)

        dbase = RegisterDb()
        dbase.name = name.stem
        dbase.filename = name
        dbase.modified = True

        self._project.new_register_set(dbase, name)
        node = self.new_regset(dbase)
        self._sidebar.select(node)
        # self.set_project_modified()
        return

    def add_regset_callback(self, _obj: Gtk.Button) -> None:
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

                if self._project:
                    name = Path(filename)
                    dbase = RegisterDb(name)
                    dbase.filename = name
                    dbase.modified = True

                    self._project.new_register_set(dbase, name)
                    node = self.new_regset(dbase)
                    self._sidebar.select(node)
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

    def show_preview_callback(self, _obj: Gtk.Button) -> None:
        reg = self.get_selected_registers()[0]

        if reg and self._regset:
            SummaryWindow(
                self._widgets,
                reg,
                self._regset.name,
                self._project,
                self._regset,
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
