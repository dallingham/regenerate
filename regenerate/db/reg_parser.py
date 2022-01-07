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
from typing import Dict, NamedTuple
from hashlib import md5

from .name_base import Uuid
from .xml_base import XmlBase
from .register import Register
from .bitfield import BitField
from .bit_values import BitValues
from .bitfield_types import ID_TO_TYPE
from .enums import ResetType, ShareType
from .parameters import ParameterDefinition, ParameterValue


class ValueInfo(NamedTuple):
    "Holds the information for the field list value"

    value: str
    token: str


class ResetInfo(NamedTuple):
    "Holds the reset information during parsing"

    reset_type: ResetType
    parameter: str


def cnv_hex(attrs: Dict[str, str], key: str, default: int = 0) -> int:
    """
    Looks for the key in the attrs array, converting the returned value to
    a hex value if it exists, otherwise it returns the default value.
    """
    try:
        return int(attrs[key], 16)
    except ValueError:
        return default


def cnv_int(attrs: Dict[str, str], key: str, default: int = 0) -> int:
    """
    Looks for the key in the attrs array, converting the returned value to
    an integer if it exists, otherwise it returns the default value.
    """
    return int(attrs[key]) if key in attrs else default


def cnv_bool(attrs: Dict[str, str], key: str, default: bool = False) -> bool:
    """
    Looks for the key in the attrs array, converting the returned value to
    a boolean value if it exists, otherwise it returns the default value.
    """
    return bool(int(attrs[key])) if key in attrs else default


def cnv_str(attrs: Dict[str, str], key: str, default: str = "") -> str:
    """
    Looks for the key in the attrs array, returning the string if it exists,
    otherwise it returns the default value.
    """
    return attrs.get(key, default)


class RegParser(XmlBase):
    "Parses the XML file, loading up the register database."

    def __init__(self, dbase, name=None):
        super().__init__()

        self.__db = dbase
        if name:
            self.__db.uuid = _mk_uuid(name)

        self.__reg = None
        self.__field = None
        self.__in_ports = False
        self.__value = ValueInfo("", "")
        self.__reset_info = ResetInfo(ResetType.NUMERIC, "")
        self.__found_parameters = set()

    def parse(self, input_file) -> None:
        """
        Parses the specified input file.
        """
        parser = xml.parsers.expat.ParserCreate()
        parser.StartElementHandler = self.start_element
        parser.EndElementHandler = self.end_element
        parser.CharacterDataHandler = self.characters
        parser.ParseFile(input_file)
        self.__db.modified = True

    def _start_module(self, attrs: Dict[str, str]) -> None:
        """
        Called when the module tag is first encounterd. Pulls off the ID tag
        if it exists, and pulls out the description
        """
        self.__db.name = attrs["name"]
        if "owner" in attrs:
            self.__db.owner = attrs["owner"]
        if "organization" in attrs:
            self.__db.organization = attrs["organization"]
        self.__db.internal_only = bool(int(attrs.get("internal", "0")))
        array = attrs.get("array", "mem")
        self.__db.coverage = bool(int(attrs.get("coverage", "1")))
        self.__db.array_is_reg = array == "reg"
        self.__db.descriptive_title = cnv_str(attrs, "title")

    def _start_parameter(self, attrs: Dict[str, str]) -> None:
        """Start a parameter read"""

        self.__db.parameters.add(
            ParameterDefinition(
                attrs["name"],
                int(attrs["value"], 0),
                int(attrs["min"], 0),
                int(attrs["max"], 0),
            )
        )

    def _end_parameters(self, _attrs: Dict[str, str]) -> None:
        """Called at the end of the parameter statement"""

        current_params = set({n.name for n in self.__db.parameters.get()})
        for name in self.__found_parameters:
            if name not in current_params:
                self.__db.parameters.add(ParameterDefinition(name, 1, 0, 4096))

    def _start_base(self, attrs: Dict[str, str]) -> None:
        """
        Called when the base tag is encountered. Attributes are:

           offset (optional)
           addr_width
           data_width
        """
        self.__db.ports.address_bus_width = cnv_int(attrs, "addr_width", 32)
        self.__db.ports.data_bus_width = cnv_int(attrs, "data_width", 32)

    def _start_signal(self, attrs: Dict[str, str]) -> None:
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

    def _start_input(self, attrs: Dict[str, str]) -> None:
        """
        Called when the input tag is encountered. Attributes are;

          function
          load
        """
        self.__field.control_signal = cnv_str(attrs, "load")

    def _start_register(self, attrs: Dict[str, str]) -> None:
        """
        Called when the register tag is encountered. Attributes are:

          nocode
          dont_test
          hide
        """
        self.__reg = Register()
        self.__reg.flags.do_not_generate_code = cnv_bool(attrs, "nocode")
        self.__reg.flags.do_not_test = cnv_bool(attrs, "dont_test")
        self.__reg.flags.do_not_reset_test = self.__reg.flags.do_not_test
        self.__reg.flags.do_not_cover = cnv_bool(attrs, "dont_cover")
        self.__reg.flags.do_not_use_uvm = cnv_bool(attrs, "dont_use_uvm")
        self.__reg.flags.hide = cnv_bool(attrs, "hide")
        if "share" in attrs:
            self.__reg.share = ShareType(int(attrs["share"]))
        else:
            self.__reg.share = ShareType.NONE

    def _start_ports(self, _attrs: Dict[str, str]) -> None:
        """Called when the ports tag is encountered."""
        self.__in_ports = True

    def _start_value(self, attrs: Dict[str, str]) -> None:
        """
        Called when the value tag is encountered. Attributes are:

          val
          token
        """
        self.__value = ValueInfo(attrs["val"], attrs.get("token", ""))

    def _start_range(self, attrs: Dict[str, str]) -> None:
        """
        Called when the range tag is encountered. Attributes are:

          start
          stop
        """
        start = cnv_int(attrs, "start")
        stop = cnv_int(attrs, "stop")
        self.__field = BitField(stop, start)
        self.__reg.add_bit_field(self.__field)

    def _start_reset(self, attrs: Dict[str, str]) -> None:
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
                self.__reset_info = ResetInfo(
                    ResetType(int(attrs.get("type", "0"))),
                    attrs.get("parameter", ""),
                )
            except ValueError:
                self.__reset_info = ResetInfo(ResetType.NUMERIC, "")

    def _end_register(self, _text: str) -> None:
        """Called when the register tag is terminated."""
        self.__reg = None

    def _end_ports(self, _text: str) -> None:
        """Called when the ports tag is terminated."""
        self.__in_ports = False

    def _end_range(self, _text: str) -> None:
        """Called when the range tag is terminated."""
        self.__field = None

    def _end_field_type(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__field.field_type = ID_TO_TYPE[text]

    def _end_random(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__field.flags.can_randomize = bool(int(text))

    def _end_volatile(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__field.flags.volatile = bool(int(text))

    def _end_error_field(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__field.flags.is_error_field = bool(int(text))

    def _end_side_effect(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__field.output_has_side_effect = bool(int(text))

    def _end_nocode(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__reg.flags.do_not_generate_code = bool(int(text))

    def _end_dont_test(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__reg.flags.do_not_test = bool(int(text))

    def _end_dont_cover(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__reg.flags.do_not_cover = bool(int(text))

    def _end_hide(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__reg.flags.hide = bool(int(text))

    def _end_dont_use_uvm(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__reg.flags.do_not_use_uvm = bool(int(text))

    def _end_share(self, text: str) -> None:
        """Called when the range tag is terminated."""
        self.__reg.share = int(text)

    def _end_reset(self, text: str) -> None:
        """
        Called when the register tag is terminated. If we are in a port
        definition, then the text contains the reset signal name.
        """
        if self.__in_ports:
            return

        self.__field.reset_type = self.__reset_info.reset_type
        if self.__reset_info.reset_type == ResetType.INPUT:
            self.__field.reset_input = text.strip()
        elif self.__reset_info.reset_type == ResetType.PARAMETER:
            self.__field.reset_parameter = self.__reset_info.parameter
            self.__field.set_reset_value_int(int(text, 16))
            self.__found_parameters.add(self.__reset_info.parameter)
        else:
            self.__field.set_reset_value_int(int(text, 16))

    def _end_token(self, text: str) -> None:
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        self.__reg.token = text

    def _end_dimension(self, text: str) -> None:
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        self.__reg.dimension = ParameterValue()
        self.__reg.dimension.set_int(int(text))

    def _end_ram_size(self, text: str) -> None:
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        self.__reg.ram_size = int(text)

    def _end_mneumonic(self, text: str) -> None:
        """
        Called when the token tag is terminated. The text is the
        register token value.
        """
        self.__reg.token = text

    def _end_address(self, text: str) -> None:
        """
        Called when the register tag is terminated. The address is the
        text value (base 10). At this point, the register can be added to
        the database, since the address is used as the key.
        """
        self.__reg.address = int(text)
        self.__db.add_register(self.__reg)

    def _end_uuid(self, text: str) -> None:
        """
        Called when the register tag is terminated. The address is the
        text value (base 10). At this point, the register can be added to
        the database, since the address is used as the key.
        """
        if self.__field:
            self.__field.uuid = text.strip()
        elif self.__reg:
            self.__reg.uuid = text.strip()

    def _end_signal(self, text: str) -> None:
        """
        Called when the signal tag is terminated. The text value is assigned
        to the field's output signal
        """
        self.__field.output_signal = text

    def _end_value(self, text: str) -> None:
        """
        Called when the value tag is terminated. The value, token and text
        value are added to the field's value list.
        """
        bfval = BitValues()
        try:
            bfval.value = int(self.__value.value, 16)
        except ValueError:
            bfval.value = int(self.__value.value, 0)

        bfval.token = self.__value.token
        bfval.description = text
        self.__field.values.append(bfval)

    def _end_input(self, text: str) -> None:
        """
        Called when the input tag is terminated. The text value is assigned
        to the field's input signal
        """
        self.__field.input_signal = text

    def _end_width(self, text: str) -> None:
        """
        Called when the width tag is terminated. The text value is assigned
        as the register's width. This is assumed to be base 10.
        """
        self.__reg.width = int(text)

    def _end_name(self, text: str) -> None:
        """
        Called when the name tag is terminated. If a field is active, then
        the text value is assigned to the field. Otherwise, it is assigned to
        the register.
        """
        if self.__field:
            self.__field.name = text
        else:
            self.__reg.name = text

    def _end_description(self, text: str) -> None:
        """
        Called when the description tag is terminated. If a field is active,
        then the text value is assigned to the field. Otherwise, it is
        assigned to the register.
        """
        if self.__field:
            self.__field.description = text
        else:
            self.__reg.description = text

    def _end_overview(self, text: str) -> None:
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.doc_pages.update_page("Overview", text, ["Confidential"])

    def _end_owner(self, text: str) -> None:
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.owner = text

    def _end_title(self, text: str) -> None:
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.descriptive_title = text

    def _end_org(self, text: str) -> None:
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.organization = text

    def _end_array(self, text: str) -> None:
        """
        Called when the overview tag is terminated. The text value is assigned
        to the database's overview_text
        """
        self.__db.array_is_reg = text == "reg"

    def _end_addr(self, text: str) -> None:
        """
        Called when the addr tag is terminated. The text value is assigned
        to the database's address_bus_name
        """
        self.__db.ports.address_bus_name = text

    def _end_data_in(self, text: str) -> None:
        """
        Called when the data_in tag is terminated. The text value is assigned
        to the database's write_data_name
        """
        self.__db.ports.write_data_name = text

    def _end_data_out(self, text: str) -> None:
        """
        Called when the data_out tag is terminated. The text value is assigned
        to the database's read_data_name
        """
        self.__db.ports.read_data_name = text

    def _end_be(self, text: str) -> None:
        """
        Called when the be tag is terminated. The text value is assigned
        to the database's byte_strobe_name
        """
        self.__db.ports.byte_strobe_name = text

    def _end_interface(self, text: str) -> None:
        """
        Called when the interface tag is terminated. The text value is assigned
        to the database's write_strobe_name
        """
        self.__db.use_interface = bool(text)

    def _end_wr(self, text: str) -> None:
        """
        Called when the wr tag is terminated. The text value is assigned
        to the database's write_strobe_name
        """
        self.__db.ports.write_strobe_name = text

    def _end_ack(self, text: str) -> None:
        """
        Called when the ack tag is terminated. The text value is assigned
        to the database's acknowledge_name
        """
        self.__db.ports.acknowledge_name = text

    def _end_rd(self, text: str) -> None:
        """
        Called when the rd tag is terminated. The text value is assigned
        to the database's read_strobe_name
        """
        self.__db.ports.read_strobe_name = text

    def _end_clk(self, text: str) -> None:
        """
        Called when the clk tag is terminated. The text value is assigned
        to the database's clock_name
        """
        self.__db.ports.clock_name = text


def _mk_uuid(string: str) -> Uuid:
    """
    Convert the string into a UUID.

    Take the hash value of the string and convert it to hex.

    Parameters:
        string (str): input string

    Returns:

    """
    md5_func = md5()
    md5_func.update(bytes(string, "ascii"))
    return md5_func.hexdigest()
