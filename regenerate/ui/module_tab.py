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
Handle the module tab
"""

from typing import Callable, List, Optional

from gi.repository import Gtk

from regenerate.db import RegisterSet, RegProject, LOGGER

from .entry import (
    EntryWidth,
    EntryRadio,
    EntrySwitch,
    EntryText,
    EntryWord,
    EntryInt,
)
from .base_doc import BaseDoc


class ModuleDoc(BaseDoc):
    "Documentation editor for the Block documentation"

    def __init__(
        self,
        notebook: Gtk.Notebook,
        modified: Callable,
    ):
        super().__init__(
            notebook,
            modified,
        )
        self.regset: Optional[RegisterSet] = None
        self.changing = False

    def change_db(self, regset: RegisterSet, _project: Optional[RegProject]):
        "Changes the register set associated with the object"
        self.regset = regset

        self.changing = True
        self.remove_pages()
        if regset:
            for page in regset.doc_pages.get_page_names():
                text = regset.doc_pages.get_page(page)
                if text is not None:
                    self.add_page(page, text)
        self.changing = False

    def remove_page_from_doc(self, title: str):
        if self.regset is not None:
            self.regset.doc_pages.remove_page(title)

    def update_page_from_doc(self, title: str, text: str, tags: List[str]):
        if not self.changing and self.regset is not None:
            self.regset.doc_pages.update_page(title, text, tags)


class ModuleTabs:
    "Manages the data on the Module/Regset tabs"

    def __init__(self, find_obj: Callable, modified: Callable):

        port_list = [
            (
                "interface_name",
                "interface_name",
                EntryWord,
                "Missing interface name",
                None,
            ),
            (
                "addr_width",
                "address_bus_width",
                EntryInt,
                "Missing address bus width",
                None,
            ),
            (
                "modport",
                "modport_name",
                EntryWord,
                "Missing modport name",
                None,
            ),
            (
                "imodport",
                "imodport_name",
                EntryWord,
                "Missing modport name",
                None,
            ),
            (
                ("reset_low", "reset_high"),
                "reset_active_level",
                EntryRadio,
                None,
                None,
            ),
            ("sync_reset", "sync_reset", EntrySwitch, None, None),
            ("secondary_reset", "secondary_reset", EntrySwitch, None, None),
            (
                "data_width",
                "data_bus_width",
                EntryWidth,
                None,
                self.width_changed,
            ),
        ]

        item_list = [
            ("regset_name", "name", EntryWord, "Missing register set name"),
            (
                "owner",
                "owner",
                EntryText,
                "Missing owner name or email address",
            ),
            (
                "organization",
                "organization",
                EntryText,
                "Missing company/organization name",
            ),
            (
                "title",
                "descriptive_title",
                EntryText,
                "Missing description of the module",
            ),
            ("internal_only", "internal_only", EntrySwitch, None),
            ("coverage", "coverage", EntrySwitch, None),
            ("interface", "use_interface", EntrySwitch, None),
        ]

        self.port_object_list = []
        self.top_object_list = []

        find_obj("interface").connect(
            "notify::active", self.on_sysv_intf_toggled
        )

        for (
            widget_name,
            db_name,
            class_type,
            placeholder,
            callback,
        ) in port_list:
            if placeholder is not None:
                self.port_object_list.append(
                    class_type(
                        find_obj(widget_name),
                        db_name,
                        self.after_modified,
                        placeholder=placeholder,
                    )
                )
            elif isinstance(widget_name, tuple):
                self.port_object_list.append(
                    class_type(
                        (
                            find_obj(widget_name[0]),
                            find_obj(widget_name[1]),
                        ),
                        db_name,
                        self.after_modified,
                    )
                )
            elif callback:
                self.port_object_list.append(
                    class_type(
                        find_obj(widget_name),
                        db_name,
                        callback,
                    )
                )
            else:
                self.port_object_list.append(
                    class_type(
                        find_obj(widget_name),
                        db_name,
                        self.after_modified,
                    )
                )

        for (widget_name, db_name, class_type, placeholder) in item_list:
            if placeholder is not None:
                obj = class_type(
                    find_obj(widget_name),
                    db_name,
                    self.after_modified,
                    placeholder=placeholder,
                )
            else:
                obj = class_type(
                    find_obj(widget_name),
                    db_name,
                    self.after_modified,
                )
            self.top_object_list.append(obj)
        self.preview = ModuleDoc(
            find_obj("regset_doc_notebook"),
            self.after_modified,
        )

        self.regset = None
        self.set_modified = modified
        self.sync_reset = find_obj("sync_reset")
        self.secondary_reset = find_obj("secondary_reset")
        self.icon = find_obj("mod_def_warn")
        self.modport_field = find_obj("modport")
        self.imodport_field = find_obj("imodport")
        self.interface_field = find_obj("interface_name")
        self.modport_label_field = find_obj("modport_label")
        self.imodport_label_field = find_obj("imodport_label")
        self.interface_label_field = find_obj("interface_label")

    def width_changed(self) -> bool:
        "Called when the data bus with is changing"

        if self.regset is None:
            return False
        new_width = self.regset.ports.data_bus_width
        for reg in self.regset.get_all_registers():
            if reg.width > new_width:
                LOGGER.error(
                    "Width cannot be changed - registers exist that are larger than %d bits",
                    reg.width,
                )
                return False
        self.after_modified()
        return True

    def on_sysv_intf_toggled(self, button, _state):
        "Enable/disable fields if the SystemVerilog interface is enabled"

        enable = button.get_active()
        self.modport_field.set_sensitive(enable)
        self.modport_label_field.set_sensitive(enable)
        self.imodport_field.set_sensitive(enable)
        self.imodport_label_field.set_sensitive(enable)
        self.interface_field.set_sensitive(enable)
        self.interface_label_field.set_sensitive(enable)

    def change_db(self, regset, project) -> None:
        "Changes the register set to a new register set"

        self.regset = regset
        if regset:
            for obj in self.port_object_list:
                obj.change_db(regset.ports)
            for obj in self.top_object_list:
                obj.change_db(regset)
            self.preview.change_db(regset, project)
        else:
            for obj in self.port_object_list:
                obj.change_db(None)
            for obj in self.top_object_list:
                obj.change_db(None)

    def after_modified(self) -> None:
        "Called after modification to set visible properties"

        warn = False
        if self.regset is not None:
            msgs: List[str] = []

            if self.regset.descriptive_title == "":
                warn = True
                msgs.append("No title was provided for the register set.")
            if self.regset.name == "":
                warn = True
                msgs.append("No register set name was provided.")
            self.icon.set_property("visible", warn)
            self.icon.set_tooltip_text("\n".join(msgs))
            self.set_modified()
