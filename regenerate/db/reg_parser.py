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
import uuid

from .register import Register
from .bitfield import BitField
from .bit_values import BitValues
from .bitfield_types import ID_TO_TYPE
from .enums import ResetType
from .parammap import ParameterData


def cnv_hex(attrs, key, default=0):
    """
    Looks for the key in the attrs array, converting the returned value to
    a hex value if it exists, otherwise it returns the default value.
    """
    try:
        return int(attrs[key], 16)
    except ValueError:
        return default


def cnv_int(attrs, key, default=0):
    """
    Looks for the key in the attrs array, converting the returned value to
    an integer if it exists, otherwise it returns the default value.
    """
    try:
        return int(attrs.get(key))
    except ValueError:
        return default


def cnv_bool(attrs, key, default=False):
    """
    Looks for the key in the attrs array, converting the returned value to
    a boolean value if it exists, otherwise it returns the default value.
    """
    try:
        return bool(int(attrs[key]))
    except ValueError:
        return default
    except KeyError:
        return default


def cnv_str(attrs, key, default=""):
    """
    Looks for the key in the attrs array, returning the string if it exists,
    otherwise it returns the default value.
    """
    return attrs.get(key, default)


class RegParser:
    """
    Parses the XML file, loading up the register database.
    """

    def __init__(self, dbase):
        self.__db = dbase
        self.__reg = None
        self.__field = None
        self.__in_ports = False
        self.__current_val = 0
        self.__current_token = ""
        self.__reset_type = 0
        self.__reset_parameter = ""
        self.__token_list = []
        self.save_id = None
        self.existing_ids = set()
        self.found_parameters = set()

    def parse(self, input_file):
        """
        Parses the specified input file.
        """
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.characters
        parser.ParseFile(input_file)
        self.__db.modified = True

    def start_element(self, tag, attrs):
        """Called every time an XML element begins"""
        self.__token_list = []
        mname = "start_" + tag
        if hasattr(self, mname):
            method = getattr(self, mname)
            method(attrs)

    def end_element(self, tag):
        """Called every time an XML element end """
        text = "".join(self.__token_list)
        mname = "end_" + tag
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
        self.__db.module_name = attrs["name"]
        if "owner" in attrs:
            self.__db.owner = attrs["owner"]
        if "organization" in attrs:
            self.__db.organization = attrs["organization"]
        self.__db.internal_only = bool(int(attrs.get("internal", "0")))
        if "id" in attrs:
            self.save_id = cnv_str(attrs, "id").upper()
        array = attrs.get("array", "mem")
        self.__db.coverage = bool(int(attrs.get("coverage", "1")))
        self.__db.array_is_reg = array == "reg"
        self.__db.descriptive_title = cnv_str(attrs, "title")

    def start_parameter(self, attrs):
        """Start a parameter read"""

        self.__db.add_parameter(
            ParameterData(
                attrs["name"],
                int(attrs["value"], 0),
                int(attrs["min"], 0),
                int(attrs["max"], 0),
            )
        )

    def end_parameters(self, _attrs):
        """Called at the end of the parameter statement"""

        current_params = set({n.name for n in self.__db.get_parameters()})
        for name in self.found_parameters:
            if name not in current_params:
                self.__db.add_parameter(ParameterData(name, "1", "0", "4096"))

    def start_base(self, attrs):
        """
        Called when the base tag is encountered. Attributes are:

           offset (optional)
           addr_width
           data_width
        """
        self.__db.ports.address_bus_width = cnv_int(attrs, "addr_width", 32)
        self.__db.ports.data_bus_width = cnv_int(attrs, "data_width", 32)

    def start_signal(self, attrs):
        """
        Called when the signal tag is encountered. Attributes are:

           enb
           static
           side_effect
           type
        """
        self.__field.use_output_enable = cnv_bool(attrs, "enb")
        self.__field.output_is_static = cnv_bool(attrs, "static")
        if "side_effect" in attrs:
            self.__field.output_has_side_effect = cnv_bool(
                attrs, "side_effect"
            )
        if "volatile" in attrs:
            self.__field.flags.volatile = cnv_bool(attrs, "volatile")
        if "random" in attrs:
            self.__field.flags.can_randomize = cnv_bool(attrs, "random")
        if "error_field" in attrs:
            self.__field.flags.is_error_field = cnv_bool(attrs, "error_field")
        ftype = attrs.get("field_type")
        if ftype:
            self.__field.field_type = ID_TO_TYPE[ftype]

    def start_input(self, attrs):
        """
        Called when the input tag is encountered. Attributes are;

          function
          load
        """
        self.__field.control_signal = cnv_str(attrs, "load")

    def start_register(self, attrs):
        """
        Called when the register tag is encountered. Attributes are:

          nocode
          dont_test
          hide
        """
        self.__reg = Register()
        self.__reg.flags.do_not_generate_code = cnv_bool(attrs, "nocode")
        self.__reg.flags.do_not_test = cnv_bool(attrs, "dont_test")
        self.__reg.flags.do_not_cover = cnv_bool(attrs, "dont_cover")
        self.__reg.flags.do_not_use_uvm = cnv_bool(attrs, "dont_use_uvm")
        self.__reg.flags.hide = cnv_bool(attrs, "hide")
        self.__reg.share = int(attrs.get("share", 0))

    def start_ports(self, _attrs):
        """Called when the ports tag is encountered."""
        self.__in_ports = True

    def start_value(self, attrs):
        """
        Called when the value tag is encountered. Attributes are:

          val
          token
        """
        self.__current_val = attrs["val"]
        self.__current_token = attrs.get("token", "")

    def start_range(self, attrs):
        """
        Called when the range tag is encountered. Attributes are:

          start
          stop
        """
        start = cnv_int(attrs, "start")
        stop = cnv_int(attrs, "stop")
        self.__field = BitField(stop, start)
        self.__reg.add_bit_field(self.__field)

    def start_be(self, attrs):
        """
        Called when the be tag is encountered. Attributes are:

          active
        """
        self.__db.ports.byte_strobe_active_level = cnv_int(attrs, "active")

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
            self.__db.ports.reset_active_level = cnv_int(attrs, "active")
        else:
            try:
                self.__reset_type = int(attrs.get("type", "0"))
                self.__reset_parameter = attrs.get("parameter", "")
            except ValueError:
                self.__reset_type = ResetType.NUMERIC

    def end_register(self, _text):
        """Called when the register tag is terminated."""
        self.__reg = None

    def end_ports(self, _text):
        """Called when the ports tag is terminated."""
        self.__in_ports = False

    def end_range(self, _text):
        """Called when the range tag is terminated."""
        self.__field = None

    def end_field_type(self, text):
        """Called when the range tag is terminated."""
        self.__field.field_type = ID_TO_TYPE[text]

    def end_random(self, text):
        """Called when the range tag is terminated."""
        self.__field.flags.can_randomize = bool(int(text))

    def end_volatile(self, text):
        """Called when the range tag is terminated."""
        self.__field.flags.volatile = bool(int(text))

    def end_error_field(self, text):
        """Called when the range tag is terminated."""
        self.__field.flags.is_error_field = bool(int(text))

    def end_side_effect(self, text):
        """Called when the range tag is terminated."""
        self.__field.output_has_side_effect = bool(int(text))

    def end_nocode(self, text):
        """Called when the range tag is terminated."""
        self.__reg.flags.do_not_generate_code = bool(int(text))

    def end_dont_test(self, text):
        """Called when the range tag is terminated."""
        self.__reg.flags.do_not_test = bool(int(text))

    def end_dont_cover(self, text):
        """Called when the range tag is terminated."""
        self.__reg.flags.do_not_cover = bool(int(text))

    def end_hide(self, text):
        """Called when the range tag is terminated."""
        self.__reg.flags.hide = bool(int(text))

    def end_dont_use_uvm(self, text):
        """Called when the range tag is terminated."""
        self.__reg.flags.do_not_use_uvm = bool(int(text))

    def end_share(self, text):
        """Called when the range tag is terminated."""
        self.__reg.share = int(text)

    def end_reset(self, text):
        """
        Called when the register tag is terminated. If we are in a port
        definition, then the text contains the reset signal name.
        """
        if self.__in_ports:
            self.__db.ports.reset_name = text
        elif self.__reset_type == 1:
            self.__field.reset_input = text.strip()
            self.__field.reset_type = ResetType.INPUT
        elif self.__reset_type == 2:
            self.__field.reset_parameter = self.__reset_parameter
            self.__field.reset_value = int(text, 16)
            self.__field.reset_type = ResetType.PARAMETER
            self.found_parameters.add(self.__reset_parameter)
        else:
            self.__field.reset_value = int(text, 16)
            self.__field.reset_type = ResetType.NUMERIC

    def end_token(self, text):
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        self.__reg.token = text

    def end_dimension(self, text):
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        try:
            self.__reg.dimension = text
        except ValueError:
            self.__reg.dimension = "1"

    def end_uuid(self, text):
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        # force the generation of a new ID if a duplicate is found

        if text in self.existing_ids:
            text = uuid.uuid4().hex
        self.existing_ids.add(text)

        if self.__field:
            self.__field.uuid = text
        else:
            self.__reg.uuid = text

    def end_ram_size(self, text):
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        self.__reg.ram_size = int(text)

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
        bfval = BitValues()
        try:
            bfval.value = int(self.__current_val, 16)
        except ValueError:
            bfval.value = int(self.__current_val, 0)

        bfval.token = self.__current_token
        bfval.description = text
        self.__field.values.append(bfval)

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
            self.__field.name = text
        else:
            self.__reg.name = text

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

    def end_owner(self, text):
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.owner = text

    def end_title(self, text):
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.descriptive_title = text

    def end_org(self, text):
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.organization = text

    def end_array(self, text):
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.array_is_reg = text == "reg"

    def end_addr(self, text):
        """
        Called when the addr tag is terminated. The text value is assigned
        to the database's address_bus_name
        """
        self.__db.ports.address_bus_name = text

    def end_data_in(self, text):
        """
        Called when the data_in tag is terminated. The text value is assigned
        to the database's write_data_name
        """
        self.__db.ports.write_data_name = text

    def end_data_out(self, text):
        """
        Called when the data_out tag is terminated. The text value is assigned
        to the database's read_data_name
        """
        self.__db.ports.read_data_name = text

    def end_be(self, text):
        """
        Called when the be tag is terminated. The text value is assigned
        to the database's byte_strobe_name
        """
        self.__db.ports.byte_strobe_name = text

    def end_interface(self, text):
        """
        Called when the interface tag is terminated. The text value is assigned
        to the database's write_strobe_name
        """
        self.__db.use_interface = bool(text)

    def end_wr(self, text):
        """
        Called when the wr tag is terminated. The text value is assigned
        to the database's write_strobe_name
        """
        self.__db.ports.write_strobe_name = text

    def end_ack(self, text):
        """
        Called when the ack tag is terminated. The text value is assigned
        to the database's acknowledge_name
        """
        self.__db.ports.acknowledge_name = text

    def end_rd(self, text):
        """
        Called when the rd tag is terminated. The text value is assigned
        to the database's read_strobe_name
        """
        self.__db.ports.read_strobe_name = text

    def end_clk(self, text):
        """
        Called when the clk tag is terminated. The text value is assigned
        to the database's clock_name
        """
        self.__db.ports.clock_name = text
