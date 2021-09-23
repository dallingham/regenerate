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
Data entry classes.
"""
from typing import Callable, Optional
import string

from gi.repository import GObject, Gtk
from regenerate.db import LOGGER


class EntryWidth:
    """Connects a database value to a selector."""

    def __init__(
        self, widget: Gtk.ComboBox, field_name: str, modified: Callable
    ):

        self.widget = widget
        self.field_name = field_name
        self.data_obj = None
        self.modified = modified
        self.widget.connect("changed", self.on_change)
        self.build_data_width_box()

    def build_data_width_box(self):
        """
        Builds the option menu for the bit width descriptor. Glade no longer
        allows us to set the values in the glade file, but this allows us to
        set a more descriptive text along with a numerical value. We can select
        the active entry, and extract the actual value from the ListStore. The
        first column of the ListStore is displayed, and the second value is
        the numerical value.
        """

        self.options = (
            (8, "8 bits"),
            (16, "16 bits"),
            (32, "32 bits"),
            (64, "64 bits"),
        )

        store = Gtk.ListStore(str, int)
        for (val, text) in self.options:
            store.append(row=[text, val])

        self.widget.set_model(store)
        cell = Gtk.CellRendererText()
        self.widget.pack_start(cell, True)
        self.widget.add_attribute(cell, "text", 0)

    def change_db(self, data_obj):
        """Change the database to a new one"""

        self.data_obj = data_obj
        if data_obj:
            self.widget.set_active(
                self.convert_value_to_index(
                    getattr(self.data_obj, self.field_name)
                )
            )
        else:
            self.widget.set_active(0)

    def on_change(self, obj):
        """Called on the change event"""

        if self.data_obj:
            setattr(self.data_obj, self.field_name, 8 << obj.get_active())
            self.modified()

    def convert_value_to_index(self, value):
        """Convert the bit size to an index"""

        if value == 8:
            return 0
        if value == 16:
            return 1
        if value == 32:
            return 2
        return 3

    def convert_index_to_value(self, index):
        """Converts the index back to a bit size value"""

        return self.options[index][0]


class EntryBool:
    """Connects a database value (boolean) to a checkbox."""

    def __init__(
        self, widget: Gtk.CheckButton, field_name: str, modified: Callable
    ):
        self.widget = widget
        self.field_name = field_name
        self.data_obj = None
        self.modified = modified
        self.widget.connect("toggled", self.on_change)

    def change_db(self, data_obj):
        """Change the database"""

        self.data_obj = data_obj
        if data_obj:
            self.widget.set_active(getattr(data_obj, self.field_name))
        else:
            self.widget.set_active(0)

    def on_change(self, obj):
        """Called on the change event"""

        if self.data_obj:
            setattr(self.data_obj, self.field_name, obj.get_active())
            self.modified()


class EntrySwitch:
    """Connects a database value (boolean) to a checkbox."""

    def __init__(
        self, widget: Gtk.Switch, field_name: str, modified: Callable
    ):
        self.widget = widget
        self.field_name = field_name
        self.data_obj = None
        self.modified = modified
        self.widget.connect("notify::active", self.on_change)

    def change_db(self, data_obj):
        """Change the database"""

        self.data_obj = data_obj
        if data_obj:
            self.widget.set_state(getattr(data_obj, self.field_name))
        else:
            self.widget.set_state(0)

    def on_change(self, obj, _active):
        """Called on the change event"""
        if self.data_obj:
            setattr(self.data_obj, self.field_name, obj.get_active())
            self.modified()


class EntryText:
    """Connects a database text value to an entry box."""

    def __init__(
        self,
        widget: Gtk.Entry,
        field_name: str,
        modified: Callable,
        placeholder: Optional[str] = None,
    ):
        self.widget = widget
        self.field_name = field_name
        self.data_obj = None
        self.modified = modified
        self.widget.connect("changed", self.on_change)
        try:
            if placeholder:
                self.widget.set_placeholder_text(placeholder)
        except AttributeError:
            pass

    def change_db(self, data_obj):
        """Called with the database is changed"""

        self.data_obj = data_obj
        if data_obj:
            val = f"{getattr(data_obj, self.field_name)}"
            self.widget.set_text(val)
        else:
            self.widget.set_text("")

    def on_change(self, obj):
        """Called on the change event"""

        if self.data_obj:
            setattr(self.data_obj, self.field_name, obj.get_text())
            self.modified()


class EntryValid(EntryText):
    """
    Provides the base for a validating text entry. Connects the validation
    code to the insert-text function.
    """

    def __init__(
        self,
        widget: Gtk.Entry,
        field_name: str,
        modified: Callable,
        valid_data: str,
        placeholder: Optional[str] = None,
    ):
        super().__init__(widget, field_name, modified, placeholder)
        self.valid_data = valid_data
        self.widget.connect("insert-text", self.on_insert)

    def on_insert(
        self, entry: Gtk.Entry, text: str, _length: int, position: int
    ):
        """Called when the user inserts some text, by typing or pasting."""

        position = entry.get_position()

        # Build a new string with allowed characters only.
        result = "".join([c for c in text if c in self.valid_data])

        if result != "":
            # Insert the new text at cursor (and block the handler to
            # avoid recursion).
            entry.handler_block_by_func(self.on_insert)
            entry.insert_text(result, position)
            entry.handler_unblock_by_func(self.on_insert)

            # Set the new cursor position immediately after the inserted text.
            new_pos = position + len(result)

            # Can't modify the cursor position from within this handler,
            # so we add it to be done at the end of the main loop:
            GObject.idle_add(entry.set_position, new_pos)

        # We handled the signal so stop it from being processed further.
        entry.stop_emission("insert_text")


class EntryWord(EntryValid):
    """
    Connects a database value to a text entry, but restricts the input
    to a single word (no spaces).
    """

    def __init__(
        self,
        widget: Gtk.Entry,
        field_name: str,
        modified: Callable,
        placeholder=Optional[str],
    ):
        super().__init__(
            widget,
            field_name,
            modified,
            string.ascii_letters + string.digits + "_",
            placeholder=placeholder,
        )


class EntryInt(EntryValid):
    """
    Connects a database value to a text entry, but restricts the input
    to a digits.
    """

    def __init__(
        self,
        widget: Gtk.Entry,
        field_name: str,
        modified: Callable,
        placeholder: Optional[str],
    ):
        super().__init__(
            widget,
            field_name,
            modified,
            string.digits,
            placeholder=placeholder,
        )

    def on_change(self, obj: Gtk.Entry):
        """Called on the change event"""

        if self.data_obj:
            if obj.get_text():
                int_val = int(obj.get_text())
            else:
                int_val = 0
            setattr(self.data_obj, self.field_name, int_val)
            self.modified()

    def change_db(self, data_obj):
        """Change the database"""

        self.data_obj = data_obj
        if data_obj:
            self.widget.set_text(f"{getattr(data_obj, self.field_name)}")
        else:
            self.widget.set_text("")


class EntryHex(EntryValid):
    """
    Connects a database value to a text entry, but restricts the input
    to a digits.
    """

    def __init__(
        self,
        widget: Gtk.Entry,
        field_name: str,
        modified: Callable,
        placeholder: Optional[str] = None,
    ):
        super().__init__(
            widget,
            field_name,
            modified,
            string.hexdigits + "x",
            placeholder=placeholder,
        )

    def on_change(self, obj: Gtk.Entry) -> None:
        """Called on the change event"""

        if self.data_obj:
            try:
                text = obj.get_text()
                if text:
                    int_val = int(text, 0)
                else:
                    int_val = 0
                setattr(self.data_obj, self.field_name, int_val)
                self.modified()
            except ValueError:
                LOGGER.error("Invalid number (%s). Possible missing 0x", text)

    def change_db(self, data_obj):
        """Change the database"""

        self.data_obj = data_obj
        if data_obj:
            val = f"0x{getattr(data_obj, self.field_name):08x}"
            self.widget.set_text(val)
        else:
            self.widget.set_text("")
