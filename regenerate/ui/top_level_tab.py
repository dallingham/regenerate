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

from gi.repository import Gtk, Gdk, GObject

from regenerate.db.block_inst import BlockInst
from regenerate.ui.instance_list import InstMdl, InstanceList
from regenerate.ui.enums import InstCol


class TopLevelTab:
    def __init__(self, find_obj, check_subsystem_addresses, modified):

        self.top_block_add = find_obj("top_block_add")

        self.blkinst_list = InstanceList(
            find_obj("instances"),
            check_subsystem_addresses,
        )
        self.prj = None
        self.blkinst_model = None
        self.project_modified = modified

    def change_project(self, prj):
        self.prj = prj
        self.blkinst_model = InstMdl(prj)
        self.blkinst_list.set_model(self.blkinst_model)
        self.blkinst_list.set_project(self.prj)
        self.build_add_block_menu()

    def delete_blkinst(self):
        """
        Called with the remove button is clicked
        """
        model, node = self.blkinst_list.get_selected_instance()
        if node:
            grp = model.get_value(node, InstCol.OBJ)
            self.blkinst_model.remove(node)
            self.project_modified(True)
            print(self.prj.block_insts)
            self.prj.block_insts = [
                blkinst
                for blkinst in self.prj.block_insts
                if blkinst.inst_name != grp.inst_name
            ]
            print(self.prj.block_insts)
            # self.prj.remove_group_from_grouping_list(grp)

    def build_add_block_menu(self):
        self.blk_menu = Gtk.Menu()
        for block in self.prj.blocks:
            menu_item = Gtk.MenuItem(block)
            menu_item.connect("activate", self.menu_selected, block)
            menu_item.show()
            self.blk_menu.append(menu_item)
            self.top_block_add.set_popup(self.blk_menu)

    def menu_selected(self, _obj, block):
        block_inst = BlockInst()
        block_inst.block = block

        existing_names = set({blk.inst_name for blk in self.prj.block_insts})

        name = block
        count = 0
        while name in existing_names:
            name = f"{block}{count}"
            count += 1

        address_set = set({blk.address_base for blk in self.prj.block_insts})
        max_address = max(address_set) + 0x10000

        block_inst.inst_name = name
        block_inst.address_base = max_address

        self.prj.block_insts.append(block_inst)
        self.blkinst_model.add_instance(block_inst)
