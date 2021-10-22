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
Data entry classes.
"""
import re

from gi.repository import GObject, Gtk


class ValidWordEntry(Gtk.Entry, Gtk.Editable):

    __gtype_name__ = "ValidWordEntry"

    def __init__(self):
        super(ValidWordEntry, self).__init__()

    def do_insert_text(self, new_text, length, position):
        regexp = re.compile("^[A-Za-z0-9_]+$")

        if regexp.match(new_text) is not None:
            self.get_buffer().insert_text(position, new_text, length)
            return position + length

        return position


class ValidHexEntry(Gtk.Entry, Gtk.Editable):

    __gtype_name__ = "ValidHexEntry"

    def __init__(self):
        super(ValidHexEntry, self).__init__()

    def do_insert_text(self, new_text, length, position):
        regexp = re.compile("^[xA-Fa-f0-9_]+$")

        if regexp.match(new_text) is not None:
            self.get_buffer().insert_text(position, new_text, length)
            return position + length

        return position


class ValidIntEntry(Gtk.Entry, Gtk.Editable):

    __gtype_name__ = "ValidIntEntry"

    def __init__(self):
        super(ValidIntEntry, self).__init__()

    def do_insert_text(self, new_text, length, position):
        regexp = re.compile("^[0-9]+$")

        if regexp.match(new_text) is not None:
            self.get_buffer().insert_text(position, new_text, length)
            return position + length

        return position
