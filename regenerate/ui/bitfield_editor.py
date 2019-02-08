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

#  Standard imports

import gtk
import os
import pango

# Imports that might fail, and we can recover from

try:
    from pygments.lexers import VerilogLexer
    from pygments.styles import get_style_by_name
    USE_HIGHLIGHT = True
    STYLE = get_style_by_name('emacs')
except ImportError:
    USE_HIGHLIGHT = False

# regenerate imports

from regenerate.db import BitField, TYPE_TO_ID
from regenerate.db import TYPE_TO_DESCR, TYPE_TO_ENABLE
from regenerate.settings.paths import GLADE_BIT, INSTALL_PATH
from regenerate.ui.error_dialogs import ErrorMsg
from regenerate.ui.help_window import HelpWindow
from regenerate.ui.spell import Spell
from regenerate.ui.utils import clean_format_if_needed
from regenerate.writers.verilog_reg_def import REG


def modified(f):
    """Decorator to set modified values"""

    def modify_value(self, obj):
        f(self, obj)
        self.modified()

    return modify_value


class BitFieldEditor(object):
    """Bit field editing class."""

    def __init__(self, dbase, register, bit_field, modified, top_builder):
        self._db = dbase
        self.modified = modified
        self._register = register
        self._bit_field = bit_field
        self._builder = gtk.Builder()
        self._top_builder = top_builder
        self._builder.add_from_file(GLADE_BIT)
        self._top_window = self._builder.get_object("editfield")
        self._control_obj = self._builder.get_object('control')
        self._name_obj = self._builder.get_object("field_name")
        self._register_obj = self._builder.get_object("register_name")
        self._output_obj = self._builder.get_object("output")
        self._type_obj = self._builder.get_object('type')
        self._input_obj = self._builder.get_object("input")
        self._reset_obj = self._builder.get_object("reset_value")
        self._static_obj = self._builder.get_object('static')
        self._text_buffer = self._builder.get_object("descr").get_buffer()
        self._value_tree_obj = self._builder.get_object('values')
        self._output_enable_obj = self._builder.get_object("outen")
        self._side_effect_obj = self._builder.get_object("side_effect")
        self._verilog_obj = self._builder.get_object('verilog_code')
        self._volatile_obj = self._builder.get_object('volatile')
        self._random_obj = self._builder.get_object('random')
        self._error_field_obj = self._builder.get_object('error_bit')
        self._col = None
        self._top_window.set_title("Edit Bit Field - [{0:02x}] {1}".format(
            register.address, register.register_name))

        self._spell = Spell(self._builder.get_object("descr"))

        self._top_window.set_icon_from_file(
            os.path.join(INSTALL_PATH, "media", "flop.svg"))
        (input_enb, control_enb) = TYPE_TO_ENABLE[bit_field.field_type]
        self._input_obj.set_sensitive(input_enb)
        self._control_obj.set_sensitive(control_enb)

        pango_font = pango.FontDescription("monospace")
        self._builder.get_object("descr").modify_font(pango_font)

        self.build_values_list()

        self._list_model = gtk.ListStore(str, str, str)
        self._model_selection = self._value_tree_obj.get_selection()
        self._value_tree_obj.set_model(self._list_model)

        self._used_tokens = set()
        for value in self._bit_field.values:
            self._used_tokens.add(value[1])
            self._list_model.append(row=value)

        self._initialize_from_data(bit_field)
        self._output_obj.set_sensitive(self._output_enable_obj.get_active())
        self._check_data()

        self._text_buffer.connect('changed', self._description_changed)

        try:
            edge = "posedge" if self._db.reset_active_level else "negedge"
            condition = "" if self._db.reset_active_level else "~"
            be_level = "" if self._db.byte_strobe_active_level else "~"

            name_map = {
                'MODULE': self._db.module_name,
                'BE_LEVEL': be_level,
                'RESET_CONDITION': condition,
                'RESET_EDGE': edge
            }
            text = REG[TYPE_TO_ID[bit_field.field_type].lower()] % name_map
        except KeyError:
            text = ""

        buf = self._verilog_obj.get_buffer()
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

        self._verilog_obj.modify_font(pango_font)
        self._builder.connect_signals(self)
        self._top_window.show_all()

    def _initialize_from_data(self, bit_field):
        """
        Initializes the dialog's data fields from the object
        """
        self._register_obj.set_text(
            "<b>{0}</b>".format(self._register.register_name))
        self._register_obj.set_use_markup(True)

        self._name_obj.set_text(bit_field.full_field_name())
        self._type_obj.set_text(TYPE_TO_DESCR[bit_field.field_type])

        if bit_field.reset_type == BitField.RESET_NUMERIC:
            self._reset_obj.set_text("{0:x}".format(bit_field.reset_value))
        else:
            self._reset_obj.set_text(bit_field.reset_parameter)

        (input_enb, control_enb) = TYPE_TO_ENABLE[bit_field.field_type]
        if input_enb and not bit_field.input_signal:
            bit_field.input_signal = "{0}_DATA_IN".format(bit_field.field_name)

        if control_enb and not bit_field.control_signal:
            bit_field.control_signal = "{0}_LOAD".format(bit_field.field_name)

        self._output_obj.set_text(bit_field.output_signal)
        self._input_obj.set_text(bit_field.input_signal)

        self._volatile_obj.set_active(bit_field.volatile)
        self._random_obj.set_active(bit_field.can_randomize)
        self._error_field_obj.set_active(bit_field.is_error_field)

        self._static_obj.set_active(bit_field.output_is_static)
        self._side_effect_obj.set_active(bit_field.output_has_side_effect)
        self._text_buffer.set_text(bit_field.description)
        self._output_enable_obj.set_active(bit_field.use_output_enable)
        self._control_obj.set_text(self._bit_field.control_signal)

    def on_help_clicked(self, obj):
        HelpWindow(self._top_builder, "bitfield_value_help.rst")

    def on_property_help_clicked(self, obj):
        HelpWindow(self._top_builder, "bitfield_signal_prop_help.rst")

    def on_signal_help_clicked(self, obj):
        HelpWindow(self._top_builder, "bitfield_signal_help.rst")

    def _set_field_value(self, val, obj):
        setattr(self._bit_field, val, obj.get_active())

    @modified
    def on_output_changed(self, obj):
        self._bit_field.output_signal = obj.get_text()
        self._check_data()

    @modified
    def on_input_changed(self, obj):
        self._bit_field.input_signal = obj.get_text()
        self._check_data()

    @modified
    def on_volatile_changed(self, obj):
        self._set_field_value("volatile", obj)

    @modified
    def on_random_toggled(self, obj):
        self._set_field_value("can_randomize", obj)

    @modified
    def on_error_bit_toggled(self, obj):
        self._set_field_value("is_error_field", obj)

    @modified
    def on_static_toggled(self, obj):
        self._set_field_value("output_is_static", obj)

    @modified
    def on_control_changed(self, obj):
        self._bit_field.control_signal = obj.get_text()
        self._check_data()

    def build_values_list(self):
        """
        Builds the columns associated with the list view
        """
        render = gtk.CellRendererText()
        render.set_property('editable', True)
        render.connect('edited', self._change_val)
        column = gtk.TreeViewColumn('Value', render, text=0)
        column.set_min_width(50)
        self._value_tree_obj.append_column(column)
        self._col = column

        render = gtk.CellRendererText()
        render.set_property('editable', True)
        render.connect('edited', self._change_text)
        column = gtk.TreeViewColumn('Token', render, text=1)
        column.set_min_width(100)
        self._value_tree_obj.append_column(column)

        render = gtk.CellRendererText()
        render.set_property('editable', True)
        render.connect('edited', self._change_description)
        column = gtk.TreeViewColumn('Description', render, text=2)
        self._value_tree_obj.append_column(column)

    def on_add_clicked(self, obj):
        """
        Called with the add button is clicked. Search the existing values
        in the list, finding the next highest value to use as the default.
        """

        last = len(self._list_model)
        max_values = 2 ** self._bit_field.width

        if last >= max_values:
            ErrorMsg(
                "Maximum number of values reached",
                "The width of the field only allows for {0} values".format(last))
            return

        try:
            largest = max([int(val[0], 16) for val in self._list_model
                           if val[0] != ""])
        except ValueError:
            largest = -1

        last -= 1
        if (last == -1 or self._list_model[last][0] or
                self._list_model[last][1] or self._list_model[last][2]):
            new_val = "" if largest >= max_values else "{0:x}".format(
                largest + 1)
            node = self._list_model.append(row=(new_val, '', ''))
            path = self._list_model.get_path(node)
        else:
            path = (last, )

        self._value_tree_obj.set_cursor(path,
                                        focus_column=self._col,
                                        start_editing=True)
        self.modified()

    @modified
    def on_remove_clicked(self, obj):
        """
        Called with the remove button is clicked
        """
        self._list_model.remove(self._model_selection.get_selected()[1])
        self._update_values()

    def _change_val(self, text, path, new_text):  # IGNORE:W0613
        """
        Called with the value has changed value field. Checks to make sure that
        value is a valid hex value, and within the correct range.
        """
        new_text = new_text.strip()

        start = self._bit_field.lsb
        stop = self._bit_field.msb
        maxval = (2 ** (stop - start + 1)) - 1

        try:
            if new_text == "" or int(new_text, 16) > maxval:
                return
        except ValueError:
            return

        node = self._list_model.get_iter(path)
        self._list_model.set_value(node, 0, new_text)
        self._update_values()
        self.modified()

    @modified
    def on_side_effect_toggled(self, obj):
        self._bit_field.output_has_side_effect = obj.get_active()

    def _update_values(self):
        new_list = []
        for row in self._list_model:
            new_list.append((row[0], row[1], row[2]))
        self._bit_field.values = new_list

    def _change_text(self, text, path, new_text):
        """
        Updates the data model when the text value is changed in the model.
        """
        if new_text in self._used_tokens:
            ErrorMsg("Duplicate token",
                     'The token "{0}" has already been used'.format(new_text))
        else:
            node = self._list_model.get_iter(path)
            old_text = self._list_model.get_value(node, 1)
            self._list_model.set_value(node, 1, new_text)

            if old_text and old_text in self._used_tokens:
                self._used_tokens.remove(old_text)
            if new_text:
                self._used_tokens.add(new_text)
            self._update_values()
            self.modified()

    def _change_description(self, text, path, new_text):
        """
        Updates the data model when the text value is changed in the model.
        """
        node = self._list_model.get_iter(path)
        try:
            new_text.decode("ascii")
        except:
            ErrorMsg("Invalid ASCII characters detected",
                     "Look for strange punctuations, like dashs and "
                     "quotes that look valid, but are not actual "
                     "ascii characters.")
        self._list_model.set_value(node, 2, new_text)
        self._update_values()
        self.modified()

    @modified
    def on_output_enable_toggled(self, obj):
        """
        Enables the output field based on the output enable field
        """
        active = self._output_enable_obj.get_active()
        self._bit_field.use_output_enable = active
        self._output_obj.set_sensitive(obj.get_active())
        self._check_data()

    def on_descr_key_press_event(self, obj, event):
        """
        Called on a double click event. If we detect a double click with
        the first button, we call the edit_register method.
        """
        if event.keyval == gtk.keysyms.F12:
            if clean_format_if_needed(obj):
                self.modified()
            return True
        return False

    def on_destroy_event(self, obj):
        self._spell.detach()

    def on_delete_event(self, obj, event):
        self._spell.detach()

    def on_close_clicked(self, obj):
        """
        Saves the data from the interface to the internal BitField structure
        """
        self._top_window.destroy()

    @modified
    def _description_changed(self, obj):
        self._bit_field.description = self._text_buffer.get_text(
            self._text_buffer.get_start_iter(),
            self._text_buffer.get_end_iter(), False)

    def _check_data(self):
        """
        Checks the input signal validity
        """
        input_error = False
        output_error = False
        control_error = False

        if control_error is False:
            clear_error(self._control_obj)
        if input_error is False:
            clear_error(self._input_obj)
        if output_error is False:
            clear_error(self._output_obj)


def set_error(obj, message):
    obj.set_property('secondary-icon-stock', gtk.STOCK_DIALOG_ERROR)
    obj.set_property('secondary-icon-tooltip-text', message)


def clear_error(obj):
    obj.set_property('secondary-icon-stock', None)
    obj.set_property('secondary-icon-tooltip-text', '')
