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

from gi.repository import Gtk
from regenerate.settings.paths import GLADE_PREF
from regenerate.settings import ini
"""
Provides the preferences dialog box
"""


class Preferences(object):

    def __init__(self, parent):
        self.__builder = Gtk.Builder()
        self.__builder.add_from_file(GLADE_PREF)
        self.__properties = self.__builder.get_object('preferences')

        value = bool(int(ini.get('user', 'load_last_project', 0)))
        self.__builder.get_object('load_last_project').set_active(value)

        value = ini.get('user', 'column_width', "80")
        self.__builder.get_object('column_width').set_value(float(value))

        self.__builder.connect_signals(self)
        self.__properties.set_transient_for(parent)
        self.__properties.show()

    def on_load_last_project_toggled(self, obj):
        ini.set('user', 'load_last_project', int(bool(obj.get_active())))

    def on_column_width_value_changed(self, obj):
        ini.set('user', 'column_width', obj.get_value_as_int())

    def on_close_button_clicked(self, obj):
        self.__properties.destroy()
