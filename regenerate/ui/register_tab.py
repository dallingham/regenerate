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

from typing import Dict, Optional, Callable, Tuple
from pathlib import Path

from gi.repository import Gtk, Pango
from regenerate.settings.paths import HELP_PATH
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
from .columns import ReadOnlyColumn
from .enums import SelectCol, BitCol, RegCol
from .module_tab import ModuleTabs
from .parameter_list import ParameterList
from .reg_description import RegisterDescription
from .register_list import RegisterModel, RegisterList
from .summary_window import SummaryWindow
from .filter_mgr import FilterManager
from .file_dialogs import get_new_filename
from .select_model import SelectModel


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


class RegSetList:
    """Register List list manager"""

    def __init__(self, obj: Gtk.TreeView, selection_callback: Callable):

        self.prj: Optional[RegProject] = None

        self._obj = obj
        self._obj.get_selection().connect("changed", selection_callback)
        self._obj.set_reorderable(True)
        self._model: Optional[SelectModel] = None
        self._build_prj_window()

    def _build_prj_window(self):
        """Build the project window"""

        column = ReadOnlyColumn("Register Sets", 1)
        column.renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column.renderer.set_padding(6, 3)
        column.set_min_width(140)
        column.set_cell_data_func(column.renderer, _set_format)
        self._obj.append_column(column)

    def set_model(self, model: SelectModel):
        """Sets the model"""

        self._model = model
        self._obj.set_model(model)

    def get_selected(self) -> Tuple[SelectModel, Gtk.TreeIter]:
        """Return the selected object"""
        return self._obj.get_selection().get_selected()

    def select(self, node: Gtk.TreeIter) -> None:
        """Select the specified row"""

        selection = self._obj.get_selection()
        if node and selection:
            selection.select_iter(node)

    def select_path(self, path: str) -> None:
        """Select based on path"""

        selection = self._obj.get_selection()
        selection.select_path(path)

    def change_project(self, prj: RegProject) -> None:
        "Change the project"
        self.prj = prj


def _set_format(
    _col: ReadOnlyColumn,
    renderer: Gtk.CellRendererText,
    model: SelectModel,
    titer: Gtk.TreeIter,
    _data,
):
    "Determines if the text should be highlighted"
    if model.get_value(titer, 0):
        renderer.set_property("weight", Pango.Weight.BOLD)
        renderer.set_property("style", Pango.Style.ITALIC)
    else:
        renderer.set_property("weight", Pango.Weight.NORMAL)
        renderer.set_property("style", Pango.Style.NORMAL)


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
        self.modified_callback = modified
        self.db_selected_action = db_selected_action
        self.reg_selected_action = reg_selected_action
        self.field_selected_action = field_selected_action

        self.reg_model: Optional[RegisterModel] = None
        self.modelsort: Optional[Gtk.TreeModelSort] = None

        self.skip_changes = False
        self.reg_set_model = None
        self.widgets = RegSetWidgets(find_obj)

        self.widgets.reg_notebook.set_sensitive(False)
        self.widgets.reg_notebook.hide()
        self.reg_selected_action.set_sensitive(False)

        self.connect_signals()

        self.regset_select_notebook = find_obj("regset_select_notebook")
        self.regset_select_notebook.set_show_tabs(False)
        self.regset_select_help = find_obj("regset_select_help")
        help_path = Path(HELP_PATH) / "regset_select_help.html"
        try:
            with help_path.open() as ifile:
                self.regset_select_help.load_html(ifile.read(), "text/html")
        except IOError:
            pass

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

        self.regset: Optional[RegisterDb] = None
        self.project: Optional[RegProject] = None
        self.name2status: Dict[str, RegSetStatus] = {}

        self.widgets.filter_obj.set_placeholder_text("Signal Filter")
        self.filter_manage = FilterManager(self.widgets.filter_obj)

        self.clear()

    def connect_signals(self) -> None:
        "Connect signals to the elements"

        self.widgets.notebook.connect("switch-page", self.reg_page_changed)
        self.widgets.add_regset_button.connect(
            "clicked", self.add_regset_callback
        )
        self.widgets.remove_regset_button.connect(
            "clicked", self.remove_regset_callback
        )
        self.widgets.new_regset_button.connect(
            "clicked", self.new_regset_callback
        )
        self.widgets.add_field_button.connect(
            "clicked",
            self.add_bit_callback,
        )
        self.widgets.remove_field_button.connect(
            "clicked",
            self.remove_bit_callback,
        )
        self.widgets.edit_field_button.connect(
            "clicked",
            self.edit_bit_callback,
        )
        self.widgets.copy_reg_button.connect(
            "clicked", self.duplicate_register_callback
        )
        self.widgets.no_sharing.connect(
            "toggled", self.no_sharing_toggle_callback
        )
        self.widgets.read_access.connect(
            "toggled", self.read_access_toggle_callback
        )
        self.widgets.write_access.connect(
            "toggled", self.write_access_toggle_callback
        )
        self.widgets.preview_button.connect(
            "clicked",
            self.show_preview_callback,
        )
        self.widgets.add_reg_button.connect(
            "clicked",
            self.add_register_callback,
        )
        self.widgets.remove_reg_button.connect(
            "clicked",
            self.remove_register_callback,
        )

    def filter_visible(self, visible: bool) -> None:
        "Shows or hides the filter object"
        if visible:
            self.widgets.filter_obj.show()
        else:
            self.widgets.filter_obj.hide()

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
        if self.reg_model is None:
            return

        for row in self.reg_model:
            reg = row[-1]
            if (
                reg.dimension.is_parameter
                and reg.dimension.int_str() != row[RegCol.DIM]
            ):
                row[RegCol.DIM] = reg.dimension.int_str()

    def set_parameters_modified(self):
        self.set_modified()
        self.reglist_obj.set_parameters(self.regset.parameters.get())
        self.bitfield_obj.set_parameters(self.regset.parameters.get())
        self.selected_reg_changed(None)

    def set_modified(self):
        "Sets the modified flag"

        if not self.skip_changes:
            self.regset.modified = True
            self.reg_set_model.set_markup(self.node, True)

            # update register set names in the register model
            for row in self.reg_set_model:
                row[1] = row[-1].name

            self.modified_callback()

    def enable_registers(self, value: bool) -> None:
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

    def new_regset(self, regset: RegisterDb) -> Optional[Gtk.TreeIter]:
        "Inserts the register set into the tree"

        if self.reg_set_model is None:
            return None

        self.reg_model = RegisterModel()
        filter_model = self.reg_model.filter_new()
        self.modelsort = Gtk.TreeModelSort(filter_model)
        self.filter_manage.change_filter(filter_model, True)

        self.reglist_obj.set_model(self.modelsort)

        for key in regset.get_keys():
            reg = regset.get_register(key)
            if reg:
                self.reg_model.append_register(reg)

        bit_model = BitModel()

        node = self.reg_set_model.add(regset)
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
        "Callback for the array_is_reg value"
        if self.regset:
            self.regset.array_is_reg = obj.get_active()
            self.set_modified()

    def change_project(self, prj):
        "Change the project"

        if id(prj) != id(self.project):
            self.reg_set_obj.change_project(prj)
            self.project = prj
            self.name2status = {}
            self.rebuild_model()
        self.update_display(False)
        self.reg_set_obj.select_path(0)

    def rebuild_model(self):
        "Rebuild the model in the register set"
        if (
            len(self.project.regsets) != len(self.reg_set_model)
            or len(self.project.regsets) == 0
        ):
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

    def update_display(self, show_msg=False):
        old_skip = self.skip_changes
        self.skip_changes = True
        self.redraw(show_msg)
        self.skip_changes = old_skip

    def redraw(self, show_msg=False):
        """Redraws the information in the register list."""
        if self.regset:
            self.module_tabs.change_db(self.regset, self.project)
            self.parameter_list.set_db(self.regset)
            self.reglist_obj.set_parameters(self.regset.parameters.get())
            self.bitfield_obj.set_parameters(self.regset.parameters.get())
            if self.regset.array_is_reg:
                self.widgets.register_notation.set_active(True)
            else:
                self.widgets.array_notation.set_active(True)
        else:
            self.module_tabs.change_db(None, None)
        self.rebuild_model()

        if self.project.regsets:
            self.regset_select_notebook.set_current_page(0)
        else:
            self.regset_select_notebook.set_current_page(1)

        self.update_bit_count()
        self.set_description_warn_flag()

    def get_selected_register(self):
        return self.reglist_obj.get_selected_register()

    def clear(self):
        self.reg_set_model = SelectModel()
        self.reg_set_obj.set_model(self.reg_set_model)

    def regset_sel_changed(self, _obj):
        model, node = self.reg_set_obj.get_selected()
        if node:
            self.regset = model[node][SelectCol.OBJ]
        else:
            self.regset = None

        old_skip = self.skip_changes
        self.skip_changes = True

        if self.regset:
            self.regset.reg_select = self.reglist_obj.get_selected_row()
            self.regset.bit_select = self.bitfield_obj.get_selected_row()

            status = self.name2status[self.regset.uuid]
            self.reg_model = status.reg_model
            self.filter_manage.change_filter(status.modelfilter)
            self.modelsort = status.modelsort
            self.node = status.node

            self.reg_description.set_project(self.project)

            status = self.name2status[self.regset.uuid]
            self.filter_manage.change_filter(status.modelfilter)
            self.reglist_obj.set_model(status.modelsort)

            self.bit_model = status.bit_model
            self.bitfield_obj.set_model(self.bit_model)

            self.redraw()
            self.enable_registers(True)
        else:
            self.regset = None
            self.dbase = None
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
            self.widgets.no_reset_test.set_active(reg.flags.do_not_reset_test)
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

    def remove_register_callback(self, _obj: Gtk.Button) -> None:
        self.remove_register()

    def remove_register(self) -> None:
        row = self.reglist_obj.get_selected_position()
        reg = self.get_selected_register()
        if reg and self.regset:
            self.reglist_obj.delete_selected_node()
            self.regset.delete_register(reg)
            self.reglist_obj.select_row(row)
            self.set_modified()

    def add_register_callback(self, _obj: Gtk.Button) -> None:
        self.new_register()

    def new_register(self) -> None:
        dbase = self.regset
        if dbase:
            register = Register()
            register.width = dbase.ports.data_bus_width
            register.address = calculate_next_address(dbase, register.width)
            self.insert_new_register(register)

    def insert_new_register(self, register):
        if self.widgets.notebook.get_current_page() == 0:
            self.reglist_obj.add_new_register(register)
            self.regset.add_register(register)
            self.set_register_warn_flags(register)
            self.set_modified()

    def add_bit_callback(self, _obj: Gtk.Button):
        register = self.get_selected_register()
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

        self.bitfield_obj.add_new_field(field)
        self.set_modified()
        self.set_register_warn_flags(register)

    def remove_bit_callback(self, _obj: Gtk.Button):
        register = self.get_selected_register()
        row = self.bitfield_obj.get_selected_row()
        field = self.bit_model.get_bitfield_at_path(row[0])
        register.delete_bit_field(field)
        node = self.bit_model.get_iter(row[0])
        self.bit_model.remove(node)
        self.set_register_warn_flags(register)
        self.set_modified()

    def edit_bit_callback(self, _obj: Gtk.Button):
        register = self.get_selected_register()
        field = self.bitfield_obj.select_field()
        if field and self.regset:
            BitFieldEditor(
                self.regset,
                register,
                field,
                self.set_field_modified,
                None,  # self.builder,
                None,  # self.top_window,
            )

    def update_register_addr(self, register, new_addr, new_length=0):
        self.regset.delete_register(register)
        register.address = new_addr
        register.ram_size = new_length
        share_reg = self.find_shared_address(register)
        if share_reg:
            if share_reg.share == ShareType.READ:
                register.share = ShareType.WRITE
            else:
                register.share = ShareType.READ
            self.set_share(register)
        self.regset.add_register(register)

    def find_shared_address(self, reg):
        for shared_reg in self.regset.get_all_registers():
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
        if self.regset:
            text = f"{self.regset.total_bits()}"
        else:
            text = ""
        self.widgets.reg_count.set_text(text)

    def set_description_warn_flag(self):
        if self.regset:
            warn = self.regset.overview_text == ""
        else:
            warn = False
        self.widgets.mod_descr_warn.set_property("visible", warn)

    def no_sharing_toggle_callback(self, obj):
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

    def read_access_toggle_callback(self, obj):
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

    def write_access_toggle_callback(self, obj):
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
        for reg in self.regset.get_all_registers():
            if reg.address == reg_addr:
                cnt += 1
        return cnt > 1

    def duplicate_register_callback(self, _obj: Gtk.Button):
        reg = self.get_selected_register()
        if reg and self.regset:
            reg_copy = duplicate_register(self.regset, reg)
            self.reglist_obj.add_new_register(reg_copy)
            self.regset.add_register(reg_copy)
            self.set_register_warn_flags(reg_copy)
            self.set_modified()

    def bit_changed(self, _obj):
        self.field_selected_action.set_sensitive(True)

    def remove_regset_callback(self, _obj: Gtk.Button):
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

    def remove_regset_from_project(self, uuid: str):
        if self.project:
            self.project.remove_register_set(uuid)

    def remove_regset_from_groups(self, uuid: str):
        if self.project:
            for block in self.project.blocks.values():
                block.remove_register_set(uuid)

    def new_regset_callback(self, _obj: Gtk.Button):
        """
        Creates a new database, and initializes the interface.
        """
        name_str = get_new_filename()
        if not name_str or not self.project:
            return

        name = Path(name_str).with_suffix(REG_EXT)

        dbase = RegisterDb()
        dbase.name = name.stem
        dbase.filename = name
        dbase.modified = True

        self.project.new_register_set(dbase, name)
        node = self.new_regset(dbase)
        self.reg_set_obj.select(node)

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

                if self.project:
                    name = Path(filename)
                    dbase = RegisterDb(name)
                    dbase.filename = name
                    dbase.modified = True

                    self.project.new_register_set(dbase, name)
                    node = self.new_regset(dbase)
                    self.reg_set_obj.select(node)
                # self.set_project_modified()
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
        reg = self.get_selected_register()

        if reg and self.regset:
            SummaryWindow(
                self.widgets, reg, self.regset.name, self.project, self.regset
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
