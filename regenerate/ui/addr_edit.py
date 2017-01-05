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
Provides the edit dialog that allows the user to edit the bit field
information.
"""

import gtk
import os

class AddrMapEdit(object):

    def __init__(self, map_name, subsystem_list, builder):

        label = gtk.Label(
            'Select subsystems for the "{0}" address map'.format(map_name))
        label.set_padding(6, 6)
        dialog = gtk.Dialog("Address Map Subsystem Selection",
                            None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
                            )
        dialog.vbox.pack_start(label)
        label.show()
        table = gtk.Table(len(subsystem_list), 3)
        table.show()
        dialog.vbox.pack_end(table)

        self.cb_list = []

        item_list = []
        for i, val in enumerate(subsystem_list):
            item, active = val
            checkbox = gtk.CheckButton(item)
            checkbox.set_active(active)
            checkbox.show()
            table.attach(checkbox, 1, 2, i, i+1, xpadding=12, ypadding=6)
            item_list.append((item, checkbox))
        response = dialog.run()

        if response == gtk.RESPONSE_REJECT:
            self.cb_list = None
        else:
            self.cb_list = [item for (item, check) in item_list
                            if check.get_active()]
        dialog.destroy()

    def get_list(self):
        return self.cb_list

