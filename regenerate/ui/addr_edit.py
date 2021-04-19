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

from typing import List, Tuple

from gi.repository import Gtk
from regenerate.db import BlockInst, RegProject
from regenerate.ui.columns import ToggleColumn, EditableColumn, ComboMapColumn
from regenerate.ui.base_window import BaseWindow


class AddrMapEdit(BaseWindow):
    """
    Creates a dialog box allowing the selection of subsystem groups
    for an address map.
    """

    def __init__(
        self,
        map_name: str,
        subsystem_list: List[Tuple[BlockInst, bool]],
        project: RegProject,
        parent: Gtk.Window,
        callback,
    ):

        super().__init__()
        self.project = project
        self.callback = callback

        label = Gtk.Label(
            f'Select subsystems for the "{map_name}" address map'
        )
        label.set_padding(6, 6)

        dialog = Gtk.Dialog(
            "Address Map Subsystem Selection",
            None,
            Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.REJECT,
                Gtk.STOCK_OK,
                Gtk.ResponseType.ACCEPT,
            ),
        )

        box = dialog.get_content_area()
        box.pack_start(label, False, False, 12)
        box.set_homogeneous(False)
        dialog.set_default_size(580, 320)
        dialog.set_transient_for(parent)
        self.configure(dialog)

        label.show()

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )
        scrolled_window.show()
        box.pack_end(scrolled_window, True, True, 12)

        self.view = Gtk.TreeView()
        self.model = Gtk.TreeStore(bool, str, str, object, str)
        self.view.set_model(self.model)

        self.view.show()
        col = ToggleColumn(
            "Enabled",
            self._enable_changed,
            0,
            visible_callback=self.visible_callback2,
        )

        self.view.append_column(col)

        col = EditableColumn("Subsystem", None, 1)
        col.set_min_width(200)
        self.view.append_column(col)

        options = [
            ("Full Access", 0),
            ("Read Only", 1),
            ("Write Only", 2),
            ("No Access", 3),
        ]

        col = ComboMapColumn(
            "Access Method",
            self._access_changed,
            options,
            2,
            visible_callback=self.visible_callback,
        )

        self.view.append_column(col)

        scrolled_window.add(self.view)

        self.cb_list = []

        for val in subsystem_list:
            blk_inst, active = val
            title = blk_inst.name
            top = self.model.append(None, row=(active, title, "", None, None))
            blk = project.blocks[blk_inst.blkid]
            for item in blk.regsets.values():
                access = project.get_access(map_name, blk_inst.name, item.name)
                self.model.append(
                    top,
                    row=(
                        True,
                        item.name,
                        options[access][0],
                        item,
                        blk_inst.name,
                    ),
                )

        self.map_name = map_name

        response = dialog.run()

        if response == Gtk.ResponseType.REJECT:
            self.cb_list = None
        else:
            self.cb_list = [row[1] for row in self.model if row[0]]
        dialog.destroy()

    def visible_callback(self, _column, cell, model, *obj):
        """Determines if the cell is visible"""

        node = obj[0]
        cell.set_property("visible", len(model.get_path(node)) != 1)

    def visible_callback2(self, _column, cell, model, *obj):
        """Determines if the cell is visible"""

        node = obj[0]
        cell.set_property("visible", len(model.get_path(node)) == 1)

    def _enable_changed(self, _cell, path, _source):
        """Called when enable changed"""

        self.model[path][0] = not self.model[path][0]
        self.callback()

    def _access_changed(self, obj, path, node, val):
        """Called when the access changed"""

        mdl = obj.get_property("model")
        val = mdl.get_value(node, 0)
        val_int = mdl.get_value(node, 1)
        self.model[path][2] = val

        self.project.set_access(
            self.map_name, self.model[path][-1], self.model[path][1], val_int
        )
        self.callback()

    def get_list(self):
        """Return the callback list"""

        return self.cb_list
