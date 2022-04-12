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

from typing import Callable

from gi.repository import Gtk, Gdk, Pango
from regenerate.db import (
    RegisterSet,
    Register,
    BitField,
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


def modified(func: Callable):
    """Decorator to set modified values"""

    def modify_value(self, obj):
        func(self, obj)
        self.modified()

    return modify_value


class BitFieldEditor(BaseWindow):
    """Bit field editing class."""

    def __init__(
        self,
        dbase: RegisterSet,
        register: Register,
        bit_field: BitField,
        modified_func: Callable,
        parent: Gtk.Window,
    ):
        super().__init__()

        self._regset = dbase
        self.modified = modified_func
        self._bit_field = bit_field
        self._builder = Gtk.Builder()
        self._builder.add_from_file(str(GLADE_BIT))

        self._control_obj = self._builder.get_object("control")
        self._output_obj = self._builder.get_object("output")
        self._output_enable_obj = self._builder.get_object("outen")
        self._input_obj = self._builder.get_object("input")
        self._value_obj = self._builder.get_object("values")
        self._col = None

        pango_font = Pango.FontDescription("monospace")
        self._setup_description(pango_font)

        (input_enb, control_enb) = TYPE_TO_ENABLE[bit_field.field_type]
        self._input_obj.set_sensitive(input_enb)
        self._control_obj.set_sensitive(control_enb)

        self._build_values_list()

        self._initialize_from_data(bit_field)
        self._output_obj.set_sensitive(self._get_active("outen"))

        self._check_data()

        verilog_obj = self._builder.get_object("verilog_code")
        highlight_text(
            self._build_register_text(bit_field), verilog_obj.get_buffer()
        )
        verilog_obj.modify_font(pango_font)

        self._builder.connect_signals(self)
        self._configure_window(register, parent)
        self._parent = parent

    def _setup_description(self, pango_font: Pango.FontDescription) -> None:
        """
        Finds the bitfield description object, sets the font to a monospace
        font, and attaches the spell checker to the buffere
        """
        descr = self._builder.get_object("descr")
        descr.modify_font(pango_font)
        self.spell = Spell(descr)

    def _configure_window(
        self, register: Register, parent: Gtk.Window
    ) -> None:
        """
        Sets up the dialog window, setting the title, parent,
        and window icon
        """
        self._top_window = self._builder.get_object("editfield")
        self._top_window.set_transient_for(parent)
        self._top_window.set_title(
            f"Edit Bit Field - [{register.address:02x}] {register.name}"
        )
        self.configure(self._top_window)
        self._top_window.show_all()

    def _build_register_text(self, bit_field: BitField) -> str:
        """Returns the type of the verilog instantiation of the type"""
        try:
            if self._regset.ports.reset_active_level:
                edge = "posedge"
                condition = ""
                rst_name = "RST"
            else:
                edge = "negedge"
                condition = "!"
                rst_name = "RSTn"

            trigger = (
                "" if self._regset.ports.sync_reset else f" or {edge} RSTn"
            )
            name_map = {
                "MODULE": self._regset.name,
                "RST": rst_name,
                "RESET_CONDITION": condition,
                "RESET_TRIGGER": trigger,
                "RESET_EDGE": edge,
            }
            ftype = bit_field.field_type
            t2id = TYPE_TO_ID[ftype].lower()
            text = REG[t2id] % name_map
        except KeyError:
            text = "Error generating the implmentation"
        return text

    def _initialize_from_data(self, bit_field: BitField) -> None:
        """Initializes the dialog's data fields from the object"""

        self._set_text("field_name", bit_field.full_field_name())
        self._set_text("type", TYPE_TO_DESCR[bit_field.field_type])

        if bit_field.reset_type == ResetType.NUMERIC:
            self._set_text("reset_value", bit_field.reset_string())
        else:
            self._set_text("reset_value", bit_field.reset_parameter)

        (input_enb, control_enb) = TYPE_TO_ENABLE[bit_field.field_type]
        if input_enb and not bit_field.input_signal:
            bit_field.input_signal = f"{bit_field.name}_DATA_IN"

        if control_enb and not bit_field.control_signal:
            bit_field.control_signal = f"{bit_field.name}_LOAD"

        self._output_obj.set_text(bit_field.output_signal)
        self._input_obj.set_text(bit_field.input_signal)

        self._set_active("volatile", bit_field.flags.volatile)
        self._set_active("random", bit_field.flags.can_randomize)
        self._set_active("error_bit", bit_field.flags.is_error_field)
        self._set_active("static", bit_field.output_is_static)
        self._set_active("side_effect", bit_field.output_has_side_effect)
        self._set_active("outen", bit_field.use_output_enable)
        self._set_active("alt_reset", bit_field.use_alternate_reset)
        self._builder.get_object("alt_reset").set_sensitive(
            self._regset.ports.secondary_reset
        )

        text_buffer = self._builder.get_object("descr").get_buffer()
        text_buffer.connect("changed", self._description_changed)
        text_buffer.set_text(bit_field.description)

        self._control_obj.set_text(self._bit_field.control_signal)

    def on_help_clicked(self, _obj: Gtk.Button) -> None:
        "Display the help window"
        HelpWindow("bitfield_value_help.rst")

    def on_property_help_clicked(self, _obj: Gtk.Button) -> None:
        "Display the help window"
        HelpWindow("bitfield_signal_prop_help.html", "Bit Field Properties")

    def on_signal_help_clicked(self, _obj: Gtk.Button) -> None:
        "Display the help window"
        HelpWindow("bitfield_signal_help.html", "Bit Field Signals")

    def _set_field_value(self, val: str, obj: Gtk.CheckButton) -> None:
        "Sets the field value"
        setattr(self._bit_field, val, obj.get_active())

    def _set_flag_value(self, val: str, obj: Gtk.CheckButton) -> None:
        "Sets the field value"
        setattr(self._bit_field.flags, val, obj.get_active())

    @modified
    def on_output_changed(self, obj: Gtk.Entry) -> None:
        "Called with the output signal changed"
        self._bit_field.output_signal = obj.get_text()
        self._check_data()

    @modified
    def on_input_changed(self, obj: Gtk.Entry) -> None:
        "Called with the input signal changed"
        self._bit_field.input_signal = obj.get_text()
        self._check_data()

    @modified
    def on_volatile_changed(self, obj: Gtk.ToggleButton) -> None:
        "Called with the volatile flag changed"
        self._set_flag_value("volatile", obj)

    @modified
    def on_random_toggled(self, obj: Gtk.ToggleButton) -> None:
        "Called with the random flag changed"
        self._set_flag_value("can_randomize", obj)

    @modified
    def on_error_bit_toggled(self, obj: Gtk.ToggleButton) -> None:
        "Called with the error field flag changed"
        self._set_flag_value("is_error_field", obj)

    @modified
    def on_static_toggled(self, obj: Gtk.ToggleButton) -> None:
        "Called with the static flag changed"
        self._set_field_value("output_is_static", obj)

    @modified
    def on_control_changed(self, obj: Gtk.Entry) -> None:
        "Called with the control signal changed"
        self._bit_field.control_signal = obj.get_text()
        self._check_data()

    @modified
    def on_add_clicked(self, _obj: Gtk.Button) -> None:
        """
        Called with the add button is clicked. Search the existing values
        in the list, finding the next highest value to use as the default.
        """

        last = len(self.value_model)
        max_values = 2 ** self._bit_field.width

        if last >= max_values:
            ErrorMsg(
                "Maximum number of values reached",
                f"The width of the field only allows for {last} values",
                parent=self._parent,
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
            new_val = "" if largest >= max_values else f"{(largest+1):x}"
            node = self.value_model.append(row=(new_val, "", ""))
            path = self.value_model.get_path(node)
        else:
            path = (last,)

        focus_column = self._col
        self._value_obj.set_cursor(path, focus_column, start_editing=True)

    @modified
    def on_remove_clicked(self, _obj: Gtk.Button) -> None:
        "Called with the remove button is clicked"
        self.value_model.remove(self.model_selection.get_selected()[1])
        self._update_values()

    @modified
    def on_side_effect_toggled(self, obj: Gtk.CheckButton) -> None:
        "Called with the side effect flag toggled"
        self._bit_field.output_has_side_effect = obj.get_active()

    def _update_values(self) -> None:
        "Update the bit field values from the model"
        # pylint: disable=E1133

        self._bit_field.values = [
            BitValues(val[0], val[1], val[2]) for val in self.value_model
        ]
        self._bit_field.values = []
        for val in self.value_model:
            bfval = BitValues()
            bfval.value = int(val[0])
            bfval.token = val[1]
            bfval.description = val[2]
            self._bit_field.values.append(bfval)

    @modified
    def on_output_enable_toggled(self, obj: Gtk.CheckButton) -> None:
        """
        Enables the output field based on the output enable field
        """
        active = self._output_enable_obj.get_active()
        self._bit_field.use_output_enable = active
        self._output_obj.set_sensitive(obj.get_active())
        self._check_data()

    @modified
    def on_alt_reset_toggled(self, button: Gtk.CheckButton) -> None:
        """
        Enables the output field based on the output enable field
        """
        active = button.get_active()
        self._bit_field.use_alternate_reset = active
        self._check_data()

    def on_descr_key_press_event(
        self, text_view: Gtk.TextView, event: Gdk.EventKey
    ) -> bool:
        """
        Called on a double click event. If we detect a double click with
        the first button, we call the edit_register method.
        """
        if event.keyval == Gdk.KEY_F12:
            if clean_format_if_needed(text_view):
                self.modified()
            return True
        return False

    def on_destroy_event(self, _obj: Gtk.Dialog) -> None:
        """On destroy, detach the spell checker"""
        self.spell.detach()

    def on_delete_event(self, _obj: Gtk.Dialog, _event: Gdk.EventType) -> None:
        """On delete, detach the spell checker"""
        self.spell.detach()

    def on_close_clicked(self, _obj: Gtk.Button) -> None:
        """
        Saves the data from the interface to the internal BitField structure
        """
        self._top_window.destroy()

    @modified
    def _description_changed(self, obj: Gtk.TextBuffer) -> None:
        "Called with the description changes"
        self._bit_field.description = obj.get_text(
            obj.get_start_iter(), obj.get_end_iter(), False
        )

    def _check_data(self) -> None:
        "Checks the input signal validity"
        input_error = False
        output_error = False
        control_error = False

        if not control_error:
            clear_error(self._control_obj)
        if not input_error:
            clear_error(self._input_obj)
        if not output_error:
            clear_error(self._output_obj)

    def _set_active(self, name: str, value: bool) -> None:
        "Set the active flag"
        self._builder.get_object(name).set_active(value)

    def _get_active(self, name: str) -> bool:
        "Get the active flag"
        return self._builder.get_object(name).get_active()

    def _set_text(self, name: str, value: str) -> None:
        "Set the text"
        self._builder.get_object(name).set_text(value)

    def _build_values_list(self) -> None:
        """
        Builds the columns associated with the list view
        """
        self._col = build_column("Value", 0, 50, self._change_val)
        self._value_obj.append_column(self._col)

        self._value_obj.append_column(
            build_column("Token", 1, 100, self._change_text)
        )

        self._value_obj.append_column(
            build_column("Description", 2, 0, self.change_description)
        )

        self.value_model = Gtk.ListStore(str, str, str)
        self.model_selection = self._value_obj.get_selection()
        self._value_obj.set_model(self.value_model)

        self.used_tokens = set()
        for value in self._bit_field.values:
            self.used_tokens.add(value.token)
            self.value_model.append(
                row=(str(value.value), value.token, value.description)
            )

    def _change_text(self, _text, path, new_text):
        """
        Updates the data model when the text value is changed in the model.
        """
        if new_text in self.used_tokens:
            ErrorMsg(
                "Duplicate token",
                f'The token "{new_text}" has already been used',
                parent=self._parent,
            )
        else:
            node = self.value_model.get_iter(path)
            old_text = self.value_model.get_value(node, 1)
            self.value_model.set_value(node, 1, new_text)

            if old_text and old_text in self.used_tokens:
                self.used_tokens.remove(old_text)
            if new_text:
                self.used_tokens.add(new_text)
            self._update_values()
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
                parent=self._parent,
            )
        self.value_model.set_value(node, 2, new_text)
        self._update_values()
        self.modified()

    def _change_val(self, _text, path, new_text):
        """
        Called with the value has changed value field. Checks to make sure that
        value is a valid hex value, and within the correct range.
        """
        new_text = new_text.strip()

        start = self._bit_field.lsb
        stop = self._bit_field.msb.resolve()
        maxval = (2 ** (stop - start + 1)) - 1

        try:
            if new_text == "" or int(new_text, 16) > maxval:
                return
        except ValueError:
            return

        node = self.value_model.get_iter(path)
        self.value_model.set_value(node, 0, new_text)
        self._update_values()
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
