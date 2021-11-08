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
Provides a dialog window that displays the contents of a file, converting
the contents from restructuredText to HTML.
"""

from typing import Optional
from pathlib import Path
from gi.repository import Gtk, Gdk

from regenerate.settings.paths import INSTALL_PATH, HELP_PATH
from regenerate.ui.preview import html_string
from regenerate.ui.base_window import BaseWindow


class HelpWindow(BaseWindow):
    """
    Presents help contents in a window
    """

    window = None
    wkit = None
    container = None
    button = None

    def __init__(self, filename: str, title: Optional[str] = None):

        super().__init__()

        self._filename = filename

        if HelpWindow.window is None:
            builder = Gtk.Builder()
            bfile = Path(INSTALL_PATH) / "ui" / "help.ui"
            builder.add_from_file(str(bfile))

            HelpWindow.window = builder.get_object("help_win")
            self.configure(HelpWindow.window)
            HelpWindow.wkit = builder.get_object("html_view")
            builder.get_object("go_back").connect("clicked", self._go_back)
            builder.get_object("go_home").connect("clicked", self._go_home)
            builder.get_object("go_forward").connect(
                "clicked", self._go_forward
            )
            HelpWindow.window.connect("destroy", _destroy)
            HelpWindow.window.connect("delete_event", _delete)
            HelpWindow.window.show_all()
        else:
            HelpWindow.window.show()

        self.load_home_page()

        if title:
            HelpWindow.window.set_title(f"{title} - regenerate")

    def load_home_page(self) -> None:
        """Loads the original page specified when created. Treats this
        file as if it were the home page"""

        if HelpWindow.wkit is None:
            return

        if Path(self._filename).suffix == ".rst":
            data = self.load_file(self._filename)
            try:
                HelpWindow.wkit.load_html(html_string(data), "text/html")
            except:
                HelpWindow.wkit.load_html_string(
                    html_string(data), "text/html"
                )
        else:
            full_path = str(Path(HELP_PATH) / self._filename)
            HelpWindow.wkit.load_uri(f"file:///{full_path}")

    def _go_back(self, _obj: Gtk.Button) -> None:
        "Goes back to the previous page"
        if HelpWindow.wkit:
            HelpWindow.wkit.go_back()

    def _go_home(self, _obj: Gtk.Button) -> None:
        "Reloads the home page"
        self.load_home_page()

    def _go_forward(self, _obj: Gtk.Button) -> None:
        "Goes forward"
        if HelpWindow.wkit:
            HelpWindow.wkit.go_forward()

    def load_file(self, filename: str) -> str:
        "Loads the file if found"

        try:
            fname = Path(HELP_PATH) / filename
            with fname.open() as ifile:
                data = ifile.read()
        except IOError as msg:
            data = f"Help file '{fname}' could not be found\n{str(msg)}"
        return data


def _destroy(_obj) -> bool:
    "Hide the window with the destroy event is received"
    if HelpWindow.window:
        HelpWindow.window.hide()
    return True


def _delete(window: Gtk.Window, _event: Gdk.Event) -> bool:
    "Hide the window with the delete event is received"
    window.hide()
    return True
