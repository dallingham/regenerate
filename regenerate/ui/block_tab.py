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

import os
from pathlib import Path
from typing import Optional, List, Callable, Set, Tuple
from gi.repository import Gtk, GdkPixbuf, Pango
from regenerate.settings.paths import INSTALL_PATH
from regenerate.db import RegisterInst, Block, BLK_EXT, LOGGER, RegProject
from .columns import ReadOnlyColumn, EditableColumn, MenuEditColumn
from .parameter_list import ParameterList
from .base_doc import BaseDoc
from .param_overrides import BlockOverridesList
from .enums import SelectCol
from .entry import (
    EntryText,
    EntryWord,
    EntryHex,
    ValidHexEntry,
)
from .file_dialogs import create_file_selector
from .select_model import SelectModel


class BlockTab:
    "Manages the block tab"

    def __init__(self, find_obj: Callable, block_remove_callback: Callable):

        self.block_remove_callback = block_remove_callback
        self.block_name = EntryWord(
            find_obj("block_name"),
            "name",
            self.modified,
            "Enter the block name",
        )
        self.block_description = EntryText(
            find_obj("block_description"),
            "description",
            self.modified,
            "Enter the block description",
        )
        self.grid = find_obj("blk_grid")
        label = find_obj("blk_addr_size_label")
        new_entry = ValidHexEntry()
        new_entry.show()
        self.block_size = EntryHex(new_entry, "address_size", self.modified)
        self.grid.attach_next_to(
            new_entry, label, Gtk.PositionType.RIGHT, 1, 1
        )

        self.block_notebook = find_obj("block_notebook")
        self.block_regsets = find_obj("block_regsets")
        self.block_reg_add = find_obj("block_reg_add")
        self.block_reg_remove = find_obj("block_reg_remove")
        self.block_docs = find_obj("block_doc_pages")
        self.regmodel: Optional[Gtk.ListStore] = None
        self.project: Optional[RegProject] = None
        self.block: Optional[Block] = None
        self.disable_modified = True
        self._parameter_names: Set[Tuple[str, str]] = set()

        self.block_obj = BlockSelectList(
            find_obj("block_select_list"), self.block_selection_changed
        )

        self.block_model = SelectModel()
        self.block_obj.set_model(self.block_model)

        self.preview = BlockDoc(
            self.block_docs,
            self.after_modified,
        )

        self.overrides_list = BlockOverridesList(
            find_obj("block_override_list"),
            find_obj("block_override_add"),
            find_obj("block_override_remove"),
            self.overrides_modified,
        )

        self.parameter_list = find_obj("block_param_list")
        self.parameter_list = ParameterList(
            self.parameter_list,
            find_obj("block_param_add"),
            find_obj("block_param_remove"),
            self.set_parameters_modified,
        )

        find_obj("block_add_block").connect("clicked", self.add_block_clicked)
        find_obj("block_new_block").connect("clicked", self.new_block_clicked)
        find_obj("block_remove_block").connect(
            "clicked", self.remove_block_clicked
        )

        self.build()
        self.block_reg_remove.connect("clicked", self.on_remove_clicked)
        self.block_notebook.connect("switch-page", self.page_changed)

    def clear(self) -> None:
        "Clears data from the tab"

        self.block_model = SelectModel()
        self.block_obj.set_model(self.block_model)
        self.regmodel = Gtk.ListStore(str, str, str, str, str, object)
        self.block_regsets.set_model(self.regmodel)
        self.block_name.change_db(None)
        self.block_description.change_db(None)
        self.block_size.change_db(None)
        self.preview.change_block(None, None)

    def page_changed(
        self, _obj: Gtk.Notebook, _page: Gtk.Grid, page_num: int
    ) -> None:
        "Called when the notebook page changes"
        if page_num == 1:
            self.overrides_list.update_display()

    def redraw(self) -> None:
        "Redraw the screen"

        self.block_model.update()
        if self.block:
            self.set_parameters(self.block.parameters.get())
            self.overrides_list.set_parameters(self.block.parameters.get())
        self.overrides_list.update_display()

    def clear_flags(self) -> None:
        self.block_model.update()

    def overrides_modified(self) -> None:
        self.modified()

    def block_selection_changed(self, obj: Gtk.TreeSelection) -> None:
        "Called with the block selection changes"

        model, node = obj.get_selected()
        if node:
            block = model[node][-1]
            self.disable_modified = True
            self.select_block(block.uuid)
            self.disable_modified = False
            self.parameter_list.set_db(self.block)
            self.preview.change_block(self.block, self.project)

    def after_modified(self) -> None:
        self.modified()

    def build(self) -> None:
        "Build the interface"

        column = EditableColumn("Instance", self.instance_changed, 1)
        self.block_regsets.append_column(column)
        column.set_min_width(175)
        column.set_expand(False)
        column.set_resizable(True)

        column = ReadOnlyColumn("Register Set", 0)
        self.block_regsets.append_column(column)
        column.set_min_width(175)
        column.set_expand(False)
        column.set_resizable(True)

        column = EditableColumn(
            "Offset", self.address_changed, 2, monospace=True
        )
        self.block_regsets.append_column(column)
        column.set_min_width(125)
        column.set_expand(False)
        column.set_resizable(True)

        column = MenuEditColumn(
            "Repeat", self.repeat_menu, self.repeat_text, [], 3
        )
        self.block_regsets.append_column(column)
        column.set_min_width(150)
        column.set_expand(False)
        column.set_resizable(True)
        self.repeat_col = column

        column = EditableColumn("HDL path", self.hdl_path_changed, 4)
        self.block_regsets.append_column(column)
        column.set_expand(True)
        column.set_resizable(True)

    def modified(self) -> None:
        "Called when the data has been modified"

        if self.disable_modified or self.block is None:
            return

        self.block_obj.update_data()
        model, node = self.block_obj.get_selected()
        if node:
            model[node][SelectCol.ICON] = Gtk.STOCK_EDIT
            self.block.modified = True

    def instance_changed(
        self, _cell: Gtk.CellRendererText, path: str, text: str, col: int
    ) -> None:
        "Called when the instance name changed for a register instance"

        if self.block is None or self.regmodel is None:
            return

        old_text = self.regmodel[int(path)][col]
        self.regmodel[int(path)][col] = text

        for rset in self.block.regset_insts:
            if rset.name == old_text:
                rset.name = text
                self.modified()

    def address_changed(
        self, _cell: Gtk.CellRendererText, path: str, new_text: str, col: int
    ) -> None:
        "Called with the address changed"

        if self.block is None or self.regmodel is None:
            return

        try:
            value = int(new_text, 0)
        except ValueError:
            return

        reg_name = self.regmodel[int(path)][0]
        self.regmodel[int(path)][col] = f"0x{int(new_text,0):08x}"
        self.block.modified = True
        for rset in self.block.regset_insts:
            if rset.name == reg_name:
                rset.offset = value
                self.modified()

    def repeat_menu(
        self,
        cell: Gtk.CellRendererCombo,
        path: str,
        node: Gtk.TreeIter,
        col: int,
    ) -> None:
        "Called with the repeat value changes due to the menu selection"

        if self.block is None or self.regmodel is None:
            return

        model = cell.get_property("model")
        new_text = model.get_value(node, 0)
        new_uuid = model.get_value(node, 1)
        self.block.modified = True

        reg_name = self.regmodel[int(path)][1]
        for rset in self.block.regset_insts:
            if rset.name == reg_name:
                rset.repeat.set_param(new_uuid)
                break
        self.regmodel[int(path)][col] = new_text
        self.modified()

    def repeat_text(
        self, _cell: Gtk.CellRendererCombo, path: str, new_text: str, col: int
    ) -> None:
        "Called with the repeat value changes due to text being edited"

        if self.block is None or self.regmodel is None:
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
        reg_name = self.regmodel[row][1]
        self.block.modified = True
        for rset in self.block.regset_insts:
            if rset.name == reg_name:
                if (
                    rset.repeat.is_parameter
                    and rset.repeat.txt_value == new_text
                ):
                    return
                rset.repeat.set_int(value)
                self.regmodel[row][col] = rset.repeat.int_str()
        self.modified()

    def hdl_path_changed(
        self, _cell: Gtk.CellRendererText, path: str, new_text: str, col: int
    ) -> None:
        "Called with the HDL path changes"

        if self.block is None or self.regmodel is None:
            return

        row = int(path)
        reg_inst = self.regmodel[row][-1]
        self.regmodel[row][col] = new_text
        self.block.modified = True
        for rset in self.block.regset_insts:
            if rset.uuid == reg_inst.uuid:
                rset.hdl = new_text
        self.modified()

    def set_project(self, project: RegProject):
        "Change the project"

        self.clear()
        self.disable_modified = True
        self.project = project

        if self.project:
            key_list = project.blocks.keys()
            if key_list:
                self.select_block(list(key_list)[0])
            self.build_add_regset_menu()
            self.block_obj.set_project(project)
            self.disable_modified = False

    def build_add_regset_menu(self):
        "Builds the menu to add a register set to a block"

        if self.block and self.project:
            reg_menu = Gtk.Menu()

            sorted_dict = {
                key: value
                for key, value in sorted(
                    self.project.regsets.items(), key=lambda item: item[1].name
                )
            }

            for regset_id in sorted_dict:
                regset = self.project.regsets[regset_id]
                menu_item = Gtk.MenuItem(regset.name)
                menu_item.connect("activate", self.menu_selected, regset)
                menu_item.show()
                reg_menu.append(menu_item)
            self.block_reg_add.set_popup(reg_menu)

    def set_parameters(self, parameters) -> None:
        "Sets the parameters"

        self._parameter_names = set({(p.name, p.uuid) for p in parameters})
        self.overrides_list.set_parameters(parameters)
        self.repeat_col.update_menu(sorted(list(self._parameter_names)))

    def set_parameters_modified(self) -> None:
        "Called when the parameters have been modified"

        if self.block is None:
            return

        self.modified()
        self.set_parameters(self.block.parameters.get())

    def find_name_inst_name(self, regset_name: str) -> str:
        "Finds the next available instance name"

        if self.block is None:
            return ""

        names = set({rset.name for rset in self.block.regset_insts})

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

    def menu_selected(self, _obj, regset) -> None:
        "Called when the menu entry has been selected"

        if self.regmodel is None or self.project is None or self.block is None:
            return

        new_name = self.find_name_inst_name(regset.name)

        reginst = RegisterInst(rset=regset.uuid, inst=new_name)
        reg_cont = self.project.regsets[regset.uuid]

        self.block.regset_insts.append(reginst)
        self.block.regsets[regset.uuid] = reg_cont

        self.regmodel.append(
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

    def on_remove_clicked(self, _obj: Gtk.Button) -> None:
        "Called when the remove button has been clicked"

        if self.block is None:
            return

        model, node = self.block_regsets.get_selection().get_selected()

        to_be_deleted = model[node][-1]

        self.block.regset_insts = [
            regset
            for regset in self.block.regset_insts
            if regset.uuid != to_be_deleted.uuid
        ]
        model.remove(node)
        self.modified()

    def select_block(self, blkid: str) -> None:
        "Builds a new register model from the selected block ID"

        if self.regmodel is None or self.project is None:
            return

        self.block = self.project.blocks[blkid]

        self.preview.change_block(self.block, self.project)
        self.block_name.change_db(self.block)
        self.block_description.change_db(self.block)
        self.block_size.change_db(self.block)

        self.regmodel = Gtk.ListStore(str, str, str, str, str, object)
        self.block_regsets.set_model(self.regmodel)
        self.overrides_list.set_project(self.block)

        for reginst in self.block.regset_insts:
            regset = self.block.regsets[reginst.regset_id]
            self.regmodel.append(
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

        if self.project is None:
            return

        filename_list = create_file_selector(
            "Create a new Block file",
            None,
            "Block files",
            f"*{BLK_EXT}",
            Gtk.FileChooserAction.SAVE,
            Gtk.STOCK_SAVE,
        )
        for filename in filename_list:
            filepath = Path(filename)

            if filepath.suffix != BLK_EXT:
                filepath = filepath.with_suffix(BLK_EXT)

            self.block = Block()
            self.block.filename = filepath
            self.block.name = filepath.stem

            self.project.blocks[self.block.uuid] = self.block
            node = self.block_model.add(self.block)
            self.block_obj.select(node)

            self.modified()
            self.project.modified = True

    def add_block_clicked(self, _obj: Gtk.Button) -> None:
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        if self.block is None or self.project is None:
            return

        filename_list = create_file_selector(
            "Add Block Files to the Project",
            None,
            "Block files",
            f"*{BLK_EXT}",
            Gtk.FileChooserAction.OPEN,
            Gtk.STOCK_OPEN,
        )

        for filename in filename_list:

            name = Path(filename)
            blk = Block()
            blk.open(name)
            blk.modified = True

            self.project.blocks[blk.uuid] = blk
            self.block_model.add(blk)

            for regset in blk.regsets:
                if regset not in self.project.regsets:
                    self.project.regsets[regset] = blk.regsets[regset]
        self.project.modified = True

    def remove_block_clicked(self, _obj: Gtk.Button) -> None:
        "Called with the remove block button has been pressed"

        if self.block is None or self.project is None:
            return

        model, node = self.block_obj.get_selected()
        obj = model.get_value(node, 2)

        model.remove(node)
        self.project.remove_block(obj.uuid)
        self.block_remove_callback()
        self.project.modified = True


class BlockSelectList:
    """Block list"""

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
        self.project = None

    def update_data(self):
        "Refreshes the data in the model after the block has been changed"

        for row in self.__model:
            row[1] = row[2].name

    def set_project(self, project):
        "Updates after a change in the project"

        self.__model.clear()
        self.project = project

        sorted_dict = {
            key: value
            for key, value in sorted(
                self.project.blocks.items(), key=lambda item: item[1].name
            )
        }

        for blkid in sorted_dict:
            self.__model.add(self.project.blocks[blkid])

    def set_model(self, model):
        """Sets the model"""

        self.__model = model
        self.__obj.set_model(model)

    def __build_prj_window(self):
        """Build the block window"""

        # renderer = Gtk.CellRendererPixbuf()
        # column = Gtk.TreeViewColumn("", renderer, stock_id=0)
        # column.set_min_width(20)
        # self.__obj.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        renderer.set_padding(6, 3)
        column = Gtk.TreeViewColumn("Blocks", renderer, text=1)
        column.set_min_width(140)
        column.set_cell_data_func(renderer, self.set_format)
        self.__obj.append_column(column)

    def set_format(self, _col, renderer, model, titer, data):
        val = model.get_value(titer, 0)

        if val:
            renderer.set_property("weight", Pango.Weight.BOLD)
            renderer.set_property("style", Pango.Style.ITALIC)
        else:
            renderer.set_property("weight", Pango.Weight.NORMAL)
            renderer.set_property("style", Pango.Style.NORMAL)

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
        self.block: Optional[Block] = None
        self.changing = False

    def change_block(
        self, block: Optional[Block], _project: Optional[RegProject]
    ):
        self.block = block

        self.changing = True
        self.remove_pages()
        if block:
            for page in block.doc_pages.get_page_names():
                text = block.doc_pages.get_page(page)
                if text is not None:
                    self.add_page(page, text)
        self.changing = False

    def remove_page_from_doc(self, title: str):
        if self.block is not None:
            self.block.doc_pages.remove_page(title)

    def update_page_from_doc(self, title: str, text: str, tags: List[str]):
        if not self.changing and self.block is not None:
            self.block.doc_pages.update_page(title, text, tags)
