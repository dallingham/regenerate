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

from gi.repository import Gdk, Gtk, GtkSource

from regenerate.db import RegisterDb, RegProject

from .entry import (
    EntryWidth,
    EntryBool,
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
        self.dbase: Optional[RegisterDb] = None
        self.changing = False

    def change_db(self, dbase: RegisterDb, _project: Optional[RegProject]):
        self.dbase = dbase

        self.changing = True
        self.remove_pages()
        if dbase:
            for page in dbase.doc_pages.get_page_names():
                text = dbase.doc_pages.get_page(page)
                if text is not None:
                    self.add_page(page, text)
        self.changing = False

    def remove_page_from_doc(self, title: str):
        if self.dbase is not None:
            self.dbase.doc_pages.remove_page(title)

    def update_page_from_doc(self, title: str, text: str, tags: List[str]):
        if not self.changing and self.dbase is not None:
            self.dbase.doc_pages.update_page(title, text, tags)


class ModuleTabs:
    "Manages the data on the Module/Regset tabs"

    def __init__(self, find_obj: Callable, modified: Callable):

        port_list = [
            (
                "interface_name",
                "interface_name",
                EntryWord,
                "Missing interface name",
            ),
            ("modport", "modport_name", EntryWord, "Missing modport name"),
            ("clock_signal", "clock_name", EntryWord, "Missing clock name"),
            ("reset_signal", "reset_name", EntryWord, "Missing reset name"),
            ("reset_level", "reset_active_level", EntryBool, None),
            ("byte_en_level", "byte_strobe_active_level", EntryBool, None),
            ("data_width", "data_bus_width", EntryWidth, None),
            (
                "write_data_bus",
                "write_data_name",
                EntryWord,
                "Missing write data bus name",
            ),
            (
                "read_data_bus",
                "read_data_name",
                EntryWord,
                "Missing read data bus name",
            ),
            (
                "byte_en_signal",
                "byte_strobe_name",
                EntryWord,
                "Missing byte enable name",
            ),
            (
                "write_strobe",
                "write_strobe_name",
                EntryWord,
                "Missing write strobe name",
            ),
            (
                "ack",
                "acknowledge_name",
                EntryWord,
                "Missing acknowledge signal name",
            ),
            (
                "read_strobe",
                "read_strobe_name",
                EntryWord,
                "Missing read strobe name",
            ),
            (
                "address_bus",
                "address_bus_name",
                EntryWord,
                "Missing address bus name",
            ),
            (
                "address_width",
                "address_bus_width",
                EntryInt,
                "Missing address bus width",
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
            ("internal_only", "internal_only", EntryBool, None),
            ("coverage", "coverage", EntryBool, None),
            ("interface", "use_interface", EntryBool, None),
        ]

        self.port_object_list = []
        self.top_object_list = []

        for (widget_name, db_name, class_type, placeholder) in port_list:
            if placeholder is not None:
                self.port_object_list.append(
                    class_type(
                        find_obj(widget_name),
                        db_name,
                        self.after_modified,
                        placeholder=placeholder,
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
                self.top_object_list.append(obj)
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

        self.dbase = None
        self.set_modified = modified
        self.icon = find_obj("mod_def_warn")

    def change_db(self, dbase, project) -> None:
        "Changes the register set to a new register set"

        self.dbase = dbase
        if dbase:
            for obj in self.port_object_list:
                obj.change_db(dbase.ports)
            for obj in self.top_object_list:
                obj.change_db(dbase)
            self.preview.change_db(dbase, project)
        else:
            for obj in self.port_object_list:
                obj.change_db(None)
            for obj in self.top_object_list:
                obj.change_db(None)

    def after_modified(self) -> None:
        "Called after modification to set visible properties"

        warn = False
        msgs: List[str] = []

        if self.dbase is not None:
            if self.dbase.descriptive_title == "":
                warn = True
                msgs.append("No title was provided for the register set.")
            if self.dbase.name == "":
                warn = True
                msgs.append("No register set name was provided.")
            self.icon.set_property("visible", warn)
            self.icon.set_tooltip_text("\n".join(msgs))
            self.set_modified()
