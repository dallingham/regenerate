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

import os
from regenerate.settings.paths import HELP_PATH
from regenerate.ui.preview import html_string
from regenerate.ui.base_window import BaseWindow
from regenerate.ui.html_display import HtmlDisplay


class HelpWindow(BaseWindow):
    """
    Presents help contents in a window
    """

    window = None
    wkit = None
    container = None
    button = None

    def __init__(self, builder, filename):

        super().__init__()

        try:
            fname = os.path.join(HELP_PATH, filename)
            with open(fname) as ifile:
                data = ifile.read()
        except IOError as msg:
            data = f"Help file '{fname}' could not be found\n{str(msg)}"

        if HelpWindow.window is None:
            HelpWindow.window = builder.get_object("help_win")
            self.configure(HelpWindow.window)
            HelpWindow.wkit = HtmlDisplay()
            help(HelpWindow.wkit)
            HelpWindow.container = builder.get_object("help_scroll")
            HelpWindow.container.add(HelpWindow.wkit)
            HelpWindow.button = builder.get_object("help_close")
            HelpWindow.button.connect("clicked", self.hide)
            HelpWindow.window.connect("destroy", self.destroy)
            HelpWindow.window.connect("delete_event", self.delete)
            HelpWindow.window.show_all()
        else:
            HelpWindow.window.show()

        try:
            HelpWindow.wkit.load_html(html_string(data), "text/html")
        except:
            HelpWindow.wkit.load_html_string(html_string(data), "text/html")

    def destroy(self, _obj):
        """Hide the window with the destroy event is received"""
        HelpWindow.window.hide()
        return True

    def delete(self, _obj, _event):
        """Hide the window with the delete event is received"""
        HelpWindow.window.hide()
        return True

    def hide(self, _obj):
        """Hide the window"""
        HelpWindow.window.hide()
