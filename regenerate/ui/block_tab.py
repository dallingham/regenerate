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
from gi.repository import Gtk, Gdk, GdkPixbuf, Pango
from regenerate.settings.paths import INSTALL_PATH
from regenerate.db import RegisterInst, Block, BLK_EXT, LOGGER
from regenerate.ui.enums import SelectCol
from regenerate.ui.columns import ReadOnlyColumn, EditableColumn
from regenerate.ui.preview_editor import PreviewEditor
from regenerate.ui.module_tab import PageInfo
from regenerate.ui.spell import Spell
from regenerate.ui.utils import clean_format_if_needed
from regenerate.ui.module_tab import (
    ModuleText,
    ModuleWord,
    ModuleHex,
)


class BlockTab:
    def __init__(self, find_obj, block_remove_callback):

        self.block_remove_callback = block_remove_callback
        self.block_name = ModuleWord(
            find_obj("block_name"),
            "name",
            self.modified,
            "Enter the block name",
        )
        self.block_description = ModuleText(
            find_obj("block_description"),
            "description",
            self.modified,
            "Enter the block description",
        )
        self.block_size = ModuleHex(
            find_obj("block_size"), "address_size", self.modified
        )
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
            "doc_pages",
            self.after_modified,
        )

        find_obj("block_add_block").connect("clicked", self.add_block_clicked)
        find_obj("block_new_block").connect("clicked", self.new_block_clicked)
        find_obj("block_remove_block").connect(
            "clicked", self.remove_block_clicked
        )

        self.build()
        self.block_reg_remove.connect("clicked", self.on_remove_clicked)

    def redraw(self):
        self.block_model.update()

    def clear_flags(self):
        self.block_model.update()

    def block_selection_changed(self, obj):
        model, node = obj.get_selected()
        if node:
            block_name = model[node][1]
            self.disable_modified = True
            self.select_block(block_name)
            self.disable_modified = False

    def after_modified(self):
        if not self.disable_modified:
            self.block.modified = True
            self.modified = True

    def build(self):
        column = ReadOnlyColumn("Register Set", 0)
        self.block_regsets.append_column(column)
        column.set_min_width(175)
        column.set_expand(False)
        column.set_resizable(True)

        column = EditableColumn("Instance", self.instance_changed, 1)
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

        model, node = self.block_obj.get_selected()
        if node:
            model[node][SelectCol.ICON] = Gtk.STOCK_EDIT
            self.block.modified = True

    def instance_changed(self, _cell, path, new_text, col):
        old_text = self.regmodel[int(path)][col]
        self.regmodel[int(path)][col] = new_text

        for rset in self.block.regset_insts:
            if rset.inst == old_text:
                rset.inst = new_text
                self.modified()

    def offset_changed(self, _cell, path, new_text, col):
        try:
            reg_name = self.regmodel[int(path)][0]
            self.regmodel[int(path)][col] = f"0x{int(new_text,0):08x}"
            self.block.modified = True
            for rset in self.block.regset_insts:
                if rset.inst == reg_name:
                    rset.offset = int(new_text, 0)
                    self.modified()
        except ValueError:
            ...

    def repeat_changed(self, cell, path, new_text, col):
        try:
            reg_name = self.regmodel[int(path)][0]
            self.regmodel[int(path)][col] = f"{int(new_text)}"
            self.block.modified = True
            for rset in self.block.regset_insts:
                if rset.inst == reg_name:
                    rset.repeat = int(new_text)
            self.modified()
        except ValueError:
            ...

    def hdl_path_changed(self, _cell, path, new_text, col):
        reg_name = self.regmodel[int(path)][0]
        self.regmodel[int(path)][col] = new_text
        self.block.modified = True
        for rset in self.block.regset_insts:
            if rset.inst == reg_name:
                rset.hdl = new_text

    #        self.modified()

    def set_project(self, project):
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
            for regset in self.project.regsets:
                menu_item = Gtk.MenuItem(regset)
                menu_item.connect("activate", self.menu_selected, regset)
                menu_item.show()
                self.reg_menu.append(menu_item)
            self.block_reg_add.set_popup(self.reg_menu)

    def find_name_inst_name(self, regset):
        names = set({rset.inst for rset in self.block.regset_insts})

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

        new_name = self.find_name_inst_name(regset)

        reginst = RegisterInst(rset=regset, inst=new_name)
        reg_cont = self.project.regsets[new_name]

        self.block.regset_insts.append(reginst)
        self.block.regsets[new_name] = reg_cont

        self.regmodel.append(
            row=(
                reginst.set_name,
                reginst.inst,
                f"0x{reginst.offset:08x}",
                f"{reginst.repeat}",
                reginst.hdl,
            )
        )
        self.modified()

    def on_remove_clicked(self, _obj):
        model, node = self.block_regsets.get_selection().get_selected()
        inst_name = model[node][1]

        self.block.regset_insts = [
            regset
            for regset in self.block.regset_insts
            if regset.inst != inst_name
        ]
        model.remove(node)
        # self.modified()

    def select_block(self, blk_name):
        self.block = self.project.blocks[blk_name]

        self.block_name.change_db(self.block)
        self.block_description.change_db(self.block)
        self.block_size.change_db(self.block)

        self.regmodel = Gtk.ListStore(str, str, str, str, str)
        self.block_regsets.set_model(self.regmodel)
        self.preview.change_block(self.block)

        for regset in self.block.regset_insts:
            self.regmodel.append(
                row=(
                    regset.set_name,
                    regset.inst,
                    f"0x{regset.offset:08x}",
                    f"{regset.repeat}",
                    regset.hdl,
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

            self.blk = Block()
            self.blk.filename = filename
            self.blk.name = Path(filename).stem

            self.project.blocks[self.blk.name] = self.blk
            node = self.block_model.add_block(self.blk)

            # self.project_modified(False)
            # if self.recent_manager:
            #     self.recent_manager.add_item(f"file:///{str(filename)}")
            # self.find_obj("save_btn").set_sensitive(True)
            # self.prj_loaded.set_sensitive(True)
            # self.load_project_tab()
        choose.destroy()

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
                blk.filename = name
                blk.modified = True

                self.project.blocks[blk.name] = blk
                node = self.block_model.add_block(blk)

        for regset in blk.regsets:
            if regset not in self.project.regsets:
                self.project.regsets[regset] = blk.regsets[regset]

        choose.destroy()

    def remove_block_clicked(self, _obj):
        model, node = self.block_obj.get_selected()
        obj = model.get_value(node, 2)

        model.remove(node)
        self.project.remove_block(obj.name)
        self.block_remove_callback()

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

    def set_project(self, project):
        self.__model.clear()
        self.project = project
        for block in sorted(self.project.blocks):
            self.__model.add_block(self.project.blocks[block])

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


class BlockDoc:
    """
    Handles the Project documentation. Sets the font to a monospace font,
    sets up the changed handler, sets up the spell checker, and makes
    the link to the preview editor.

    Requires a callback functions from the main window to mark the
    the system as modified.
    """

    def __init__(self, notebook, db_field, modified):
        self.pango_font = Pango.FontDescription("monospace")

        self.notebook = notebook
        self.db_field = db_field
        self.dbase = None
        self.current_page = 0

        self.remove_pages()
        self.name_2_textview = {}
        self.callback = modified

    def remove_pages(self):
        page_count = self.notebook.get_n_pages()
        for page in range(0, page_count):
            self.notebook.remove_page(0)

    def add_page(self, name, data):
        paned = Gtk.VPaned()

        scrolled_window = Gtk.ScrolledWindow()
        paned.add1(scrolled_window)

        scrolled_window2 = Gtk.ScrolledWindow()
        paned.add2(scrolled_window2)
        paned.set_position(300)

        text = Gtk.TextView()
        text.set_wrap_mode(Gtk.WrapMode.WORD)
        buf = text.get_buffer()
        scrolled_window.add(text)

        self.preview = PreviewEditor(buf, scrolled_window2, False)
        paned.show_all()

        page = self.notebook.append_page(paned, Gtk.Label(name))

        text.modify_font(self.pango_font)
        text.set_margin_left(10)
        text.set_margin_right(10)
        text.set_margin_top(10)
        text.set_margin_bottom(10)

        handler = buf.connect("changed", self.on_changed)

        self.name_2_textview[page] = PageInfo(handler, buf, name)

        Spell(buf)
        buf.set_text(data)

    def change_block(self, blk: Block):
        """Change the database so the preview window can resolve references"""
        self.remove_pages()

        self.blk = blk
        pages = blk.doc_pages

        for page in pages.get_page_names():
            self.add_page(page, pages.get_page(page))

    def on_changed(self, obj):
        """A change to the text occurred"""
        new_text = obj.get_text(
            obj.get_start_iter(), obj.get_end_iter(), False
        )
        info = self.name_2_textview.get(self.notebook.get_current_page())
        if info:
            self.blk.doc_pages.update_page(info.name, new_text)
            self.callback()

    def on_key_press_event(self, obj, event):
        """Look for the F12 key"""
        if event.keyval == Gdk.KEY_F12:
            if clean_format_if_needed(obj):
                self.callback()
            return True
        return False
