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
Provides reusable dialog boxes for messages
"""

from gi.repository import Gtk

DEF_DIALOG_FLAGS = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT


class BaseMsg(Gtk.MessageDialog):
    """
    Base message class
    """

    def __init__(
        self, title, msg, dialog_type, buttons=Gtk.ButtonsType.CLOSE, parent=None
    ):

        super().__init__(
            parent,
            DEF_DIALOG_FLAGS,
            dialog_type,
            buttons=buttons,
        )

        if parent is not None:
            self.set_transient_for(parent)
        self.set_markup('<span weight="bold" size="larger">%s</span>' % title)
        self.format_secondary_markup(msg)
        self.run_dialog()

    def run_dialog(self):
        """
        Runs the dialog box then destroys the window
        """
        self.run()
        self.destroy()


class ErrorMsg(BaseMsg):
    """
    Error message dialog box
    """

    def __init__(self, title, msg="", parent=None):
        super().__init__(title, msg, Gtk.MessageType.ERROR, parent=parent)


class WarnMsg(BaseMsg):
    """
    Warning message dialog box
    """

    def __init__(self, title, msg="", parent=None):
        super().__init__(
            title, msg, Gtk.MessageType.WARNING, parent=parent
        )


class Question(Gtk.MessageDialog):
    """
    Question message dialog box
    """

    DISCARD = -1
    CANCEL = -2
    SAVE = -3

    def __init__(self, title, msg, parent=None):

        super().__init__(
            parent,
            DEF_DIALOG_FLAGS,
            Gtk.MessageType.QUESTION,
        )

        self.set_markup('<span weight="bold" size="larger">{}</span>'.format(title))
        self.format_secondary_markup(msg)
        self.add_button("Discard Changes", self.DISCARD)
        self.add_button(Gtk.STOCK_CANCEL, self.CANCEL)
        self.add_button("Save Changes", self.SAVE)
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
