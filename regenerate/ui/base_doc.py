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
from .help_window import HelpWindow


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
            "Do you wish to permanently delete this page?"
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
        button: Gtk.Button,
        textbuf: GtkSource.Buffer,
        tagbox: Gtk.HBox,
        name: str,
        tags: List[str],
    ):
        self.tags = tags
        self.handler = handler
        self.button = button
        self.textbuf = textbuf
        self.tagbox = tagbox
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
    ):
        self.notebook = notebook
        self.project: Optional[RegProject] = None
        self.preview: Optional[PreviewEditor] = None

        search = Gtk.SearchEntry()
        self.search_bar = Gtk.SearchBar()
        self.search_bar.connect_entry(search)
        self.search_bar.add(search)
        self.search_bar.show_all()
        self.search_bar.set_search_mode(True)

        # next_btn = Gtk.ToolButton()
        # next_btn.set_stock_id(Gtk.STOCK_GO_DOWN)
        # next_btn.set_tooltip_text("Find next")
        # next_btn.show()

        add = Gtk.ToolButton()
        add.set_stock_id(Gtk.STOCK_ADD)
        add.set_tooltip_text("Add a new page")
        add.show()

        preview = Gtk.ToolButton()
        preview.set_stock_id(Gtk.STOCK_FILE)
        preview.set_tooltip_text("Open preview window")
        preview.show()

        add_tag = Gtk.ToolButton()
        add_tag.set_stock_id(Gtk.STOCK_PROPERTIES)
        add_tag.set_tooltip_text("Add a tag to the page")
        add_tag.show()

        help_btn = Gtk.ToolButton()
        help_btn.set_stock_id(Gtk.STOCK_HELP)
        help_btn.set_tooltip_text("Display help")
        help_btn.show()

        hbox = Gtk.HBox()
        hbox.pack_start(self.search_bar, False, True, 0)
        hbox.pack_start(add, False, True, 0)
        hbox.pack_start(add_tag, False, True, 0)
        hbox.pack_start(preview, False, True, 0)
        hbox.pack_start(help_btn, False, True, 0)
        hbox.show()
        self.notebook.set_action_widget(hbox, Gtk.PackType.END)

        preview.connect("clicked", self._preview)
        add.connect("clicked", self._add_notebook_page_callback)
        add_tag.connect("clicked", self._add_tag)
        help_btn.connect("clicked", _help)
        search.connect("next-match", self._next_match, search)
        search.connect("previous-match", self._prev_match)
        search.connect("search-changed", self._search_changed)
        search.connect("stop-search", self._stop_search)

        self.page_map: List[PageInfo] = []
        self.remove_pages()
        self.callback = modified
        self.notebook.connect("switch-page", self.switch_page)

    def _next_match(self, button, obj):
        page_num = self.notebook.get_current_page()
        info = self.page_map[page_num]
        widget = self.notebook.get_nth_page(page_num)
        textview = widget.get_children()[0].get_children()[0]

        last_pos = info.textbuf.get_mark("last_pos")
        if last_pos is None:
            return

        text_iter = info.textbuf.get_iter_at_mark(last_pos)
        search_str = obj.get_text()
        found = text_iter.forward_search(search_str, 0, None)
        if found:
            match_start, match_end = found
            info.textbuf.select_range(match_start, match_end)
            last_pos = info.textbuf.create_mark("last_pos", match_end, False)
            textview.scroll_to_mark(last_pos, 0, True, 0.0, 0.5)

    def _prev_match(self, *obj):
        print("prev_match", *obj)

    def _search_changed(self, obj):
        page_num = self.notebook.get_current_page()
        info = self.page_map[page_num]
        widget = self.notebook.get_nth_page(page_num)
        textview = widget.get_children()[0].get_children()[0]

        search_str = obj.get_text()
        start_iter = info.textbuf.get_start_iter()
        found = start_iter.forward_search(search_str, 0, None)
        if found:
            match_start, match_end = found
            info.textbuf.select_range(match_start, match_end)
            last_pos = info.textbuf.create_mark("last_pos", match_end, False)
            textview.scroll_to_mark(last_pos, 0, True, 0.0, 0.5)

    def _stop_search(self, *obj):
        print("stop_search", *obj)

    def _preview(self, _obj: Gtk.Button) -> None:
        "Display the preview window"
        info = self.page_map[self.notebook.get_current_page()]
        PreviewDisplay(info.textbuf)

    def remove_pages(self) -> None:
        "Removes all pages from the notebook"

        page_count = self.notebook.get_n_pages()
        if page_count:
            for _ in range(0, page_count):
                self.notebook.remove_page(0)
        if self.page_map:
            self.page_map = []

    def _add_tag(self, _button: Gtk.Button) -> None:
        "GTK callback to adds tag to the page"

        dialog = Gtk.Dialog(
            "Add a Tag",
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

        label = Gtk.Label("Enter the tag name")
        name = Gtk.Entry()
        name.set_activates_default(True)

        # pylint: disable=E1101

        vbox = dialog.get_content_area()
        vbox.pack_start(label, False, False, 6)
        vbox.pack_start(name, False, False, 6)

        dialog.show_all()
        res = dialog.run()
        if res == Gtk.ResponseType.ACCEPT:
            tag_name = name.get_text()

            info = self.page_map[self.notebook.get_current_page()]
            if tag_name not in info.tags:
                info.tags.append(tag_name)
                label_tag = self.make_tag(tag_name, info)
                info.tagbox.pack_start(label_tag, False, False, 3)

            self.callback()
        dialog.destroy()

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

        # pylint: disable=E1101

        vbox = dialog.get_content_area()
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

        edit_window.show_all()

        hbox = Gtk.HBox()
        label = Gtk.Label(name)
        label.set_padding(3, 3)
        label.show()

        button = Gtk.Button.new_from_icon_name(
            "window-close", Gtk.IconSize.MENU
        )
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.hide()

        button_align = Gtk.Alignment(xscale=0, xalign=1)
        button_align.add(button)

        hbox.pack_start(label, True, True, 6)
        hbox.pack_start(button_align, False, False, 0)
        hbox.show_all()

        flow = Gtk.HBox()
        for tag in data[1]:
            flow.pack_start(self.make_tag(tag, data[1]), False, False, 3)
        flow.show()

        top_box = Gtk.VBox()
        top_box.pack_start(edit_window, True, True, 0)
        top_box.pack_start(flow, False, False, 3)
        top_box.show()

        page_info = PageInfo(handler, button, text_buffer, flow, name, data[1])
        self.page_map.append(page_info)
        self.notebook.append_page(top_box, hbox)
        button.connect("clicked", self.delete_page, page_info)

    def delete_tag(self, _button: Gtk.Button, extra):
        "Deletes the tag associated with the button"

        data, tag, frame = extra
        if tag in data:
            data.remove(tag)
        frame.hide()
        self.callback()

    def make_tag(self, name: str, data) -> Gtk.Frame:
        "Creates a tag and adds it"

        label = Gtk.Label()
        label.set_markup(f"<b>{name}</b>")
        close = Gtk.Button.new_from_icon_name(
            "window-close", Gtk.IconSize.MENU
        )
        close.set_relief(Gtk.ReliefStyle.NONE)

        box = Gtk.HBox()
        box.pack_start(label, True, True, 3)
        box.pack_start(close, False, False, 0)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.OUT)
        frame.add(box)
        frame.show_all()
        close.connect("clicked", self.delete_tag, (data, name, frame))
        return frame

    def switch_page(self, notebook, _obj, page):
        "Called with the page switches, changing the buttons"

        current = notebook.get_current_page()
        try:
            old_info = self.page_map[current]
            old_info.button.hide()
        except IndexError:
            pass
        self.page_map[page].button.show()
        widget = self.notebook.get_nth_page(page)
        textview = widget.get_children()[0].get_children()[0]
        # self.search_bar.set_key_capture_widget(textview)

    def delete_page(self, _button: Gtk.Button, info: PageInfo):
        "Delete the current document page"

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


def _help(_button: Gtk.Button) -> None:
    "Display the help window"
    HelpWindow("doc.html", "Documentation")
