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

from gi.repository import Gtk, Gdk, Pango
from regenerate.db import (
    TYPE_TO_ID,
    TYPE_TO_DESCR,
    TYPE_TO_ENABLE,
    ResetType,
    BitValues,
)
from regenerate.settings.paths import GLADE_BIT
from regenerate.ui.error_dialogs import ErrorMsg
from regenerate.ui.help_window import HelpWindow
from regenerate.ui.base_window import BaseWindow
from regenerate.ui.spell import Spell
from regenerate.ui.utils import clean_format_if_needed
from regenerate.ui.highlight import highlight_text
from regenerate.writers.verilog_reg_def import REG


def modified(func):
    """Decorator to set modified values"""

    def modify_value(self, obj):
        func(self, obj)
        self.modified()

    return modify_value


class BitFieldEditor(BaseWindow):
    """Bit field editing class."""

    def __init__(
        self, dbase, register, bit_field, modified_func, top_builder, parent
    ):

        super().__init__()

        self.dbase = dbase
        self.modified = modified_func
        self.register = register
        self.bit_field = bit_field
        self.builder = Gtk.Builder()
        self.builder.add_from_file(GLADE_BIT)

        self.top_builder = top_builder
        self.control_obj = self.builder.get_object("control")
        self.output_obj = self.builder.get_object("output")
        self.output_enable_obj = self.builder.get_object("outen")
        self.input_obj = self.builder.get_object("input")
        self.value_obj = self.builder.get_object("values")
        self.col = None

        pango_font = Pango.FontDescription("monospace")
        self.setup_description(pango_font)

        (input_enb, control_enb) = TYPE_TO_ENABLE[bit_field.field_type]
        self.input_obj.set_sensitive(input_enb)
        self.control_obj.set_sensitive(control_enb)

        self.build_values_list()

        self.initialize_from_data(bit_field)
        self.output_obj.set_sensitive(self.get_active("outen"))

        self.check_data()

        verilog_obj = self.builder.get_object("verilog_code")
        highlight_text(
            self.build_register_text(bit_field), verilog_obj.get_buffer()
        )
        verilog_obj.modify_font(pango_font)

        self.builder.connect_signals(self)
        self.configure_window(register, parent)
        self.parent = parent

    def setup_description(self, pango_font):
        """
        Finds the bitfield description object, sets the font to a monospace
        font, and attaches the spell checker to the buffere
        """
        descr = self.builder.get_object("descr")
        descr.modify_font(pango_font)
        self.spell = Spell(descr)

    def configure_window(self, register, parent):
        """
        Sets up the dialog window, setting the title, parent,
        and window icon
        """
        self.top_window = self.builder.get_object("editfield")
        self.top_window.set_transient_for(parent)
        self.top_window.set_title(
            "Edit Bit Field - [{0:02x}] {1}".format(
                register.address, register.name
            )
        )
        self.configure(self.top_window)
        self.top_window.show_all()

    def build_register_text(self, bit_field):
        """Returns the type of the verilog instantiation of the type"""
        try:
            edge = (
                "posedge" if self.dbase.ports.reset_active_level else "negedge"
            )
            condition = "" if self.dbase.ports.reset_active_level else "~"
            be_level = "" if self.dbase.ports.byte_strobe_active_level else "~"

            name_map = {
                "MODULE": self.dbase.module_name,
                "BE_LEVEL": be_level,
                "RESET_CONDITION": condition,
                "RESET_EDGE": edge,
            }
            text = REG[TYPE_TO_ID[bit_field.field_type].lower()] % name_map
        except KeyError:
            text = ""
        return text

    def initialize_from_data(self, bit_field):
        """Initializes the dialog's data fields from the object"""

        self.set_text("field_name", bit_field.full_field_name())
        self.set_text("type", TYPE_TO_DESCR[bit_field.field_type])

        if bit_field.reset_type == ResetType.NUMERIC:
            self.set_text("reset_value", f"{bit_field.reset_value:x}")
        else:
            self.set_text("reset_value", bit_field.reset_parameter)

        (input_enb, control_enb) = TYPE_TO_ENABLE[bit_field.field_type]
        if input_enb and not bit_field.input_signal:
            bit_field.input_signal = f"{bit_field.name}_DATA_IN"

        if control_enb and not bit_field.control_signal:
            bit_field.control_signal = f"{bit_field.name}_LOAD"

        self.output_obj.set_text(bit_field.output_signal)
        self.input_obj.set_text(bit_field.input_signal)

        self.set_active("volatile", bit_field.flags.volatile)
        self.set_active("random", bit_field.flags.can_randomize)
        self.set_active("error_bit", bit_field.flags.is_error_field)
        self.set_active("static", bit_field.output_is_static)
        self.set_active("side_effect", bit_field.output_has_side_effect)
        self.set_active("outen", bit_field.use_output_enable)

        text_buffer = self.builder.get_object("descr").get_buffer()
        text_buffer.connect("changed", self._description_changed)
        text_buffer.set_text(bit_field.description)

        self.control_obj.set_text(self.bit_field.control_signal)

    def on_help_clicked(self, _obj):
        "Display the help window"
        HelpWindow(self.top_builder, "bitfield_value_help.rst")

    def on_property_help_clicked(self, _obj):
        "Display the help window"
        HelpWindow(self.top_builder, "bitfield_signal_prop_help.rst")

    def on_signal_help_clicked(self, _obj):
        "Display the help window"
        HelpWindow(self.top_builder, "bitfield_signal_help.rst")

    def _set_field_value(self, val, obj):
        "Sets the field value"
        setattr(self.bit_field, val, obj.get_active())

    def _set_flag_value(self, val, obj):
        "Sets the field value"
        setattr(self.bit_field.flag, val, obj.get_active())

    @modified
    def on_output_changed(self, obj):
        "Called with the output signal changed"
        self.bit_field.output_signal = obj.get_text()
        self.check_data()

    @modified
    def on_input_changed(self, obj):
        "Called with the input signal changed"
        self.bit_field.input_signal = obj.get_text()
        self.check_data()

    @modified
    def on_volatile_changed(self, obj):
        "Called with the volatile flag changed"
        self._set_flag_value("volatile", obj)

    @modified
    def on_random_toggled(self, obj):
        "Called with the random flag changed"
        self._set_flag_value("can_randomize", obj)

    @modified
    def on_error_bit_toggled(self, obj):
        "Called with the error field flag changed"
        self._set_flag_value("is_error_field", obj)

    @modified
    def on_static_toggled(self, obj):
        "Called with the static flag changed"
        self._set_field_value("output_is_static", obj)

    @modified
    def on_control_changed(self, obj):
        "Called with the control signal changed"
        self.bit_field.control_signal = obj.get_text()
        self.check_data()

    def on_add_clicked(self, _obj):
        """
        Called with the add button is clicked. Search the existing values
        in the list, finding the next highest value to use as the default.
        """

        last = len(self.value_model)
        max_values = 2 ** self.bit_field.width

        if last >= max_values:
            ErrorMsg(
                "Maximum number of values reached",
                f"The width of the field only allows for {last} values",
                parent=self.parent,
            )
            return

        largest = find_largest_value(self.value_model)

        last -= 1
        if (
            last == -1
            or self.value_model[last][0]
            or self.value_model[last][1]
            or self.value_model[last][2]
        ):
            new_val = (
                "" if largest >= max_values else "{0:x}".format(largest + 1)
            )
            node = self.value_model.append(row=(new_val, "", ""))
            path = self.value_model.get_path(node)
        else:
            path = (last,)

        focus_column = self.col
        self.value_obj.set_cursor(path, focus_column, start_editing=True)
        self.modified()

    @modified
    def on_remove_clicked(self, _obj):
        "Called with the remove button is clicked"
        self.value_model.remove(self.model_selection.get_selected()[1])
        self.update_values()

    @modified
    def on_side_effect_toggled(self, obj):
        "Called with the side effect flag toggled"
        self.bit_field.output_has_side_effect = obj.get_active()

    def update_values(self):
        "Update the bit field values from the model"
        self.bit_field.values = [
            (val[0], val[1], val[2]) for val in self.value_model
        ]
        self.bit_field.values = []
        for val in self.value_model:
            bfval = BitValues()
            bfval.value = int(val[0])
            bfval.token = val[1]
            bfval.description = val[2]
            self.bit_field.values.append(bfval)

    @modified
    def on_output_enable_toggled(self, obj):
        """
        Enables the output field based on the output enable field
        """
        active = self.output_enable_obj.get_active()
        self.bit_field.use_output_enable = active
        self.output_obj.set_sensitive(obj.get_active())
        self.check_data()

    def on_descr_key_press_event(self, obj, event):
        """
        Called on a double click event. If we detect a double click with
        the first button, we call the edit_register method.
        """
        if event.keyval == Gdk.KEY_F12:
            if clean_format_if_needed(obj):
                self.modified()
            return True
        return False

    def on_destroy_event(self, _obj):
        """On destroy, detach the spell checker"""
        self.spell.detach()

    def on_delete_event(self, _obj, _event):
        """On delete, detach the spell checker"""
        self.spell.detach()

    def on_close_clicked(self, _obj):
        """
        Saves the data from the interface to the internal BitField structure
        """
        self.top_window.destroy()

    @modified
    def _description_changed(self, obj):
        "Called with the description changes"
        self.bit_field.description = obj.get_text(
            obj.get_start_iter(), obj.get_end_iter(), False
        )

    def check_data(self):
        "Checks the input signal validity"
        input_error = False
        output_error = False
        control_error = False

        if control_error is False:
            clear_error(self.control_obj)
        if input_error is False:
            clear_error(self.input_obj)
        if output_error is False:
            clear_error(self.output_obj)

    def set_active(self, name, value):
        "Set the active flag"
        self.builder.get_object(name).set_active(value)

    def get_active(self, name):
        "Get the active flag"
        return self.builder.get_object(name).get_active()

    def set_text(self, name, value):
        "Set the text"
        self.builder.get_object(name).set_text(value)

    def build_values_list(self):
        """
        Builds the columns associated with the list view
        """
        self.col = build_column("Value", 0, 50, self.change_val)
        self.value_obj.append_column(self.col)

        self.value_obj.append_column(
            build_column("Token", 1, 100, self.change_text)
        )

        self.value_obj.append_column(
            build_column("Description", 2, 0, self.change_description)
        )

        self.value_model = Gtk.ListStore(str, str, str)
        self.model_selection = self.value_obj.get_selection()
        self.value_obj.set_model(self.value_model)

        self.used_tokens = set()
        for value in self.bit_field.values:
            self.used_tokens.add(value.token)
            self.value_model.append(
                row=(str(value.value), value.token, value.description)
            )

    def change_text(self, _text, path, new_text):
        """
        Updates the data model when the text value is changed in the model.
        """
        if new_text in self.used_tokens:
            ErrorMsg(
                "Duplicate token",
                f'The token "{new_text}" has already been used',
                parent=self.parent,
            )
        else:
            node = self.value_model.get_iter(path)
            old_text = self.value_model.get_value(node, 1)
            self.value_model.set_value(node, 1, new_text)

            if old_text and old_text in self.used_tokens:
                self.used_tokens.remove(old_text)
            if new_text:
                self.used_tokens.add(new_text)
            self.update_values()
            self.modified()

    def change_description(self, _text, path, new_text):
        """
        Updates the data model when the text value is changed in the model.
        """
        node = self.value_model.get_iter(path)
        try:
            new_text = new_text.encode("ascii").decode()
        except UnicodeEncodeError:
            ErrorMsg(
                "Invalid ASCII characters detected",
                "Look for strange punctuations, like dashs and "
                "quotes that look valid, but are not actual "
                "ascii characters.",
                parent=self.parent,
            )
        self.value_model.set_value(node, 2, new_text)
        self.update_values()
        self.modified()

    def change_val(self, _text, path, new_text):
        """
        Called with the value has changed value field. Checks to make sure that
        value is a valid hex value, and within the correct range.
        """
        new_text = new_text.strip()

        start = self.bit_field.lsb
        stop = self.bit_field.msb.resolve()
        maxval = (2 ** (stop - start + 1)) - 1

        try:
            if new_text == "" or int(new_text, 16) > maxval:
                return
        except ValueError:
            return

        node = self.value_model.get_iter(path)
        self.value_model.set_value(node, 0, new_text)
        self.update_values()
        self.modified()


def set_error(obj, message):
    "Set the error icon message"
    obj.set_property("secondary-icon-stock", Gtk.STOCK_DIALOG_ERROR)
    obj.set_property("secondary-icon-tooltip-text", message)


def clear_error(obj):
    "Clear the error icon message"
    obj.set_property("secondary-icon-stock", None)
    obj.set_property("secondary-icon-tooltip-text", "")


def find_largest_value(model):
    "Find the largets value from the model"

    try:
        value_list = [
            int(value, 16) for (value, token, descr) in model if value != ""
        ]
        return max(value_list)
    except ValueError:
        return -1


def build_column(title, text_col, size, callback):
    "Build the column"

    render = Gtk.CellRendererText()
    render.set_property("editable", True)
    render.connect("edited", callback)
    column = Gtk.TreeViewColumn(title, render, text=text_col)
    if size:
        column.set_min_width(size)
    return column
