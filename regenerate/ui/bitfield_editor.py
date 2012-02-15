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

import gtk
import re
import pango

from regenerate.db import BitField, TYPES
from regenerate.settings.paths import GLADE_BIT
from error_dialogs import ErrorMsg, Question

VALID_SIGNAL = re.compile("^[A-Za-z][A-Za-z0-9_]*$")

TYPE2STR = {}
for i in TYPES:
    TYPE2STR[i[0]] = i[5]

TYPE_ENB = {}
for i in TYPES:
    TYPE_ENB[i[0]] = (i[2], i[3])

class BitFieldEditor(object):
    """
    Bit field editing class.
    """

    def __init__(self, register, bit_field, modified):
        self.__modified = modified
        self.__register = register
        self.__bit_field = bit_field
        self.__builder = gtk.Builder()
        self.__builder.add_from_file(GLADE_BIT)
        self.__top_window = self.__builder.get_object("editfield")
        self.__bits = self.__builder.get_object("bits")
        self.__control_obj = self.__builder.get_object('control')
        self.__name_obj = self.__builder.get_object("field_name")
        self.__register_obj = self.__builder.get_object("register_name")
        self.__output_obj = self.__builder.get_object("output")
        self.__type_obj = self.__builder.get_object('type')
        self.__input_obj = self.__builder.get_object("input")
        self.__reset_obj = self.__builder.get_object("reset_value")
        self.__static_obj = self.__builder.get_object('static')
        self.__text_buffer = self.__builder.get_object("descr").get_buffer()
        self.__value_tree_obj = self.__builder.get_object('values')
        self.__output_enable_obj = self.__builder.get_object("outen")
        self.__side_effect_obj = self.__builder.get_object("side_effect")
        self.__col = None
        self.__top_window.set_title(
            "Edit Bit Field - [%02x] %s" % (register.address,
                                            register.register_name))

        self.__input_obj.set_sensitive(TYPE_ENB[bit_field.field_type][0])
        self.__control_obj.set_sensitive(TYPE_ENB[bit_field.field_type][1])

        pango_font = pango.FontDescription("monospace")
        self.__builder.get_object("descr").modify_font(pango_font)

        self.build_values_list()

        self.__list_model = gtk.ListStore(str, str, str)
        self.__model_selection = self.__value_tree_obj.get_selection()
        self.__value_tree_obj.set_model(self.__list_model)

        self.__used_tokens = set()
        for value in self.__bit_field.values:
            self.__used_tokens.add(value[1])
            self.__list_model.append(row=value)

        self.__initialize_from_data(bit_field)
        self.__output_obj.set_sensitive(self.__output_enable_obj.get_active())
        self.__check_data()

        self.__text_buffer.connect('changed', self.__description_changed)
        self.__builder.connect_signals(self)
        self.__top_window.show_all()

    def __initialize_from_data(self, bit_field):
        """
        Initializes the dialog's data fields from the object
        """
        self.__register_obj.set_text("<b>%s</b>" %
                                     self.__register.register_name)
        self.__register_obj.set_use_markup(True)
        self.__name_obj.set_text(bit_field.field_name)
        start = self.__bit_field.start_position
        stop = self.__bit_field.stop_position
        if start == stop:
            self.__bits.set_text(str(start))
        else:
            self.__bits.set_text("%d:%d" % (stop, start))
        self.__type_obj.set_text(TYPE2STR[bit_field.field_type])

        if bit_field.reset_type == BitField.RESET_NUMERIC:
            self.__reset_obj.set_text("%x" % bit_field.reset_value)
        else:
            self.__reset_obj.set_text(bit_field.reset_parameter)
        self.__output_obj.set_text(bit_field.output_signal)
        self.__input_obj.set_text(bit_field.input_signal)

        self.__static_obj.set_active(bit_field.output_is_static)
        self.__side_effect_obj.set_active(bit_field.output_has_side_effect)
        self.__text_buffer.set_text(bit_field.description)
        self.__output_enable_obj.set_active(bit_field.use_output_enable)
        self.__control_obj.set_text(self.__bit_field.control_signal)

    def on_output_changed(self, obj):
        self.__bit_field.output_signal = obj.get_text()
        self.__check_data()
        self.__modified()

    def on_input_changed(self, obj):
        self.__bit_field.input_signal = obj.get_text()
        self.__check_data()
        self.__modified()

    def on_control_changed(self, obj):
        self.__bit_field.control_signal = obj.get_text()
        self.__check_data()
        self.__modified()

    def build_values_list(self):
        """
        Builds the columns associated with the list view
        """
        render = gtk.CellRendererText()
        render.set_property('editable', True)
        render.connect('edited', self.__change_val)
        column = gtk.TreeViewColumn('Value', render, text=0)
        column.set_min_width(50)
        self.__value_tree_obj.append_column(column)
        self.__col = column

        render = gtk.CellRendererText()
        render.set_property('editable', True)
        render.connect('edited', self.__change_text)
        column = gtk.TreeViewColumn('Token', render, text=1)
        column.set_min_width(100)
        self.__value_tree_obj.append_column(column)

        render = gtk.CellRendererText()
        render.set_property('editable', True)
        render.connect('edited', self.__change_description)
        column = gtk.TreeViewColumn('Description', render, text=2)
        self.__value_tree_obj.append_column(column)

    def on_add_clicked(self, obj):
        """
        Called with the add button is clicked. Search the existing values
        in the list, finding the next highest value to use as the default.
        """

        start = self.__bit_field.start_position
        stop = self.__bit_field.stop_position
        last = len(self.__list_model)
        max_values = 2 ** (stop - start + 1)

        if last >= max_values:
            ErrorMsg("Maximum number of values reached",
                     "The width of the field only allows for %d values" % last)
            return

        try:
            largest = max([int(val[0], 16) for val in self.__list_model
                           if val[0] != ""])
        except ValueError:
            largest = -1

        last -= 1
        if (last == -1 or self.__list_model[last][0] or
            self.__list_model[last][1] or self.__list_model[last][2]):
            if largest >= max_values:
                new_val = ""
            else:
                new_val = "%x" % (largest + 1,)
            node = self.__list_model.append(row=(new_val, '', ''))
            path = self.__list_model.get_path(node)
        else:
            path = (last, )

        self.__value_tree_obj.set_cursor(path, focus_column=self.__col,
                                         start_editing=True)
        self.__modified()

    def  on_remove_clicked(self, obj):  # IGNORE:W0613 - obj is unused
        """
        Called with the remove button is clicked
        """
        self.__list_model.remove(self.__model_selection.get_selected()[1])
        self.__update_values()
        self.__modified()

    def __change_val(self, text, path, new_text): # IGNORE:W0613
        """
        Called with the value has changed value field. Checks to make sure that
        value is a valid hex value, and within the correct range.
        """
        new_text = new_text.strip()

        start = self.__bit_field.start_position
        stop = self.__bit_field.stop_position
        maxval = (2 ** (stop - start + 1)) - 1

        try:
            if new_text == "" or int(new_text, 16) > maxval:
                return
        except ValueError:
            return

        node = self.__list_model.get_iter(path)
        self.__list_model.set_value(node, 0, new_text)
        self.__update_values()
        self.__modified()

    def on_side_effect_toggled(self, obj):
        self.__bit_field.side_effect = obj.get_active()
        self.__modified()

    def __update_values(self):
        new_list = []
        for row in self.__list_model:
            new_list.append((row[0], row[1], row[2]))
        self.__bit_field.values = new_list

    def __change_text(self, text, path, new_text):
        """
        Updates the data model when the text value is changed in the model.
        """
        if new_text in self.__used_tokens:
            ErrorMsg("Duplicate token",
                     'The token "%s" has already been used' % new_text)
        else:
            node = self.__list_model.get_iter(path)
            old_text = self.__list_model.get_value(node, 1)
            self.__list_model.set_value(node, 1, new_text)

            if old_text and old_text in self.__used_tokens:
                self.__used_tokens.remove(old_text)
            if new_text:
                self.__used_tokens.add(new_text)
            self.__update_values()
            self.__modified()

    def __change_description(self, text, path, new_text):
        """
        Updates the data model when the text value is changed in the model.
        """
        node = self.__list_model.get_iter(path)
        try:
            new_text.decode("ascii")
        except:
            ErrorMsg("Invalid ASCII characters detected",
                     "Look for strange punctuations, like dashs and quotes that "
                     "look valid, but are not actual ascii characters.")
        self.__list_model.set_value(node, 2, new_text)
        self.__update_values()
        self.__modified()

    def on_output_enable_toggled(self, obj):
        """
        Enables the output field based on the output enable field
        """
        self.__bit_field.use_output_enable = self.__output_enable_obj.get_active()
        self.__output_obj.set_sensitive(obj.get_active())
        self.__check_data()
        self.__modified()

    def __set_bits_activate(self, obj):
        """
        Called when the set bits mode has been activated, changing the
        label appropriately.
        """
        self.__control_obj.set_sensitive(False)
        self.__input_obj.set_sensitive(True)
        self.__builder.get_object('input0_label').set_text('Input signal')

    def __clear_bits_activate(self, obj):
        """
        Called when the clear bits mode has been activated, changing the
        label appropriately.
        """
        self.__control_obj.set_sensitive(False)
        self.__input_obj.set_sensitive(True)
        self.__builder.get_object('input0_label').set_text('Input signal')

    def __parallel_load_activate(self, obj):
        """
        Called when the parallel load mode has been activated, changing the
        label appropriately.
        """
        self.__control_obj.set_sensitive(True)
        self.__input_obj.set_sensitive(True)
        self.__builder.get_object('input0_label').set_text('Load data')

    def __ctrl_signal_activate(self, obj):
        """
        Called when the control signal has been activated, changing the
        label appropriately.
        """
        self.__control_obj.set_sensitive(False)
        self.__input_obj.set_sensitive(False)
        self.__builder.get_object('input0_label').set_text('Input signal')

    def on_descr_key_press_event(self, obj, event):
        """
        Called on a double click event. If we detect a double click with
        the first button, we call the edit_register method.
        """
        if event.keyval == gtk.keysyms.F10:
            bounds = self.__text_buffer.get_selection_bounds()
            if bounds:
                old_text = self.__text_buffer.get_text(bounds[0], bounds[1])
                new_text = " ".join(old_text.replace("\n", " ").split())
                self.__text_buffer.delete(bounds[0], bounds[1])
                self.__text_buffer.insert(bounds[0], new_text)
                self.__modified()
            return True
        return False

    def on_close_clicked(self, obj):
        """
        Saves the data from the interface to the internal BitField structure
        """
        self.__top_window.destroy()

    def __description_changed(self, obj):
        self.__bit_field.description = self.__text_buffer.get_text(
            self.__text_buffer.get_start_iter(),
            self.__text_buffer.get_end_iter(), False)
        self.__modified()

    def __check_data(self):
        """
        Checks the input signal validity
        """
        input_error = False
        output_error = False
        control_error = False

        input_sig = self.__input_obj.get_text()
        out_enable = self.__output_obj.get_text()
        control_sig = self.__control_obj.get_text()

        if control_error == False:
            clear_error(self.__control_obj)
        if input_error == False:
            clear_error(self.__input_obj)
        if output_error == False:
            clear_error(self.__output_obj)


def set_error(obj, message):
    obj.set_property('secondary-icon-stock', gtk.STOCK_DIALOG_ERROR)
    obj.set_property('secondary-icon-tooltip-text', message)


def clear_error(obj):
    obj.set_property('secondary-icon-stock', None)
    obj.set_property('secondary-icon-tooltip-text', '')
