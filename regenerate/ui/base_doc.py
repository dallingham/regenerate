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
from .spell import Spell
from .utils import clean_format_if_needed
from .preview_editor import PreviewEditor
from .preview_display import PreviewDisplay
from .textview import RstEditor


class DeleteVerify(Gtk.MessageDialog):
    """
    Question message dialog box
    """

    DISCARD = -1
    CANCEL = -2

    def __init__(self, name: str, parent=None):

        super().__init__(
            parent,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.QUESTION,
        )

        self.set_markup(
            f'<span weight="bold" size="larger">Delete "{name}"</span>'
        )
        self.format_secondary_markup(
            f"Do you wish to permanently delete this page?"
        )
        self.add_button("Delete Page", self.DISCARD)
        self.add_button(Gtk.STOCK_CANCEL, self.CANCEL)
        self.set_default_response(self.CANCEL)
        if parent is not None:
            self.set_transient_for(parent)
        self.show_all()

    def run_dialog(self):
        """
        Runs the dialog box, calls the appropriate callback,
        then destroys the window
        """
        status = self.run()
        self.destroy()
        return status


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
        undo_btn: Optional[Gtk.Button] = None,
        redo_btn: Optional[Gtk.Button] = None,
        preview_btn: Optional[Gtk.Button] = None,
    ):
        self.notebook = notebook
        self.project: Optional[RegProject] = None
        self.preview: Optional[PreviewEditor] = None
        self.add_id = add_btn.connect(
            "clicked", self._add_notebook_page_callback
        )
        if undo_btn:
            self.undo_id = undo_btn.connect("clicked", self._undo)
        if redo_btn:
            self.redo_id = redo_btn.connect("clicked", self._redo)
        if preview_btn:
            self.prev_id = preview_btn.connect("clicked", self._preview)

        self.remove_pages()
        self.page_map: List[PageInfo] = []
        self.callback = modified
        self.links = {}

    def _preview(self, obj: Gtk.Button) -> None:
        info = self.page_map[self.notebook.get_current_page()]
        PreviewDisplay(info.textbuf)

    def _undo(self, _obj: Gtk.Button) -> None:
        info = self.page_map[self.notebook.get_current_page()]
        if info.textbuf.can_undo():
            info.textbuf.undo()

    def _redo(self, _obj: Gtk.Button) -> None:
        info = self.page_map[self.notebook.get_current_page()]
        if info.textbuf.can_redo():
            info.textbuf.redo()

    def remove_pages(self) -> None:
        "Removes all pages from the notebook"

        page_count = self.notebook.get_n_pages()
        for _ in range(0, page_count):
            self.notebook.remove_page(0)
        self.page_map = []
        button = Gtk.Button.new_from_icon_name(
            "window-close", Gtk.IconSize.MENU
        )
        button.show_all()

    #        self.notebook.append_page(Gtk.Label("New Page"), button)

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

    def add_page(self, name: str, data: Tuple[str, List[str]]) -> None:
        """
        Adds a page and creates a restructuredText editor associated with their
        page name.
        """

        edit_window = Gtk.ScrolledWindow()
        text_editor = self._create_text_editor()
        edit_window.add(text_editor)

        text_buffer = text_editor.get_buffer()
        text_editor.set_wrap_mode(Gtk.WrapMode.WORD)
        text_buffer.set_text(data[0])
        handler = text_buffer.connect("changed", self._text_changed_callback)
        Spell(text_buffer)

        preview_window = Gtk.ScrolledWindow()
        self.preview = PreviewEditor(text_buffer, preview_window, False)
        edit_window.show_all()

        hbox = Gtk.HBox()
        label = Gtk.Label(name)
        button = Gtk.Button.new_from_icon_name(
            "window-close", Gtk.IconSize.MENU
        )
        button.set_relief(Gtk.ReliefStyle.NONE)

        button_align = Gtk.Alignment(xscale=0, xalign=1)
        button_align.add(button)

        hbox.pack_start(label, True, True, 6)
        hbox.pack_start(button_align, False, False, 0)
        hbox.show_all()

        self.notebook.append_page(edit_window, hbox)
        page_info = PageInfo(handler, text_buffer, name, data[1])
        self.page_map.append(page_info)
        button.connect("clicked", self.delete_page, page_info)

    def delete_page(self, _button: Gtk.Button, info: PageInfo):
        page = 0
        for i in range(0, self.notebook.get_n_pages()):
            if self.page_map[i] == info:
                page = i

        dialog = DeleteVerify(info.name)
        status = dialog.run_dialog()
        if status == DeleteVerify.CANCEL:
            return

        self.notebook.remove_page(page)
        info = self.page_map[page]

        for i in range(page + 1, self.notebook.get_n_pages()):
            self.page_map[i] = self.page_map[i + 1]
        del self.page_map[self.notebook.get_n_pages()]
        self.remove_page_from_doc(info.name)
        self.callback()

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
