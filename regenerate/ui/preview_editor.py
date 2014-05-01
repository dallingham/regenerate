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
Provides a preview editor, tying a text buffer to a webkit display. All
changes to the buffer cause an update on the webkit display, after the
text is converted from restructuredText to HTML.
"""

from regenerate.db import LOGGER

try:
    import webkit
    from preview import html_string
    PREVIEW_ENABLED = True
except ImportError:
    PREVIEW_ENABLED = False
    LOGGER.warning("Webkit is not installed, preview of formatted "
                   "comments will not be available")


class PreviewEditor(object):
    """
    Connects a text buffer to a webkit display.
    """

    def __init__(self, text_buffer, webkit_container):
        if not PREVIEW_ENABLED:
            return

        self.__webkit = webkit.WebView()
        self.__container = webkit_container
        self.__container.add(self.__webkit)
        self.__container.hide()
        self.__text_buffer = text_buffer
        self.__text_buffer.connect('changed', self._changed)
        self.__update = False
        self.__adjust = self.__container.get_vadjustment()
        self.__active_db = None

    def __update_text(self):
        """
        Extracts text from the buffer, converts it to HTML, and loads it
        into the webkit display
        """
        text = self.__text_buffer.get_text(
            self.__text_buffer.get_start_iter(),
            self.__text_buffer.get_end_iter())
        if self.__active_db:
            data = []
            for reg in self.__active_db.get_all_registers():
                data.append(".. _`%s`: /" % reg.register_name)
            text = text + "\n\n" + "\n".join(data)
        self.__webkit.load_string(html_string(text), "text/html", "utf-8", "")

    def set_dbase(self, dbase):
        self.__active_db = dbase

    def enable(self):
        """
        Enables updating and display of the webkit display
        """
        if PREVIEW_ENABLED:
            self.__update_text()
            self.__container.show()
            self.__webkit.show()
        self.__update = True

    def disable(self):
        """
        Disables updating and display of the webkit display
        """
        self.__update = False
        if PREVIEW_ENABLED:
            self.__webkit.hide()
            self.__container.hide()

    def _changed(self, obj):
        """
        Text buffer callback tying the buffer to the display
        """
        if self.__update:
            pos = self.__adjust.get_value()
            self.__update_text()
            if pos <= self.__adjust.get_upper():
                self.__adjust.set_value(pos)
