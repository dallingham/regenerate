#
# Manage registers in a hardware design
#
# Copyright (C) 2010  Donald N. Allingham
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
Provides a dialog to hold a traceback should a report fail to genreate.
"""

from io import StringIO
import traceback
from pathlib import Path

from gi.repository import Gtk, Gdk
from regenerate.settings.paths import INSTALL_PATH


class TraceBack:
    "Displays traceback information"

    def __init__(self, dest: Path):
        builder = Gtk.Builder()
        bfile = Path(INSTALL_PATH) / "ui" / "traceback.ui"
        builder.add_from_file(str(bfile))
        self.dialog = builder.get_object("traceback_top")
        close_btn = builder.get_object("trace_close")
        copy_btn = builder.get_object("copy_btn")

        self.buffer = builder.get_object("textbuffer")
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        close_btn.connect("clicked", self.close_window)
        copy_btn.connect("clicked", self.copy_text)

        fname = builder.get_object("filename")
        fname.set_text(str(dest))
        data = StringIO()
        traceback.print_exc(file=data)
        self.data = data.getvalue()
        self.buffer.set_text(self.data)
        self.dialog.show_all()

    def close_window(self, _button: Gtk.Button) -> None:
        "Closes the dialog"
        self.dialog.destroy()

    def copy_text(self, _button: Gtk.Button) -> None:
        "Copies the text to the clipboard"
        self.clipboard.set_text(self.data, -1)
