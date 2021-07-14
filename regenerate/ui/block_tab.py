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
from typing import Optional, List
from gi.repository import Gtk, Gdk, GdkPixbuf, Pango
from regenerate.settings.paths import INSTALL_PATH
from regenerate.db import RegisterInst, Block, BLK_EXT
from regenerate.ui.columns import ReadOnlyColumn, EditableColumn
from regenerate.ui.parameter_list import ParameterList
from regenerate.ui.base_doc import BaseDoc
from regenerate.ui.param_overrides import BlockOverridesList
from regenerate.ui.enums import SelectCol
from regenerate.ui.entry import (
    EntryText,
    EntryWord,
    EntryHex,
)


class BlockTab:
    def __init__(self, find_obj, block_remove_callback):

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
        self.block_size = EntryHex(
            find_obj("block_size"), "address_size", self.modified
        )
        self.block_notebook = find_obj("block_notebook")
        self.block_regsets = find_obj("block_regsets")
        self.block_reg_add = find_obj("block_reg_add")
        self.block_reg_remove = find_obj("block_reg_remove")
        self.block_docs = find_obj("block_doc_pages")
        self.project = None
        self.block = None
        self.disable_modified = True

        self.block_obj = BlockSelectList(
            find_obj("block_select_list"), self.block_selection_changed
        )

        self.block_model = BlockSelectModel()
        self.block_obj.set_model(self.block_model)

        self.preview = BlockDoc(
            self.block_docs,
            self.after_modified,
            find_obj("add_block_doc"),
            find_obj("remove_block_doc"),
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

    def clear(self):
        self.block_model = BlockSelectModel()
        self.block_obj.set_model(self.block_model)
        self.regmodel = Gtk.ListStore(str, str, str, str, str, object)
        self.block_regsets.set_model(self.regmodel)
        self.block_name.change_db(None)
        self.block_description.change_db(None)
        self.block_size.change_db(None)
        self.preview.change_block(None)

    def page_changed(self, obj, page, page_num):
        if page_num == 1:
            self.overrides_list.update_display()

    def redraw(self):
        self.block_model.update()
        self.overrides_list.update_display()

    def clear_flags(self):
        self.block_model.update()

    def overrides_modified(self):
        self.modified()

    def block_selection_changed(self, obj):
        model, node = obj.get_selected()
        if node:
            block = model[node][-1]
            self.disable_modified = True
            self.select_block(block.uuid)
            self.disable_modified = False
            self.parameter_list.set_db(self.block)

    def after_modified(self):
        self.modified()

    def build(self):
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
            "Offset", self.offset_changed, 2, monospace=True
        )
        self.block_regsets.append_column(column)
        column.set_min_width(125)
        column.set_expand(False)
        column.set_resizable(True)

        column = EditableColumn(
            "Repeat", self.repeat_changed, 3, monospace=True
        )
        self.block_regsets.append_column(column)
        column.set_min_width(50)
        column.set_expand(False)
        column.set_resizable(True)

        column = EditableColumn("HDL path", self.hdl_path_changed, 4)
        self.block_regsets.append_column(column)
        column.set_expand(True)
        column.set_resizable(True)

    def modified(self):
        if self.disable_modified:
            return

        self.block_obj.update_data()
        model, node = self.block_obj.get_selected()
        if node:
            model[node][SelectCol.ICON] = Gtk.STOCK_EDIT
            self.block.modified = True

    def instance_changed(self, _cell, path, new_text, col):
        old_text = self.regmodel[int(path)][col]
        self.regmodel[int(path)][col] = new_text

        for rset in self.block.regset_insts:
            if rset.name == old_text:
                rset.name = new_text
                self.modified()

    def offset_changed(self, _cell, path, new_text, col):
        try:
            reg_name = self.regmodel[int(path)][0]
            self.regmodel[int(path)][col] = f"0x{int(new_text,0):08x}"
            self.block.modified = True
            for rset in self.block.regset_insts:
                if rset.name == reg_name:
                    rset.offset = int(new_text, 0)
                    self.modified()
        except ValueError:
            ...

    def repeat_changed(self, _cell, path, new_text, col):
        try:
            reg_name = self.regmodel[int(path)][0]
            self.regmodel[int(path)][col] = f"{int(new_text)}"
            self.block.modified = True
            for rset in self.block.regset_insts:
                if rset.name == reg_name:
                    rset.repeat = int(new_text)
            self.modified()
        except ValueError:
            ...

    def hdl_path_changed(self, _cell, path, new_text, col):
        reg_inst = self.regmodel[int(path)][-1]
        self.regmodel[int(path)][col] = new_text
        self.block.modified = True
        for rset in self.block.regset_insts:
            if rset.uuid == reg_inst.uuid:
                rset.hdl = new_text
        self.modified()

    def set_project(self, project):
        self.clear()
        self.disable_modified = True
        self.project = project
        key_list = project.blocks.keys()
        if key_list:
            self.select_block(list(key_list)[0])
        self.build_add_regset_menu()
        self.block_obj.set_project(project)
        self.disable_modified = False

    def build_add_regset_menu(self):
        if self.block:
            self.reg_menu = Gtk.Menu()

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
                self.reg_menu.append(menu_item)
            self.block_reg_add.set_popup(self.reg_menu)

    def set_parameters_modified(self):
        self.modified()
        # self.reglist_obj.set_parameters(self.active.get_parameters())
        # self.bitfield_obj.set_parameters(self.active.get_parameters())

    def find_name_inst_name(self, regset):
        names = set({rset.name for rset in self.block.regset_insts})

        if regset not in names:
            new_name = regset
        else:
            index = 0
            while True:
                new_name = f"{regset}{index}"
                if new_name not in names:
                    break
                index += 1
        return new_name

    def menu_selected(self, _obj, regset):

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
                f"{reginst.repeat}",
                reginst.hdl,
                reginst,
            )
        )
        self.modified()

    def on_remove_clicked(self, _obj):
        model, node = self.block_regsets.get_selection().get_selected()

        to_be_deleted = model[node][-1]

        self.block.regset_insts = [
            regset
            for regset in self.block.regset_insts
            if regset.uuid != to_be_deleted.uuid
        ]
        model.remove(node)
        self.modified()

    def select_block(self, blkid):
        self.block = self.project.blocks[blkid]

        self.preview.change_block(self.block)
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

    def new_block_clicked(self, _obj):
        choose = self.create_save_selector(
            "New Block", "Block", f"*.{BLK_EXT}"
        )

        response = choose.run()
        if response == Gtk.ResponseType.OK:
            filename = Path(choose.get_filename())

            if filename.suffix != BLK_EXT:
                filename = filename.with_suffix(BLK_EXT)

            self.block = Block()
            self.block.filename = filename
            self.block.name = Path(filename).stem

            self.project.blocks[self.block.uuid] = self.block
            node = self.block_model.add_block(self.block)
            self.block_obj.select(node)

            self.modified()
            # if self.recent_manager:
            #     self.recent_manager.add_item(f"file:///{str(filename)}")
            # self.find_obj("save_btn").set_sensitive(True)
            # self.prj_loaded.set_sensitive(True)
            # self.load_project_tab()
        choose.destroy()
        self.project.modified = True

    def add_block_clicked(self, _obj):
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        choose = self.create_open_selector(
            "Open Block Database",
            "Block files",
            [
                f"*{BLK_EXT}",
            ],
        )
        choose.set_select_multiple(True)
        response = choose.run()
        if response == Gtk.ResponseType.OK:
            for filename in choose.get_filenames():

                name = Path(filename)
                blk = Block()
                blk.open(name)
                blk.modified = True

                self.project.blocks[blk.uuid] = blk
                self.block_model.add_block(blk)

                for regset in blk.regsets:
                    if regset not in self.project.regsets:
                        self.project.regsets[regset] = blk.regsets[regset]

        choose.destroy()
        self.project.modified = True

    def remove_block_clicked(self, _obj):
        model, node = self.block_obj.get_selected()
        obj = model.get_value(node, 2)

        model.remove(node)
        self.project.remove_block(obj.uuid)
        self.block_remove_callback()
        self.project.modified = True

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

    def create_file_selector(self, title, m_name, m_regex, action, icon):
        """
        Creates a file save selector, using the mime type and regular
        expression to control the selector.
        """
        choose = Gtk.FileChooserDialog(
            title,
            None,  # self.top_window,
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
            mime_filter.add_pattern(m_regex[0])
            choose.add_filter(mime_filter)
        choose.show()
        return choose


class BlockSelectModel(Gtk.ListStore):
    """
    Provides the model for the block list
    """

    def __init__(self):
        super().__init__(str, str, object)

        Gdk.threads_init()
        self.file_list = {}
        self.paths = set()

    def set_modified(self):
        model, node = self.block_obj.get_selected()
        model[node][SelectCol.ICON] = Gtk.STOCK_EDIT

    def load_icons(self):
        """Clear paths and the file list"""
        self.paths = set()
        self.file_list = {}

    def add_block(self, block: Block, modified=False):
        """Add the the database to the model"""

        base = block.name

        if modified or block.modified:
            node = self.append(
                row=[
                    Gtk.STOCK_EDIT,
                    base,
                    block,
                ]
            )
        else:
            node = self.append(row=["", base, block])
        self.file_list[str(block.filename)] = node
        self.paths.add(block.filename.parent)
        return node

    def update(self):
        for row in self:
            if row[2].modified:
                row[0] = Gtk.STOCK_EDIT
            else:
                row[0] = ""


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
        for row in self.__model:
            row[1] = row[2].name

    def set_project(self, project):
        self.__model.clear()
        self.project = project

        sorted_dict = {
            key: value
            for key, value in sorted(
                self.project.blocks.items(), key=lambda item: item[1].name
            )
        }

        for blkid in sorted_dict:
            self.__model.add_block(self.project.blocks[blkid])

    def set_model(self, model):
        """Sets the model"""

        self.__model = model
        self.__obj.set_model(model)

    def __build_prj_window(self):
        """Build the block window"""

        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("", renderer, stock_id=0)
        column.set_min_width(20)
        self.__obj.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Blocks", renderer, text=1)
        column.set_min_width(140)
        self.__obj.append_column(column)

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
    def __init__(
        self,
        notebook: Gtk.Notebook,
        modified,
        add_btn: Gtk.Button,
        del_btn: Gtk.Button,
    ):
        super().__init__(notebook, modified, add_btn, del_btn)
        self.block: Optional[Block] = None
        self.changing = False

    def change_block(self, block: Optional[Block]):
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
