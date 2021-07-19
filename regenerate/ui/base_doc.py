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
import abc
from typing import Optional, List, Tuple, Callable
from gi.repository import Gtk, Gdk, GtkSource
from regenerate.db import RegProject
from regenerate.ui.spell import Spell
from regenerate.ui.utils import clean_format_if_needed
from regenerate.ui.preview_editor import PreviewEditor
from .textview import RstEditor


class PageInfo:
    "Holds the textbuffer"

    def __init__(
        self,
        handler: int,
        textbuf: GtkSource.Buffer,
        name: str,
        tags: List[str],
    ):
        self.tags = tags
        self.handler = handler
        self.textbuf = textbuf
        self.name = name


class BaseDoc:
    """
    Connects a set of SourceViews to pages in the passed notebook. The initial
    notebook should be empty. Connects the buttons to add or delete pages
    from the set.

    This is an abstract class, and must be derived from in order to be able to
    be used.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(
        self,
        notebook: Gtk.Notebook,
        modified: Callable,
        add_btn: Gtk.Button,
        del_btn: Gtk.Button,
    ):
        self.notebook = notebook
        self.project: Optional[RegProject] = None
        self.preview: Optional[PreviewEditor] = None
        self.add_id = add_btn.connect(
            "clicked", self._add_notebook_page_callback
        )
        self.del_id = del_btn.connect(
            "clicked", self._delete_notebook_page_callback
        )
        self.remove_pages()
        self.page_map: List[PageInfo] = []
        self.callback = modified

    def remove_pages(self) -> None:
        "Removes all pages from the notebook"

        page_count = self.notebook.get_n_pages()
        for _ in range(0, page_count):
            self.notebook.remove_page(0)

    def _add_notebook_page_callback(self, _obj: Gtk.Button) -> None:
        "GTK callback to adds page to the notebook"

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

        vbox = dialog.vbox
        vbox.pack_start(label, False, False, 6)
        vbox.pack_start(name, False, False, 6)

        dialog.show_all()
        res = dialog.run()
        if res == Gtk.ResponseType.ACCEPT:
            title = name.get_text()
            self.add_page(title, ("", ["Confidential"]))
            self.update_page_from_doc(title, "", ["Confidential"])
            self.callback()
        dialog.destroy()

    def _delete_notebook_page_callback(self, _obj: Gtk.Button) -> None:
        "GTK callback to deletes a page from the notebook"

        page = self.notebook.get_current_page()
        self.notebook.remove_page(page)
        info = self.page_map[page]

        for i in range(page + 1, self.notebook.get_n_pages()):
            self.page_map[i] = self.page_map[i + 1]
        del self.page_map[self.notebook.get_n_pages()]
        self.remove_page_from_doc(info.name)
        self.callback()

    def add_page(self, name: str, data: Tuple[str, List[str]]) -> None:
        """
        Adds a page and creates a restructuredText editor associated with their
        page name.
        """

        paned = Gtk.VPaned()
        paned.set_position(300)

        edit_window = Gtk.ScrolledWindow()
        paned.add1(edit_window)

        text_editor = self._create_text_editor()
        edit_window.add(text_editor)

        text_buffer = text_editor.get_buffer()
        text_buffer.set_text(data[0])
        handler = text_buffer.connect("changed", self._text_changed_callback)
        Spell(text_buffer)

        preview_window = Gtk.ScrolledWindow()
        paned.add2(preview_window)
        self.preview = PreviewEditor(text_buffer, preview_window, False)
        paned.show_all()

        self.notebook.append_page(paned, Gtk.Label(name))
        self.page_map.append(PageInfo(handler, text_buffer, name, data[1]))

    def _create_text_editor(self) -> RstEditor:
        "Create the text editor and configure it"

        text_editor = RstEditor()
        text_editor.set_margin_left(10)
        text_editor.set_margin_right(10)
        text_editor.set_margin_top(10)
        text_editor.set_margin_bottom(10)
        text_editor.connect("key_press_event", self.on_key_press_event)
        text_editor.show()
        return text_editor

    def _text_changed_callback(self, obj: GtkSource.Buffer):
        """
        A change to the text occurred. Grab the text, update the data and
        update the display.
        """

        new_text = obj.get_text(
            obj.get_start_iter(), obj.get_end_iter(), False
        )
        info = self.page_map[self.notebook.get_current_page()]

        self.update_page_from_doc(info.name, new_text, info.tags)
        self.callback()

    def on_key_press_event(self, obj: RstEditor, event: Gdk.EventKey) -> bool:
        """Look for the F12 key"""
        if event.keyval == Gdk.KEY_F12:
            if clean_format_if_needed(obj):
                self.callback()
            return True
        return False

    @abc.abstractmethod
    def remove_page_from_doc(self, _title: str) -> None:
        """
        Removes a page from the class. Must be overriden by the derived
        class.
        """
        return

    @abc.abstractmethod
    def update_page_from_doc(
        self, _title: str, _text: str, tags: List[str]
    ) -> None:
        """
        Adds/Updates a page from the class. Must be overriden by the derived
        class.
        """
        return
