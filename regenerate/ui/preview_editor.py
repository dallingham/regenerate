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


class PreviewEditor:
    """
    Connects a text buffer to a webkit display.
    """

    def __init__(self, text_buffer, webkit_container, use_reg=True):

        self.__container = webkit_container
        child = self.__container.get_child()
        if child:
            self.__container.remove(child)
        self.__text_buffer = text_buffer
        self.__update = False
        self.__adjust = self.__container.get_vadjustment()
        self.__use_reg = use_reg
        self.links = {}

    def set_project(self, project: Optional[RegProject]):
        """Sets the database"""

        self.links = get_register_paths(project) if project else {}
