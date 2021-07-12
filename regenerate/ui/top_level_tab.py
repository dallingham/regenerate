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
Top level tags
"""

from typing import Callable, Optional

from gi.repository import Gtk

from regenerate.db import BlockInst, RegProject, Block
from regenerate.ui.instance_list import InstMdl, InstanceList
from regenerate.ui.enums import InstCol
from regenerate.ui.param_overrides import OverridesList
from regenerate.ui.parameter_list import ParameterList


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

    def param_list_modified(self) -> None:
        "Callback to set the modified flag when the parameter list is modified"
        self.project_modified(True)

    def overrides_modified(self) -> None:
        "Callback to set the modified flag when the overrides have modified"
        self.project_modified(True)

    def update(self) -> None:
        "Update the block instance list"
        self.blkinst_list.update()

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

        blk_menu = Gtk.Menu()
        for block in self.prj.blocks.values():
            menu_item = Gtk.MenuItem(block.name)
            menu_item.connect("activate", self.menu_selected, block)
            menu_item.show()
            blk_menu.append(menu_item)
        self.top_block_add.set_popup(blk_menu)

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
