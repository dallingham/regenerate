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

import regenerate.extras
from regenerate.db import LOGGER
from regenerate.ui.base_window import BaseWindow
from regenerate.ui.html_display import HtmlDisplay


class SummaryWindow(BaseWindow):

    window = None
    wkit = None
    container = None
    button = None

    def __init__(self, builder, reg, regset_name, project):

        super().__init__()

        if SummaryWindow.window is None:
            SummaryWindow.window = builder.get_object("summary_window")
            self.configure(SummaryWindow.window)
            SummaryWindow.wkit = HtmlDisplay()
            SummaryWindow.container = builder.get_object("summary_scroll")
            SummaryWindow.container.add(SummaryWindow.wkit)
            SummaryWindow.button = builder.get_object("summary_button")
            SummaryWindow.button.connect("clicked", self.hide)
            SummaryWindow.window.connect("destroy", self.destroy)
            SummaryWindow.window.connect("delete_event", self.delete)
            SummaryWindow.window.show_all()
        else:
            SummaryWindow.window.show()

        reg_info = regenerate.extras.RegisterRst(
            reg, regset_name, project, show_uvm=True
        )
        text = reg_info.html_css()
        try:
            SummaryWindow.wkit.load_html(text, "text/html")
        except:
            SummaryWindow.wkit.load_html_string(text, "text/html")

    def destroy(self, obj):
        SummaryWindow.window.hide()
        return True

    def delete(self, obj, event):
        SummaryWindow.window.hide()
        return True

    def hide(self, obj):
        SummaryWindow.window.hide()
