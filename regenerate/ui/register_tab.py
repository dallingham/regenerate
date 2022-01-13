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
Provides the register tab
"""

import os

from typing import Dict, Optional, Callable, List, Tuple
from pathlib import Path

from gi.repository import Gtk, Gdk
from regenerate.db import (
    Register,
    BitField,
    LOGGER,
    RegisterSet,
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
from .reg_movement import (
    insert_registers_after,
    insert_register_at,
    copy_parameters,
    copy_registers,
)


class RegSetWidgets:
    "Track the widgets uses in the register tab"

    def __init__(self, find_obj):
        self.top_window = find_obj("regenerate")
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
        self.reorder_field_button = find_obj("reorder-fields")
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

    def __init__(self, container, reg_model, mdlfilter, bmodel, node):
        self.container = container
        self.reg_model = reg_model
        self.modelfilter = mdlfilter
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
        self._bit_model = BitModel()

        self._skip_changes = False
        self._widgets = RegSetWidgets(find_obj)
        self.node: Optional[Gtk.TreeIter] = None

        self._regset_select_notebook = find_obj("regset_select_notebook")

        self._sidebar = SelectSidebar(
            find_obj("regset_sidebar"),
            "Register Sets",
            "regset_select_help.html",
            self._new_regset_callback,
            self._add_regset_callback,
            self._remove_regset_callback,
            self._add_model_callback,
        )
        self._sidebar.set_selection_changed_callback(self._regset_sel_changed)

        self._widgets.reg_notebook.set_sensitive(False)
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
            self._update_register_address,
            self._set_register_warn_flags,
        )

        self._widgets.reglist.connect(
            "button-press-event", self.on_button_press_event
        )

        self._bitfield_obj = BitList(
            self._widgets.bitfield_list,
            self._bit_changed,
            self.set_modified,
        )

        self.reg_description = RegisterDescription(
            self._widgets.descript,
            self._widgets.regset_preview,
            self._reg_descript_callback,
        )

        self._regset: Optional[RegisterSet] = None
        self._project: Optional[RegProject] = None
        self._name2status: Dict[str, RegSetStatus] = {}

        self._widgets.filter_obj.set_placeholder_text("Signal Filter")
        self._filter_manage = FilterManager(self._widgets.filter_obj)

        self._copied_source = None
        self._copied_registers: List[Register] = []

        self._menu = self._build_menu()

        self.clear()

    def _connect_signals(self) -> None:
        "Connect signals to the elements"

        self._widgets.notebook.connect("switch-page", self._reg_page_changed)
        self._widgets.add_field_button.connect(
            "clicked",
            self._add_bit_callback,
        )
        self._widgets.remove_field_button.connect(
            "clicked",
            self._remove_bit_callback,
        )
        self._widgets.reorder_field_button.connect(
            "clicked",
            self._reorder_callback,
        )
        self._widgets.edit_field_button.connect(
            "clicked",
            self._edit_bit_callback,
        )
        self._widgets.copy_reg_button.connect(
            "clicked", self._duplicate_reg_callback
        )
        self._widgets.no_sharing.connect("toggled", self._no_sharing_callback)
        self._widgets.read_access.connect(
            "toggled", self._read_access_callback
        )
        self._widgets.write_access.connect(
            "toggled", self._write_access_callback
        )
        self._widgets.preview_button.connect(
            "clicked",
            self._show_preview_callback,
        )
        self._widgets.add_reg_button.connect(
            "clicked",
            self._add_register_callback,
        )
        self._widgets.remove_reg_button.connect(
            "clicked",
            self._remove_register_callback,
        )
        self._widgets.reglist.connect(
            "key-press-event",
            self._treeview_key_press_callback,
        )

    def on_button_press_event(self, _obj, event):
        "Callback for a button press on the register list. Display the menu"

        if event.button == 3:
            self._menu.popup(
                None, None, None, 1, 0, Gtk.get_current_event_time()
            )
            return True
        return False

    def _build_menu(self) -> Gtk.Menu:
        menu = Gtk.Menu()

        item = Gtk.MenuItem("Add new register at selected address")
        item.connect("activate", self.on_insert_new_register)
        item.show()
        menu.add(item)

        item = Gtk.MenuItem("Copy selected registers")
        item.connect("activate", self.on_copy_registers)
        item.show()
        menu.add(item)

        item = Gtk.MenuItem("Paste copied registers")
        item.connect("activate", self.on_paste_registers)
        item.show()
        menu.add(item)

        item = Gtk.MenuItem("Align selected addresses to bus width")
        item.connect("activate", self.on_align_addresses)
        item.show()
        menu.add(item)

        item = Gtk.MenuItem("Compact selected addresses")
        item.connect("activate", self.on_compact_tightly)
        item.show()
        menu.add(item)

        return menu

    def on_insert_new_register(self, _button: Gtk.Button) -> None:
        """
        Insert a new, empty register when the button is clicked.

        Parameters:
            _button (Gtk.Button): button that triggered the event (unused)

        """
        if self._regset is None or self._reg_model is None:
            return

        selected_list = self.get_selected_registers()

        if len(selected_list) != 1:
            LOGGER.error(
                "Inserting a register requires a sinle register to be selected"
            )
            return
        selected_reg = selected_list[0]

        new_register = insert_register_at(self._regset, selected_reg)

        self.force_reglist_rebuild(new_register)
        path = self._reg_model.get_path_from_register(new_register)
        self._reglist_obj.select_row(path)
        self._widgets.reglist.scroll_to_cell(path, None, True, 0.5, 0.0)

    def on_copy_registers(self, _button: Gtk.Button) -> None:
        "Stores references to the registers to be copied"
        self.copy_selected_registers()

    def on_paste_registers(self, _button: Gtk.Button) -> None:
        "Inserts the stored registers into current register set"
        self.paste_copied_registers()

    def on_align_addresses(self, _button: Gtk.Button) -> None:
        "Aligns each register on a bus width boundary"

        regset = self.current_regset()
        if regset is None:
            return

        size = regset.ports.data_bus_width // 8
        addr = 0

        for reg in regset.get_all_registers():
            reg.address = addr
            addr += size
        self.set_modified()
        reg_list = self._reglist_obj.get_selected_registers()
        if reg_list:
            self.force_reglist_rebuild(reg_list[0])
        else:
            self.force_reglist_rebuild(None)

    def on_compact_tightly(self, _button: Gtk.Button) -> None:
        "Packs the selected registers tightly together"

        regset = self.current_regset()
        if regset is None:
            return

        if not _sequential_greater_than_2(self):
            return

        reglist = self.get_selected_registers()

        address = reglist[0].address
        size = reglist[0].width // 8
        bus_width = regset.ports.data_bus_width // 8

        for reg in reglist[1:]:
            if address + size <= _next_boundary(address, bus_width):
                reg.address = address + size
            else:
                reg.address = _next_boundary(address, bus_width)
            address += size
            size = reg.width // 8
        self.force_reglist_rebuild(reglist[0])
        self.set_modified()

    def _treeview_key_press_callback(
        self, _obj: Gtk.TreeView, event: Gdk.EventKey
    ) -> bool:
        "Catch C-c to copy registers and C-v to paste_registers"

        if (
            event.keyval == Gdk.keyval_from_name("c")
            and event.state == Gdk.ModifierType.CONTROL_MASK
        ):
            self.copy_selected_registers()
            return True
        if (
            event.keyval == Gdk.keyval_from_name("v")
            and event.state == Gdk.ModifierType.CONTROL_MASK
        ):
            self.paste_copied_registers()
            return True
        return False

    def _reg_page_changed(self, _obj, _page, _page_num: int) -> None:
        """When the notebook page changes, update any fields that are
        out of date due to parameter name changes"""

        self._update_size_parameters()
        self._update_field_parameters()
        self._reglist_obj.update_bit_width(self._regset.ports.data_bus_width)

    def _update_field_parameters(self) -> None:
        "Update any displayed parameter names if they have changed"
        for row in self._bit_model:
            field = row[BitCol.FIELD]
            if (
                field.reset_type == ResetType.PARAMETER
                and field.reset_parameter != row[BitCol.RESET]
            ):
                row[BitCol.RESET] = field.reset_parameter

    def _update_size_parameters(self) -> None:
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

    def _enable_registers(self, value: bool) -> None:
        """
        Enables UI items when a database has been loaded.

        This includes enabling the register window, the register
        related buttons, and the export menu.

        Parameters:
           value (bool): True enables the register elements
        """
        self._widgets.notebook.set_sensitive(value)
        self._db_selected_action.set_sensitive(value)
        self._widgets.reg_notebook.set_sensitive(value)
        if not value:
            self._widgets.bitfield_list.get_model().clear()

    def _reg_descript_callback(self, reg: Register) -> None:
        "Called when the description field has been edited"
        self.set_modified()
        self._set_register_warn_flags(reg)

    def _add_model_callback(
        self, regset: RegisterSet, node: Gtk.TreeIter
    ) -> None:
        "Called when a new register set has been added to the sidebar"

        if regset.uuid not in self._name2status:

            self._reg_model = RegisterModel(regset.ports.data_bus_width)
            filter_model = self._reg_model.filter_new()
            self._filter_manage.change_filter(filter_model, True)

            for key in regset.get_keys():
                reg = regset.get_register(key)
                if reg:
                    self._reg_model.append_register(reg)

            status = RegSetStatus(
                regset,
                self._reg_model,
                self._filter_manage.get_model(),
                BitModel(),
                node,
            )

            self._name2status[regset.uuid] = status

    def _regset_sel_changed(self, _obj: Gtk.TreeSelection) -> None:
        "Called when the register set selection has changed"

        self._regset = self._sidebar.get_selected_object()

        old_skip = self._skip_changes
        self._skip_changes = True

        if self._regset:
            self._update_on_selection_changed()
        else:
            self._regset = None
            self._reglist_obj.set_model(None)
            self._enable_registers(False)
        self._skip_changes = old_skip

    def _update_on_selection_changed(self) -> None:
        """
        Update the display when the register set selection is changed.

        Updates the register list and the bit model, and changes the
        filter.

        """
        status = self._name2status[self._regset.uuid]
        self._reg_model = status.reg_model
        self._filter_manage.change_filter(status.modelfilter)
        self.node = status.node

        self.reg_description.set_project(self._project)

        status = self._name2status[self._regset.uuid]
        self._filter_manage.change_filter(status.modelfilter)
        self._reglist_obj.set_model(status.modelfilter)

        self._bit_model = status.bit_model
        self._bitfield_obj.set_model(self._bit_model)

        self.update_display()
        self._enable_registers(True)

    def _set_register_warn_flags(self, reg, mark=True) -> None:
        "Sets the warning messages and flags"

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
                if _check_field(field):
                    txt = (
                        f"Missing field description for '{field.name}' "
                        "field of this register. Select the field in the "
                        "Bit Fields table and click on the Edit button "
                        "to add a description."
                    )
                    msg.append(txt)
                    warn_bit = True
                if _check_reset(field):
                    txt = f"Missing reset parameter name for '{field.name}'"
                    msg.append(txt)
                    warn_bit = True
        if mark:
            self._widgets.descript_warn.set_property("visible", warn_reg)
            self._widgets.bit_warn.set_property("visible", warn_bit)
        self._reg_model.set_warning_for_register(reg, warn_reg or warn_bit)

        if msg:
            self._reg_model.set_tooltip(reg, "\n".join(msg))
        else:
            self._reg_model.set_tooltip(reg, None)

    def _selected_reg_changed(self, _obj) -> None:
        """
        GTK callback that checks the selected objects, and then enables the
        appropriate buttons on the interface.
        """
        old_skip = self._skip_changes
        self._skip_changes = True
        reglist = self.get_selected_registers()
        reg = None if len(reglist) != 1 else reglist[0]
        self.reg_description.set_register(reg)
        if reg:
            self._update_on_selected_reg_change(reg)
        else:
            self._widgets.reg_notebook.set_sensitive(False)
            self._reg_selected_action.set_sensitive(False)
            self._widgets.bitfield_list.get_model().clear()
        self._skip_changes = old_skip

    def _redraw_bit_table(self, reg: Register) -> None:
        self._bit_model.clear()
        self._bit_model.register = reg
        self._bitfield_obj.set_mode(reg.share)
        for key in reg.get_bit_field_keys():
            field = reg.get_bit_field(key)
            self._bit_model.append_field(field)

    def _update_on_selected_reg_change(self, reg):
        self._widgets.reg_notebook.show()
        self._widgets.reg_notebook.set_sensitive(True)
        self._reg_selected_action.set_sensitive(True)
        self._redraw_bit_table(reg)

        self._widgets.no_rtl.set_active(reg.flags.do_not_generate_code)
        self._widgets.no_uvm.set_active(reg.flags.do_not_use_uvm)
        self._widgets.no_test.set_active(reg.flags.do_not_test)
        self._widgets.no_reset_test.set_active(reg.flags.do_not_reset_test)
        self._widgets.no_cover.set_active(reg.flags.do_not_cover)
        self._widgets.hide_doc.set_active(reg.flags.hide)

        self._set_register_warn_flags(reg)
        self._set_bits_warn_flag()
        self._set_share(reg)

    def _set_share(self, reg: Register) -> None:
        "Sets the sharing radio button based off the register value"

        if reg.share == ShareType.NONE:
            self._widgets.no_sharing.set_active(True)
        elif reg.share == ShareType.READ:
            self._widgets.read_access.set_active(True)
        else:
            self._widgets.write_access.set_active(True)

    def _remove_register_callback(self, _obj: Gtk.Button) -> None:
        "Called when the remove register button has been pressed"
        self.remove_register()

    def remove_register(self) -> None:
        """
        Remove the selected register from the interface and database.
        """
        if self._regset:
            for reg in self._reglist_obj.get_selected_registers():
                self._regset.delete_register(reg)
            self._reglist_obj.delete_selected_node()
            self.set_modified()

    def _add_register_callback(self, _obj: Gtk.Button) -> None:
        """
        Add a new register when the button is pressed

        Parameters:
            _obj (Gtk.Button): GTK button that caused the callback (unused)

        """
        self.new_register()

    def _add_bit_callback(self, _obj: Gtk.Button) -> None:
        """
        Add a new bit field to the selected register when the button is pressed

        Parameters:
            _obj (Gtk.Button): GTK button that caused the callback (unused)

        """
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
        self._set_register_warn_flags(register)

    def _reorder_callback(self, _obj: Gtk.Button) -> None:
        from .bit_reorder import ReorderFields

        ReorderFields(self.get_selected_registers()[0], self._reorder_update)

    def _reorder_update(self, register: Register) -> None:
        self._redraw_bit_table(register)
        self.set_modified()

    def _remove_bit_callback(self, _obj: Gtk.Button) -> None:
        """
        Remove the selected bits from the register when the button is pressed.

        Parameters:
            _obj (Gtk.Button): GTK button that caused the callback (unused)

        """
        register = self.get_selected_registers()[0]
        field_list = self._bitfield_obj.selected_fields()
        if self._regset:
            for field in field_list:
                register.delete_bit_field(field)

            for row in reversed(self._bitfield_obj.get_selected_rows()):
                node = self._bit_model.get_iter(row)
                self._bit_model.remove(node)
            self._set_register_warn_flags(register)
            self.set_modified()

    def _edit_bit_callback(self, _obj: Gtk.Button) -> None:
        """
        Bring up the Edit Bitfield Window when the button is pressed

        Parameters:
            _obj (Gtk.Button): GTK button that caused the callback (unused)

        """
        register = self.get_selected_registers()[0]
        field_list = self._bitfield_obj.selected_fields()
        if self._regset:
            for field in field_list:
                BitFieldEditor(
                    self._regset,
                    register,
                    field,
                    self._set_field_modified,
                    self._widgets.top_window,
                )

    def _find_shared_address(self, reg: Register) -> Optional[Register]:
        """
        Finds the register that shares the same address.

        Search the register list for a register that is not the same register,
        yet shares the same address.

        Parameters:
           reg (Register): Register that is looking for its shared register

        Returns:
           Optional[Register]: Returns the register if found, else None

        """
        if self._regset:
            reglist = self._regset.get_all_registers()
            if reglist:
                for shared_reg in reglist:
                    if (
                        shared_reg.uuid != reg.uuid
                        and shared_reg.address == reg.address
                    ):
                        return shared_reg
        return None

    def _set_field_modified(self):
        reg = self.get_selected_registers()[0]
        self._set_register_warn_flags(reg)
        self._set_bits_warn_flag()
        self.set_modified()

    def _set_bits_warn_flag(self):
        warn = False
        for row in self._bit_model:
            icon = _check_field(row[BitCol.FIELD])
            row[BitCol.ICON] = icon
            if icon:
                warn = True
        return warn

    def _no_sharing_callback(self, obj):
        if obj.get_active():
            register = self.get_selected_registers()[0]

            if self._duplicate_address(register.address):
                self._set_share(register)
                LOGGER.error(
                    "Register cannot be set to non-sharing "
                    "if it shares an address with another"
                )
            else:
                register.share = ShareType.NONE
                self.set_modified()
            self._bitfield_obj.set_mode(register.share)

    def _read_access_callback(self, obj):
        if obj.get_active():
            register = self.get_selected_registers()[0]

            other = self._find_shared_address(register)
            if other and other.share != ShareType.WRITE:
                self._set_share(register)
                LOGGER.error("The shared register is not of Write Access type")
            elif register.is_completely_read_only():
                register.share = ShareType.READ
                self.set_modified()
            else:
                self._set_share(register)
                LOGGER.error("All bits in the register must be read only")
            self._bitfield_obj.set_mode(register.share)

    def _write_access_callback(self, obj):
        if obj.get_active():
            register = self.get_selected_registers()[0]

            other = self._find_shared_address(register)
            if other and other.share != ShareType.READ:
                self._set_share(register)
                LOGGER.error("The shared register is not of Read Access type")
            elif register.is_completely_write_only():
                register.share = ShareType.WRITE
                self.set_modified()
            else:
                self._set_share(register)
                LOGGER.error("All bits in the register must be write only")
            self._bitfield_obj.set_mode(register.share)

    def _duplicate_reg_callback(self, _obj: Gtk.Button) -> None:
        reg = self.get_selected_registers()[0]
        if reg and self._regset:
            reg_copy = duplicate_register(self._regset, reg)
            self._reglist_obj.add_new_register(reg_copy)
            self._regset.add_register(reg_copy)
            self._set_register_warn_flags(reg_copy)
            self.set_modified()

    def _show_preview_callback(self, _obj: Gtk.Button) -> None:
        reg = self.get_selected_registers()[0]

        if reg and self._regset:
            SummaryWindow(
                self._widgets,
                reg,
                self._regset.name,
                self._project,
                self._regset,
            )

    def _insert_new_register(self, register):
        if self._widgets.notebook.get_current_page() == 0:
            self._reglist_obj.add_new_register(register)
            self._regset.add_register(register)
            self._set_register_warn_flags(register)
            self.set_modified()

    def _set_description_warn_flag(self):
        warn = self._regset.overview_text == "" if self._regset else False
        self._widgets.mod_descr_warn.set_property("visible", warn)

    def _duplicate_address(self, reg_addr: int) -> int:
        cnt = sum(
            reg.address == reg_addr for reg in self._regset.get_all_registers()
        )
        return cnt > 1

    def _update_register_address(self, register, new_addr, new_length=0):
        self._regset.delete_register(register)
        register.address = new_addr
        register.ram_size = new_length
        share_reg = self._find_shared_address(register)
        if share_reg:
            if share_reg.share == ShareType.READ:
                register.share = ShareType.WRITE
            else:
                register.share = ShareType.READ
            self._set_share(register)
        self._regset.add_register(register)

    def _bit_changed(self, _obj) -> None:
        self._field_selected_action.set_sensitive(True)

    def _remove_regset_callback(self, _obj: Gtk.Button):
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        old_skip = self._skip_changes
        self._skip_changes = True

        uuid = self._sidebar.remove_selected()
        self._remove_regset_from_project(uuid)
        self._remove_regset_from_groups(uuid)
        self._skip_changes = old_skip
        self._sidebar.select(0)
        self.set_modified()

    def _remove_regset_from_project(self, uuid: str) -> None:
        if self._project:
            self._project.remove_register_set(uuid)

    def _remove_regset_from_groups(self, uuid: str) -> None:
        if self._project:
            for block in self._project.blocks.values():
                block.remove_register_set(uuid)

    def _new_regset_callback(self, _obj: Gtk.Button):
        """
        Creates a new database, and initializes the interface.
        """
        name_str = get_new_filename()
        if name_str and self._project:
            regset = RegisterSet()
            regset.filename = Path(name_str).with_suffix(REG_EXT)
            regset.name = regset.filename.stem
            regset.modified = True

            self._project.new_register_set(regset, regset.filename)
            node = self.new_regset(regset)
            self._sidebar.select(node)

    def _add_regset_callback(self, _obj: Gtk.Button) -> None:
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        choose = _create_open_selector(
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
                    dbase = RegisterSet(name)
                    dbase.filename = name
                    dbase.modified = True

                    self._project.new_register_set(dbase, name)
                    node = self.new_regset(dbase)
                    self._sidebar.select(node)
        choose.destroy()

    def filter_visible(self, visible: bool) -> None:
        "Shows or hides the filter object"
        if visible:
            self._widgets.filter_obj.show()
        else:
            self._widgets.filter_obj.hide()

    def selected_regset(self) -> Optional[RegisterSet]:
        "Returns the selected register set"
        return self._regset

    def set_parameters(self, parameters) -> None:
        "Sets the parameters associated with the tab"

        self._reglist_obj.set_parameters(parameters)
        self._bitfield_obj.set_parameters(parameters)

    def set_parameters_regset(self, regset: RegisterSet) -> None:
        "Sets the register set associated with the parameter list"
        self._parameter_list.set_db(regset)

    def set_parameters_modified(self) -> None:
        "Mark the parameters as modified, and reset the parameter lists"

        self.set_modified()
        self._reglist_obj.set_parameters(self._regset.parameters.get())
        self._bitfield_obj.set_parameters(self._regset.parameters.get())
        self._selected_reg_changed(None)

    def force_reglist_rebuild(self, register: Optional[Register]) -> None:
        "Force a rebuild of the register model"
        self._reglist_obj.rebuild_model(register)

    def set_modified(self) -> None:
        "Sets the modified flag"

        if not self._skip_changes:
            self._regset.modified = True
            self._sidebar.update()
            self._modified_callback()

    def new_regset(self, regset: RegisterSet) -> Optional[Gtk.TreeIter]:
        "Inserts the register set into the tree"

        self._reg_model = RegisterModel(regset.ports.data_bus_width)
        filter_model = self._reg_model.filter_new()
        self._filter_manage.change_filter(filter_model, True)

        self._reglist_obj.set_model(filter_model)

        for reg in regset.get_all_registers():
            self._reg_model.append_register(reg)

        node = self._sidebar.add(regset)
        status = RegSetStatus(
            regset,
            self._reg_model,
            self._filter_manage.get_model(),
            BitModel(),
            node,
        )

        self._name2status[regset.uuid] = status
        return node

    def array_changed(self, obj) -> None:
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

    def update_sidebar(self) -> None:
        "Updates the sidebar"
        self._sidebar.update()

    def rebuild_model(self) -> None:
        "Rebuild the model in the register set"

        if self._project and (
            len(self._project.regsets) != self._sidebar.size()
            or len(self._project.regsets) == 0
        ):
            self._sidebar.clear()

            sorted_dict = sorted(
                self._project.regsets.items(),
                key=lambda item: item[1].name,
            )

            for rsid in sorted_dict:
                regset = self._project.regsets[rsid]
                self.new_regset(regset)

    def update_display(self, show_msg=False) -> None:
        "Redraw the display, turning off changes"

        old_skip = self._skip_changes
        self._skip_changes = True
        self.redraw(show_msg)
        self._skip_changes = old_skip

    def redraw(self, _show_msg=False):
        """Redraws the information in the register list."""

        if self._regset:
            self._redraw_when_regset_active()
        else:
            self._module_tabs.change_db(None, None)

        if self._project.regsets:
            self._regset_select_notebook.set_current_page(0)
        else:
            self._regset_select_notebook.set_current_page(1)

        self.update_bit_count()
        self._set_description_warn_flag()

    def _redraw_when_regset_active(self):
        self._module_tabs.change_db(self._regset, self._project)
        self._parameter_list.set_db(self._regset)
        self._reglist_obj.set_parameters(self._regset.parameters.get())
        self._reglist_obj.update_bit_width(self._regset.ports.data_bus_width)
        self._bitfield_obj.set_parameters(self._regset.parameters.get())
        if self._regset.array_is_reg:
            self._widgets.register_notation.set_active(True)
        else:
            self._widgets.array_notation.set_active(True)

    def get_selected_registers(self) -> List[Register]:
        "Returns the list of selected registers"
        return self._reglist_obj.get_selected_registers()

    def get_selected_reg_paths(self) -> List[Tuple[Gtk.TreePath, Register]]:
        "Returns a list of the tree paths and the associated register"
        return self._reglist_obj.get_selected_reg_paths()

    def clear(self) -> None:
        "Clears the sidebar model"
        self._sidebar.clear()

    def current_regset(self) -> Optional[RegisterSet]:
        "Returns the selected register set"
        return self._regset

    def new_register(self) -> None:
        "Adds a new, empty register to the interface and database"

        if self._regset:
            register = Register()
            register.width = self._regset.ports.data_bus_width
            register.address = calculate_next_address(
                self._regset, register.width
            )
            self._insert_new_register(register)

    def update_bit_count(self):
        "Updates the bit count"

        if self._regset:
            self._widgets.reg_count.set_text(f"{self._regset.total_bits()}")
        else:
            self._widgets.reg_count.set_text("")

    def copy_selected_registers(self) -> None:
        "Copy the selected registers from the active register set"

        if self._regset:
            self._copied_source = self._regset
            self._copied_registers = self.get_selected_registers()
            LOGGER.warning("Copied %d registers", len(self._copied_registers))

    def paste_copied_registers(self) -> None:
        "Insert the copied registers at the selected point in the active set"

        if self._regset is None:
            return

        if (
            self._copied_source
            and self._copied_source.uuid != self._regset.uuid
        ):
            self._paste_copied_registers_to_different_regset()

    def _paste_copied_registers_to_different_regset(self):
        new_list, new_params = copy_registers(
            self._regset, self._copied_registers
        )
        param_old_to_new = copy_parameters(self._regset, new_params)

        selected_regs = self.get_selected_registers()

        first_reg = new_list[0]

        if selected_regs:
            insert_registers_after(
                self._regset, new_list, selected_regs[0], param_old_to_new
            )
        else:
            insert_registers_after(
                self._regset, new_list, None, param_old_to_new
            )
        for reg in new_list:
            self._reglist_obj.load_reg_into_model(reg)

        if len(param_old_to_new) > 0:
            LOGGER.warning(
                "Inserted %d registers, %d parameters",
                len(new_list),
                len(param_old_to_new),
            )
        elif len(new_list) == 1:
            LOGGER.warning("Inserted 1 register")
        else:
            LOGGER.warning("Inserted %d registers", len(new_list))

        self.force_reglist_rebuild(first_reg)
        self.set_modified()
        self.update_display()


def _next_boundary(address: int, width: int) -> int:
    "Returns next bus width boundary"
    return ((address // width) * width) + width


def _is_contiguous(path_list) -> bool:
    "Returns True if the numbers in the list are sequential"
    return sorted(path_list) == list(range(min(path_list), max(path_list) + 1))


def _sequential_greater_than_2(regtab: RegSetTab) -> bool:
    "Checks that the list is sequential and has more than two elements"

    if not _is_contiguous(regtab.get_selected_reg_paths()):
        LOGGER.error("Selected registers must be contiguous to be compacted")
        return False

    if len(regtab.get_selected_registers()) < 2:
        LOGGER.error(
            "Compaction requires a minimum of 2 registers be selected"
        )
        return False

    return True


def _check_field(field):
    "Returns the icon to used based of the description"
    if field.description.strip() == "":
        return Gtk.STOCK_DIALOG_WARNING
    return None


def _check_reset(field):
    "Returns the icon to used based of the parameter name"
    if (
        field.reset_type == ResetType.PARAMETER
        and field.reset_parameter.strip() == ""
    ):
        return Gtk.STOCK_DIALOG_WARNING
    return None


def _create_open_selector(title: str, name: str, mime_types: List[str]):
    """
    Creates a file save selector, using the mime type and regular
    expression to control the selector.
    """
    choose = Gtk.FileChooserDialog(
        title,
        None,
        Gtk.FileChooserAction.OPEN,
        (
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
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
