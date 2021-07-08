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

import string

from gi.repository import GObject, Gtk, Gdk

from regenerate.db import RegProject, LOGGER
from regenerate.ui.spell import Spell
from regenerate.ui.utils import clean_format_if_needed
from regenerate.ui.preview_editor import PreviewEditor
from regenerate.ui.base_doc import BaseDoc
from .textview import RstEditor

class ModuleWidth:
    """Connects a database value to a selector."""

    def __init__(self, widget, db_name, modified):

        self.widget = widget
        self.dbname = db_name
        self.dbase = None
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

    def change_db(self, dbase):
        """Change the database to a new one"""

        self.dbase = dbase
        if dbase:
            self.widget.set_active(
                self.convert_value_to_index(getattr(self.dbase, self.dbname))
            )
        else:
            self.widget.set_active(0)

    def on_change(self, obj):
        """Called on the change event"""

        if self.dbase:
            setattr(self.dbase, self.dbname, 8 << obj.get_active())
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


class ModuleBool:
    """Connects a database value (boolean) to a checkbox."""

    def __init__(self, widget, db_name, modified):

        self.widget = widget
        self.dbname = db_name
        self.dbase = None
        self.modified = modified
        self.widget.connect("toggled", self.on_change)

    def change_db(self, dbase):
        """Change the database"""

        self.dbase = dbase
        if dbase:
            self.widget.set_active(getattr(dbase, self.dbname))
        else:
            self.widget.set_active(0)

    def on_change(self, obj):
        """Called on the change event"""

        if self.dbase:
            setattr(self.dbase, self.dbname, obj.get_active())
            self.modified()


class ModuleText:
    """Connects a database text value to an entry box."""

    def __init__(self, widget, db_name, modified, placeholder=None):

        self.widget = widget
        self.dbname = db_name
        self.dbase = None
        self.modified = modified
        self.widget.connect("changed", self.on_change)
        try:
            if placeholder:
                self.widget.set_placeholder_text(placeholder)
        except AttributeError:
            pass

    def change_db(self, dbase):
        """Called with the database is changed"""

        self.dbase = dbase
        if dbase:
            val = f"{getattr(dbase, self.dbname)}"
            self.widget.set_text(val)
        else:
            self.widget.set_text("")

    def on_change(self, obj):
        """Called on the change event"""

        if self.dbase:
            setattr(self.dbase, self.dbname, obj.get_text())
            self.modified()


class ModuleValid(ModuleText):
    """
    Provides the base for a validating text entry. Connects the validation
    code to the insert-text function.
    """

    def __init__(
        self, widget, db_name, modified, valid_data, placeholder=None
    ):
        super().__init__(widget, db_name, modified, placeholder)
        self.valid_data = valid_data
        self.widget.connect("insert-text", self.on_insert)

    def on_insert(self, entry, text, _length, position):
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


class ModuleWord(ModuleValid):
    """
    Connects a database value to a text entry, but restricts the input
    to a single word (no spaces).
    """

    def __init__(self, widget, db_name, modified, placeholder=None):
        super().__init__(
            widget,
            db_name,
            modified,
            string.ascii_letters + string.digits + "_",
            placeholder=placeholder,
        )


class ModuleInt(ModuleValid):
    """
    Connects a database value to a text entry, but restricts the input
    to a digits.
    """

    def __init__(self, widget, db_name, modified, placeholder=None):
        super().__init__(
            widget, db_name, modified, string.digits, placeholder=placeholder
        )

    def on_change(self, obj):
        """Called on the change event"""

        if self.dbase:
            if obj.get_text():
                int_val = int(obj.get_text())
            else:
                int_val = 0
            setattr(self.dbase, self.dbname, int_val)
            self.modified()

    def change_db(self, dbase):
        """Change the database"""

        self.dbase = dbase
        if dbase:
            val = f"{getattr(dbase, self.dbname)}"
            self.widget.set_text(val)
        else:
            self.widget.set_text("")


class ModuleHex(ModuleValid):
    """
    Connects a database value to a text entry, but restricts the input
    to a digits.
    """

    def __init__(self, widget, db_name, modified, placeholder=None):
        super().__init__(
            widget,
            db_name,
            modified,
            string.hexdigits + "x",
            placeholder=placeholder,
        )

    def on_change(self, obj) -> None:
        """Called on the change event"""

        if self.dbase:
            try:
                text = obj.get_text()
                if text:
                    int_val = int(text, 0)
                else:
                    int_val = 0
                setattr(self.dbase, self.dbname, int_val)
                self.modified()
            except ValueError:
                LOGGER.error("Invalid number (%s). Possible missing 0x", text)

    def change_db(self, dbase):
        """Change the database"""

        self.dbase = dbase
        if dbase:
            val = f"0x{getattr(dbase, self.dbname):08x}"
            self.widget.set_text(val)
        else:
            self.widget.set_text("")


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

    def preview_enable(self):
        """Enables the preview window"""

        self.preview.enable()

    def preview_disable(self):
        """Disables the preview window"""

        self.preview.disable()

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
    def __init__(self, find_obj, modified):

        port_list = [
            ("clock_signal", "clock_name", ModuleWord, "Missing clock name"),
            ("reset_signal", "reset_name", ModuleWord, "Missing reset name"),
            ("reset_level", "reset_active_level", ModuleBool, None),
            ("byte_en_level", "byte_strobe_active_level", ModuleBool, None),
            ("data_width", "data_bus_width", ModuleWidth, None),
            (
                "write_data_bus",
                "write_data_name",
                ModuleWord,
                "Missing write data bus name",
            ),
            (
                "read_data_bus",
                "read_data_name",
                ModuleWord,
                "Missing read data bus name",
            ),
            (
                "byte_en_signal",
                "byte_strobe_name",
                ModuleWord,
                "Missing byte enable name",
            ),
            (
                "write_strobe",
                "write_strobe_name",
                ModuleWord,
                "Missing write strobe name",
            ),
            (
                "ack",
                "acknowledge_name",
                ModuleWord,
                "Missing acknowledge signal name",
            ),
            (
                "read_strobe",
                "read_strobe_name",
                ModuleWord,
                "Missing read strobe name",
            ),
            (
                "address_bus",
                "address_bus_name",
                ModuleWord,
                "Missing address bus name",
            ),
            (
                "address_width",
                "address_bus_width",
                ModuleInt,
                "Missing address bus width",
            ),
        ]

        item_list = [
            ("regset_name", "name", ModuleWord, "Missing register set name"),
            (
                "owner",
                "owner",
                ModuleText,
                "Missing owner name or email address",
            ),
            (
                "organization",
                "organization",
                ModuleText,
                "Missing company/organization name",
            ),
            (
                "title",
                "descriptive_title",
                ModuleText,
                "Missing description of the module",
            ),
            ("internal_only", "internal_only", ModuleBool, None),
            ("coverage", "coverage", ModuleBool, None),
            ("interface", "use_interface", ModuleBool, None),
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

    def change_db(self, dbase):
        self.dbase = dbase
        if dbase:
            for obj in self.port_object_list:
                obj.change_db(dbase.ports)
            for obj in self.top_object_list:
                obj.change_db(dbase)
            self.preview.change_db(dbase)

    def after_modified(self):

        warn = False
        msgs = []

        if self.dbase.descriptive_title == "":
            warn = True
            msgs.append("No title was provided for the register set.")
        if self.dbase.name == "":
            warn = True
            msgs.append("No register set name was provided.")
        self.icon.set_property("visible", warn)
        self.icon.set_tooltip_text("\n".join(msgs))
        self.set_modified()

    def preview_enable(self):
        """Enables the preview window"""
        self.preview.preview_enable()

    def preview_disable(self):
        """Disables the preview window"""
        self.preview.preview_disable()


class ProjectTabs:
    """Handles the project tabs"""

    def __init__(self, builder, modified):

        item_list = [
            ("project_name", "name", ModuleText, "Missing project name"),
            ("short_name", "short_name", ModuleWord, "Missing short name"),
            (
                "company_name",
                "company_name",
                ModuleText,
                "Missing company name",
            ),
        ]

        self.object_list = []

        for (widget_name, db_name, class_type, placeholder) in item_list:
            if placeholder is not None:
                self.object_list.append(
                    class_type(
                        builder.get_object(widget_name),
                        db_name,
                        self.after_modified,
                        placeholder=placeholder,
                    )
                )
            else:
                self.object_list.append(
                    class_type(
                        builder.get_object(widget_name),
                        db_name,
                        self.after_modified,
                    )
                )

        self.preview = ProjectDoc(
            builder.get_object("prj_doc_notebook"),
            self.after_modified,
            builder.get_object("add_top_doc"),
            builder.get_object("del_top_doc"),
        )

        self.dbase = None
        self.set_modified = modified
        self.icon = builder.get_object("mod_def_warn")

    def change_db(self, dbase):
        self.dbase = dbase
        self.preview.set_project(dbase)
        for obj in self.object_list:
            obj.change_db(dbase)

    def after_modified(self):
        self.set_modified()


class ProjectDoc(BaseDoc):
    def __init__(
        self,
        notebook: Gtk.Notebook,
        modified,
        add_btn: Gtk.Button,
        del_btn: Gtk.Button,
    ):
        super().__init__(notebook, modified, add_btn, del_btn)
        self.changing = False

    def set_project(self, project: RegProject):
        """Change the database so the preview window can resolve references"""
        self.changing = True

        self.project = project
        self.remove_pages()

        for page in project.doc_pages.get_page_names():
            self.add_page(page, self.project.doc_pages.get_page(page))

        self.changing = False

    def remove_page_from_doc(self, title):
        if not self.changing:
            self.project.doc_pages.remove_page(title)

    def update_page_from_doc(self, title, text):
        if not self.changing:
            self.project.doc_pages.update_page(title, text)
