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
from regenerate.settings.paths import HELP_PATH
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

    def __init__(
        self, builder: Gtk.Builder, filename: str, title: Optional[str] = None
    ):

        super().__init__()

        if HelpWindow.window is None:
            HelpWindow.window = builder.get_object("help_win")
            self.configure(HelpWindow.window)
            HelpWindow.wkit = builder.get_object("html_view")
            HelpWindow.button = builder.get_object("help_close")
            HelpWindow.button.connect("clicked", _hide)
            HelpWindow.window.connect("destroy", _destroy)
            HelpWindow.window.connect("delete_event", _delete)
            HelpWindow.window.show_all()
        else:
            HelpWindow.window.show()

        if Path(filename).suffix == ".rst":
            data = self.load_file(filename)
            try:
                HelpWindow.wkit.load_html(html_string(data), "text/html")
            except:
                HelpWindow.wkit.load_html_string(
                    html_string(data), "text/html"
                )
        else:
            full_path = str(Path(HELP_PATH) / filename)
            HelpWindow.wkit.load_uri(f"file:///{full_path}")

        if title:
            HelpWindow.window.set_title(f"{title} - regenerate")

    def load_file(self, filename: str) -> str:
        "Loads the file if found"

        try:
            fname = Path(HELP_PATH) / filename
            with fname.open() as ifile:
                data = ifile.read()
        except IOError as msg:
            data = f"Help file '{fname}' could not be found\n{str(msg)}"
        return data


def _destroy(_obj):
    """Hide the window with the destroy event is received"""
    if HelpWindow.window:
        HelpWindow.window.hide()
    return True


def _delete(window: Gtk.Window, _event: Gdk.Event):
    """Hide the window with the delete event is received"""
    window.hide()
    return True


def _hide(_button: Gtk.Button):
    "Hide the window"
    if HelpWindow.window:
        HelpWindow.window.hide()
