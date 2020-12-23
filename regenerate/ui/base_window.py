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
Base class for windows, setting the icons
"""

import os
from regenerate.settings.paths import INSTALL_PATH


class BaseWindow:
    """
    Provides the base window class. Currently, only provides the
    common icon, selecting the SVG if possible, if not, defaulting
    to the PNG.
    """

    def __init__(self):
        pass

    def configure(self, obj):
        """Sets the icon image to the passed object"""
        try:
            image = os.path.join(INSTALL_PATH, "media", "flop.svg")
            obj.set_icon_from_file(image)
        except:
            image = os.path.join(INSTALL_PATH, "media", "flop.png")
            obj.set_icon_from_file(image)
