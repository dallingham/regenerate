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
Handle the module tab
"""

from typing import Dict, Optional
from gi.repository import Gtk, Gdk
from regenerate.db import RegProject
from regenerate.ui.spell import Spell
from regenerate.ui.utils import clean_format_if_needed
from regenerate.ui.preview_editor import PreviewEditor
from .textview import RstEditor

class PageInfo:
    def __init__(self, handler, textbuf, name):
        self.handler = handler
        self.textbuf = textbuf
        self.name = name


class BaseDoc:
    def __init__(
        self,
        notebook: Gtk.Notebook,
        modified,
        add_btn: Gtk.Button,
        del_btn: Gtk.Button,
    ):
        self.notebook = notebook
        self.project: Optional[RegProject] = None
        self.add_id = add_btn.connect("clicked", self.add_doc_page)
        self.del_id = del_btn.connect("clicked", self.del_doc_page)
        self.remove_pages()
        self.name_2_textview: Dict[str, PageInfo] = {}
        self.callback = modified

    def remove_pages(self):
        page_count = self.notebook.get_n_pages()
        for _ in range(0, page_count):
            self.notebook.remove_page(0)

    def add_doc_page(self, _obj):
        dialog = Gtk.Dialog(
            "New Documentation Category",
            None,
            Gtk.DialogFlags.MODAL,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.REJECT,
                Gtk.STOCK_OK,
                Gtk.ResponseType.ACCEPT,
            ),
        )
        dialog.set_default_response(Gtk.ResponseType.ACCEPT)
        dialog.set_resizable(False)
        dialog.set_border_width(8)

        label = Gtk.Label("Enter the title for the documentation category")
        name = Gtk.Entry()
        name.set_activates_default(True)

        dialog.vbox.pack_start(label, False, False, 6)
        dialog.vbox.pack_start(name, False, False, 6)

        dialog.show_all()
        res = dialog.run()
        if res == Gtk.ResponseType.ACCEPT:
            title = name.get_text()
            self.add_page(title, "")
            self.update_page_from_doc(title, "")
            self.callback()
        dialog.destroy()

    def del_doc_page(self, _obj):
        page = self.notebook.get_current_page()
        self.notebook.remove_page(page)
        info = self.name_2_textview[page]

        for i in range(page + 1, self.notebook.get_n_pages()):
            self.name_2_textview[i] = self.name_2_textview[i + 1]
        del self.name_2_textview[self.notebook.get_n_pages()]
        self.remove_page_from_doc(info.name)
        self.callback()

    def add_page(self, name, data):
        paned = Gtk.VPaned()

        scrolled_window = Gtk.ScrolledWindow()
        paned.add1(scrolled_window)

        scrolled_window2 = Gtk.ScrolledWindow()
        paned.add2(scrolled_window2)
        paned.set_position(300)

        text = RstEditor()
        text.show()
        buf = text.get_buffer()
        scrolled_window.add(text)

        self.preview = PreviewEditor(buf, scrolled_window2, False)
        paned.show_all()

        page = self.notebook.append_page(paned, Gtk.Label(name))

        text.set_margin_left(10)
        text.set_margin_right(10)
        text.set_margin_top(10)
        text.set_margin_bottom(10)

        handler = buf.connect("changed", self.on_changed)

        self.name_2_textview[page] = PageInfo(handler, buf, name)

        Spell(buf)
        buf.set_text(data)

    def on_changed(self, obj):
        """A change to the text occurred"""
        new_text = obj.get_text(
            obj.get_start_iter(), obj.get_end_iter(), False
        )
        info = self.name_2_textview[self.notebook.get_current_page()]

        self.update_page_from_doc(info.name, new_text)
        self.callback()

    def on_key_press_event(self, obj, event):
        """Look for the F12 key"""
        if event.keyval == Gdk.KEY_F12:
            if clean_format_if_needed(obj):
                self.callback()
            return True
        return False

    def remove_page_from_doc(self, title):
        ...

    def update_page_from_doc(self, title, text):
        ...
