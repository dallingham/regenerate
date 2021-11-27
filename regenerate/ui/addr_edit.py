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

from typing import List, Tuple, Callable, Optional

from gi.repository import Gtk
from regenerate.db import BlockInst, RegProject, AddressMap
from regenerate.ui.columns import ToggleColumn, EditableColumn, ComboMapColumn
from regenerate.ui.base_window import BaseWindow


class AddrMapEdit(BaseWindow):
    """
    Creates a dialog box allowing the selection of blocks
    for an address map.
    """

    def __init__(
        self,
        addr_map: AddressMap,
        blk_inst_list: List[Tuple[BlockInst, bool]],
        project: RegProject,
        parent: Gtk.Window,
        callback: Callable,
    ):
        # pylint: disable=E1133

        super().__init__()
        self.project = project
        self.callback = callback
        self.cb_list: Optional[List[str]] = None
        self.map_id = addr_map.uuid
        self.map_name = addr_map.name
        self.options = [
            ("Full Access", 0),
            ("Read Only", 1),
            ("Write Only", 2),
            ("No Access", 3),
        ]

        dialog = self.build_dialog(parent)
        self.populate(blk_inst_list)

        response = dialog.run()

        if response != Gtk.ResponseType.REJECT:
            self.cb_list = [row[4].uuid for row in self.model if row[0]]

        dialog.destroy()

    def build_dialog(self, parent: Gtk.Window):
        "Builds the dialog window"

        label = Gtk.Label(
            f'Select blk_insts for the "{self.map_name}" address map'
        )
        label.set_padding(6, 6)
        label.show()

        dialog = Gtk.Dialog(
            "Address Map Block Selection",
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

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )
        scrolled_window.show()
        box.pack_end(scrolled_window, True, True, 12)

        self.view = Gtk.TreeView()
        self.model = Gtk.TreeStore(bool, str, str, object, object)
        self.view.set_model(self.model)

        self.view.show()
        col = ToggleColumn(
            "Enabled",
            self._enable_changed,
            0,
            visible_callback=_enable_visible_callback,
        )

        self.view.append_column(col)

        col = EditableColumn("Block Instance", None, 1)
        col.set_min_width(200)
        self.view.append_column(col)

        col = ComboMapColumn(
            "Access Method",
            self._access_changed,
            self.options,
            2,
            visible_callback=_access_visible_callback,
        )

        self.view.append_column(col)

        scrolled_window.add(self.view)
        return dialog

    def populate(self, blk_inst_list: List[Tuple[BlockInst, bool]]):
        "Populate the model with the block instance information"

        for val in blk_inst_list:
            blk_inst, active = val
            title = blk_inst.name
            top = self.model.append(
                None, row=(active, title, "", None, blk_inst)
            )
            blk = self.project.blocks[blk_inst.blkid]
            for item in blk.regset_insts:
                access = self.project.get_access(
                    self.map_id, blk_inst.uuid, item.uuid
                )
                self.model.append(
                    top,
                    row=(
                        True,
                        item.name,
                        self.options[access][0],
                        item,
                        blk_inst,
                    ),
                )

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

        blkinst = self.model[path][-1]
        reginst = self.model[path][-2]
        self.project.set_access(
            self.map_id, blkinst.uuid, reginst.uuid, val_int
        )
        self.callback()

    def get_list(self) -> Optional[List[str]]:
        """Return the callback list"""

        return self.cb_list


def _access_visible_callback(
    _column: ComboMapColumn,
    cell: Gtk.CellRendererCombo,
    model: Gtk.TreeStore,
    node: Gtk.TreeIter,
    _data,
):
    """Determines if the cell is visible"""

    cell.set_property("visible", len(model.get_path(node)) != 1)


def _enable_visible_callback(
    _column: ComboMapColumn,
    cell: Gtk.CellRendererCombo,
    model: Gtk.TreeStore,
    node: Gtk.TreeIter,
    _data,
):
    """Determines if the cell is visible"""

    cell.set_property("visible", len(model.get_path(node)) == 1)
