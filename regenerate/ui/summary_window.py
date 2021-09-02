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
Provides the summary window
"""

from gi.repository import Gtk, Gdk

import regenerate.extras
from regenerate.ui.base_window import BaseWindow
from regenerate.ui.html_display import HtmlDisplay


class SummaryWindow(BaseWindow):
    """Provides the summary window"""

    window = None
    wkit = None
    container = None
    button = None

    def __init__(self, widgets, reg, _regset_name, project, dbase):

        super().__init__()

        if SummaryWindow.window is None:
            SummaryWindow.window = widgets.summary_window
            self.configure(SummaryWindow.window)
            SummaryWindow.wkit = HtmlDisplay()
            SummaryWindow.container = widgets.summary_scroll
            SummaryWindow.container.add(SummaryWindow.wkit)
            SummaryWindow.button = widgets.summary_button
            SummaryWindow.button.connect("clicked", self.hide)
            SummaryWindow.window.connect("destroy", self.destroy)
            SummaryWindow.window.connect("delete_event", self.delete)
            SummaryWindow.window.show_all()
        else:
            SummaryWindow.window.show()

        reg_info = regenerate.extras.RegisterRst(
            reg, project=project, show_uvm=True, dbase=dbase
        )
        text = reg_info.html_css()
        SummaryWindow.wkit.show_html(text)

    def destroy(self, _obj: Gtk.Window):
        """Hide the window on the destroy event"""
        if self.window:
            self.window.hide()
        return True

    def delete(self, _obj: Gtk.Window, _event: Gdk.Event):
        """Hide the window on the delete event"""
        if self.window:
            self.window.hide()
        return True

    def hide(self, _obj: Gtk.Button):
        """Hide the window"""
        if self.window:
            self.window.hide()
