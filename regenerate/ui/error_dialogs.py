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

import gtk

DEF_DIALOG_FLAGS = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT


class BaseMsg(gtk.MessageDialog):
    """
    Base message class
    """

    def __init__(self, title, msg, dialog_type, buttons=gtk.BUTTONS_CLOSE, parent=None):

        super(BaseMsg, self).__init__(
            parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            dialog_type,
            buttons=buttons
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
        super(ErrorMsg, self).__init__(
            title, msg, gtk.MESSAGE_ERROR, parent=parent
        )


class WarnMsg(BaseMsg):
    """
    Warning message dialog box
    """

    def __init__(self, title, msg="", parent=None):
        super(WarnMsg, self).__init__(
            title, msg, gtk.MESSAGE_WARNING, parent=parent
        )


class Question(gtk.MessageDialog):
    """
    Question message dialog box
    """

    DISCARD = -1
    CANCEL = -2
    SAVE = -3

    def __init__(self, title, msg, parent=None):

        super(Question, self).__init__(
            parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_QUESTION
        )

        self.set_markup(
            '<span weight="bold" size="larger">{0}</span>'.format(title))
        self.format_secondary_markup(msg)
        self.add_button('Discard Changes', self.DISCARD)
        self.add_button(gtk.STOCK_CANCEL, self.CANCEL)
        self.add_button('Save Changes', self.SAVE)
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
