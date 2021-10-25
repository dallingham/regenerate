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
Top level tabxs
"""

from typing import Callable, Optional
from pathlib import Path
from gi.repository import Gtk

from regenerate.db import BlockInst, RegProject, Block
from regenerate.settings.paths import HELP_PATH
from .instance_list import InstMdl, InstanceList
from .enums import InstCol
from .param_overrides import OverridesList
from .parameter_list import ParameterList


class TopLevelTab:
    "Top level tabs"

    def __init__(
        self,
        find_obj: Callable,
        check_subsystem_addresses: Callable,
        modified: Callable,
    ):
        self.prj: Optional[RegProject] = None
        self.blkinst_model: Optional[InstMdl] = None

        self.top_block_add = find_obj("top_block_add")
        self.block_or_help = find_obj("block_or_help")
        self.block_or_help.set_show_tabs(False)

        self.top_get_started = find_obj("top_get_started")

        help_path = Path(HELP_PATH) / "top_get_started.html"

        try:
            with help_path.open() as ifile:
                self.top_get_started.load_html(ifile.read(), "text/html")
        except IOError:
            pass

        self.blkinst_list = InstanceList(
            find_obj("instances"),
            check_subsystem_addresses,
        )
        self.project_modified = modified
        self.overrides_list = OverridesList(
            find_obj("prj_subparam_list"),
            find_obj("override_add"),
            find_obj("override_remove"),
            self.overrides_modified,
        )
        self.parameter_list = find_obj("prj_param_list")
        self.parameter_list = ParameterList(
            self.parameter_list,
            find_obj("top_param_add"),
            find_obj("top_param_remove"),
            self.param_list_modified,
        )
        self.instance_delete_btn = find_obj("instance_delete_btn")
        self.connect_signals(find_obj)

    def connect_signals(self, find_obj: Callable):
        "Connect the signals to the widgets"
        find_obj("instance_delete_btn").connect(
            "clicked", self.delete_instance_callback
        )

    def update_buttons(self):
        if self.blkinst_list.get_selected_instance()[1]:
            self.instance_delete_btn.set_sensitive(True)
        else:
            self.instance_delete_btn.set_sensitive(False)

    def delete_instance_callback(self, _obj: Gtk.Button) -> None:
        "Delete the selected block instance"
        self.delete_blkinst()

    def param_list_modified(self) -> None:
        "Callback to set the modified flag when the parameter list is modified"
        self.project_modified(True)

    def overrides_modified(self) -> None:
        "Callback to set the modified flag when the overrides have modified"
        self.project_modified(True)

    def update(self) -> None:
        "Update the block instance list"
        self.blkinst_list.update()
        self.build_add_block_menu()
        self.update_buttons()

    def change_project(self, prj: RegProject) -> None:
        "Change the project, updating the displays"

        self.prj = prj
        self.blkinst_model = InstMdl(prj)
        self.blkinst_list.set_model(self.blkinst_model)
        self.blkinst_list.set_project(self.prj)
        self.build_add_block_menu()
        self.overrides_list.set_project(self.prj)
        self.parameter_list.set_db(self.prj)

    def delete_blkinst(self) -> None:
        "Called with the remove button is clicked"

        if self.prj is None or self.blkinst_model is None:
            return

        model, node = self.blkinst_list.get_selected_instance()
        if node:
            grp = model.get_value(node, InstCol.OBJ)
            self.blkinst_model.remove(node)
            self.project_modified(True)
            self.prj.block_insts = [
                blkinst
                for blkinst in self.prj.block_insts
                if blkinst.name != grp.name
            ]

    def build_add_block_menu(self) -> None:
        "Builds the menu used to add a new block"

        if self.prj is None:
            return

        empty = True
        blk_menu = Gtk.Menu()
        for block in self.prj.blocks.values():
            menu_item = Gtk.MenuItem(block.name)
            menu_item.connect("activate", self.menu_selected, block)
            menu_item.show()
            empty = False
            blk_menu.append(menu_item)
            self.top_block_add.set_sensitive(True)

        if empty:
            self.top_block_add.set_sensitive(False)
            self.top_block_add.set_tooltip_markup(
                (
                    "No blocks have been defined. Blocks\n"
                    "can be defined on the <b>Blocks</b> tab\n"
                    "on the left side of the window."
                )
            )
            self.block_or_help.set_current_page(1)
        else:
            self.top_block_add.set_popup(blk_menu)
            self.top_block_add.set_tooltip_text(
                "Select a block to add to the top level"
            )
            self.block_or_help.set_current_page(0)

    def menu_selected(self, _obj: Gtk.MenuItem, block: Block) -> None:
        "Adds the block as a new block instance"

        if self.prj is None or self.blkinst_model is None:
            return

        block_inst = BlockInst()
        block_inst.blkid = block.uuid

        existing_names = set({blk.name for blk in self.prj.block_insts})

        name = block.name
        count = 0
        while name in existing_names:
            name = f"{name}{count}"
            count += 1

        address_set = set({blk.address_base for blk in self.prj.block_insts})
        if address_set:
            max_address = max(address_set) + 0x10000
        else:
            max_address = 0

        block_inst.name = name
        block_inst.address_base = max_address

        self.prj.block_insts.append(block_inst)
        self.blkinst_model.add_instance(block.name, block_inst)
