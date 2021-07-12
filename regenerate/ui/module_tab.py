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

from gi.repository import Gtk, Gdk
from typing import Callable, List

from regenerate.ui.utils import clean_format_if_needed
from regenerate.ui.preview_editor import PreviewEditor
from .entry import (
    EntryWidth,
    EntryBool,
    EntryText,
    EntryWord,
    EntryInt,
)
from .textview import RstEditor
from .spell import Spell


class ModuleDoc:
    """
    Handles the Register description. Sets the font to a monospace font,
    sets up the changed handler, sets up the spell checker, and makes
    the link to the preview editor.

    Requires a callback functions from the main window to mark the
    the system as modified.
    """

    def __init__(self, text_view, web_view, db_name, modified, use_reg=True):

        editor = RstEditor()
        editor.show()
        text_view.add(editor)
        Spell(editor)

        self.buf = editor.get_buffer()
        self.buf.connect("changed", self.on_changed)

        self.preview = PreviewEditor(self.buf, web_view, use_reg)
        self.db_name = db_name
        self.dbase = None
        self.callback = modified

    def change_db(self, dbase):
        """Change the database so the preview window can resolve references"""

        self.dbase = dbase
        if self.dbase:
            self.buf.set_text(getattr(self.dbase, self.db_name))
        self.preview.set_dbase(self.dbase)

    def on_changed(self, _obj):
        """A change to the text occurred"""

        if self.dbase:
            new_text = self.buf.get_text(
                self.buf.get_start_iter(), self.buf.get_end_iter(), False
            )
            setattr(self.dbase, self.db_name, new_text)
            self.callback()

    def on_key_press_event(self, obj, event):
        """Look for the F12 key"""

        if event.keyval == Gdk.KEY_F12:
            if clean_format_if_needed(obj):
                self.callback()
            return True
        return False


class ModuleTabs:
    def __init__(self, find_obj: Callable, modified: Callable):

        port_list = [
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
            find_obj("scroll_text"),
            find_obj("scroll_webkit"),
            "overview_text",
            self.after_modified,
        )

        self.dbase = None
        self.set_modified = modified
        self.icon = find_obj("mod_def_warn")

    def change_db(self, dbase) -> None:
        self.dbase = dbase
        if dbase:
            for obj in self.port_object_list:
                obj.change_db(dbase.ports)
            for obj in self.top_object_list:
                obj.change_db(dbase)
            self.preview.change_db(dbase)
        else:
            for obj in self.port_object_list:
                obj.change_db(None)
            for obj in self.top_object_list:
                obj.change_db(None)
            self.preview.change_db(None)

    def after_modified(self) -> None:

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
