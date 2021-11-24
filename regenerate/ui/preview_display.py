#
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
Handles the preview display that shows the rendered reStructuredText

Creates a HTML viewer that is associated with a text buffer. On start up
and when the refresh button is pressed, the latest text is pulled from the
text buffer, converted from reStructuredText to HTML, and displayed.
"""

from gi.repository import Gtk

from .preview import html_string
from .html_display import HtmlDisplay
from .base_window import BaseWindow


class PreviewDisplay(BaseWindow):
    "Restructured Text previewer"

    def __init__(
        self,
        textbuf: Gtk.TextBuffer,
    ):
        super().__init__()

        self.window = Gtk.Window()
        self.window.set_resizable(True)
        self.window.set_default_size(800, 600)
        self.configure(self.window)
        self.textbuf = textbuf
        self.container = HtmlDisplay()

        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        refresh = Gtk.ToolButton()
        refresh.set_stock_id(Gtk.STOCK_REFRESH)
        refresh.set_label("Refresh")
        toolbar.insert(refresh, 0)

        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )
        scroll_window.add(self.container)

        vbox = Gtk.VBox(spacing=0)
        vbox.pack_start(toolbar, False, False, 0)
        vbox.pack_start(scroll_window, True, True, 0)

        self.window.add(vbox)
        self.window.show_all()
        refresh.connect("clicked", self.on_refresh_button_clicked)
        self.update()

    def on_refresh_button_clicked(self, _button: Gtk.Button):
        "Updates the display with the latest text from the assi"
        self.update()

    def update(self):
        "Pulls the data from the associated text buffer, converts to HTML"

        text = self.textbuf.get_text(
            self.textbuf.get_start_iter(),
            self.textbuf.get_end_iter(),
            False,
        )
        self.container.load_html(html_string(text), "text/html")
