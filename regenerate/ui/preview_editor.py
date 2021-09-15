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

from typing import Optional
from regenerate.db import RegProject
from regenerate.db.utils import get_register_paths

from regenerate.ui.preview import html_string
from regenerate.ui.html_display import HtmlDisplay


class PreviewEditor:
    """
    Connects a text buffer to a webkit display.
    """

    def __init__(self, text_buffer, webkit_container, use_reg=True):

        #        self.__webkit = HtmlDisplay()
        self.__container = webkit_container
        child = self.__container.get_child()
        if child:
            self.__container.remove(child)
        #        self.__container.add(self.__webkit)
        #        self.__container.hide()
        self.__text_buffer = text_buffer
        #        self.__text_buffer.connect("changed", self._changed)
        self.__update = False
        self.__adjust = self.__container.get_vadjustment()
        self.__use_reg = use_reg
        self.links = {}
        self.enable()

    def __update_text(self):
        """
        Extracts text from the buffer, converts it to HTML, and loads it
        into the webkit display
        """
        return
        text = self.__text_buffer.get_text(
            self.__text_buffer.get_start_iter(),
            self.__text_buffer.get_end_iter(),
            False,
        )
        if self.__use_reg:
            links = []
            for key, data in self.links.items():
                links.append(f".. _`{key}`: /{data[0]}/{data[1]}/{data[2]}")
            text = text + "\n\n" + "\n".join(links)

        self.__webkit.show_html(html_string(text))

    def set_project(self, project: Optional[RegProject]):
        """Sets the database"""

        if project:
            self.links = get_register_paths(project)
        else:
            self.links = {}

    def enable(self):
        """
        Enables updating and display of the webkit display
        """
        return
        self.__update_text()
        self.__container.show()
        self.__webkit.show()
        self.__update = True

    def disable(self):
        """
        Disables updating and display of the webkit display
        """
        return
        self.__update = False
        self.__webkit.hide()
        self.__container.hide()

    def _changed(self, _obj):
        """
        Text buffer callback tying the buffer to the display
        """
        return
        if self.__update:
            pos = self.__adjust.get_value()
            self.__update_text()
            if pos <= self.__adjust.get_upper():
                self.__adjust.set_value(pos)
