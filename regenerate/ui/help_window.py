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


try:
    import webkit
    WEBKIT = True
except ImportError:
    WEBKIT = False

from regenerate.settings.paths import HELP_PATH
import os.path
from preview import html_string


class HelpWindow(object):

    window = None
    wkit = None
    container = None
    button = None

    def __init__(self, builder, filename):

        if not WEBKIT:
            return

        try:
            fname = os.path.join(HELP_PATH, filename)
            f = open(fname)
            data = f.read()
        except IOError, msg:
            data = "Help file '%s' could not be found" % fname

        if HelpWindow.window is None:
            HelpWindow.window = builder.get_object("help_win")
            HelpWindow.wkit = webkit.WebView()
            HelpWindow.container = builder.get_object('help_scroll')
            HelpWindow.container.add(HelpWindow.wkit)
            HelpWindow.button = builder.get_object('help_close')
            HelpWindow.button.connect('clicked', self.hide)
            HelpWindow.window.connect('destroy', self.destroy)
            HelpWindow.window.connect('delete_event', self.delete)

        HelpWindow.wkit.load_string(html_string(data), "text/html", "utf-8", "")
        HelpWindow.window.show_all()

    def destroy(self, obj):
        HelpWindow.window.hide()
        return True

    def delete(self, obj, event):
        HelpWindow.window.hide()
        return True

    def hide(self, obj):
        HelpWindow.window.hide()
