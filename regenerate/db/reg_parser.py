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
Parses the register database, loading the database.
"""

import xml.parsers.expat

from register import Register
from regenerate.db import BitField, TYPES, BFT_TYPE, BFT_ID

CONVERT_TYPE = {}
for i in TYPES:
    CONVERT_TYPE[i[BFT_ID]] = i[BFT_TYPE]

def cnv_hex(attrs, key, default=0):
    """
    Looks for the key in the attrs array, converting the returned value to
    a hex value if it exists, otherwise it returns the default value.
    """
    try:
        return int(attrs[key], 16)
    except:
        return default


def cnv_int(attrs, key, default=0):
    """
    Looks for the key in the attrs array, converting the returned value to
    an integer if it exists, otherwise it returns the default value.
    """
    try:
        return int(attrs.get(key))
    except:
        return default


def cnv_bool(attrs, key, default=False):
    """
    Looks for the key in the attrs array, converting the returned value to
    a boolean value if it exists, otherwise it returns the default value.
    """
    try:
        return bool(int(attrs[key]))
    except:
        return default


def cnv_str(attrs, key, default=""):
    """
    Looks for the key in the attrs array, returning the string if it exists,
    otherwise it returns the default value.
    """
    return attrs.get(key, default)


def set_modified(obj, attrs):
    """
    Looks for the 'modified'in the attrs array, converting the string to an
    integer if it exists, and assigning it to the objects last_modified
    property
    """
    if 'modified' in attrs:
        obj.last_modified = int(attrs['modified'])


class RegParser(object):
    """
    Parses the XML file, loading up the register database.
    """

    def __init__(self, dbase):
        self.__db = dbase
        self.__reg = None
        self.__field = None
        self.__in_ports = False
        self.__current_val = 0
        self.__current_token = ''
        self.__reset_type = 0
        self.__reset_parameter = ""
        self.__token_list = []
        self.save_id = None

    def parse(self, input_file):
        """
        Parses the specified input file.
        """
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.characters
        parser.ParseFile(input_file)

    def start_element(self, tag, attrs):
        """
        Called every time an XML element begins
        """
        self.__token_list = []
        mname = 'start_' + tag
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(attrs)

    def end_element(self, tag):
        """
        Called every time an XML element end
        """
        text = ''.join(self.__token_list)
        mname = 'end_' + tag
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(text)

    def characters(self, data):
        """
        Called with segments of the character data. This is not predictable
        in how it is called, so we must collect the information for assembly
        later.
        """
        self.__token_list.append(data)

    def start_module(self, attrs):
        """
        Called when the module tag is first encounterd. Pulls off the ID tag
        if it exists, and pulls out the description
        """
        self.__db.module_name = attrs['name']
        if 'owner' in attrs:
            self.__db.owner = attrs['owner']
        if 'id' in attrs:
            self.save_id = cnv_str(attrs, 'id').upper()
        self.__db.descriptive_title = cnv_str(attrs, 'title')

    def start_instance(self, attrs):
        """
        Called when the instance tag is encounted. Attributes are:

          id
          base
        """
        self.__db.instances.append((attrs['id'], cnv_hex(attrs, 'base')))

    def start_base(self, attrs):
        """
        Called when the base tag is encountered. Attributes are:

           offset (optional)
           addr_width
           data_width
        """
        if 'offset' in attrs:
            self.__db.instances.append((self.save_id,
                                        cnv_hex(attrs, 'offset')))
        self.__db.address_bus_width = cnv_int(attrs, 'addr_width', 32)
        self.__db.data_bus_width = cnv_int(attrs, 'data_width', 32)

    def start_signal(self, attrs):
        """
        Called when the signal tag is encountered. Attributes are:

           enb
           static
           side_effect
           type
        """
        self.__field.use_output_enable = cnv_bool(attrs, 'enb')
        self.__field.output_is_static = cnv_bool(attrs, 'static')
        self.__field.output_has_side_effect = cnv_bool(attrs, 'side_effect')
        if attrs.get('type'):
            t = cnv_int(attrs, 'type')
            oneshot = cnv_int(attrs, 'oneshot')
            if t == BitField.READ_ONLY:
                self.__field.field_type = BitField.TYPE_READ_ONLY
            elif t == BitField.READ_WRITE:
                if oneshot == BitField.ONE_SHOT_ANY:
                    self.__field.field_type = BitField.TYPE_READ_WRITE_1S
                elif oneshot == BitField.ONE_SHOT_ONE:
                    self.__field.field_type = BitField.TYPE_READ_WRITE_1S_1
                else:
                    self.__field.field_type = BitField.TYPE_READ_WRITE
            elif t == BitField.WRITE_1_TO_CLEAR:
                if oneshot == BitField.ONE_SHOT_ANY:
                    self.__field.field_type = BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S
                elif oneshot == BitField.ONE_SHOT_ONE:
                    self.__field.field_type = BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S_1
                else:
                    self.__field.field_type = BitField.TYPE_WRITE_1_TO_CLEAR_SET
            elif t == BitField.WRITE_1_TO_SET:
                self.__field.field_type = BitField.TYPE_WRITE_1_TO_SET
            else: 
                self.__field.field_type = BitField.TYPE_WRITE_ONLY
        else:
            self.__field.field_type = CONVERT_TYPE[attrs.get('field_type', 'RO')]
            
    def start_input(self, attrs):
        """
        Called when the input tag is encountered. Attributes are;

          function
          load
        """
        if attrs.get('function'):
            old_type = self.__field.field_type
            
            func = cnv_int(attrs, 'function', BitField.FUNC_ASSIGNMENT)
            if old_type == BitField.TYPE_READ_ONLY:
                if func == BitField.FUNC_PARALLEL:
                    self.__field.field_type = BitField.TYPE_READ_ONLY_LOAD
            elif old_type == BitField.TYPE_READ_WRITE:
                if func == BitField.FUNC_SET_BITS:
                    self.__field.field_type = BitField.TYPE_READ_WRITE_SET
                elif func == BitField.FUNC_PARALLEL:
                    self.__field.field_type = BitField.TYPE_READ_WRITE_LOAD
            elif old_type == BitField.TYPE_READ_WRITE_1S:
                if func == BitField.FUNC_SET_BITS:
                    self.__field.field_type = BitField.TYPE_READ_WRITE_SET_1S
                elif func == BitField.FUNC_PARALLEL:
                    self.__field.field_type = BitField.TYPE_READ_WRITE_LOAD_1S
            elif old_type == BitField.TYPE_READ_WRITE_1S_1:
                if func == BitField.FUNC_SET_BITS:
                    self.__field.field_type = BitField.TYPE_READ_WRITE_SET_1S_1
                elif func == BitField.FUNC_PARALLEL:
                    self.__field.field_type = BitField.TYPE_READ_WRITE_LOAD_1S_1
            elif old_type == BitField.TYPE_WRITE_1_TO_CLEAR_SET:
                if func == BitField.FUNC_PARALLEL:
                    self.__field.field_type = BitField.TYPE_WRITE_1_TO_CLEAR_LOAD
            elif old_type == BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S:
                if func == BitField.FUNC_PARALLEL:
                    self.__field.field_type = BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S
            elif old_type == BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S_1:
                if func == BitField.FUNC_PARALLEL:
                    self.__field.field_type = BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1

        self.__field.control_signal = cnv_str(attrs, 'load')

    def start_token(self, attrs):
        """
        Called when the token tag is encountered
        """
        set_modified(self.__reg.get_token_obj(), attrs)

    def start_mneumonic(self, attrs):
        """
        Called when the token tag is encountered. Outdated and kept for
        backward compatibility
        """
        set_modified(self.__reg.get_token_obj(), attrs)

    def start_description(self, attrs):
        """
        Called when the description tag is encountered.
        """
        if not self.__field:
            set_modified(self.__reg.get_description_obj(), attrs)

    def start_address(self, attrs):
        """
        Called when the address tag is encountered.
        """
        set_modified(self.__reg.get_address_obj(), attrs)

    def start_width(self, attrs):
        """
        Called when the width tag is encountered.
        """
        set_modified(self.__reg.get_width_obj(), attrs)

    def start_name(self, attrs):
        """
        Called when the name tag is encountered.
        """
        set_modified(self.__reg.get_address_obj(), attrs)

    def start_register(self, attrs):
        """
        Called when the register tag is encountered. Attributes are:

          nocode
          dont_test
          hide
        """
        self.__reg = Register()
        self.__reg.do_not_generate_code = cnv_bool(attrs, 'nocode')
        self.__reg.do_not_test = cnv_bool(attrs, 'dont_test')
        self.__reg.hide = cnv_bool(attrs, 'hide')

    def start_ports(self, attrs):
        """
        Called when the ports tag is encountered.
        """
        self.__in_ports = True

    def start_value(self, attrs):
        """
        Called when the value tag is encountered. Attributes are:

          val
          token
        """
        self.__current_val = attrs['val']
        self.__current_token = attrs.get('token', '')

    def start_modified(self, attrs):
        """
        Called when the modified tag is encountered. Attributes are:

          time
        """
        if 'time' in attrs and self.__field:
            self.__field.last_modified = cnv_int(attrs, 'time')

    def start_range(self, attrs):
        """
        Called when the range tag is encountered. Attributes are:

          start
          stop
        """
        self.__field = BitField(cnv_int(attrs, 'stop'),
                                cnv_int(attrs, 'start'))
        self.__reg.add_bit_field(self.__field)

    def start_be(self, attrs):
        """
        Called when the be tag is encountered. Attributes are:

          active
        """
        self.__db.be_level = cnv_int(attrs, 'active')

    def start_reset(self, attrs):
        """
        Called with the reset tag is encountered. If it is a ports definition,
        then it refers to a global reset, and the attributes are:

          active

        If not, then it refers to the reset value of a bit field, in which
        case the attribute is:

          type

        if type is not specified, the it is assumed to be RESET_NUMERIC
        """
        if self.__in_ports:
            self.__db.reset_active_level = cnv_int(attrs, 'active')
        else:
            try:
                self.__reset_type = int(attrs.get('type', "0"))
                self.__reset_parameter = attrs.get('parameter', '')
            except ValueError:
                self.__reset_type = BitField.RESET_NUMERIC

    def end_register(self, text):
        """
        Called when the register tag is terminated.
        """
        self.__reg = None

    def end_ports(self, text):
        """
        Called when the ports tag is terminated.
        """
        self.__in_ports = False

    def end_range(self, text):
        """
        Called when the range tag is terminated.
        """
        self.__field = None

    def end_reset(self, text):
        """
        Called when the register tag is terminated. If we are in a port
        definition, then the text contains the reset signal name.
        """
        if self.__in_ports:
            self.__db.reset_name = text
        elif self.__reset_type == 1:
            self.__field.reset_input = text.strip()
            self.__field.reset_type = BitField.RESET_INPUT
        elif self.__reset_type == 2:
            self.__field.reset_parameter = self.__reset_parameter
            self.__field.reset_value = int(text, 16)
            self.__field.reset_type = BitField.RESET_PARAMETER
        else:
            self.__field.reset_value = int(text, 16)
            self.__field.reset_type = BitField.RESET_NUMERIC

    def end_token(self, text):
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        self.__reg.token = text

    def end_mneumonic(self, text):
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        self.__reg.token = text

    def end_address(self, text):
        """
        Called when the register tag is terminated. The address is the
        text value (base 10). At this point, the register can be added to
        the database, since the address is used as the key.
        """
        self.__reg.address = int(text)
        self.__db.add_register(self.__reg)

    def end_signal(self, text):
        """
        Called when the signal tag is terminated. The text value is assigned
        to the field's output signal
        """
        self.__field.output_signal = text

    def end_value(self, text):
        """
        Called when the value tag is terminated. The value, token and text
        value are added to the field's value list.
        """
        self.__field.values.append((self.__current_val,
                                    self.__current_token, text))

    def end_input(self, text):
        """
        Called when the input tag is terminated. The text value is assigned
        to the field's input signal
        """
        self.__field.input_signal = text

    def end_width(self, text):
        """
        Called when the width tag is terminated. The text value is assigned
        as the register's width. This is assumed to be base 10.
        """
        self.__reg.width = int(text)

    def end_name(self, text):
        """
        Called when the name tag is terminated. If a field is active, then
        the text value is assigned to the field. Otherwise, it is assigned to
        the register.
        """
        if self.__field:
            self.__field.field_name = text
        else:
            self.__reg.register_name = text

    def end_description(self, text):
        """
        Called when the description tag is terminated. If a field is active,
        then the text value is assigned to the field. Otherwise, it is
        assigned to the register.
        """
        if self.__field:
            self.__field.description = text
        else:
            self.__reg.description = text

    def end_overview(self, text):
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.overview_text = text

    def end_addr(self, text):
        """
        Called when the addr tag is terminated. The text value is assigned
        to the database's address_bus_name
        """
        self.__db.address_bus_name = text

    def end_data_in(self, text):
        """
        Called when the data_in tag is terminated. The text value is assigned
        to the database's write_data_name
        """
        self.__db.write_data_name = text

    def end_data_out(self, text):
        """
        Called when the data_out tag is terminated. The text value is assigned
        to the database's read_data_name
        """
        self.__db.read_data_name = text

    def end_be(self, text):
        """
        Called when the be tag is terminated. The text value is assigned
        to the database's byte_strobe_name
        """
        self.__db.byte_strobe_name = text

    def end_wr(self, text):
        """
        Called when the wr tag is terminated. The text value is assigned
        to the database's write_strobe_name
        """
        self.__db.write_strobe_name = text

    def end_rd(self, text):
        """
        Called when the rd tag is terminated. The text value is assigned
        to the database's write_strobe_name
        """
        self.__db.read_strobe_name = text

    def end_clk(self, text):
        """
        Called when the clk tag is terminated. The text value is assigned
        to the database's clock_name
        """
        self.__db.clock_name = text
