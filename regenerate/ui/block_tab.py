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
Project model and list
"""

from pathlib import Path
from typing import Optional, List, Callable, Set, Tuple
from gi.repository import Gtk
from regenerate.settings.paths import HELP_PATH
from regenerate.db import (
    RegisterInst,
    Block,
    BLK_EXT,
    LOGGER,
    RegProject,
    RegisterSet,
)
from .columns import ReadOnlyColumn, EditableColumn, MenuEditColumn
from .parameter_list import ParameterList
from .base_doc import BaseDoc
from .param_overrides import BlockOverridesList
from .entry import EntryText, EntryWord, EntryHex
from .file_dialogs import create_file_selector
from .select_sidebar import SelectSidebar


class BlockTab:
    "Manages the block tab"

    def __init__(self, find_obj: Callable, block_remove_callback: Callable):

        self._block_remove_callback = block_remove_callback
        self._block_notebook = find_obj("block_notebook")
        self._block_regsets = find_obj("block_regsets")
        self._block_reg_add = find_obj("block_reg_add")
        self._block_name_obj = find_obj("block_name")
        self._block_descr_obj = find_obj("block_description")
        self._block_size_obj = find_obj("blk_addr_size")
        self._block_reg_remove = find_obj("block_reg_remove")
        self._block_docs = find_obj("block_doc_pages")
        self._block_select_notebook = find_obj("block_select_notebook")
        self._reginst_list_notebook = find_obj("reginst_list_notebook")
        self._reginst_list_notebook.set_show_tabs(False)
        self._reginst_list_help = find_obj("reginst_list_help")

        self._sidebar = SelectSidebar(
            find_obj("block_sidebar"),
            "Blocks",
            "block_select_help.html",
            self.new_block_clicked,
            self.add_block_clicked,
            self.remove_block_clicked,
        )

        self._sidebar.set_selection_changed_callback(
            self._block_selection_changed
        )

        help_path = Path(HELP_PATH) / "reginst_list_help.html"
        try:
            with help_path.open() as ifile:
                self._reginst_list_help.load_html(ifile.read(), "text/html")
        except IOError:
            pass

        self._block_name = EntryWord(
            self._block_name_obj,
            "name",
            self.modified,
            "Enter the block name",
        )
        self._block_description = EntryText(
            self._block_descr_obj,
            "description",
            self.modified,
            "Enter the block description",
        )
        self._block_size = EntryHex(
            self._block_size_obj, "address_size", self.modified
        )

        self._reg_model: Optional[Gtk.ListStore] = None
        self._project: Optional[RegProject] = None
        self._block: Optional[Block] = None
        self.disable_modified = True
        self._parameter_names: Set[Tuple[str, str]] = set()

        self._preview = BlockDoc(
            self._block_docs,
            self.modified,
        )

        self._overrides_list = BlockOverridesList(
            find_obj("block_override_list"),
            find_obj("block_override_add"),
            find_obj("block_override_remove"),
            self._overrides_modified,
        )

        self.parameter_list = find_obj("block_param_list")
        self.parameter_list = ParameterList(
            self.parameter_list,
            find_obj("block_param_add"),
            find_obj("block_param_remove"),
            self.set_parameters_modified,
        )

        self.build()
        self._block_reg_remove.connect("clicked", self._on_remove_clicked)
        self._block_notebook.connect("switch-page", self._page_changed)

    def clear(self) -> None:
        "Clears data from the tab"

        self._sidebar.clear()
        self._reg_model = Gtk.ListStore(str, str, str, str, str, object)
        self._block_regsets.set_model(self._reg_model)
        self._block_name.change_db(None)
        self._block_description.change_db(None)
        self._block_size.change_db(None)
        self._preview.change_block(None, None)

    def _page_changed(
        self, _obj: Gtk.Notebook, _page: Gtk.Grid, page_num: int
    ) -> None:
        "Called when the notebook page changes"
        if page_num == 1:
            self._overrides_list.update_display()

    def redraw(self) -> None:
        "Redraw the screen"

        self._sidebar.update()
        self._build_add_regset_menu()
        if self._block:
            self.set_parameters(self._block.parameters.get())
            self._overrides_list.set_parameters(self._block.parameters.get())
        else:
            LOGGER.warning(
                (
                    "No block is selected. Select a block from the list or "
                    "use the buttons in the lower left corner to create or add a block."
                )
            )

        self._update_block_selection()
        self._block_name_obj.set_sensitive(self._block is not None)
        self._block_descr_obj.set_sensitive(self._block is not None)
        self._block_size_obj.set_sensitive(self._block is not None)

        self._overrides_list.update_display()
        self._build_add_regset_menu()

    def clear_flags(self) -> None:
        "Updates the sidebar to set flags correctly"
        self._sidebar.update()

    def _overrides_modified(self) -> None:
        "Called when the overrides are modified"
        self.modified()

    def _block_selection_changed(self, _obj: Gtk.TreeSelection) -> None:
        "Called with the block selection changes"
        self._update_block_selection()

    def _update_block_selection(self):
        "Updates the block selection"

        model, node = self._sidebar.get_selected()

        if node:
            self._setup_and_select_block(model, node)
        else:
            self._block_notebook.set_sensitive(False)

        if self._project and self._project.blocks:
            self._block_select_notebook.set_current_page(0)
        else:
            self._block_select_notebook.set_current_page(1)

    def _setup_and_select_block(self, model, node):
        self._block_notebook.set_sensitive(True)
        block = model[node][-1]
        self.disable_modified = True
        self.select_block(block.uuid)
        self.disable_modified = False
        self.parameter_list.set_db(self._block)
        self._preview.change_block(self._block, self._project)

    def build(self) -> None:
        "Build the interface"

        column = EditableColumn("Instance", self._instance_changed, 1)
        self._setup_column(column, 175)
        column = ReadOnlyColumn("Register Set", 0)
        self._setup_column(column, 175)
        column = EditableColumn(
            "Offset", self._address_changed, 2, monospace=True
        )
        self._setup_column(column, 125)
        column = MenuEditColumn(
            "Repeat", self._repeat_menu, self._repeat_text, [], 3
        )
        self._setup_column(column, 150)
        self.repeat_col = column

        column = EditableColumn("HDL path", self._hdl_path_changed, 4)
        self._block_regsets.append_column(column)
        column.set_expand(True)
        column.set_resizable(True)

    def _setup_column(self, column, arg1):
        self._block_regsets.append_column(column)
        column.set_min_width(arg1)
        column.set_expand(False)
        column.set_resizable(True)

    def modified(self) -> None:
        "Called when the data has been modified"

        if self.disable_modified or self._block is None:
            return

        self._sidebar.update()
        self._block.modified = True

    def _instance_changed(
        self, _cell: Gtk.CellRendererText, path: str, text: str, col: int
    ) -> None:
        "Called when the instance name changed for a register instance"

        if self._block is None or self._reg_model is None:
            return

        old_text = self._reg_model[int(path)][col]
        self._reg_model[int(path)][col] = text

        for rset in self._block.regset_insts:
            if rset.name == old_text:
                rset.name = text
                self.modified()

    def _address_changed(
        self, _cell: Gtk.CellRendererText, path: str, new_text: str, col: int
    ) -> None:
        "Called with the address changed"

        if self._block is None or self._reg_model is None:
            return

        try:
            value = int(new_text, 0)
        except ValueError:
            return

        inst = self._reg_model[int(path)][-1]
        self._reg_model[int(path)][col] = f"0x{int(new_text,0):08x}"
        self._block.modified = True

        inst.offset = value
        self.modified()

    def _repeat_menu(
        self,
        cell: Gtk.CellRendererCombo,
        path: str,
        node: Gtk.TreeIter,
        col: int,
    ) -> None:
        "Called with the repeat value changes due to the menu selection"

        if self._block is None or self._reg_model is None:
            return

        model = cell.get_property("model")
        new_text = model.get_value(node, 0)
        new_uuid = model.get_value(node, 1)
        self._block.modified = True

        reg_name = self._reg_model[int(path)][1]
        for rset in self._block.regset_insts:
            if rset.name == reg_name:
                rset.repeat.set_param(new_uuid)
                break
        self._reg_model[int(path)][col] = new_text
        self.modified()

    def _repeat_text(
        self, _cell: Gtk.CellRendererCombo, path: str, new_text: str, col: int
    ) -> None:
        "Called with the repeat value changes due to text being edited"

        if self._block is None or self._reg_model is None:
            return

        try:
            value = int(new_text, 0)
        except ValueError:
            LOGGER.warning(
                '"%s" is not a repeat count. It must be an '
                "integer greater than 0 or a defined parameter",
                new_text,
            )
            return

        row = int(path)
        reg_name = self._reg_model[row][1]
        self._block.modified = True
        for rset in self._block.regset_insts:
            if rset.name == reg_name:
                if (
                    rset.repeat.is_parameter
                    and rset.repeat.txt_value == new_text
                ):
                    return
                rset.repeat.set_int(value)
                self._reg_model[row][col] = rset.repeat.int_str()
        self.modified()

    def _hdl_path_changed(
        self, _cell: Gtk.CellRendererText, path: str, new_text: str, col: int
    ) -> None:
        "Called with the HDL path changes"

        if self._block is None or self._reg_model is None:
            return

        row = int(path)
        reg_inst = self._reg_model[row][-1]
        self._reg_model[row][col] = new_text
        self._block.modified = True
        for rset in self._block.regset_insts:
            if rset.uuid == reg_inst.uuid:
                rset.hdl = new_text
        self.modified()

    def set_project(self, project: RegProject):
        "Change the project"

        self.clear()
        self.disable_modified = True
        self._project = project

        if self._project:
            key_list = project.blocks.keys()
            if key_list:
                self.select_block(list(key_list)[0])
            self._build_add_regset_menu()
            self._sidebar.set_items(list(self._project.blocks.values()))
            self.disable_modified = False

    def _build_add_regset_menu(self):
        "Builds the menu to add a register set to a block"

        page = 1

        if self._project and self._block:
            reg_menu = Gtk.Menu()

            sorted_keys = [
                key
                for key, value in sorted(
                    self._project.regsets.items(),
                    key=lambda item: item[1].name,
                )
            ]

            empty = True
            for regset_id in sorted_keys:
                empty = False
                regset = self._project.regsets[regset_id]
                menu_item = Gtk.MenuItem(regset.name)
                menu_item.connect(
                    "activate", self.add_reginst_to_block, regset
                )
                menu_item.show()
                reg_menu.append(menu_item)

            if empty:
                self._block_reg_add.set_sensitive(False)
                self._block_reg_add.set_tooltip_markup(
                    "No register sets have been defined.\n"
                    "Register sets can be defined on the\n"
                    "<b>Register Sets</b> tab on the left side\n"
                    "of the window."
                )
            else:
                self._block_reg_add.set_sensitive(True)
                self._block_reg_add.set_tooltip_text(
                    "Select a register set to add to the block"
                )
                self._block_reg_add.set_popup(reg_menu)
                page = 0
        else:
            page = 0
            self._block_reg_add.set_sensitive(False)
            self._block_reg_add.set_tooltip_text(
                "No register sets have been defined"
            )
        self._reginst_list_notebook.set_current_page(page)

    def set_parameters(self, parameters) -> None:
        "Sets the parameters"

        self._parameter_names = set({(p.name, p.uuid) for p in parameters})
        self._overrides_list.set_parameters(parameters)
        self.repeat_col.update_menu(sorted(list(self._parameter_names)))

    def set_parameters_modified(self) -> None:
        "Called when the parameters have been modified"

        if self._block is None:
            return

        self.modified()
        self.set_parameters(self._block.parameters.get())

    def _find_name_inst_name(self, regset_name: str) -> str:
        "Finds the next available instance name"

        if self._block is None:
            return ""

        names = set({rset.name for rset in self._block.regset_insts})

        if regset_name not in names:
            new_name = regset_name
        else:
            index = 0
            while True:
                new_name = f"{regset_name}{index}"
                if new_name not in names:
                    break
                index += 1
        return new_name

    def add_reginst_to_block(self, _obj, regset: RegisterSet) -> None:
        "Called when the menu entry has been selected"

        if self._block is None:
            LOGGER.warning(
                (
                    "A block must be created or added before register set can be added. "
                    "Use the buttons in the lower left corner to create or add a block."
                )
            )
            return
        if self._reg_model is None or self._project is None:
            return

        new_name = self._find_name_inst_name(regset.name)

        reginst = RegisterInst(rset=regset.uuid, inst=new_name)
        reg_cont = self._project.regsets[regset.uuid]

        self._block.regset_insts.append(reginst)
        self._block.add_register_set(reg_cont)

        self._reg_model.append(
            row=(
                regset.name,
                new_name,
                f"0x{reginst.offset:08x}",
                f"{reginst.repeat.int_str()}",
                reginst.hdl,
                reginst,
            )
        )
        self.modified()

    def _on_remove_clicked(self, _obj: Gtk.Button) -> None:
        "Called when the remove button has been clicked"

        if self._block is None:
            return

        model, node = self._block_regsets.get_selection().get_selected()

        to_be_deleted = model[node][-1]

        self._block.regset_insts = [
            regset
            for regset in self._block.regset_insts
            if regset.uuid != to_be_deleted.uuid
        ]
        model.remove(node)
        self.modified()

    def select_block(self, blkid: str) -> None:
        "Builds a new register model from the selected block ID"

        if self._reg_model is None or self._project is None:
            return

        self._block = self._project.blocks[blkid]

        self._preview.change_block(self._block, self._project)
        self._block_name.change_db(self._block)
        self._block_description.change_db(self._block)
        self._block_size.change_db(self._block)

        self._reg_model = Gtk.ListStore(str, str, str, str, str, object)
        self._block_regsets.set_model(self._reg_model)
        self._overrides_list.set_project(self._block)

        for reginst in self._block.regset_insts:
            regset = self._block.get_regset_from_id(reginst.regset_id)
            self._reg_model.append(
                row=(
                    regset.name,
                    reginst.name,
                    f"0x{reginst.offset:08x}",
                    reginst.repeat.int_str(),
                    reginst.hdl,
                    reginst,
                )
            )
        self.modified()

    def new_block_clicked(self, _obj: Gtk.Button) -> None:
        "Called when the new block button has been clicked"

        if self._project is None:
            return

        filename_list = create_file_selector(
            "Create a new Block file",
            None,
            "Block files",
            f"*{BLK_EXT}",
            Gtk.FileChooserAction.SAVE,
            Gtk.STOCK_SAVE,
        )
        if not filename_list:
            return

        for filename in filename_list:
            filepath = Path(filename)

            if filepath.suffix != BLK_EXT:
                filepath = filepath.with_suffix(BLK_EXT)

            self._block = Block()
            self._block.filename = filepath
            self._block.name = filepath.stem

            self._project.blocks[self._block.uuid] = self._block
            node = self._sidebar.add(self._block)
            self._sidebar.select(node)

            self.modified()
            self._project.modified = True
        self._update_block_selection()

    def add_block_clicked(self, _obj: Gtk.Button) -> None:
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        if self._project is None:
            return

        filename_list = create_file_selector(
            "Add Block Files to the Project",
            None,
            "Block files",
            f"*{BLK_EXT}",
            Gtk.FileChooserAction.OPEN,
            Gtk.STOCK_OPEN,
        )

        if filename_list:
            for filename in filename_list:

                name = Path(filename)
                blk = Block()
                blk.open(name)
                blk.modified = True

                self._project.blocks[blk.uuid] = blk
                self._sidebar.add(blk)

                for regset in blk.get_regsets_dict():
                    if regset not in self._project.regsets:
                        self._project.regsets[regset] = blk.get_regset_from_id(
                            regset
                        )
            self._project.modified = True
        self._update_block_selection()

    def remove_block_clicked(self, _obj: Gtk.Button) -> None:
        "Called with the remove block button has been pressed"

        if self._block is None or self._project is None:
            return

        uuid = self._sidebar.remove_selected()
        self._project.remove_block(uuid)
        self._block_remove_callback()
        self._project.modified = True
        self._update_block_selection()


class BlockDoc(BaseDoc):
    "Documentation editor for the Block documentation"

    def __init__(
        self,
        notebook: Gtk.Notebook,
        modified: Callable,
    ):
        super().__init__(
            notebook,
            modified,
        )
        self._block: Optional[Block] = None
        self.changing = False

    def change_block(
        self, block: Optional[Block], _project: Optional[RegProject]
    ):
        "Changes the active block"

        self._block = block

        self.changing = True
        self.remove_pages()
        if block:
            for page_name in block.doc_pages.get_page_names():
                page = block.doc_pages.get_page(page_name)
                if page is not None:
                    self.add_page(page)
        self.changing = False

    def remove_page_from_doc(self, title: str):
        if self._block is not None:
            self._block.doc_pages.remove_page(title)

    def update_page_from_doc(
        self, title: str, text: str, tags: List[str]
    ) -> None:
        if not self.changing and self._block is not None:
            self._block.doc_pages.update_page(title, text, tags)

    def update_page_order(self) -> None:
        if not self.changing and self._block is not None:
            self._block.doc_pages.update_page_order(self.get_order())
