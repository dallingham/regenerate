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

import gtk
import gobject
import string


class ModuleWidth(object):
    """Connects a database value to a selector."""

    def __init__(self, widget, db_name, modified):

        self.widget = widget
        self.dbname = db_name
        self.dbase = None
        self.modified = modified
        self.widget.connect('changed', self.on_change)
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
            (64, "64 bits")
        )

        store = gtk.ListStore(str, int)
        for (val, text) in self.options:
            store.append(row=[text, val])

        self.widget.set_model(store)
        cell = gtk.CellRendererText()
        self.widget.pack_start(cell, True)
        self.widget.add_attribute(cell, 'text', 0)

    def change_db(self, dbase):
        self.dbase = dbase
        if dbase:
            self.widget.set_active(
                self.convert_value_to_index(getattr(self.dbase, self.dbname)))
        else:
            self.widget.set_active(0)

    def on_change(self, obj):
        if self.dbase:
            setattr(self.dbase, self.dbname, 8 << obj.get_active())
            self.modified()

    def convert_value_to_index(self, value):
        if value == 8:
            return 0
        elif value == 16:
            return 1
        elif value == 32:
            return 2
        else:
            return 3

    def convert_index_to_value(self, index):
        return self.options[index][0]


class ModuleBool(object):
    """Connects a database value (boolean) to a checkbox."""

    def __init__(self, widget, db_name, modified):

        self.widget = widget
        self.dbname = db_name
        self.dbase = None
        self.modified = modified
        self.widget.connect('toggled', self.on_change)

    def change_db(self, dbase):
        self.dbase = dbase
        if dbase:
            self.widget.set_active(getattr(dbase, self.dbname))
        else:
            self.widget.set_active(0)

    def on_change(self, obj):
        if self.dbase:
            setattr(self.dbase, self.dbname, obj.get_active())
            self.modified()


class ModuleText(object):
    """Connects a database text value to an entry box."""

    def __init__(self, widget, db_name, modified):

        self.widget = widget
        self.dbname = db_name
        self.dbase = None
        self.modified = modified
        self.widget.connect('changed', self.on_change)

    def change_db(self, dbase):
        self.dbase = dbase
        if dbase:
            self.widget.set_text(getattr(dbase, self.dbname))
        else:
            self.widget.set_text("")

    def on_change(self, obj):
        if self.dbase:
            setattr(self.dbase, self.dbname, obj.get_text())
            self.modified()


class ModuleValid(ModuleText):
    """
    Provides the base for a validating text entry. Connects the validation
    code to the insert-text function.
    """

    def __init__(self, widget, db_name, modified, valid_data):
        super(ModuleValid, self).__init__(widget, db_name, modified)
        self.valid_data = valid_data
        self.widget.connect('insert-text', self.on_insert)

    def on_insert(self, entry, text, length, position):
        # Called when the user inserts some text, by typing or pasting.
        position = entry.get_position()

        # Build a new string with allowed characters only.
        result = ''.join([c for c in text if c in self.valid_data])

        if result != '':
            # Insert the new text at cursor (and block the handler to
            # avoid recursion).
            entry.handler_block_by_func(self.on_insert)
            entry.insert_text(result, position)
            entry.handler_unblock_by_func(self.on_insert)

            # Set the new cursor position immediately after the inserted text.
            new_pos = position + len(result)

            # Can't modify the cursor position from within this handler,
            # so we add it to be done at the end of the main loop:
            gobject.idle_add(entry.set_position, new_pos)

        # We handled the signal so stop it from being processed further.
        entry.stop_emission("insert_text")


class ModuleWord(ModuleValid):
    """
    Connects a database value to a text entry, but restricts the input 
    to a single word (no spaces).
    """

    def __init__(self, widget, db_name, modified):
        super(ModuleWord, self).__init__(
            widget,
            db_name,
            modified,
            string.ascii_letters + string.digits + "_"
        )


class ModuleInt(ModuleValid):
    """
    Connects a database value to a text entry, but restricts the input
    to a digits.
    """

    def __init__(self, widget, db_name, modified):
        super(ModuleInt, self).__init__(
            widget,
            db_name,
            modified,
            string.digits
        )

    def on_change(self, obj):
        if self.dbase:
            if obj.get_text():
                int_val = int(obj.get_text())
            else:
                int_val = 0
            setattr(self.dbase, self.dbname, int_val)
            self.modified()

    def change_db(self, dbase):
        self.dbase = dbase
        if dbase:
            self.widget.set_text(str(getattr(dbase, self.dbname)))
        else:
            self.widget.set_text("")


class ModuleTabs(object):

    def __init__(self, builder, modified):

        item_list = [
            ('clock_signal', 'clock_name', ModuleWord),
            ('reset_signal', 'reset_name', ModuleWord),
            ('write_data_bus', "write_data_name", ModuleWord),
            ('read_data_bus', "read_data_name", ModuleWord),
            ('byte_en_signal', "byte_strobe_name", ModuleWord),
            ('write_strobe', "write_strobe_name", ModuleWord),
            ('ack', 'acknowledge_name', ModuleWord),
            ('read_strobe', 'read_strobe_name', ModuleWord),
            ('address_bus', 'address_bus_name', ModuleWord),
            ('address_width', 'address_bus_width', ModuleInt),
            ('module', 'module_name', ModuleWord),
            ('owner', 'owner', ModuleText),
            ('organization', 'organization', ModuleText),
            ('title', 'descriptive_title', ModuleText),
            ('reset_level', 'reset_active_level', ModuleBool),
            ('interface', 'use_interface', ModuleBool),
            ('byte_en_level', 'be_level', ModuleBool),
            ('internal_only', 'internal_only', ModuleBool),
            ('coverage', 'coverage', ModuleBool),
            ('data_width', 'data_bus_width', ModuleWidth),
        ]

        self.object_list = []

        for (widget_name, db_name, class_type) in item_list:
            self.object_list.append(
                class_type(
                    builder.get_object(widget_name),
                    db_name,
                    self.after_modified
                )
            )

        self.dbase = None
        self.set_modified = modified
        self.icon = builder.get_object('mod_def_warn')

    def change_db(self, dbase):
        self.dbase = dbase
        for obj in self.object_list:
            obj.change_db(dbase)

    def after_modified(self):

        warn = False
        msgs = []

        if self.dbase.descriptive_title == "":
            warn = True
            msgs.append("No title was provided for the register set.")
        if self.dbase.module_name == "":
            warn = True
            msgs.append("No module name was provided.")
        self.icon.set_property('visible', warn)
        self.icon.set_tooltip_text("\n".join(msgs))
        self.set_modified()
