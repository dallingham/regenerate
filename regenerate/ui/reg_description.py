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
Register description management
"""

from gi.repository import Gdk
from regenerate.ui.spell import Spell
from regenerate.ui.utils import clean_format_if_needed
from regenerate.ui.preview_editor import PreviewEditor
from .textview import RstEditor

class RegisterDescription:
    """
    Handles the Register description. Sets the font to a monospace font,
    sets up the changed handler, sets up the spell checker, and makes
    the link to the preview editor.

    Requires a callback functions from the main window to mark the
    the system as modified.
    """

    def __init__(self, text_view, web_view, change_callback):

        editor = RstEditor()
        editor.show()
        text_view.add(editor)
        Spell(editor)

        self.buf = editor.get_buffer()
        self.buf.connect("changed", self.changed)

        self.reg = None

        self.preview = PreviewEditor(self.buf, web_view)
        self.callback = change_callback

    def preview_enable(self):
        """Enables the preview window"""
        self.preview.enable()

    def preview_disable(self):
        """Disables the preview window"""
        self.preview.disable()

    def set_database(self, dbase):
        """Change the database so the preview window can resolve references"""
        self.preview.set_dbase(dbase)
        self.set_register(None)

    def set_register(self, reg):
        """Change the register, and update the description"""
        self.reg = reg
        if reg is None:
            self.buf.set_text("")
        else:
            self.buf.set_text(reg.description)
        self.buf.set_modified(False)

    def changed(self, _obj):
        """A change to the text occurred"""
        if self.reg:
            new_text = self.buf.get_text(
                self.buf.get_start_iter(), self.buf.get_end_iter(), False
            )
            self.reg.description = new_text
            self.callback(self.reg)

    def on_key_press_event(self, obj, event):
        """If F12 pressed, clean the selection"""

        if event.keyval == Gdk.KEY_F12:
            if clean_format_if_needed(obj):
                self.callback(self.reg)
            return True
        return False
