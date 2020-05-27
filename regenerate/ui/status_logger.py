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

import logging
from gi.repository import GObject, Gtk, Gdk


class StatusHandler(logging.Handler):
    """
    Status handler for the logger that displays the string in the
    statusbar for 5 seconds
    """

    SECONDS = 10

    def __init__(self, status_obj):
        super().__init__()
        self.status_obj = status_obj
        style = status_obj.get_style_context()
        self.normal_color = style.get_background_color(Gtk.StateType.NORMAL)
        self.status_id = status_obj.get_context_id(__name__)
        self.timer = None
        self.error_color = Gdk.RGBA()
        self.error_color.red = 0.5
        self.error_color.green = 0
        self.error_color.blue = 0
        self.error_color.alpha = 1

    def emit(self, record):
        if record.levelno == 30:
            self.status_obj.override_color(
                Gtk.StateFlags.NORMAL, self.error_color
            )
        else:
            self.status_obj.override_color(
                Gtk.StateFlags.NORMAL, self.normal_color
            )

        idval = self.status_obj.push(
            self.status_id, "ERROR: {}".format(record.getMessage())
        )
        GObject.timeout_add(self.SECONDS * 1000, self._clear, idval)

    def _clear(self, idval):
        self.status_obj.remove(self.status_id, idval)
