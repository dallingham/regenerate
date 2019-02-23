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
import gobject


class StatusHandler(logging.Handler):
    """
    Status handler for the logger that displays the string in the
    statusbar for 5 seconds
    """

    SECONDS = 8

    def __init__(self, status_obj):
        super(StatusHandler, self).__init__()
        self.status_obj = status_obj
        self.status_id = status_obj.get_context_id(__name__)
        self.timer = None

    def emit(self, record):
        idval = self.status_obj.push(self.status_id, record.getMessage())
        gobject.timeout_add(self.SECONDS * 1000, self._clear, idval)

    def _clear(self, idval):
        self.status_obj.remove(self.status_id, idval)
