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
from regenerate.ui.columns import ToggleColumn, EditableColumn, ComboMapColumn
from regenerate.ui.base_window import BaseWindow


class AddrMapEdit(BaseWindow):
    """
    Creates a dialog box allowing the selection of subsystem groups
    for an address map.
    """

    def __init__(self, map_name, subsystem_list, builder, project, parent):

        super(AddrMapEdit, self).__init__()
        self.project = project

        label = gtk.Label(
            'Select subsystems for the "{0}" address map'.format(map_name))
        label.set_padding(6, 6)

        dialog = gtk.Dialog(
            "Address Map Subsystem Selection",
            None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        )

        dialog.vbox.pack_start(label, False, False)
        dialog.vbox.set_homogeneous(False)
        dialog.set_default_size(580, 320)
        dialog.set_transient_for(parent)
        self.configure(dialog)

        label.show()

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                   gtk.POLICY_AUTOMATIC)
        scrolled_window.show()
        dialog.vbox.pack_end(scrolled_window)

        self.view = gtk.TreeView()
        self.model = gtk.TreeStore(bool, str, str, object, str)
        self.view.set_model(self.model)

        self.view.show()
        col = ToggleColumn(
            "Enabled",
            self._enable_changed,
            0,
            visible_callback=self.visible_callback2
        )

        self.view.append_column(col)

        col = EditableColumn("Subsystem", None, 1)
        col.set_min_width(200)
        self.view.append_column(col)

        options = [("Full Access", 0),
                   ("Read Only", 1),
                   ("Write Only", 2),
                   ("No Access", 3),
                   ]

        col = ComboMapColumn(
            "Access Method",
            self._access_changed,
            options,
            2,
            visible_callback=self.visible_callback
        )

        self.view.append_column(col)

        scrolled_window.add(self.view)

        self.cb_list = []

        for val in subsystem_list:
            group, active = val
            title = group.name
            top = self.model.append(None, row=(active, title, "", None, None))
            for item in group.register_sets:
                access = project.get_access(map_name, group.name, item.inst)
                self.model.append(top, row=(
                    True,
                    item.inst,
                    options[access][0],
                    item,
                    group.name)
                )

        self.map_name = map_name

        response = dialog.run()

        if response == gtk.RESPONSE_REJECT:
            self.cb_list = None
        else:
            self.cb_list = [row[1] for row in self.model if row[0]]
        dialog.destroy()

    def visible_callback(self, column, cell, model, *obj):
        node = obj[0]
        cell.set_property('visible', len(model.get_path(node)) != 1)

    def visible_callback2(self, column, cell, model, *obj):
        node = obj[0]
        cell.set_property('visible', len(model.get_path(node)) == 1)

    def _enable_changed(self, cell, path, source):
        self.model[path][0] = not self.model[path][0]

    def _access_changed(self, obj, path, node, val):
        mdl = obj.get_property('model')
        val = mdl.get_value(node, 0)
        val_int = mdl.get_value(node, 1)
        self.model[path][2] = val

        self.project.set_access(
            self.map_name,
            self.model[path][-1],
            self.model[path][1],
            val_int
        )

    def get_list(self):
        return self.cb_list
