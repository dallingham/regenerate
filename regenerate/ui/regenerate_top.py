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
regenerate

   regenerate is a program for managing the registers in the design. It allows
   you to build a database describing the registers, which can then be used
   to generate documenation, Verilog RTL descriptions, and support files.

"""

import gtk
import gobject
import pango
import xml
import os
import copy
import re
import string
import logging
from preferences import Preferences
from bit_list import BitModel, BitList, bits, reset_value
from register_list import RegisterModel, RegisterList, build_define
from instance_list import InstanceModel, InstanceList
from regenerate.db import (RegWriter, RegisterDb, Register,
                           BitField, RegProject, LOGGER, TYPES)
from columns import EditableColumn, ToggleColumn, ComboMapColumn
from regenerate.importers import IMPORTERS
from regenerate.settings.paths import GLADE_TOP, INSTALL_PATH
from regenerate.settings import ini
from regenerate import PROGRAM_VERSION, PROGRAM_NAME
from error_dialogs import ErrorMsg, WarnMsg, Question
from project import ProjectModel, ProjectList, update_file
from spell import Spell
from preview_editor import PreviewEditor, PREVIEW_ENABLED

TYPE_ENB = {}
for i in TYPES:
    TYPE_ENB[i.type] = (i.input, i.control)


DEF_EXT = '.rprj'
DEF_MIME = "*" + DEF_EXT

ADDR_FIELD = 1
NAME_FIELD = 2
TOKEN_FIELD = 3

(AM_NAME, AM_ADDR, AM_FIXED, AM_WIDTH) = range(4)

# Regular expressions to check the validity of entered names. This should
# probably be configurable, but has not been implemented yet.

VALID_SIGNAL = re.compile("^[A-Za-z][A-Za-z0-9_]*$")
VALID_BITS = re.compile("^\s*[\(\[]?(\d+)(\s*[-:]\s*(\d+))?[\)\]]?\s*$")
REGNAME = re.compile("^(.*)(\d+)(.*)$")

SIZE2STR = (
    ("32-bits", 4),
    ("64-bits", 8),
    )

INT2SIZE = {
    4: "32-bits",
    8: "64-bits",
    }

STR2SIZE = {
    "32-bits" : 4,
    "64-bits" : 8,
    }


class StatusHandler(logging.Handler):  # Inherit from logging.Handler

    def __init__(self, status_obj):
        logging.Handler.__init__(self)
        self.status_obj = status_obj
        self.status_id = status_obj.get_context_id(__name__)
        self.timer = None

    def emit(self, record):
        idval = self.status_obj.push(self.status_id, record.getMessage())
        gobject.timeout_add(15 * 1000, self._clear, idval)

    def _clear(self, idval):
        self.status_obj.remove(self.status_id, idval)


class DbaseStatus(object):
    """
    Holds the state of a particular database. This includes the database model,
    the list models for the displays, the modified status, and the selected
    rows in the models.
    """

    def __init__(self, db, filename, name, reg_model, modelsort,
                 modelfilter, bit_model):
        self.db = db
        self.path = filename
        self.reg_model = reg_model
        self.modelfilter = modelfilter
        self.modelsort = modelsort
        self.bit_field_list = bit_model
        self.name = name
        self.modified = False
        self.reg_select = None
        self.bit_select = None
        self.node = None


class MainWindow(object):
    """
    Main window of the Regenerate program
    """

    def __init__(self):

        self.__model_search_fields = (ADDR_FIELD, NAME_FIELD, TOKEN_FIELD)
        self.__project = None
        self.__builder = gtk.Builder()
        self.__builder.add_from_file(GLADE_TOP)
        self.__build_actions()
        self.__top_window = self.__builder.get_object("regenerate")
        try:
            self.__top_window.set_icon_from_file(
                os.path.join(INSTALL_PATH, "media", "flop.svg"))
        except:
            self.__top_window.set_icon_from_file(
                os.path.join(INSTALL_PATH, "media", "flop.png"))
        self.__status_obj = self.__builder.get_object("statusbar")
        LOGGER.addHandler(StatusHandler(self.__status_obj))
        self.__reg_text_buf = self.__builder.get_object("register_text_buffer")

        self.__filter = self.__builder.get_object("filter")
        self.__filter.connect('changed', self.__filter_changed)
        self.__selected_dbase = self.__builder.get_object("selected_dbase")

        pango_font = pango.FontDescription("monospace")
        self.__builder.get_object('overview').modify_font(pango_font)

        self.__overview_buf = self.__builder.get_object('overview_buffer')
        self.__overview_buf.connect('changed', self.__overview_changed)
        Spell(self.__builder.get_object('overview'))

        self.__prj_obj = ProjectList(self.__builder.get_object("project_list"),
                                     self.__prj_selection_changed)
        self.__module_notebook = self.__builder.get_object("module_notebook")
        self.__reg_notebook = self.__builder.get_object("reg_notebook")
        self.__no_rtl = self.__builder.get_object('no_rtl')
        self.__no_test = self.__builder.get_object('no_test')
        self.__hide = self.__builder.get_object('hide_doc')
        self.__module_entry_obj = self.__builder.get_object('module')
        self.__owner_entry_obj = self.__builder.get_object('owner')
        self.__title_entry_obj = self.__builder.get_object('title')
        self.__warn_bit_list = self.__builder.get_object('reg_bit_warn')
        self.__warn_reg_descr = self.__builder.get_object('reg_descr_warn')
        self.__preview_toggle = self.__builder.get_object('preview')


        self.build_project_tab()

        self.__filter_text = ""

        self.__reglist_obj = RegisterList(
            self.__builder.get_object("register_list"),
            self.__selected_reg_changed, self.set_modified,
            self.update_register_addr)

        self.use_svn = bool(int(ini.get('user', 'use_svn', 0)))
        self.use_preview = bool(int(ini.get('user', 'use_preview', 0)))

        self.__project_preview = PreviewEditor(
            self.__builder.get_object('project_doc').get_buffer(),
            self.__builder.get_object('project_webkit'))
        self.__regset_preview = PreviewEditor(
            self.__builder.get_object('overview_buffer'),
            self.__builder.get_object('scroll_webkit'))
        self.__regdescr_preview = PreviewEditor(
            self.__builder.get_object('register_text_buffer'),
            self.__builder.get_object('scroll_reg_webkit'))

        self.__filename = None
        self.__modified = False

        self.__skip_changes = False
        self.__loading_project = False
        self.active = None
        self.dbase = None
        self.__reg_model = None
        self.__bit_model = None
        self.__modelfilter = None
        self.__modelsort = None
        self.__instance_model = None

        self.__reg_text_buf.connect('changed', self.__reg_description_changed)
        self.__reg_descript = self.__builder.get_object('register_description')
        self.__reg_descript.modify_font(pango_font)
        Spell(self.__reg_descript)

        self.__prj_model = ProjectModel(self.use_svn)
        self.__prj_obj.set_model(self.__prj_model)

        self.__bitfield_obj = BitList(
            self.__builder.get_object("bitfield_list"), self.__bit_combo_edit,
            self.__bit_text_edit, self.__bit_changed)

        self.__recent_manager = gtk.recent_manager_get_default()
        recent_file_menu = self.__create_recent_menu_item()
        self.__builder.get_object('file_menu').insert(recent_file_menu, 2)

        recent_open_btn = self.__create_recent_menu()
        self.__builder.get_object("open_btn").set_menu(recent_open_btn)

        self.__clk_entry_obj = self.__builder.get_object('clock_signal')
        self.__rst_entry_obj = self.__builder.get_object('reset_signal')
        self.__rst_lvl_obj = self.__builder.get_object('reset_level')
        self.__write_data_obj = self.__builder.get_object('write_data_bus')
        self.__read_data_obj = self.__builder.get_object('read_data_bus')
        self.__write_strobe_obj = self.__builder.get_object('write_strobe')
        self.__ack_obj = self.__builder.get_object('ack')
        self.__read_strobe_obj = self.__builder.get_object('read_strobe')
        self.__byte_en_obj = self.__builder.get_object('byte_en_signal')
        self.__address_bus_obj = self.__builder.get_object('address_bus')
        self.__address_width_obj = self.__builder.get_object('address_width')
        self.__data_width_obj = self.__builder.get_object('data_width')
        self.__byte_level_obj = self.__builder.get_object('byte_en_level')

        self.__instance_obj = InstanceList(
            self.__builder.get_object('instances'),
            self.__instance_id_changed,
            self.__instance_base_changed,
            self.__instance_repeat_changed,
            self.__instance_repeat_offset_changed)

        self.__build_data_width_box()
        self.__restore_position_and_size()
        self.__preview_toggle.set_active(self.use_preview)
        if self.use_preview:
            self.__enable_preview()
        self.__top_window.show()
        self.__builder.connect_signals(self)
        self.__build_import_menu()

    def build_project_tab(self):
        self.__project_short_name_obj = self.__builder.get_object('short_name')
        self.__project_name_obj = self.__builder.get_object('project_name')
        self.__project_company_name_obj = self.__builder.get_object('company_name')

        self.__addr_map_tree_obj = self.__builder.get_object('address_tree')
        self.__addr_map_model = gtk.ListStore(str, str, bool, str)
        self.__addr_map_tree_obj.set_model(self.__addr_map_model)

        self.__map_name_column = EditableColumn('Map Name', self.map_name_changed, AM_NAME)
        self.__map_name_column.set_min_width(240)
        self.__addr_map_tree_obj.append_column(self.__map_name_column)

        column = EditableColumn('Base Address', self.map_address_changed, AM_ADDR)
        column.set_min_width(250)
        self.__addr_map_tree_obj.append_column(column)

        column = ComboMapColumn('Access Width', self.map_width_changed,
                                SIZE2STR, AM_WIDTH)
        column.set_min_width(250)
        self.__addr_map_tree_obj.append_column(column)

        column = ToggleColumn('Fixed Address', self.map_fixed_changed, AM_FIXED)
        column.set_max_width(200)
        self.__addr_map_tree_obj.append_column(column)

    def load_project_tab(self):
        self.__project_short_name_obj.set_text(self.__project.short_name)
        self.__project_name_obj.set_text(self.__project.name)
        company = self.__project.company_name
        self.__project_company_name_obj.set_text(company)

        self.__addr_map_model.clear()
        i = 0
        for base in self.__project.get_address_maps():
            addr = self.__project.get_address_base(base)
            width = self.__project.get_address_width(base)
            fixed = bool(self.__project.get_address_fixed(base))

            data = (base, "%x" % addr, fixed, INT2SIZE[width])
            n = self.__addr_map_model.append(row=data)
            i=i+1

        self.__project.clear_modified()

    def map_name_changed(self, cell, path, new_text, col):
        node = self.__addr_map_model.get_iter(path)
        name = self.__addr_map_model.get_value(node, AM_NAME)
        value = self.__addr_map_model.get_value(node, AM_ADDR)
        fixed = self.__addr_map_model.get_value(node, AM_FIXED)
        width = STR2SIZE[self.__addr_map_model.get_value(node, AM_WIDTH)]
        try:
            self.__project.remove_address_map(name)
        except:
            pass
        self.__project.set_address_map(new_text, int(value, 16), width, fixed)
        self.__addr_map_model[path][AM_NAME] = new_text
        self.__project.set_modified()

    def map_fixed_changed(self, cell, path, source):
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """
        node = self.__addr_map_model.get_iter(path)
        name = self.__addr_map_model.get_value(node, AM_NAME)
        value = self.__addr_map_model.get_value(node, AM_ADDR)
        fixed = self.__addr_map_model.get_value(node, AM_FIXED)
        width = self.__addr_map_model.get_value(node, AM_WIDTH)
        self.__addr_map_model[path][AM_FIXED] = not self.__addr_map_model[path][AM_FIXED]
        self.__project.set_address_map(name, int(value, 16), STR2SIZE[width], not fixed)

    def map_width_changed(self, cell, path, node, col):
        """
        Called with the modified toggle is changed. Toggles the value in
        the internal list.
        """
        node = self.__addr_map_model.get_iter(path)
        name = self.__addr_map_model.get_value(node, AM_NAME)
        value = self.__addr_map_model.get_value(node, AM_ADDR)
        fixed = self.__addr_map_model.get_value(node, AM_FIXED)

        model = cell.get_property('model')
        self.__addr_map_model[path][col] = model[path][0]
        width = model[path][1]
        self.__project.set_address_map(name, int(value, 16), width, fixed)

    def map_address_changed(self, cell, path, new_text, col):
        try:
            value = int(new_text, 16)
        except ValueError:
            pass
        if new_text:
            node = self.__addr_map_model.get_iter(path)
            name = self.__addr_map_model.get_value(node, AM_NAME)
            fixed = self.__addr_map_model.get_value(node, AM_FIXED)
            width = STR2SIZE[self.__addr_map_model.get_value(node, AM_WIDTH)]

            self.__project.set_address_map(name, value, width, fixed)
            self.__addr_map_model[path][AM_ADDR] = new_text
            self.__project.set_modified()

    def on_addr_map_help_clicked(self, obj):
        from help_window import HelpWindow

        HelpWindow(self.__builder, "addr_map_help.rst")

    def on_group_help_clicked(self, obj):
        from help_window import HelpWindow

        HelpWindow(self.__builder, "project_group_help.rst")

    def on_remove_map_clicked(self, obj):
        (model, node) = self.__addr_map_tree_obj.get_selection().get_selected()
        name = model.get_value(node, AM_NAME)
        model.remove(node)
        self.__project.set_modified()
        self.__project.remove_address_map(name)

    def on_add_map_clicked(self, obj):
        node = self.__addr_map_model.append(row=("NewMap", 0, False, SIZE2STR[0][0]))
        path = self.__addr_map_model.get_path(node)
        self.__project.set_modified()
        self.__project.set_address_map('NewMap', 0, False, SIZE2STR[0][1])
        self.__addr_map_tree_obj.set_cursor(path, focus_column=self.__map_name_column,
                                            start_editing=True)

    def on_project_name_changed(self, obj):
        """
        Callback function from glade to handle changes in the project name.
        When the name is changed, it is immediately updated in the project
        object.
        """
        self.__project.set_modified()
        self.__project.name = obj.get_text()

    def on_company_name_changed(self, obj):
        """
        Callback function from glade to handle changes in the company name.
        When the name is changed, it is immediately updated in the project
        object.
        """
        self.__project.set_modified()
        self.__project.company_name = obj.get_text()

    def on_offset_insert_text(self, obj, new_text, pos, *extra):
        try:
            int(new_text, 16)
        except ValueError:
            obj.stop_emission('insert-text')

    def on_short_name_changed(self, obj):
        """
        Callback function from glade to handle changes in the short name.
        When the name is changed, it is immediately updated in the project
        object. The name must not have spaces, so we immediately replace any
        spaces.
        """
        self.__project.short_name = obj.get_text().replace(' ', '').strip()
        self.__project.set_modified()
        obj.set_text(self.__project.short_name)

    def __restore_position_and_size(self):
        "Restore the desired position and size from the user's config file"

        height = int(ini.get('user', 'height', 0))
        width = int(ini.get('user', 'width', 0))
        vpos = int(ini.get('user', 'vpos', 0))
        hpos = int(ini.get('user', 'hpos', 0))
        if height and width:
            self.__top_window.resize(width, height)
        if vpos:
            self.__builder.get_object('vpaned').set_position(vpos)
        if hpos:
            self.__builder.get_object('hpaned').set_position(hpos)

    def __filter_changed(self, obj):
        self.__filter_text = self.__filter.get_text()
        self.__modelfilter.refilter()

    def __enable_registers(self, value):
        """
        Enables UI items when a database has been loaded. This includes
        enabling the register window, the register related buttons, and
        the export menu.
        """
        self.__module_notebook.set_sensitive(value)
        self.__database_selected.set_sensitive(value)

    def __enable_bit_fields(self, value):
        """
        Enables UI registers when a register has been selected. This allows
        bit fields to be edited, along with other register related items.
        """
        self.__reg_notebook(value)

    def __build_group(self, group_name, action_names):
        group = gtk.ActionGroup(group_name)
        for name in action_names:
            group.add_action(self.__builder.get_object(name))
        group.set_sensitive(False)
        return group

    def __build_actions(self):
        """
        Builds the action groups. These groups are used to control which
        buttons/functions are active at any given time. The groups are:

        project_loaded    - A project has been loaded.
        reg_selected      - A register is selected, so register operations are
                            valid
        database_selected - A database is selected, so registers can be added,
                            checked, etc.
        field_selected    - A bit field is selected, so a field can be removed
                            or edited.
        """

        project_actions = ["save_project_action", "new_set_action",
                           "add_set_action", "build_action",
                           "reg_grouping_action", "project_prop_action" ]
        if PREVIEW_ENABLED:
            project_actions.append("preview_action")
        else:
            self.__build_group("unused", ["preview_action"])

        self.__project_loaded = self.__build_group("project_loaded",
                                                   project_actions)

        self.__reg_selected = self.__build_group("reg_selected",
                                                 ['remove_register_action',
                                                  'duplicate_register_action',
                                                  'summary_action',
                                                  'add_bit_action'])

        self.__database_selected = self.__build_group("database_selected",
                                                      ['add_register_action',
                                                       'remove_set_action',
                                                       'import_action'])

        self.__field_selected = self.__build_group("field_selected",
                                                      ['remove_bit_action',
                                                       'edit_bit_action'])

        self.__svn_selected = self.__build_group("svn_enabled",
                                                 ['update_svn',
                                                  'revert_svn'])

        self.__file_modified = self.__build_group("file_modified",
                                                  ['revert_action'])

    def __build_data_width_box(self):
        """
        Builds the option menu for the bit width descriptor. Glade no longer
        allows us to set the values in the glade file, but this allows us to
        set a more descriptive text along with a numerical value. We can select
        the active entry, and extract the actual value from the ListStore. The
        first column of the ListStore is displayed, and the second value is
        the numerical value.
        """
        store = gtk.ListStore(str, int)
        store.append(row=["32 bits", 32])
        store.append(row=["64 bits", 64])
        self.__data_width_obj.set_model(store)
        cell = gtk.CellRendererText()
        self.__data_width_obj.pack_start(cell, True)
        self.__data_width_obj.add_attribute(cell, 'text', 0)

    def __bit_combo_edit(self, cell, path, node, col):
        """
        The callback function that occurs whenever a combo entry is altered
        in the BitList. The 'col' value tells us which column was selected,
        and the path tells us the row. So [path][col] is the index into the
        table.
        """
        model = cell.get_property('model')
        self.__bit_model[path][col] = model.get_value(node, 0)
        field = self.__bit_model.get_bitfield_at_path(path)
        if col == BitModel.TYPE_COL:
            field.field_type = model.get_value(node, 1)
            register = self.__reglist_obj.get_selected_register()
            if not field.output_signal:
                field.output_signal = "%s_%s" % (register.token,
                                                 field.field_name)

            if TYPE_ENB[field.field_type][0] and not field.input_signal:
                field.input_signal = "%s_%s_IN" % (register.token,
                                                   field.field_name)

            if TYPE_ENB[field.field_type][1] and not field.control_signal:
                field.control_signal = "%s_%s_LD" % (register.token,
                                                     field.field_name)
        elif col == BitModel.RESET_TYPE_COL:
            field.reset_type = model.get_value(node, 1)
            if field.reset_type == BitField.RESET_NUMERIC:
                val = reset_value(field)
                self.__bit_model[path][BitModel.RESET_COL] = val
            elif field.reset_type == BitField.RESET_INPUT:
                self.__bit_model[path][BitModel.RESET_COL] = field.reset_input
            else:
                self.__bit_model[path][BitModel.RESET_COL] = field.reset_parameter

        self.set_modified()

    def __bit_update_bits(self, field, path, new_text):
        """
        Called when the bits column of the BitList is edited. If the new text
        does not match a valid bit combination (determined by the VALID_BITS
        regular expression, then we do not modifiy the ListStore, which
        prevents the display from being altered. If it does match, we extract
        the start or start and stop positions, and alter the model and the
        corresponding field.
        """
        match = VALID_BITS.match(new_text)
        if match:
            groups = match.groups()
            if groups[2]:
                stop = int(groups[0])
                start = int(groups[2])
                if (stop != field.stop_position or
                    start != field.start_position):
                    field.stop_position = stop
                    field.start_position = start
                    self.set_modified()
            else:
                start = int(groups[0])
                if (start != field.stop_position or
                    start != field.start_position):
                    field.stop_position = start
                    field.start_position = start
                    self.set_modified()
            self.__bit_model[path][BitModel.BIT_COL] = bits(field)
            self.__bit_model[path][BitModel.SORT_COL] = field.start_position

    def __bit_update_name(self, field, path, new_text):
        """
        Called when the bits name of the BitList is edited. If the new text
        is different from the stored value, we alter the model (to change the
        display) and alter the corresponding field.
        """
        if new_text != field.field_name:
            new_text = new_text.upper().replace(' ', '_')
            field.field_name = new_text.replace('/', '_').replace('-', '_')
            self.__bit_model[path][BitModel.NAME_COL] = field.field_name
            self.set_modified()

    def __bit_update_reset(self, field, path, new_text):
        """
        Called when the reset value of the BitList is edited. If the new text
        is different from the stored value, we alter the model (to change the
        display) and alter the corresponding field.
        """
        if field.reset_type == BitField.RESET_NUMERIC:
            try:
                field.reset_value = int(new_text, 16)
                self.__bit_model[path][BitModel.RESET_COL] = reset_value(field)
                self.set_modified()
            except ValueError:
                return
        elif field.reset_type == BitField.RESET_INPUT:
            field.reset_input = new_text
            self.__bit_model[path][BitModel.RESET_COL] = field.reset_input
            self.set_modified()
        else:
            field.reset_parameter = new_text
            self.__bit_model[path][BitModel.RESET_COL] = field.reset_parameter
            self.set_modified()

    def __bit_text_edit(self, cell, path, new_text, col):
        """
        Primary callback when a text field is edited in the BitList. Based off
        the column, we pass it to a function to handle the data.
        """
        field = self.__bit_model.get_bitfield_at_path(path)
        if col == BitModel.BIT_COL:
            self.__bit_update_bits(field, path, new_text)
        elif col == BitModel.NAME_COL:
            self.__bit_update_name(field, path, new_text)
        elif col == BitModel.RESET_COL:
            self.__bit_update_reset(field, path, new_text)

    def __instance_id_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__instance_model.change_id(path, new_text)
        self.__set_module_definition_warn_flag()
        self.__project.set_modified()

    def __instance_base_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__instance_model.change_base(path, new_text)
        self.__set_module_definition_warn_flag()
        self.__project.set_modified()

    def __instance_repeat_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        if len(path) > 1:
            self.__instance_model.change_repeat(path, new_text)
            self.__set_module_definition_warn_flag()
            self.__project.set_modified()

    def __instance_repeat_offset_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        if len(path) > 1:
            self.__instance_model.change_repeat_offset(path, new_text)
            self.__set_module_definition_warn_flag()
            self.__project.set_modified()

    def on_filter_icon_press(self, obj, icon, event):
        if icon == gtk.ENTRY_ICON_SECONDARY:
            if event.type == gtk.gdk.BUTTON_PRESS:
                obj.set_text("")
        elif icon == gtk.ENTRY_ICON_PRIMARY:
            if event.type == gtk.gdk.BUTTON_PRESS:
                menu = self.__builder.get_object("filter_menu")
                menu.popup(None, None, None, 1, 0)

    def on_address_token_name_toggled(self, obj):
        if obj.get_active():
            self.__model_search_fields = (ADDR_FIELD, NAME_FIELD, TOKEN_FIELD)
            self.__modelfilter.refilter()

    def on_token_name_toggled(self, obj):
        if obj.get_active():
            self.__model_search_fields = (NAME_FIELD, TOKEN_FIELD)
            self.__modelfilter.refilter()

    def on_token_toggled(self, obj):
        if obj.get_active():
            self.__model_search_fields = (TOKEN_FIELD, )
            self.__modelfilter.refilter()

    def on_address_toggled(self, obj):
        if obj.get_active():
            self.__model_search_fields = (ADDR_FIELD, )
            self.__modelfilter.refilter()

    def on_name_toggled(self, obj):
        if obj.get_active():
            self.__model_search_fields = (NAME_FIELD, )
            self.__modelfilter.refilter()

    def __enable_preview(self):
        self.__project_preview.enable()
        self.__regset_preview.enable()
        self.__regdescr_preview.enable()

    def __disable_preview(self):
        self.__project_preview.disable()
        self.__regset_preview.disable()
        self.__regdescr_preview.disable()

    def on_preview_toggled(self, obj):
        if obj.get_active():
            self.__enable_preview()
            self.use_preview = True
        else:
            self.__disable_preview()
            self.use_preview = False

    def on_summary_action_activate(self, obj):
        """
        """
        reg = self.__reglist_obj.get_selected_register()

        if reg:
            from summary_window import SummaryWindow
            SummaryWindow(self.__builder, reg)

    def on_build_action_activate(self, obj):
        from build import Build

        dbmap = {}
        for item in self.__prj_model:
            name = item[ProjectModel.NAME]
            modified = item[ProjectModel.MODIFIED]
            obj = item[ProjectModel.OBJ]
            dbmap[name] = (obj, modified)
        Build(self.__project, dbmap)

    def on_revert_svn_activate(self, obj):
        pass

    def on_project_list_button_press_event(self, obj, event):
        if event.button == 3:
            menu = self.__builder.get_object("svn_prj_menu")
            menu.popup(None, None, None, 1, 0)

    def on_update_svn_activate(self, obj):
        (store, node) = self.__prj_obj.get_selected()
        if node and store[node][ProjectModel.OOD]:
            filename = store[node][ProjectModel.FILE]

            idval = self.__status_obj.get_context_id('mod')
            self.__status_obj.push(idval, "Updating %s from SVN" % filename)
            self.set_busy_cursor(True)
            update_file(filename)
            self.__input_xml(filename)
            store[node][ProjectModel.FILE] = self.dbase
            store[node][ProjectModel.MODIFIED] = False
            store[node][ProjectModel.OOD] = False
            store[node][ProjectModel.ICON] = ""
            self.__status_obj.pop(idval)
            self.set_busy_cursor(False)

    def on_revert_action_activate(self, obj):
        (store, node) = self.__prj_obj.get_selected()
        if node and store[node][ProjectModel.MODIFIED]:
            filename = store[node][ProjectModel.FILE]

            self.set_busy_cursor(True)
            self.__input_xml(filename)
            store[node][ProjectModel.FILE] = self.dbase
            store[node][ProjectModel.MODIFIED] = False
            store[node][ProjectModel.OOD] = False
            store[node][ProjectModel.ICON] = ""
            self.set_busy_cursor(False)
            self.__file_modified.set_sensitive(False)

    def on_project_properties_activate(self, obj):
        Properties(self.__project)

    def on_user_preferences_activate(self, obj):
        Preferences()

    def on_delete_instance_clicked(self, obj):
        """
        Called with the remove button is clicked
        """
        selected = self.__instance_obj.get_selected_instance()
        if selected and selected[1]:
            self.__instance_model.remove(selected[1])
            self.__set_module_definition_warn_flag()
            self.__project.set_modified()

    def  on_add_instance_clicked(self, obj):
        self.__instance_obj.new_instance()
        self.__set_module_definition_warn_flag()
        self.__project.set_modified()

    def __data_changed(self, obj):
        """
        Typically attached to the 'changed' callback of ui widgets to
        keep track of changes in the interface.
        """
        self.set_modified()

    def on_address_width_insert_text(self, obj, new_text, pos, *extra):
        try:
            int(new_text)
        except ValueError:
            obj.stop_emission('insert-text')

    def __build_import_menu(self):
        """
        Builds the export menu from the items in writers.IMPORTERS. The export
        menu is extracted from the glade description, the submenu is built,
        and added to the export menu.
        """
        menu = self.__builder.get_object('import_menu')
        submenu = gtk.Menu()
        menu.set_submenu(submenu)
        for item in IMPORTERS:
            menu_item = gtk.MenuItem(label=item[1])
            menu_item.connect('activate', self.__import_data, item)
            menu_item.show()
            submenu.append(menu_item)
        submenu.show()
        menu.set_submenu(submenu)

    def on_notebook_switch_page(self, obj, page, page_num):
        if self.__reglist_obj.get_selected_register():
            self.__reg_selected.set_sensitive(page_num == 0)
        else:
            self.__reg_selected.set_sensitive(False)

    def __bit_changed(self, obj):
        if self.__bitfield_obj.get_selected_row():
            self.__field_selected.set_sensitive(True)
        else:
            self.__field_selected.set_sensitive(False)

    def __prj_selection_changed(self, obj):
        data = self.__prj_obj.get_selected()
        old_skip = self.__skip_changes
        self.__skip_changes = True
        if (data):
            (store, node) = data
            if self.active:
                self.active.reg_select = self.__reglist_obj.get_selected_row()
                self.active.bit_select = self.__bitfield_obj.get_selected_row()

            if node:
                self.active = store.get_value(node, ProjectModel.OBJ)
                row = store[node]
                self.__svn_selected.set_sensitive(row[ProjectModel.OOD])
                self.__file_modified.set_sensitive(row[ProjectModel.MODIFIED])
                self.dbase = self.active.db
                self.__reg_model = self.active.reg_model
                self.__modelfilter = self.active.modelfilter
                self.__modelsort = self.active.modelsort
                self.__reglist_obj.set_model(self.__modelsort)
                self.__bit_model = self.active.bit_field_list
                self.__bitfield_obj.set_model(self.__bit_model)
                text = "<b>%s - %s</b>" % (self.dbase.module_name,
                                           self.dbase.descriptive_title)
                self.__selected_dbase.set_text(text)
                self.__selected_dbase.set_use_markup(True)
                self.__selected_dbase.set_ellipsize(pango.ELLIPSIZE_END)
                if self.active.reg_select:
                    for row in self.active.reg_select:
                        self.__reglist_obj.select_row(row)
                if self.active.bit_select:
                    for row in self.active.bit_select:
                        self.__bitfield_obj.select_row(row)
                self.redraw()
                self.__enable_registers(True)
            else:
                self.active = None
                self.dbase = None
                self.__selected_dbase.set_text("")
                self.__svn_selected.set_sensitive(False)
                self.__reglist_obj.set_model(None)
                self.__enable_registers(False)
        else:
            self.__enable_registers(False)
            self.__svn_selected.set_sensitive(False)
        self.__skip_changes = old_skip

    def __selected_reg_changed(self, obj):
        """
        GTK callback that checks the selected objects, and then enables the
        appropriate buttons on the interface.
        """
        old_skip = self.__skip_changes
        self.__skip_changes = True
        reg = self.__reglist_obj.get_selected_register()
        if reg:
            self.__bit_model.clear()
            for key in reg.get_bit_field_keys():
                field = reg.get_bit_field(key)
                self.__bit_model.append_field(field)
            self.__reg_text_buf.set_text(reg.description)
            self.__reg_text_buf.set_modified(False)
            self.__no_rtl.set_active(reg.do_not_generate_code)
            self.__no_test.set_active(reg.do_not_test)
            self.__hide.set_active(reg.hide)
            self.__reg_notebook.set_sensitive(True)
            self.__reg_selected.set_sensitive(True)  # FIXME
            self.__set_register_warn_flags(reg)
            self.__set_bits_warn_flag()
        else:
            if self.__bit_model:
                self.__bit_model.clear()
            self.__reg_text_buf.set_text("")
            self.__reg_notebook.set_sensitive(False)
            self.__reg_selected.set_sensitive(False)
        self.__skip_changes = old_skip

    def __reg_description_changed(self, obj):
        reg = self.__reglist_obj.get_selected_register()
        if reg:
            reg.description = self.__reg_text_buf.get_text(
                self.__reg_text_buf.get_start_iter(),
                self.__reg_text_buf.get_end_iter())
            self.set_modified()
            self.__set_register_warn_flags(reg)

    def set_modified(self):
        """
        Indicates that the database has been modified. The modified
        value is set, and the status bar is updated with an appropriate
        message.
        """
        if (self.active and not self.active.modified and
            not self.__skip_changes):
            self.active.modified = True
            self.__prj_model.set_markup(self.active.node, True)
            self.__file_modified.set_sensitive(True)

    def clear_modified(self, prj=None):
        """
        Clears the modified tag in the status bar.
        """
        if prj == None:
            prj = self.active
        self.__modified = False
        if prj:
            self.__prj_model.set_markup(prj.node, False)

    def on_add_bit_action_activate(self, obj):
        register = self.__reglist_obj.get_selected_register()
        field = BitField()
        field.start_position = register.find_next_unused_bit()
        field.stop_position = field.start_position
        register.add_bit_field(field)
        self.__bitfield_obj.add_new_field(field)
        self.set_modified()
        self.__set_register_warn_flags(register)

    def on_edit_field_clicked(self, obj):
        register = self.__reglist_obj.get_selected_register()
        field = self.__bitfield_obj.select_field()
        if field:
            from bitfield_editor import BitFieldEditor
            BitFieldEditor(self.dbase, register, field,
                           self.__set_field_modified)

    def __set_field_modified(self):
        reg = self.__reglist_obj.get_selected_register()
        self.__set_register_warn_flags(reg)
        self.__set_bits_warn_flag()
        self.set_modified()

    def on_remove_bit_action_activate(self, obj):
        register = self.__reglist_obj.get_selected_register()
        row = self.__bitfield_obj.get_selected_row()
        field = self.__bit_model.get_bitfield_at_path(row[0])
        register.delete_bit_field(field)
        node = self.__bit_model.get_iter(row[0])
        self.__bit_model.remove(node)
        self.__set_register_warn_flags(register)
        self.set_modified()

    def __insert_new_register(self, register):
        self.__reglist_obj.add_new_register(register)
        self.dbase.add_register(register)
        self.__set_register_warn_flags(register)
        self.set_modified()

    def update_register_addr(self, register, new_addr):
        self.dbase.delete_register(register)
        register.address = new_addr
        self.dbase.add_register(register)

    def on_duplicate_register_action_activate(self, obj):
        """
        Makes a copy of the current register, modifying the address, and
        changing name and token
        """
        reg = self.__reglist_obj.get_selected_register()
        if reg:
            reg_copy = duplicate_register(self.dbase, reg)
            self.__insert_new_register(reg_copy)
            self.__set_register_warn_flags(reg_copy)

    def __create_file_selector(self, title, m_name, m_regex, action, icon):
        """
        Creates a file save selector, using the mime type and regular
        expression to control the selector.
        """
        choose = gtk.FileChooserDialog(
            title, self.__top_window, action,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, icon, gtk.RESPONSE_OK))
        if m_name:
            # Always add automatic (match all files) filter
            mime_filter = gtk.FileFilter()
            mime_filter.set_name(m_name)
            mime_filter.add_pattern(m_regex)
            choose.add_filter(mime_filter)
        choose.show()
        return choose

    def __create_save_selector(self, title, mime_name=None, mime_regex=None):
        """
        Creates a file save selector, using the mime type and regular
        expression to control the selector.
        """
        return self.__create_file_selector(
            title, mime_name, mime_regex, gtk.FILE_CHOOSER_ACTION_SAVE,
            gtk.STOCK_SAVE)

    def __create_open_selector(self, title, mime_name=None, mime_regex=None):
        """
        Creates a file save selector, using the mime type and regular
        expression to control the selector.
        """
        return self.__create_file_selector(
            title, mime_name, mime_regex, gtk.FILE_CHOOSER_ACTION_OPEN,
            gtk.STOCK_OPEN)

    def on_add_register_set_activate(self, obj):
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        choose = self.__create_open_selector("Open Register Database",
                                             'XML files', '*.xml')
        choose.set_select_multiple(True)
        response = choose.run()
        if response == gtk.RESPONSE_OK:
            for filename in choose.get_filenames():
                self.open_xml(filename)
                self.__project.add_register_set(filename)
            self.__prj_model.load_icons()
        choose.destroy()

    def on_remove_register_set_activate(self, obj):
        """
        GTK callback that creates a file open selector using the
        create_selector method, then runs the dialog, and calls the
        open_xml routine with the result.
        """
        data = self.__prj_obj.get_selected()
        old_skip = self.__skip_changes
        self.__skip_changes = True
        if data:
            (store, node) = data
            filename = store.get_value(node, ProjectModel.FILE)
            store.remove(node)
            self.__project.remove_register_set(filename)
        self.__skip_changes = old_skip

    def get_new_filename(self):
        """
        Opens up a file selector, and returns the selected file. The
        selected file is added to the recent manager.
        """
        name = None
        choose = gtk.FileChooserDialog(
            "New", self.__top_window, gtk.FILE_CHOOSER_ACTION_SAVE,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE,
             gtk.RESPONSE_OK))
        choose.show()

        response = choose.run()
        if response == gtk.RESPONSE_OK:
            name = choose.get_filename()
        choose.destroy()
        return name

    def on_new_project_clicked(self, obj):
        choose = self.__create_save_selector(
            "New Project", "Regenerate Project", DEF_MIME)
        response = choose.run()
        if response == gtk.RESPONSE_OK:
            filename = choose.get_filename()
            ext = os.path.splitext(filename)
            if ext[1] != DEF_EXT:
                filename = filename + DEF_EXT

            self.__project = RegProject()
            self.__project.path = filename
            self.__initialize_project_address_maps()
            base_name = os.path.basename(filename)
            self.__project.name = os.path.splitext(base_name)[0]
            self.__prj_model = ProjectModel(self.use_svn)
            self.__prj_obj.set_model(self.__prj_model)
            self.__project.save()
            if self.__recent_manager:
                self.__recent_manager.add_item("file://" + filename)
            self.__builder.get_object('save_btn').set_sensitive(True)
            self.__project_loaded.set_sensitive(True)
            self.load_project_tab()
        choose.destroy()

    def on_open_action_activate(self, obj):
        choose = self.__create_open_selector(
            "Open Project", "Regenerate Project", DEF_MIME)
        response = choose.run()
        filename = choose.get_filename()
        uri = choose.get_uri()
        choose.destroy()
        if response == gtk.RESPONSE_OK:
            self.open_project(filename, uri)

    def set_busy_cursor(self, value):
        """
        This seems to cause Windows to hang, so don't change the cursor
        to indicate busy under Windows.
        """
        if os.name == 'posix':
            if value:
                cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
                self.__top_window.window.set_cursor(cursor)
            else:
                self.__top_window.window.set_cursor(None)
            while gtk.events_pending():
                gtk.main_iteration()

    def open_project(self, filename, uri):
        self.__loading_project = True
        self.__prj_model = ProjectModel(self.use_svn)
        self.__prj_obj.set_model(self.__prj_model)
        self.__project = RegProject(filename)
        self.__initialize_project_address_maps()

        ini.set("user", "last_project", filename)
        idval = self.__status_obj.get_context_id('mod')
        self.__status_obj.push(idval, "Loading %s ..." % filename)
        self.set_busy_cursor(True)
        for f in self.__project.get_register_set():
            self.open_xml(f, False)
        self.__loading_project = False
        self.__prj_obj.select_path(0)
        self.__prj_model.load_icons()
        if self.__recent_manager and uri:
            self.__recent_manager.add_item(uri)
        self.__builder.get_object('save_btn').set_sensitive(True)
        self.set_busy_cursor(False)
        base = os.path.splitext(os.path.basename(filename))[0]
        self.__top_window.set_title("%s (%s) - regenerate" %
                                    (base, self.__project.name))
        self.__status_obj.pop(idval)
        self.load_project_tab()
        self.__project_loaded.set_sensitive(True)

    def __initialize_project_address_maps(self):
        self.__instance_model = InstanceModel()
        self.__instance_obj.set_model(self.__instance_model)
        self.__instance_obj.set_project(self.__project)

    def on_new_register_set_activate(self, obj):
        """
        Creates a new database, and initializes the interface.
        """
        name = self.get_new_filename()
        if not name:
            return

        (base, ext) = os.path.splitext(os.path.basename(name))
        if ext != ".xml":
            name = name + ".xml"

        self.dbase = RegisterDb()
        self.dbase.module_name = base
        self.__reg_model = RegisterModel()
        self.__modelfilter = self.__reg_model.filter_new()
        self.__modelsort = gtk.TreeModelSort(self.__modelfilter)
        self.__modelfilter.set_visible_func(self.visible_cb)
        self.__reglist_obj.set_model(self.__modelsort)

        self.__bit_model = BitModel()
        self.__bitfield_obj.set_model(self.__bit_model)

        self.__set_module_definition_warn_flag()

        self.active = DbaseStatus(self.dbase, name, base, self.__reg_model,
                                  self.__modelsort, self.__modelfilter,
                                  self.__bit_model)
        self.active.node = self.__prj_model.add_dbase(name, self.active)
        self.__prj_obj.select(self.active.node)
        self.redraw()

        self.__prj_model.load_icons()
        self.__project.add_register_set(name)

        self.__module_notebook.set_sensitive(True)
        self.__set_module_definition_warn_flag()
        self.clear_modified()

    def visible_cb(self, model, iter):
        if self.__filter_text == "":
            return True
        else:
            text = self.__filter_text.upper()
            try:
                for i in self.__model_search_fields:
                    if model.get_value(iter, i).upper().find(text) != -1:
                        return True
                return False
            except:
                LOGGER.error("Error filtering")

    def __input_xml(self, name, load=True):
        self.__skip_changes = True
        self.dbase = RegisterDb()
        self.__load_database(name)
        if not os.access(name, os.W_OK):
            WarnMsg("Read only file",
                    'You will not be able to save this file unless\n'
                    'you change permissions.')

        self.__reg_model = RegisterModel()
        self.__modelfilter = self.__reg_model.filter_new()
        self.__modelsort = gtk.TreeModelSort(self.__modelfilter)
        self.__modelfilter.set_visible_func(self.visible_cb)
        self.__bit_model = BitModel()

        if load:
            self.__reglist_obj.set_model(self.__modelsort)
            self.__bitfield_obj.set_model(self.__bit_model)

        self.__update_display()
        self.clear_modified()

    def __update_display(self):

        if self.__reg_model:
            self.__reg_model.clear()
            for key in self.dbase.get_keys():
                register = self.dbase.get_register(key)
                self.__reg_model.append_register(register)
                self.__set_register_warn_flags(register)
        self.redraw()
        self.__skip_changes = False

    def open_xml(self, name, load=True):
        """
        Opens the specified XML file, parsing the data and building the
        internal RegisterDb data structure.
        """
        if name:
            try:
                self.__input_xml(name, load)
            except IOError, msg:
                ErrorMsg("Could not load existing register set", str(msg))
            base = os.path.splitext(os.path.basename(name))[0]
            self.active = DbaseStatus(self.dbase, name, base, self.__reg_model,
                                      self.__modelsort,
                                      self.__modelfilter,
                                      self.__bit_model)

            self.active.node = self.__prj_model.add_dbase(name, self.active)
            if load:
                self.__prj_obj.select(self.active.node)
                self.__module_notebook.set_sensitive(True)
        self.__set_module_definition_warn_flag()

    def __load_database(self, filename):
        """
        Reads the specified XML file, and redraws the screen.
        """
        try:
            self.dbase.read_xml(filename)
            self.__filename = filename
        except xml.parsers.expat.ExpatError, msg:
            ErrorMsg("Not a valid regenerate file", str(msg))

    def on_save_clicked(self, obj):
        """
        Called with the save button is clicked (gtk callback). Saves the
        database.
        """
        for item in self.__prj_model:
            if item[ProjectModel.MODIFIED]:
                try:
                    writer = RegWriter(item[ProjectModel.OBJ].db)
                    writer.save(item[ProjectModel.OBJ].path)
                    self.clear_modified(item[ProjectModel.OBJ])
                except IOError, msg:
                    ErrorMsg("Could not save database", str(msg))

        self.__project.set_new_order([item[0] for item in self.__prj_model])
        (grps, gmap) = self.__instance_obj.get_groups()
        self.__project.set_grouping_list(grps)
        self.__project.set_grouping_map(gmap)
        self.__project.save()
        self.active.modified = False

    def __exit(self):
        """
        Save the window size, along with the positions of the paned windows,
        then exit.
        """
        (width, height) = self.__top_window.get_size()
        ini.set('user', 'use_preview', int(self.use_preview))
        ini.set('user', 'width', width)
        ini.set('user', 'height', height)
        ini.set('user', 'vpos',
                self.__builder.get_object('vpaned').get_position())
        ini.set('user', 'hpos',
                self.__builder.get_object('hpaned').get_position())
        gtk.main_quit()

    def __save_and_quit(self):
        """
        Saves the database and quits. If the filename does not exist, prompt
        for a filename.
        """
        self.on_save_clicked(None)
        self.__exit()

    def on_save_as_clicked(self, obj):
        """
        Called when the Save As button is clicked. Clears the filename first
        so that the user is prompted for a filename.
        """
        self.__filename = None
        self.on_save_clicked(obj)

    def __import_data(self, obj, data):
        """
        Imports the data using the specified data importer.
        """
        choose = self.__create_open_selector(data[1][1], data[2],
                                             "*" + data[3])
        response = choose.run()
        if response == gtk.RESPONSE_OK:
            filename = choose.get_filename()
            if filename:
                self.__import_using_importer(filename, data[0])
        choose.destroy()

    def __import_using_importer(self, name, importer_class):
        """
        Saves the file using the specified writer class.
        """
        importer = importer_class(self.dbase)
        try:
            importer.import_data(name)
            self.__update_display()
            self.set_modified()
        except IOError, msg:
            ErrorMsg("Could not create %s " % name, str(msg))

    def redraw(self):
        """
        Redraws the information in the register list.
        """
        self.__module_entry_obj.set_text(self.dbase.module_name)
        self.__owner_entry_obj.set_text(self.dbase.owner)
        self.__title_entry_obj.set_text(self.dbase.descriptive_title)
        self.__data_width_obj.set_active((self.dbase.data_bus_width / 32) - 1)

        self.__overview_buf.set_text(self.dbase.overview_text)
        self.__overview_buf.set_modified(False)

        self.__clk_entry_obj.set_text(self.dbase.clock_name)
        self.__rst_entry_obj.set_text(self.dbase.reset_name)
        self.__rst_lvl_obj.set_active(self.dbase.reset_active_level)

        self.__write_data_obj.set_text(self.dbase.write_data_name)
        self.__read_data_obj.set_text(self.dbase.read_data_name)
        self.__write_strobe_obj.set_text(self.dbase.write_strobe_name)
        self.__ack_obj.set_text(self.dbase.acknowledge_name)
        self.__read_strobe_obj.set_text(self.dbase.read_strobe_name)
        self.__byte_en_obj.set_text(self.dbase.byte_strobe_name)

        self.__address_bus_obj.set_text(self.dbase.address_bus_name)
        self.__address_width_obj.set_text(str(self.dbase.address_bus_width))
        self.__data_width_obj.set_active(self.dbase.data_bus_width != 32)
        self.__byte_level_obj.set_active(self.dbase.byte_strobe_active_level)

        self.__set_description_warn_flag()
        self.__set_module_definition_warn_flag()

    def __overview_changed(self, obj):
        self.dbase.overview_text = obj.get_text(obj.get_start_iter(),
                                                obj.get_end_iter())
        self.__set_description_warn_flag()
        self.set_modified()

    def on_regenerate_delete_event(self, obj, event):
        self.on_quit_activate(obj)

    def on_quit_activate(self, *obj):
        """
        Called when the quit button is clicked.  Checks to see if the
        data needs to be saved first.
        """
        if (self.__modified or self.__prj_model.is_not_saved() or
            (self.__project and self.__project.is_not_saved())):
            dialog = Question('Save Changes?',
                              "The file has been modified. "
                              "Do you want to save your changes?")
            status = dialog.run()
            if status == Question.DISCARD:
                self.__exit()
            elif status == Question.SAVE:
                self.__save_and_quit()
            dialog.destroy()
        else:
            self.__exit()
        return True

    def on_remove_register_action_activate(self, obj):
        """
        Deletes the selected object (either a register or a bit range)
        """
        reg = self.__reglist_obj.get_selected_register()
        if reg:
            self.__reglist_obj.delete_selected_node()
            self.dbase.delete_register(reg)
            self.set_modified()

    def on_data_width_changed(self, obj):
        if obj.get_active():
            self.dbase.data_bus_width = 64
        else:
            self.dbase.data_bus_width = 32
        self.set_modified()

    def on_byte_en_level_toggled(self, obj):
        self.dbase.byte_strobe_active_level = obj.get_active()
        self.set_modified()

    def on_reset_level_toggled(self, obj):
        self.dbase.reset_active_level = obj.get_active()
        self.set_modified()

    def on_address_bus_changed(self, obj):
        self.dbase.address_bus_name = obj.get_text()
        self.__set_module_ports_warn_flag()
        self.set_modified()

    def on_address_width_changed(self, obj):
        try:
            new_width = int(obj.get_text())
            self.dbase.address_bus_width = new_width
            self.set_modified()
        except ValueError:
            pass  # keep old value

    def on_write_strobe_changed(self, obj):
        self.dbase.write_strobe_name = obj.get_text()
        self.__set_module_ports_warn_flag()
        self.set_modified()

    def on_ack_changed(self, obj):
        self.dbase.acknowledge_name = obj.get_text()
        self.__set_module_ports_warn_flag()
        self.set_modified()

    def on_read_strobe_changed(self, obj):
        self.dbase.read_strobe_name = obj.get_text()
        self.__set_module_ports_warn_flag()
        self.set_modified()

    def on_byte_en_signal_changed(self, obj):
        self.dbase.byte_strobe_name = obj.get_text()
        self.__set_module_ports_warn_flag()
        self.set_modified()

    def on_read_data_bus_changed(self, obj):
        self.dbase.read_data_name = obj.get_text()
        self.__set_module_ports_warn_flag()
        self.set_modified()

    def on_reset_signal_changed(self, obj):
        self.dbase.reset_name = obj.get_text()
        self.__set_module_ports_warn_flag()
        self.set_modified()

    def on_write_data_bus_changed(self, obj):
        self.dbase.write_data_name = obj.get_text()
        self.__set_module_ports_warn_flag()
        self.set_modified()

    def on_clock_signal_changed(self, obj):
        self.dbase.clock_name = obj.get_text()
        self.__set_module_ports_warn_flag()
        self.set_modified()

    def on_module_changed(self, obj):
        self.__check_signal(obj, "Invalid module name")
        self.dbase.module_name = obj.get_text()
        self.__set_module_definition_warn_flag()
        self.set_modified()

    def on_owner_changed(self, obj):
        self.dbase.owner = obj.get_text()
        self.set_modified()

    def on_title_changed(self, obj):
        self.dbase.descriptive_title = obj.get_text()
        self.__set_module_definition_warn_flag()
        self.set_modified()

    def on_no_rtl_toggled(self, obj):
        reg = self.__reglist_obj.get_selected_register()
        if reg:
            reg.do_not_generate_code = obj.get_active()
            self.set_modified()

    def on_no_test_toggled(self, obj):
        reg = self.__reglist_obj.get_selected_register()
        if reg:
            reg.do_not_test = obj.get_active()
            self.set_modified()

    def on_hide_doc_toggled(self, obj):
        reg = self.__reglist_obj.get_selected_register()
        if reg:
            reg.hide = obj.get_active()
            self.set_modified()

    def on_add_register_action_activate(self, obj):
        """
        Adds a new register, seeding the address with the next available
        address
        """
        register = Register()
        register.address = calculate_next_address(self.dbase)
        self.__insert_new_register(register)

    def __cb_open_recent(self, chooser):
        """
        Called when a file is chosen from the open recent dialog
        """
        recent_item = chooser.get_current_item()
        fname = recent_item.get_uri()
        if recent_item.exists():
            self.open_project(fname.replace('file://', ''), fname)

    def __create_recent_menu_item(self):
        """
        Builds the recent menu, applying the filter
        """
        recent_menu = gtk.RecentChooserMenu()
        recent_menu.set_show_not_found(False)
        recent_menu.set_show_numbers(True)
        recent_menu.connect("item-activated", self.__cb_open_recent)

        recent_menu_item = gtk.MenuItem('Open Recent')
        recent_menu_item.set_submenu(recent_menu)

        filt = gtk.RecentFilter()
        filt.add_pattern(DEF_MIME)
        recent_menu.set_filter(filt)
        recent_menu_item.show()
        return recent_menu_item

    def __create_recent_menu(self):
        """
        Builds the recent menu, applying the filter
        """
        recent_menu = gtk.RecentChooserMenu()
        recent_menu.set_show_not_found(False)
        recent_menu.set_show_numbers(True)
        recent_menu.connect("item-activated", self.__cb_open_recent)

        filt = gtk.RecentFilter()
        filt.add_pattern(DEF_MIME)
        recent_menu.set_filter(filt)
        return recent_menu

    def on_about_activate(self, obj):
        """
        Displays the About box, describing the program
        """
        box = gtk.AboutDialog()
        box.set_name(PROGRAM_NAME)
        box.set_version(PROGRAM_VERSION)
        box.set_comments(
            "%s allows you to manage your\n"
            "registers for an ASIC or FPGA based design." % PROGRAM_NAME)
        box.set_authors(['Donald N. Allingham'])
        try:
            data = file(os.path.join(INSTALL_PATH, "LICENSE.txt")).read()
            box.set_license(data)
        except IOError:
            pass
        box.set_logo(gtk.gdk.pixbuf_new_from_file(
                os.path.join(INSTALL_PATH, "media", "flop.svg")))
        box.run()
        box.destroy()

    def __check_signal(self, obj, message):
        match = VALID_SIGNAL.match(obj.get_text())
        if match:
            obj.set_property('secondary-icon-stock', None)
            obj.set_property('secondary-icon-tooltip-text', '')
            return True
        else:
            obj.set_property('secondary-icon-stock', gtk.STOCK_DIALOG_ERROR)
            obj.set_property('secondary-icon-tooltip-text', message)
            return False

    def __set_register_warn_flags(self, reg, mark=True):
        warn_reg = warn_bit = False
        msg = []
        if not reg.description:
            warn_reg = True
            msg.append("Missing register description")
        if not reg.get_bit_fields():
            warn_bit = True
            msg.append("No bit fields exist for the register")
        else:
            for key in reg.get_bit_field_keys():
                field = reg.get_bit_field(key)
                if check_field(field):
                    txt = "Missing field description for '%s'" % \
                          field.field_name
                    if field.start_position == field.stop_position:
                        txt = txt + " (bit %d)" % field.start_position
                    else:
                        txt = txt + "(bits [%d:%d])" \
                              % (field.stop_position, field.start_position)
                    msg.append(txt)
                    warn_bit = True
        if mark and not self.__loading_project:
            self.__warn_reg_descr.set_property('visible', warn_reg)
            self.__warn_bit_list.set_property('visible', warn_bit)
        self.__reg_model.set_warning_for_register(reg, warn_reg or warn_bit)
        if msg:
            tip = "\n".join(msg)
        else:
            tip = None
        self.__reg_model.set_tooltip(reg, tip)

    def __set_description_warn_flag(self):
        if not self.__loading_project:
            warn = self.dbase.overview_text == ""
            self.__builder.get_object('mod_descr_warn').set_property('visible',
                                                                     warn)

    def __set_module_definition_warn_flag(self):
        if not self.__loading_project:
            warn = False
            msgs = []

            if self.dbase.descriptive_title == "":
                warn = True
                msgs.append("No title was provided for the register set.")
            if self.dbase.module_name == "":
                warn = True
                msgs.append("No module name was provided.")
            icon = self.__builder.get_object('mod_def_warn')
            icon.set_property('visible', warn)
            icon.set_tooltip_text("\n".join(msgs))

    def __set_bits_warn_flag(self):
        warn = False
        for row in self.__bit_model:
            field = row[BitModel.FIELD_COL]
            icon = check_field(field)
            row[BitModel.ICON_COL] = icon
            if icon:
                warn = True
        return warn

    def __set_module_ports_warn_flag(self):
        data = (
            (self.__clk_entry_obj, "clock"),
            (self.__rst_entry_obj, "reset"),
            (self.__write_data_obj, "write data"),
            (self.__read_data_obj, "read data"),
            (self.__byte_en_obj, "byte enables"),
            (self.__write_strobe_obj, "write strobe"),
            (self.__ack_obj, "acknowledge"),
            (self.__address_bus_obj, "address bus"))

        if not self.__loading_project:
            warn = False
            msgs = []
            for (obj, name) in data:
                if not self.__check_signal(obj, "Illegal signal name"):
                    warn = True
                    msgs.append("Illegal signal for %s" % name)
            icon = self.__builder.get_object('mod_port_warn')
            icon.set_property('visible', warn)
            icon.set_tooltip_text("\n".join(msgs))


def clean_ascii(value):
    return value if value in string.printable else " "


def build_new_name(name, reglist):
    match = REGNAME.match(name)
    if match:
        groups = match.groups()
        index = int(groups[1]) + 1
        while "".join([groups[0], str(index), groups[2]]) in reglist:
            index += 1
        return "".join([groups[0], str(index), groups[2]])
    else:
        return None


def build_signal_set(dbase):
    """
    Builds a set of all input, output and control signal name in
    the database.
    """
    signal_list = set()
    for reg in [dbase.get_register(key) for key in dbase.get_keys()]:
        for key in reg.get_bit_field_keys():
            field = reg.get_bit_field(key)
            if field.input_signal:
                signal_list.add(field.input_signal)
            if field.output_signal:
                signal_list.add(field.output_signal)
            if field.control_signal:
                signal_list.add(field.control_signal)
    return signal_list


def calculate_next_address(dbase):
    """
    Calculates the next address based on the last address that was
    used.
    """
    keys = dbase.get_keys()
    keys.sort()
    if keys:
        last_reg = dbase.get_register(keys[-1])
        addr = last_reg.address + last_reg.width / 8
    else:
        addr = 0
    return addr


def signal_from_source(source_name, existing_list):
    """
    Builds a copy of a signal name. The existing list contains the names
    that have already been used. The build_new_name is calleded to try to
    derive a name based on the passed, looking to replace numerical values
    embedded in the name. If none is found, then _COPY is appended.
    """
    if source_name:
        signal = build_new_name(source_name, existing_list)
        if signal:
            return signal
        else:
            return source_name + "_COPY"
    else:
        return ""


def duplicate_register(dbase, reg):
    """
    Returns a new register which is a dupilcate of the original register,
    changing the register description, signals, and token based on the original
    register.
    """
    reglist = set([dbase.get_register(key).register_name
                   for key in dbase.get_keys()])
    deflist = set([dbase.get_register(key).token for key in dbase.get_keys()])
    signals = build_signal_set(dbase)

    new_name = build_new_name(reg.register_name, reglist)
    if not new_name:
        new_name = reg.register_name + " Copy"

    def_name = build_new_name(reg.token, deflist)
    if not def_name:
        def_name = build_define(new_name)

    new_reg = copy.deepcopy(reg)

    for key in reg.get_bit_field_keys():
        fld = reg.get_bit_field(key)
        nfld = new_reg.get_bit_field(key)
        nfld.input_signal = signal_from_source(fld.input_signal, signals)
        nfld.output_signal = signal_from_source(fld.output_signal, signals)
        nfld.control_signal = signal_from_source(fld.control_signal, signals)

    new_reg.address = calculate_next_address(dbase)
    new_reg.register_name = new_name
    new_reg.token = def_name
    return new_reg


def check_field(field):
    if field.description:
        return None
    else:
        return gtk.STOCK_DIALOG_WARNING
