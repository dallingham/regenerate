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
Select the available WebKit version and handle the differences.
"""

from regenerate.db import LOGGER

try:
    import gi

    gi.require_version("WebKit2", "4.0")
    from gi.repository import WebKit2 as webkit

    WEBKIT = True

except ValueError:

    try:
        gi.require_version("WebKit", "3.0")
        from gi.repository import WebKit as webkit

        WEBKIT = True

    except ImportError:

        WEBKIT = False
        PREVIEW_ENABLED = False
        LOGGER.warning(
            "Webkit is not installed, preview of formatted "
            "comments will not be available"
        )


class HtmlDisplay(webkit.WebView):
    """Wrapper interface for WebKit"""

    def show_html(self, data):
        """Shows the HTML using either Webkit 4.0 or 3.0"""

        try:
            self.load_html(data, "text/html")
        except AttributeError:
            self.load_html_string(data, "text/html")
