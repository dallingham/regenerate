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
import os
from spell import Spell

from regenerate.db import (BitField, TYPES, TYPE_TO_ID,
                           TYPE_TO_DESCR, TYPE_TO_ENABLE)
from regenerate.settings.paths import GLADE_BIT, INSTALL_PATH
from error_dialogs import ErrorMsg
from regenerate.writers.verilog_reg_def import REG
from help_window import HelpWindow

try:
    from pygments.lexers import VerilogLexer
    from pygments.styles import get_style_by_name
    USE_HIGHLIGHT = True
    STYLE = get_style_by_name('emacs')
except ImportError:
    USE_HIGHLIGHT = False

VALID_SIGNAL = re.compile("^[A-Za-z][A-Za-z0-9_]*$")

TYPE_ENB = {}
for i in TYPES:
    TYPE_ENB[i.type] = (i.input, i.control)


class BitFieldEditor(object):
    """
    Bit field editing class.
    """

    def __init__(self, dbase, register, bit_field, modified, top_builder):
        self.__db = dbase
        self.__modified = modified
        self.__register = register
        self.__bit_field = bit_field
        self.__builder = gtk.Builder()
        self.__top_builder = top_builder
        self.__builder.add_from_file(GLADE_BIT)
        self.__top_window = self.__builder.get_object("editfield")
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
        self.__verilog_obj = self.__builder.get_object('verilog_code')
        self.__volatile_obj = self.__builder.get_object('volatile')
        self.__error_field_obj = self.__builder.get_object('error_bit')
        self.__col = None
        self.__top_window.set_title(
            "Edit Bit Field - [%02x] %s" % (register.address,
                                            register.register_name))

        self.__spell = Spell(self.__builder.get_object("descr"))

        self.__top_window.set_icon_from_file(
            os.path.join(INSTALL_PATH, "media", "flop.svg"))
        (input_enb, control_enb) = TYPE_TO_ENABLE[bit_field.field_type]
        self.__input_obj.set_sensitive(input_enb)
        self.__control_obj.set_sensitive(control_enb)

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

        try:
            edge = "posedge" if self.__db.reset_active_level else "negedge"
            condition = "" if self.__db.reset_active_level else "~"
            be_level = "" if self.__db.byte_strobe_active_level else "~"

            name_map = {'MODULE': self.__db.module_name,
                        'BE_LEVEL': be_level,
                        'RESET_CONDITION': condition,
                        'RESET_EDGE': edge}
            text = REG[TYPE_TO_ID[bit_field.field_type].lower()] % name_map
        except KeyError:
            text = ""

        buf = self.__verilog_obj.get_buffer()
        if USE_HIGHLIGHT:

            styles = {}
            for token, value in VerilogLexer().get_tokens(text):
                while not STYLE.styles_token(token) and token.parent:
                    token = token.parent
                if token not in styles:
                    styles[token] = buf.create_tag()
                start = buf.get_end_iter()
                buf.insert_with_tags(start, value.encode('utf-8'),
                                     styles[token])

                for token, tag in styles.iteritems():
                    style = STYLE.style_for_token(token)
                    if style['bgcolor']:
                        tag.set_property('background', '#' + style['bgcolor'])
                    if style['color']:
                        tag.set_property('foreground', '#' + style['color'])
                    if style['bold']:
                        tag.set_property('weight', pango.WEIGHT_BOLD)
                    if style['italic']:
                        tag.set_property('style', pango.STYLE_ITALIC)
                    if style['underline']:
                        tag.set_property('underline', pango.UNDERLINE_SINGLE)
        else:
            buf.set_text(text)

        self.__verilog_obj.modify_font(pango_font)
        self.__builder.connect_signals(self)
        self.__top_window.show_all()

    def __initialize_from_data(self, bit_field):
        """
        Initializes the dialog's data fields from the object
        """
        self.__register_obj.set_text("<b>%s</b>" %
                                     self.__register.register_name)
        self.__register_obj.set_use_markup(True)

        self.__name_obj.set_text(bit_field.full_field_name())
        self.__type_obj.set_text(TYPE_TO_DESCR[bit_field.field_type])

        if bit_field.reset_type == BitField.RESET_NUMERIC:
            self.__reset_obj.set_text("%x" % bit_field.reset_value)
        else:
            self.__reset_obj.set_text(bit_field.reset_parameter)

        (input_enb, control_enb) = TYPE_TO_ENABLE[bit_field.field_type]
        if input_enb and not bit_field.input_signal:
            bit_field.input_signal = "%s_DATA_IN" % bit_field.field_name

        if control_enb and not bit_field.control_signal:
            bit_field.control_signal = "%s_LOAD" % bit_field.field_name

        self.__output_obj.set_text(bit_field.output_signal)
        self.__input_obj.set_text(bit_field.input_signal)

        self.__volatile_obj.set_active(bit_field.volatile)
        self.__error_field_obj.set_active(bit_field.is_error_field)

        self.__static_obj.set_active(bit_field.output_is_static)
        self.__side_effect_obj.set_active(bit_field.output_has_side_effect)
        self.__text_buffer.set_text(bit_field.description)
        self.__output_enable_obj.set_active(bit_field.use_output_enable)
        self.__control_obj.set_text(self.__bit_field.control_signal)

    def on_help_clicked(self, obj):
        HelpWindow(self.__top_builder, "bitfield_value_help.rst")

    def on_property_help_clicked(self, obj):
        HelpWindow(self.__top_builder, "bitfield_signal_prop_help.rst")

    def on_signal_help_clicked(self, obj):
        HelpWindow(self.__top_builder, "bitfield_signal_help.rst")

    def on_output_changed(self, obj):
        self.__bit_field.output_signal = obj.get_text()
        self.__check_data()
        self.__modified()

    def on_input_changed(self, obj):
        self.__bit_field.input_signal = obj.get_text()
        self.__check_data()
        self.__modified()

    def on_volatile_changed(self, obj):
        self.__bit_field.volatile = obj.get_active()
        self.__modified()

    def on_error_bit_toggled(self, obj):
        self.__bit_field.is_error_field = obj.get_active()
        self.__modified()

    def on_static_toggled(self, obj):
        self.__bit_field.output_is_static = obj.get_active()
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

        last = len(self.__list_model)
        max_values = 2 ** self.__bit_field.width

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
            new_val = "" if largest >= max_values else "%x" % (largest + 1,)
            node = self.__list_model.append(row=(new_val, '', ''))
            path = self.__list_model.get_path(node)
        else:
            path = (last, )

        self.__value_tree_obj.set_cursor(path, focus_column=self.__col,
                                         start_editing=True)
        self.__modified()

    def on_remove_clicked(self, obj):  # IGNORE:W0613 - obj is unused
        """
        Called with the remove button is clicked
        """
        self.__list_model.remove(self.__model_selection.get_selected()[1])
        self.__update_values()
        self.__modified()

    def __change_val(self, text, path, new_text):  # IGNORE:W0613
        """
        Called with the value has changed value field. Checks to make sure that
        value is a valid hex value, and within the correct range.
        """
        new_text = new_text.strip()

        start = self.__bit_field.lsb
        stop = self.__bit_field.msb
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
        self.__bit_field.output_has_side_effect = obj.get_active()
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
                     "Look for strange punctuations, like dashs and "
                     "quotes that look valid, but are not actual "
                     "ascii characters.")
        self.__list_model.set_value(node, 2, new_text)
        self.__update_values()
        self.__modified()

    def on_output_enable_toggled(self, obj):
        """
        Enables the output field based on the output enable field
        """
        active = self.__output_enable_obj.get_active()
        self.__bit_field.use_output_enable = active
        self.__output_obj.set_sensitive(obj.get_active())
        self.__check_data()
        self.__modified()

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

    def on_destroy_event(self, obj):
        self.__spell.detach()

    def on_delete_event(self, obj, event):
        self.__spell.detach()

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

        if control_error is False:
            clear_error(self.__control_obj)
        if input_error is False:
            clear_error(self.__input_obj)
        if output_error is False:
            clear_error(self.__output_obj)


def set_error(obj, message):
    obj.set_property('secondary-icon-stock', gtk.STOCK_DIALOG_ERROR)
    obj.set_property('secondary-icon-tooltip-text', message)


def clear_error(obj):
    obj.set_property('secondary-icon-stock', None)
    obj.set_property('secondary-icon-tooltip-text', '')
