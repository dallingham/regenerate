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
   to generate documentation, Verilog RTL descriptions, and support files.

"""

import gtk
import pango
import os
import copy
import re
import sys
import xml
from regenerate import PROGRAM_VERSION, PROGRAM_NAME
from regenerate.db import RegWriter, RegisterDb, Register
from regenerate.db import BitField, RegProject, LOGGER, TYPES
from regenerate.importers import IMPORTERS
from regenerate.settings import ini
from regenerate.settings.paths import GLADE_TOP, INSTALL_PATH
from regenerate.ui.addrmap_list import AddrMapList
from regenerate.ui.base_window import BaseWindow
from regenerate.ui.bit_list import BitModel, BitList, bits, reset_value
from regenerate.ui.error_dialogs import ErrorMsg, WarnMsg, Question
from regenerate.ui.filter_mgr import FilterManager, ADDR_FIELD
from regenerate.ui.filter_mgr import NAME_FIELD, TOKEN_FIELD
from regenerate.ui.help_window import HelpWindow
from regenerate.ui.instance_list import InstMdl, InstanceList
from regenerate.ui.preferences import Preferences
from regenerate.ui.preview_editor import PreviewEditor, PREVIEW_ENABLED
from regenerate.ui.project import ProjectModel, ProjectList, update_file
from regenerate.ui.register_list import RegisterModel, RegisterList, build_define
from regenerate.ui.spell import Spell
from regenerate.ui.status_logger import StatusHandler
from regenerate.ui.utils import clean_format_if_needed
from regenerate.extras.remap import REMAP_NAME

TYPE_ENB = {}
for data_type in TYPES:
    TYPE_ENB[data_type.type] = (data_type.input, data_type.control)

DEF_EXT = '.rprj'
DEF_MIME = "*" + DEF_EXT

# Regular expressions to check the validity of entered names. This should
# probably be configurable, but has not been implemented yet.

VALID_SIGNAL = re.compile("^[A-Za-z][A-Za-z0-9_]*$")
VALID_BITS = re.compile("^\s*[\(\[]?(\d+)(\s*[-:]\s*(\d+))?[\)\]]?\s*$")
REGNAME = re.compile("^(.*)(\d+)(.*)$")


class DbaseStatus(object):
    """
    Holds the state of a particular database. This includes the database model,
    the list models for the displays, the modified status, and the selected
    rows in the models.
    """

    def __init__(self, database, filename, name, reg_model, modelsort,
                 modelfilter, bit_model):
        self.db = database
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


class MainWindow(BaseWindow):
    """
    Main window of the Regenerate program
    """

    def __init__(self):

        BaseWindow.__init__(self)

        self.__prj = None
        self.__builder = gtk.Builder()
        self.__builder.add_from_file(GLADE_TOP)
        self.__build_actions()
        self.__top_window = self.__builder.get_object("regenerate")

        self.configure(self.__top_window)

        self.__status_obj = self.__builder.get_object("statusbar")
        LOGGER.addHandler(StatusHandler(self.__status_obj))
        self.__reg_text_buf = self.__builder.get_object("register_text_buffer")
        self.__selected_dbase = self.__builder.get_object("selected_dbase")

        pango_font = pango.FontDescription("monospace")
        self.__builder.get_object('overview').modify_font(pango_font)
        self.__builder.get_object('project_doc').modify_font(pango_font)

        self.__overview_buf = self.__builder.get_object('overview_buffer')
        self.__overview_buf.connect('changed', self.__overview_changed)
        Spell(self.__builder.get_object('overview'))

        self.__prj_obj = ProjectList(self.__builder.get_object("project_list"),
                                     self.__prj_selection_changed)
        self.__module_notebook = self.__builder.get_object("module_notebook")
        self.__reg_notebook = self.__builder.get_object("reg_notebook")
        self.__top_notebook = self.__builder.get_object("notebook1")
        self.__no_rtl = self.__builder.get_object('no_rtl')
        self.__no_test = self.__builder.get_object('no_test')
        self.__no_cover = self.__builder.get_object('no_cover')
        self.__no_uvm = self.__builder.get_object('no_uvm')
        self.__hide = self.__builder.get_object('hide_doc')
        self.__share_none = self.__builder.get_object('no_sharing')
        self.__share_write = self.__builder.get_object('write_access')
        self.__share_read = self.__builder.get_object('read_access')
        self.__module_entry_obj = self.__builder.get_object('module')
        self.__owner_entry_obj = self.__builder.get_object('owner')
        self.__org_entry_obj = self.__builder.get_object('organization')
        self.__title_entry_obj = self.__builder.get_object('title')
        self.__warn_bit_list = self.__builder.get_object('reg_bit_warn')
        self.__warn_reg_descr = self.__builder.get_object('reg_descr_warn')
        self.__preview_toggle = self.__builder.get_object('preview')

        self.build_project_tab()

        self.__reglist_obj = RegisterList(
            self.__builder.get_object("register_list"),
            self.__selected_reg_changed, self.set_modified,
            self.update_register_addr, self.__set_register_warn_flags)

        self.use_svn = bool(int(ini.get('user', 'use_svn', 0)))
        self.use_preview = bool(int(ini.get('user', 'use_preview', 0)))

        self.__prj_preview = PreviewEditor(
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

        try:
            self.__recent_manager = gtk.recent_manager_get_default()
        except AttributeError:
            self.__recent_manager = gtk.RecentManager.get_default()
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
        self.__interface_obj = self.__builder.get_object('interface')
        self.__ack_obj = self.__builder.get_object('ack')
        self.__read_strobe_obj = self.__builder.get_object('read_strobe')
        self.__byte_en_obj = self.__builder.get_object('byte_en_signal')
        self.__address_bus_obj = self.__builder.get_object('address_bus')
        self.__address_width_obj = self.__builder.get_object('address_width')
        self.__data_width_obj = self.__builder.get_object('data_width')
        self.__array_notation_obj = self.__builder.get_object('array_notation')
        self.__internal_only_obj = self.__builder.get_object('internal_only')
        self.__coverage_obj = self.__builder.get_object('coverage')
        self.__register_notation_obj = self.__builder.get_object(
            'register_notation')
        self.__byte_level_obj = self.__builder.get_object('byte_en_level')

        self.__instance_obj = InstanceList(
            self.__builder.get_object('instances'),
            self.__instance_id_changed,
            self.__instance_inst_changed,
            self.__instance_base_changed,
            self.__instance_repeat_changed,
            self.__instance_repeat_offset_changed,
            self.__instance_format_changed,
            self.__instance_hdl_changed,
            self.__instance_uvm_changed,
            self.__instance_decode_changed,
            self.__instance_array_changed,
            self.__instance_single_decode_changed)

        self.__build_data_width_box()
        self.__restore_position_and_size()
        self.__preview_toggle.set_active(self.use_preview)
        if self.use_preview:
            self.__enable_preview()
        self.__top_window.show()
        self.__builder.connect_signals(self)
        self.__build_import_menu()

        filter_obj = self.__builder.get_object("filter")
        self.__filter_manage = FilterManager(filter_obj)

    def on_instances_cursor_changed(self, obj):
        (mdl, node) = self.__instance_obj.get_selected_instance()
        btn = self.__builder.get_object("instance_edit_btn")
        if node:
            path = mdl.get_path(node)
            if len(path) == 1:
                btn.set_sensitive(True)
            else:
                btn.set_sensitive(False)
        else:
            btn.set_sensitive(False)

    def on_addrmap_cursor_changed(self, obj):
        btn = self.__builder.get_object("edit_map")
        mdl, node = obj.get_selection().get_selected()
        if node:
            path = mdl.get_path(node)
            if len(path) == 1:
                btn.set_sensitive(True)
            else:
                btn.set_sensitive(False)
        else:
            btn.set_sensitive(False)

    def on_group_doc_clicked(self, obj):
        from regenerate.ui.group_doc import GroupDocEditor

        (mdl, node) = self.__instance_obj.get_selected_instance()
        inst = mdl.get_value(node, InstMdl.OBJ_COL)
        if inst:
            GroupDocEditor(inst, self.project_modified)

    def build_project_tab(self):
        self.__prj_short_name_obj = self.__builder.get_object('short_name')
        self.__prj_name_obj = self.__builder.get_object('project_name')
        self.__prj_company_name_obj = self.__builder.get_object('company_name')
        self.__prj_doc_object = self.__builder.get_object('project_doc_buffer')

        self.__addr_map_obj = self.__builder.get_object('address_tree')
        self.__addr_map_list = AddrMapList(self.__addr_map_obj)

    def project_modified(self, value):
        self.__prj.modified = value

    def load_project_tab(self):
        self.__prj_short_name_obj.set_text(self.__prj.short_name)
        self.__prj_doc_object.set_text(self.__prj.documentation)
        self.__prj_name_obj.set_text(self.__prj.name)
        company = self.__prj.company_name
        self.__prj_company_name_obj.set_text(company)
        self.__addr_map_list.set_project(self.__prj)
        self.project_modified(False)

    def on_edit_map_clicked(self, obj):
        from regenerate.ui.addr_edit import AddrMapEdit

        map_name = self.__addr_map_list.get_selected()
        if map_name is None:
            return

        current = self.__prj.get_address_map_groups(map_name)

        new_list = [(grp, grp.name in current)
                    for grp in self.__prj.get_grouping_list()]

        dialog = AddrMapEdit(map_name, new_list, self.__builder, self.__prj)
        new_list = dialog.get_list()
        if new_list is not None:
            self.__prj.set_address_map_group_list(map_name, dialog.get_list())
            self.__addr_map_list.set_project(self.__prj)
            self.project_modified(False)

    def on_addr_map_help_clicked(self, obj):
        HelpWindow(self.__builder, "addr_map_help.rst")

    def on_group_help_clicked(self, obj):
        HelpWindow(self.__builder, "project_group_help.rst")

    def on_remove_map_clicked(self, obj):
        self.project_modified(True)
        self.__addr_map_list.remove_selected()

    def on_add_map_clicked(self, obj):
        self.__addr_map_list.add_new_map()

    def on_help_action_activate(self, obj):
        HelpWindow(self.__builder, "regenerate_help.rst")

    def on_project_name_changed(self, obj):
        """
        Callback function from glade to handle changes in the project name.
        When the name is changed, it is immediately updated in the project
        object.
        """
        self.project_modified(True)
        self.__prj.name = obj.get_text()

    def on_company_name_changed(self, obj):
        """
        Callback function from glade to handle changes in the company name.
        When the name is changed, it is immediately updated in the project
        object.
        """
        self.project_modified(True)
        self.__prj.company_name = obj.get_text()

    def on_offset_insert_text(self, obj, new_text, pos, *extra):
        try:
            int(new_text, 16)
        except ValueError:
            obj.stop_emission('insert-text')

    def on_project_documentation_changed(self, obj):
        self.project_modified(True)
        self.__prj.documentation = obj.get_text(obj.get_start_iter(),
                                                obj.get_end_iter(),
                                                False)

    def on_short_name_changed(self, obj):
        """
        Callback function from glade to handle changes in the short name.
        When the name is changed, it is immediately updated in the project
        object. The name must not have spaces, so we immediately replace any
        spaces.
        """
        self.__prj.short_name = obj.get_text().replace(' ', '').strip()
        self.project_modified(True)
        obj.set_text(self.__prj.short_name)

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

    def __enable_registers(self, value):
        """
        Enables UI items when a database has been loaded. This includes
        enabling the register window, the register related buttons, and
        the export menu.
        """
        self.__module_notebook.set_sensitive(value)
        self.__db_selected.set_sensitive(value)

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

        project_loaded - A project has been loaded.
        reg_selected   - A register is selected, so register operations are
                         valid
        db_selected    - A database is selected, so registers can be added,
                         checked, etc.
        field_selected - A bit field is selected, so a field can be removed
                         or edited.
        """

        prj_acn = ["save_project_action", "new_set_action", "add_set_action",
                   "build_action", "reg_grouping_action",
                   "project_prop_action"]
        reg_acn = ['remove_register_action', 'summary_action',
                   'duplicate_register_action', 'add_bit_action']
        db_acn = ['add_register_action', 'remove_set_action', 'import_action']
        fld_acn = ['remove_bit_action', 'edit_bit_action']
        svn_acn = ['update_svn', 'revert_svn']
        file_acn = ['revert_action']

        if PREVIEW_ENABLED:
            prj_acn.append("preview_action")
        else:
            self.__build_group("unused", ["preview_action"])

        self.__prj_loaded = self.__build_group("project_loaded", prj_acn)
        self.__reg_selected = self.__build_group("reg_selected", reg_acn)
        self.__db_selected = self.__build_group("database_selected", db_acn)
        self.__field_selected = self.__build_group("field_selected", fld_acn)
        self.__svn_selected = self.__build_group("svn_enabled", svn_acn)
        self.__file_modified = self.__build_group("file_modified", file_acn)

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
        for i in (8, 16, 32, 64):
            store.append(row=["{0} bits".format(i), i])

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
            self.__update_type_info(field, model, path, node)
        elif col == BitModel.RESET_TYPE_COL:
            self.__update_reset_field(field, model, path, node)
        self.set_modified()

    def __update_type_info(self, field, model, path, node):
        field.field_type = model.get_value(node, 1)
        register = self.__reglist_obj.get_selected_register()

        if not field.output_signal:
            field.output_signal = "%s_%s" % (register.token, field.field_name)

        if TYPE_ENB[field.field_type][0] and not field.input_signal:
            field.input_signal = "%s_%s_IN" % (
                register.token, field.field_name)

        if TYPE_ENB[field.field_type][1] and not field.control_signal:
            field.control_signal = "%s_%s_LD" % (
                register.token, field.field_name)

    def __update_reset_field(self, field, model, path, node):
        field.reset_type = model.get_value(node, 1)
        if field.reset_type == BitField.RESET_NUMERIC:
            val = reset_value(field)
            self.__bit_model[path][BitModel.RESET_COL] = val
        elif field.reset_type == BitField.RESET_INPUT:
            if not re.match("^[A-Za-z]\w*$", field.reset_input):
                field.reset_input = "%s_RST" % field.field_name
            self.__bit_model[path][BitModel.RESET_COL] = field.reset_input
        else:
            if not re.match("^[A-Za-z]\w*$", field.reset_parameter):
                field.reset_parameter = "pRST_%s" % field.field_name
            self.__bit_model[path][BitModel.RESET_COL] = field.reset_parameter

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
            stop = int(groups[0])

            if groups[2]:
                start = int(groups[2])
            else:
                start = stop

            register = self.__reglist_obj.get_selected_register()
            if stop >= register.width:
                LOGGER.error("Bit position is greater than register width")
                return

            if stop != field.msb or start != field.lsb:
                field.msb, field.lsb = stop, start
                r = self.__reglist_obj.get_selected_register()
                r.change_bit_field(field)
                self.set_modified()

            self.__bit_model[path][BitModel.BIT_COL] = bits(field)
            self.__bit_model[path][BitModel.SORT_COL] = field.start_position

    def dump(self, title):
        r = self.__reglist_obj.get_selected_register()

        print ("----------------------------------------------")
        print (title, r.register_name)

        for f in r.get_bit_fields():
            print ("'%18s' %4d %4d" % (f.field_name, f.msb, f.lsb))
            print ("\t", f)

    def __bit_update_name(self, field, path, new_text):
        """
        Called when the bits name of the BitList is edited. If the new text
        is different from the stored value, we alter the model (to change the
        display) and alter the corresponding field.
        """
        if new_text != field.field_name:
            new_text = new_text.upper().replace(' ', '_')
            new_text = new_text.replace('/', '_').replace('-', '_')

            register = self.__reglist_obj.get_selected_register()

            current_names = [f.field_name for f in register.get_bit_fields()
                             if f != field]

            if new_text not in current_names:
                self.__bit_model[path][BitModel.NAME_COL] = new_text
                field.field_name = new_text
                self.set_modified()
            else:
                LOGGER.error(
                    '"%s" has already been used as a field name' % new_text)

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
                LOGGER.error('Illegal reset value: "%s"' % new_text)
                return
        elif field.reset_type == BitField.RESET_INPUT:
            if not re.match("^[A-Za-z]\w*$", new_text):
                LOGGER.error('"%s" is not a valid input name' % new_text)
                new_text = "%s_RST" % field.field_name
            field.reset_input = new_text
            self.__bit_model[path][BitModel.RESET_COL] = field.reset_input
            self.set_modified()
        else:
            if not re.match("^[A-Za-z]\w*$", new_text):
                LOGGER.error('"%s" is not a valid parameter name' % new_text)
                new_text = "pRST_%s" % field.field_name
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
        register = self.__reglist_obj.get_selected_register()
        self.__set_register_warn_flags(register)

    def __instance_id_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        LOGGER.error("Subsystem name cannot be changed")

    def __inst_changed(self, attr, path, new_text):
        getattr(self.__instance_model, attr)(path, new_text)
        self.__set_module_definition_warn_flag()
        self.project_modified(True)

    def __inst_bool_changed(self, attr, cell, path):
        getattr(self.__instance_model, attr)(cell, path)
        self.__set_module_definition_warn_flag()
        self.project_modified(True)

    def __instance_inst_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__inst_changed("change_inst", path, new_text)

    def __instance_base_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__inst_changed("change_base", path, new_text)

    def __instance_format_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        if len(path) > 1:
            self.__inst_changed("change_format", path, new_text)

    def __instance_hdl_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__inst_changed("change_hdl", path, new_text)

    def __instance_uvm_changed(self, cell, path, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__inst_bool_changed("change_uvm", cell, path)

    def __instance_decode_changed(self, cell, path, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__inst_changed("change_decode", cell, path)

    def __instance_single_decode_changed(self, cell, path, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__inst_changed("change_single_decode", cell, path)

    def __instance_array_changed(self, cell, path, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__inst_changed("change_array", cell, path)

    def __instance_repeat_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__inst_changed("change_repeat", path, new_text)

    def __instance_repeat_offset_changed(self, cell, path, new_text, col):
        """
        Updates the data model when the text value is changed in the model.
        """
        self.__inst_changed("change_repeat_offset", path, new_text)

    def on_filter_icon_press(self, obj, icon, event):
        if icon == gtk.ENTRY_ICON_SECONDARY:
            if event.type == gtk.gdk.BUTTON_PRESS:
                obj.set_text("")
        elif icon == gtk.ENTRY_ICON_PRIMARY:
            if event.type == gtk.gdk.BUTTON_PRESS:
                menu = self.__builder.get_object("filter_menu")
                menu.popup(None, None, None, 1, 0)

    def set_search(self, values, obj):
        if obj.get_active():
            self.__filter_manage.set_search_fields(values)

    def on_address_token_name_toggled(self, obj):
        self.set_search((ADDR_FIELD, NAME_FIELD, TOKEN_FIELD), obj)

    def on_token_name_toggled(self, obj):
        self.set_search((NAME_FIELD, TOKEN_FIELD), obj)

    def on_token_toggled(self, obj):
        self.set_search((TOKEN_FIELD,), obj)

    def on_address_toggled(self, obj):
        self.set_search((ADDR_FIELD,), obj)

    def on_name_toggled(self, obj):
        self.set_search((NAME_FIELD,), obj)

    def __enable_preview(self):
        self.__prj_preview.enable()
        self.__regset_preview.enable()
        self.__regdescr_preview.enable()
        self.use_preview = True

    def __disable_preview(self):
        self.__prj_preview.disable()
        self.__regset_preview.disable()
        self.__regdescr_preview.disable()
        self.use_preview = False

    def on_preview_toggled(self, obj):
        if obj.get_active():
            self.__enable_preview()
        else:
            self.__disable_preview()

    def on_summary_action_activate(self, obj):
        """
        Displays the summary window
        """
        reg = self.__reglist_obj.get_selected_register()

        if reg:
            from regenerate.ui.summary_window import SummaryWindow
            SummaryWindow(self.__builder, reg, self.active.name, self.__prj)

    def on_build_action_activate(self, obj):
        from regenerate.ui.build import Build

        dbmap = {}
        item_list = self.__prj_model
        for item in item_list:
            name = item[ProjectModel.NAME]
            modified = item[ProjectModel.MODIFIED]
            obj = item[ProjectModel.OBJ]
            dbmap[name] = (obj, modified)
        Build(self.__prj, dbmap)

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

    def on_user_preferences_activate(self, obj):
        Preferences()

    def on_delete_instance_clicked(self, obj):
        """
        Called with the remove button is clicked
        """
        selected = self.__instance_obj.get_selected_instance()
        if selected and selected[1]:
            grp = selected[0].get_value(selected[1], InstMdl.OBJ_COL)
            self.__instance_model.remove(selected[1])
            self.__prj.remove_group_from_grouping_list(grp)
            self.__set_module_definition_warn_flag()
            self.project_modified(True)

    def on_add_instance_clicked(self, obj):
        self.__instance_obj.new_instance()
        self.__set_module_definition_warn_flag()
        self.project_modified(True)

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

    def update_bit_count(self):
        if self.dbase:
            text = "%d" % self.dbase.total_bits()
        else:
            text = ""
        self.__builder.get_object('reg_count').set_text(text)

    def on_notebook_switch_page(self, obj, page, page_num):
        if page_num == 1:
            self.update_bit_count()
        if self.__reglist_obj.get_selected_register():
            self.__reg_selected.set_sensitive(page_num == 0)
        else:
            self.__reg_selected.set_sensitive(False)

    def __bit_changed(self, obj):
        active = len(self.__bitfield_obj.get_selected_row())
        self.__field_selected.set_sensitive(active)

    def __prj_selection_changed(self, obj):
        data = self.__prj_obj.get_selected()
        old_skip = self.__skip_changes
        self.__skip_changes = True
        if data:
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

                self.__prj_preview.set_dbase(self.active.db)
                self.__regset_preview.set_dbase(self.active.db)
                self.__regdescr_preview.set_dbase(self.active.db)

                self.__filter_manage.change_filter(self.active.modelfilter)
                self.__modelsort = self.active.modelsort
                self.__reglist_obj.set_model(self.__modelsort)
                self.__bit_model = self.active.bit_field_list
                self.__bitfield_obj.set_model(self.__bit_model)
                text = "<b>%s - %s</b>" % (self.dbase.module_name, self.dbase.
                                           descriptive_title)
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
            self.__bitfield_obj.set_mode(reg.share)
            for key in reg.get_bit_field_keys():
                field = reg.get_bit_field(key)
                self.__bit_model.append_field(field)
            self.__reg_text_buf.set_text(reg.description)
            self.__reg_text_buf.set_modified(False)
            self.__no_rtl.set_active(reg.do_not_generate_code)
            self.__no_uvm.set_active(reg.do_not_use_uvm)
            self.__no_test.set_active(reg.do_not_test)
            self.__no_cover.set_active(reg.do_not_cover)
            self.__hide.set_active(reg.hide)
            self.__reg_notebook.set_sensitive(True)
            self.__reg_selected.set_sensitive(True)
            self.__set_register_warn_flags(reg)
            self.__set_bits_warn_flag()
            self.set_share(reg)
        else:
            if self.__bit_model:
                self.__bit_model.clear()
            self.__reg_text_buf.set_text("")
            self.__reg_notebook.set_sensitive(False)
            self.__reg_selected.set_sensitive(False)
        self.__skip_changes = old_skip

    def set_share(self, reg):
        if reg.share == Register.SHARE_NONE:
            self.__share_none.set_active(True)
        elif reg.share == Register.SHARE_READ:
            self.__share_read.set_active(True)
        else:
            self.__share_write.set_active(True)

    def __reg_description_changed(self, obj):
        reg = self.__reglist_obj.get_selected_register()
        if reg:
            reg.description = self.__reg_text_buf.get_text(
                self.__reg_text_buf.get_start_iter(),
                self.__reg_text_buf.get_end_iter(),
                False)
            self.set_modified()
            self.__set_register_warn_flags(reg)

    def on_register_description_key_press_event(self, obj, event):
        if event.keyval == gtk.keysyms.F12:
            if clean_format_if_needed(obj):
                self.set_modified()
            return True
        return False

    def on_overview_key_press_event(self, obj, event):
        if event.keyval == gtk.keysyms.F12:
            if clean_format_if_needed(obj):
                self.set_modified()
            return True
        return False

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
        self.__modified = False
        if prj is None:
            prj = self.active
        else:
            self.__prj_model.set_markup(prj.node, False)

    def duplicate_address(self, reg_addr):
        cnt = 0
        for reg in self.dbase.get_all_registers():
            if reg.address == reg_addr:
                cnt += 1
        return cnt > 1

    def find_shared_address(self, reg):
        for r in self.dbase.get_all_registers():
            if r != reg and r.address == reg.address:
                return r
        return None

    def on_no_sharing_toggled(self, obj):
        if obj.get_active():
            register = self.__reglist_obj.get_selected_register()

            if self.duplicate_address(register.address):
                self.set_share(register)
                LOGGER.error('Register cannot be set to non-sharing '
                             'if it shares an address with another')
            else:
                register.share = Register.SHARE_NONE
                self.set_modified()
            self.__bitfield_obj.set_mode(register.share)

    def on_read_access_toggled(self, obj):
        if obj.get_active():
            register = self.__reglist_obj.get_selected_register()

            other = self.find_shared_address(register)
            if other and other.share != Register.SHARE_WRITE:
                self.set_share(register)
                LOGGER.error('The shared register is not of Write Access type')
            elif register.is_completely_read_only():
                register.share = Register.SHARE_READ
                self.set_modified()
            else:
                self.set_share(register)
                LOGGER.error('All bits in the register must be read only')
            self.__bitfield_obj.set_mode(register.share)

    def on_write_access_toggled(self, obj):
        if obj.get_active():
            register = self.__reglist_obj.get_selected_register()

            other = self.find_shared_address(register)
            if other and other.share != Register.SHARE_READ:
                self.set_share(register)
                LOGGER.error('The shared register is not of Read Access type')
            elif register.is_completely_write_only():
                register.share = Register.SHARE_WRITE
                self.set_modified()
            else:
                self.set_share(register)
                LOGGER.error('All bits in the register must be write only')
            self.__bitfield_obj.set_mode(register.share)

    def on_add_bit_action_activate(self, obj):
        register = self.__reglist_obj.get_selected_register()
        next_pos = register.find_next_unused_bit()

        if next_pos == -1:
            LOGGER.error("All bits are used in this register")
            return

        field = BitField()
        field.lsb = next_pos

        field.msb = field.lsb
        field.field_name = "BIT%d" % field.lsb
        if register.share == Register.SHARE_WRITE:
            field.field_type = BitField.TYPE_WRITE_ONLY

        register.add_bit_field(field)

        self.__bitfield_obj.add_new_field(field)
        self.set_modified()
        self.__set_register_warn_flags(register)

    def on_edit_field_clicked(self, obj):
        register = self.__reglist_obj.get_selected_register()
        field = self.__bitfield_obj.select_field()
        if field:
            from regenerate.ui.bitfield_editor import BitFieldEditor
            BitFieldEditor(self.dbase, register, field,
                           self.__set_field_modified, self.__builder)

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
        if self.__top_notebook.get_current_page() == 0:
            self.__reglist_obj.add_new_register(register)
            self.dbase.add_register(register)
            self.__set_register_warn_flags(register)
            self.set_modified()

    def update_register_addr(self, register, new_addr, new_length=0):
        self.dbase.delete_register(register)
        register.address = new_addr
        register.ram_size = new_length
        r = self.find_shared_address(register)
        if r:
            if r.share == Register.SHARE_READ:
                register.share = Register.SHARE_WRITE
            else:
                register.share = Register.SHARE_READ
            self.set_share(register)
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
        choose.set_current_folder(os.curdir)
        if m_name:
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
        return self.__create_file_selector(title, mime_name, mime_regex,
                                           gtk.FILE_CHOOSER_ACTION_SAVE,
                                           gtk.STOCK_SAVE)

    def __create_open_selector(self, title, mime_name=None, mime_regex=None):
        """
        Creates a file save selector, using the mime type and regular
        expression to control the selector.
        """
        return self.__create_file_selector(title, mime_name, mime_regex,
                                           gtk.FILE_CHOOSER_ACTION_OPEN,
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
                self.__prj.add_register_set(filename)
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
            self.__prj.remove_register_set(filename)
        self.__skip_changes = old_skip

    def get_new_filename(self):
        """
        Opens up a file selector, and returns the selected file. The
        selected file is added to the recent manager.
        """
        name = None
        choose = gtk.FileChooserDialog("New", self.__top_window,
                                       gtk.FILE_CHOOSER_ACTION_SAVE,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        choose.set_current_folder(os.curdir)
        choose.show()

        response = choose.run()
        if response == gtk.RESPONSE_OK:
            name = choose.get_filename()
        choose.destroy()
        return name

    def on_new_project_clicked(self, obj):
        choose = self.__create_save_selector("New Project",
                                             "Regenerate Project", DEF_MIME)
        response = choose.run()
        if response == gtk.RESPONSE_OK:
            filename = choose.get_filename()
            ext = os.path.splitext(filename)
            if ext[1] != DEF_EXT:
                filename = filename + DEF_EXT

            self.__prj = RegProject()
            self.__prj.path = filename
            self.__initialize_project_address_maps()
            base_name = os.path.basename(filename)
            self.__prj.name = os.path.splitext(base_name)[0]
            self.__prj_model = ProjectModel(self.use_svn)
            self.__prj_obj.set_model(self.__prj_model)
            self.__prj.save()
            if self.__recent_manager:
                self.__recent_manager.add_item("file:///" + filename)
            self.__builder.get_object('save_btn').set_sensitive(True)
            self.__prj_loaded.set_sensitive(True)
            self.load_project_tab()
        choose.destroy()

    def on_open_action_activate(self, obj):
        choose = self.__create_open_selector("Open Project",
                                             "Regenerate Project", DEF_MIME)
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

        try:
            self.__prj = RegProject(filename)
            self.__initialize_project_address_maps()
        except xml.parsers.expat.ExpatError as msg:
            ErrorMsg("%s was not a valid project file" % filename, str(msg))
            return
        except IOError as msg:
            ErrorMsg("Could not open %s" % filename, str(msg))
            return

        ini.set("user", "last_project", filename)
        idval = self.__status_obj.get_context_id('mod')
        self.__status_obj.push(idval, "Loading %s ..." % filename)
        self.set_busy_cursor(True)

        for f in sorted(self.__prj.get_register_set(), key=sort_regset):

            try:
                self.open_xml(f, False)
            except xml.parsers.expat.ExpatError as msg:
                ErrorMsg("%s was not a valid register set file" % f)
                continue

        self.__prj_obj.select_path(0)
        self.__prj_model.load_icons()
        if self.__recent_manager and uri:
            self.__recent_manager.add_item(uri)
        self.__builder.get_object('save_btn').set_sensitive(True)
        self.set_busy_cursor(False)
        base = os.path.splitext(os.path.basename(filename))[0]
        self.__top_window.set_title("%s (%s) - regenerate" %
                                    (base, self.__prj.name))
        self.__status_obj.pop(idval)
        self.load_project_tab()
        self.__prj_loaded.set_sensitive(True)
        self.__loading_project = False
        self.__skip_changes = False

    def __initialize_project_address_maps(self):
        self.__instance_model = InstMdl(self.__prj)
        self.__instance_obj.set_model(self.__instance_model)
        self.__instance_obj.set_project(self.__prj)

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
        mdl = self.__reg_model.filter_new()
        self.__filter_manage.change_filter(mdl, True)
        self.__modelsort = gtk.TreeModelSort(mdl)
        self.__reglist_obj.set_model(self.__modelsort)

        self.__bit_model = BitModel()
        self.__bitfield_obj.set_model(self.__bit_model)

        self.__set_module_definition_warn_flag()

        self.active = DbaseStatus(self.dbase, name, base, self.__reg_model,
                                  self.__modelsort,
                                  self.__filter_manage.get_model(),
                                  self.__bit_model)
        self.active.node = self.__prj_model.add_dbase(name, self.active)
        self.__prj_obj.select(self.active.node)
        self.redraw()

        self.__prj_model.load_icons()
        self.__prj.add_register_set(name)

        self.__module_notebook.set_sensitive(True)
        self.__set_module_definition_warn_flag()
        self.clear_modified()

    def __input_xml(self, name, load=True):
        old_skip = self.__skip_changes
        self.__skip_changes = True
        self.dbase = RegisterDb()
        self.__load_database(name)
        if not os.access(name, os.W_OK):
            WarnMsg("Read only file",
                    'You will not be able to save this file unless\n'
                    'you change permissions.')

        self.__reg_model = RegisterModel()
        mdl = self.__reg_model.filter_new()
        self.__filter_manage.change_filter(mdl, True)
        self.__modelsort = gtk.TreeModelSort(mdl)
        self.__bit_model = BitModel()

        if load:
            self.__reglist_obj.set_model(self.__modelsort)
            self.__bitfield_obj.set_model(self.__bit_model)

        self.__update_display()
        self.clear_modified()
        self.__skip_changes = old_skip

    def __update_display(self):
        old_skip = self.__skip_changes
        self.__skip_changes = True
        if self.__reg_model:
            self.__reg_model.clear()
            for key in self.dbase.get_keys():
                register = self.dbase.get_register(key)
                self.__reg_model.append_register(register)
                self.__set_register_warn_flags(register)
        self.redraw()
        self.__skip_changes = old_skip

    def open_xml(self, name, load=True):
        """
        Opens the specified XML file, parsing the data and building the
        internal RegisterDb data structure.
        """
        if name:
            try:
                self.__input_xml(name, load)
            except IOError as msg:
                ErrorMsg("Could not load existing register set", str(msg))

            base = os.path.splitext(os.path.basename(name))[0]
            self.active = DbaseStatus(self.dbase, name, base, self.__reg_model,
                                      self.__modelsort,
                                      self.__filter_manage.get_model(),
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
        except xml.parsers.expat.ExpatError as msg:
            ErrorMsg("%s is not a valid regenerate file" % filename, str(msg))

    def on_save_clicked(self, obj):
        """
        Called with the save button is clicked (gtk callback). Saves the
        database.
        """
        for item in self.__prj_model:
            if item[ProjectModel.MODIFIED]:
                try:
                    old_path = item[ProjectModel.OBJ].path
                    new_path = "%s.bak" % old_path
                    if os.path.isfile(new_path):
                        os.remove(new_path)
                    if os.path.isfile(old_path):
                        os.rename(old_path, new_path)

                    writer = RegWriter(item[ProjectModel.OBJ].db)
                    writer.save(old_path)
                    self.clear_modified(item[ProjectModel.OBJ])
                except IOError as msg:
                    os.rename(new_path, old_path)
                    ErrorMsg("Could not save %s, restoring original" %
                             old_path, str(msg))
                # except:
                #     os.rename(new_path, old_path)
                #     ErrorMsg("Could not save %s, restoring original" % old_path, "")

        self.__prj.set_new_order([item[0] for item in self.__prj_model])
        self.__instance_obj.get_groups()

        current_path = self.__prj.path
        backup_path = "%s.bak" % current_path

        if os.path.isfile(backup_path):
            os.remove(backup_path)
        if os.path.isfile(current_path):
            os.rename(current_path, backup_path)

        self.__prj.save()
#        try:
#            self.__prj.save()
#        except:
#            os.path.rename(new_path, old_path)
#            ErrorMsg("Could not save %s, restoring original" % current_path, str(msg))

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
            choose.hide()
            while gtk.events_pending():
                gtk.main_iteration()

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
        except IOError as msg:
            ErrorMsg("Could not create %s " % name, str(msg))

    def redraw(self):
        """
        Redraws the information in the register list.
        """
        self.__module_entry_obj.set_text(self.dbase.module_name)
        self.__owner_entry_obj.set_text(self.dbase.owner)
        self.__org_entry_obj.set_text(self.dbase.organization)
        self.__title_entry_obj.set_text(self.dbase.descriptive_title)

        self.__overview_buf.set_text(self.dbase.overview_text)
        self.__overview_buf.set_modified(False)

        self.__clk_entry_obj.set_text(self.dbase.clock_name)
        self.__rst_entry_obj.set_text(self.dbase.reset_name)
        self.__rst_lvl_obj.set_active(self.dbase.reset_active_level)

        self.__write_data_obj.set_text(self.dbase.write_data_name)
        self.__read_data_obj.set_text(self.dbase.read_data_name)
        self.__write_strobe_obj.set_text(self.dbase.write_strobe_name)
        self.__interface_obj.set_active(self.dbase.use_interface)
        self.__ack_obj.set_text(self.dbase.acknowledge_name)
        self.__read_strobe_obj.set_text(self.dbase.read_strobe_name)
        self.__byte_en_obj.set_text(self.dbase.byte_strobe_name)

        self.__address_bus_obj.set_text(self.dbase.address_bus_name)
        self.__address_width_obj.set_text(str(self.dbase.address_bus_width))
        self.__data_width_obj.set_active(bus_index(self.dbase.data_bus_width))
        if self.dbase.array_is_reg:
            self.__register_notation_obj.set_active(True)
        else:
            self.__array_notation_obj.set_active(True)

        self.__internal_only_obj.set_active(self.dbase.internal_only)
        self.__coverage_obj.set_active(self.dbase.coverage)
        self.__byte_level_obj.set_active(self.dbase.byte_strobe_active_level)

        self.update_bit_count()

        self.__set_description_warn_flag()
        self.__set_module_definition_warn_flag()

    def __overview_changed(self, obj):
        self.dbase.overview_text = obj.get_text(obj.get_start_iter(),
                                                obj.get_end_iter(),
                                                False)
        self.__set_description_warn_flag()
        self.set_modified()

    def on_regenerate_delete_event(self, obj, event):
        return self.on_quit_activate(obj)

    def on_quit_activate(self, *obj):
        """
        Called when the quit button is clicked.  Checks to see if the
        data needs to be saved first.
        """
        if (self.__modified or self.__prj_model.is_not_saved() or
                (self.__prj and self.__prj.modified)):
            dialog = Question('Save Changes?', "The file has been modified. "
                              "Do you want to save your changes?")
            status = dialog.run()
            if status == Question.DISCARD:
                self.__exit()
                return False
            elif status == Question.SAVE:
                self.__save_and_quit()
                return False
            dialog.destroy()
            return True
        else:
            self.__exit()
        return True

    def on_remove_register_action_activate(self, obj):
        """
        Deletes the selected object (either a register or a bit range)
        """
        if self.__top_notebook.get_current_page() == 0:
            row = self.__reglist_obj.get_selected_position()
            reg = self.__reglist_obj.get_selected_register()
            if reg:
                self.__reglist_obj.delete_selected_node()
                self.dbase.delete_register(reg)
                self.__reglist_obj.select_row(row)
                self.set_modified()

    def set_db_value(self, attr, val):
        if self.dbase:
            setattr(self.dbase, attr, val)
        self.set_modified()

    def on_array_changed(self, obj):
        self.set_db_value("array_is_reg", not obj.get_active())

    def on_coverage_toggled(self, obj):
        self.set_db_value("coverage", obj.get_active())

    def on_internal_only_changed(self, obj):
        self.set_db_value("internal_only", obj.get_active())

    def on_data_width_changed(self, obj):
        self.set_db_value("data_bus_width", 8 << obj.get_active())

    def on_byte_en_level_toggled(self, obj):
        self.set_db_value("byte_strobe_active_level", obj.get_active())

    def on_reset_level_toggled(self, obj):
        self.set_db_value("reset_active_level", obj.get_active())

    def on_address_width_changed(self, obj):
        try:
            value = int(obj.get_text())
            if value > 64:
                LOGGER.error('Illegal address width: "%s"' % obj.get_text())
            else:
                self.set_db_value("address_bus_width", value)
        except ValueError:
            LOGGER.error('Illegal address width: "%s"' % obj.get_text())

    def __text_change(self, attr, obj):
        if self.dbase:
            setattr(self.dbase, attr, obj.get_text())
            self.__set_module_ports_warn_flag()
            self.set_modified()

    def on_address_bus_changed(self, obj):
        self.__text_change("address_bus_name", obj)

    def on_write_strobe_changed(self, obj):
        self.__text_change("write_strobe_name", obj)

    def on_interface_toggled(self, obj):
        self.dbase.use_interface = obj.get_active()
        self.set_modified()

    def on_ack_changed(self, obj):
        self.__text_change("acknowledge_name", obj)

    def on_read_strobe_changed(self, obj):
        self.__text_change("read_strobe_name", obj)

    def on_byte_en_signal_changed(self, obj):
        self.__text_change("byte_strobe_name", obj)

    def on_read_data_bus_changed(self, obj):
        self.__text_change("read_data_name", obj)

    def on_reset_signal_changed(self, obj):
        self.__text_change("reset_name", obj)

    def on_write_data_bus_changed(self, obj):
        self.__text_change("write_data_name", obj)

    def on_clock_signal_changed(self, obj):
        self.__text_change("clock_name", obj)

    def on_module_changed(self, obj):
        self.__check_signal(obj, "Invalid module name")
        self.__text_change("module_name", obj)

    def on_title_changed(self, obj):
        self.__text_change("descriptive_title", obj)

    def on_owner_changed(self, obj):
        self.dbase.owner = obj.get_text()
        self.set_modified()

    def on_organization_changed(self, obj):
        self.dbase.organization = obj.get_text()
        self.set_modified()

    def __button_toggle(self, attr, obj):
        reg = self.__reglist_obj.get_selected_register()
        if reg:
            setattr(reg, attr, obj.get_active())
            self.set_modified()

    def on_no_rtl_toggled(self, obj):
        self.__button_toggle("do_not_generate_code", obj)

    def on_no_uvm_toggled(self, obj):
        self.__button_toggle("do_not_use_uvm", obj)

    def on_no_test_toggled(self, obj):
        self.__button_toggle("do_not_test", obj)

    def on_no_cover_toggled(self, obj):
        self.__button_toggle("do_not_cover", obj)

    def on_hide_doc_toggled(self, obj):
        self.__button_toggle("hide", obj)

    def on_add_register_action_activate(self, obj):
        """
        Adds a new register, seeding the address with the next available
        address
        """
        register = Register()
        register.width = self.dbase.data_bus_width
        register.address = calculate_next_address(self.dbase)
        self.__insert_new_register(register)

    def __cb_open_recent(self, chooser):
        """
        Called when a file is chosen from the open recent dialog
        """
        recent_item = chooser.get_current_item()
        fname = recent_item.get_uri()
        if recent_item.exists():
            self.open_project(fname.replace('file:///', ''), fname)

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
        fname = os.path.join(INSTALL_PATH, "media", "flop.svg")
        box.set_logo(gtk.gdk.pixbuf_new_from_file(fname))
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
        if reg.token.lower() in REMAP_NAME:
            warn_reg = True
            msg.append("Register name is a SystemVerilog reserved word")
        if not reg.get_bit_fields():
            warn_bit = True
            msg.append("No bit fields exist for the register")
        else:
            for field in reg.get_bit_fields():
                if field.field_name.lower() in REMAP_NAME:
                    txt = "Field name (%s) is a SystemVerilog reserved word" % \
                        field.field_name
                    msg.append(txt)
                if check_field(field):
                    txt = "Missing field description for '%s'" % \
                        field.field_name
                    if field.width == 1:
                        txt = txt + " (bit %d)" % field.lsb
                    else:
                        txt = txt + "(bits [%d:%d])" % (field.msb, field.lsb)
                    msg.append(txt)
                    warn_bit = True
                if check_reset(field):
                    txt = "Missing reset parameter name for '%s'" % \
                        field.field_name
                    if field.lsb == field.msb:
                        txt = txt + " (bit %d)" % field.lsb
                    else:
                        txt = txt + "(bits [%d:%d])" % (field.msb, field.lsb)
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
        data = ((self.__clk_entry_obj, "clock"),
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


def build_new_name(name, reglist):
    match = REGNAME.match(name)
    if match:
        groups = match.groups()
        index = int(groups[1]) + 1
        while "".join([groups[0], str(index), groups[2]]) in reglist:
            index += 1
        return "".join([groups[0], str(index), groups[2]])
    else:
        index = 2
        while "%s %d" % (name, index) in reglist:
            index += 1
        return "%s %d" % (name, index)


def build_signal_set(dbase):
    """
    Builds a set of all input, output and control signal name in
    the database.
    """
    signal_list = set()
    for reg in dbase.get_all_registers():
        for field in reg.get_bit_fields():
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
    if keys:
        last_reg = dbase.get_register(keys[-1])
        dim = max(last_reg.dimension, 1)
        addr = last_reg.address + (dim * (last_reg.width / 8))
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

    def_name = build_new_name(reg.token, deflist)
    if not def_name:
        def_name = build_define(new_name)

    new_reg = copy.deepcopy(reg)
    # force the generation of a new UUID
    new_reg.uuid = ""

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
    if field.description.strip() == "":
        return gtk.STOCK_DIALOG_WARNING
    return None


def check_reset(field):
    if (field.reset_type == BitField.RESET_PARAMETER and
            field.reset_parameter.strip() == ""):
        return gtk.STOCK_DIALOG_WARNING
    return None


def sort_regset(x):
    return os.path.basename(x)


def bus_index(value):
    if value == 8:
        return 0
    elif value == 16:
        return 1
    elif value == 32:
        return 2
    else:
        return 3
