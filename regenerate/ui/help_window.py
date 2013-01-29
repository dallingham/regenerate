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

    def __init__(self, builder, filename):

        print "HELP"
        if WEBKIT:
            fname = os.path.join(HELP_PATH, filename)
            f = open(fname)
            help_window = builder.get_object("help_win")
            help_wkit = webkit.WebView()
            wk_container = builder.get_object('help_scroll')
            wk_container.add(help_wkit)
            button = builder.get_object('help_close')
            button.connect('clicked', lambda x, y: y.destroy(),
                           help_window)
            help_wkit.load_string(html_string(f.read()), "text/html", "utf-8", "")
            help_window.show_all()
