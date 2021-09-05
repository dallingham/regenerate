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
Provides the preferences dialog box
"""

from gi.repository import Gtk
from regenerate.settings.paths import GLADE_PREF
from regenerate.settings import ini


class Preferences:
    """Manage the preferences"""

    def __init__(self, parent: Gtk.Window):
        self._builder = Gtk.Builder()
        self._builder.add_from_file(str(GLADE_PREF))
        self._properties = self._builder.get_object("preferences")

        value = bool(int(ini.get("user", "load_last_project", 0)))
        self._builder.get_object("load_last_project").set_active(value)

        self._builder.connect_signals(self)
        self._properties.set_transient_for(parent)
        self._properties.show()

    def on_load_last_project_toggled(self, obj) -> None:
        """Called to load the last project"""
        ini.set("user", "load_last_project", int(bool(obj.get_active())))

    def on_close_button_clicked(self, _obj) -> None:
        """Close the window"""
        self._properties.destroy()
