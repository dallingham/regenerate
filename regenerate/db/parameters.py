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
Provides an object that can either be an integer or a parameter

Contains the information for register set parameters and project parameters.

ParameterDefinition consists of default, min, and max values.

"""

from typing import Dict, Any, Optional, Union, List
from .name_base import NameBase, Uuid
from .enums import ParamFunc


class ParameterValue:
    "A value that can be either an integer or a parameter"

    def __init__(self, value=0, is_parameter=False):
        self.is_parameter = is_parameter
        self.offset = 0
        self.func = ParamFunc.NONE
        self.int_value: int = value
        self.txt_value: Uuid = Uuid("")

    def __repr__(self) -> str:
        if self.is_parameter:
            if self.offset == 0:
                offset = ""
            elif self.offset > 0:
                offset = f"+{self.offset}"
            else:
                offset = f"{self.offset}"
            return f'ParameterValue(value="{self.txt_value}{offset}", is_parameter=True)'
        return (
            f" ParameterValue(value=0x{self.int_value:x}, is_parameter=False)"
        )

    def __str__(self) -> str:
        if self.is_parameter:
            pval = ParameterFinder().find(self.txt_value)
            if pval:
                if self.offset > 0:
                    return f"{pval.name}+{self.offset}"
                if self.offset < 0:
                    return f"{pval.name}{self.offset}"
                return f"{pval.name}"
            return ""
        return self.int_str()

    def param_name(self):
        """
        Return the parameter name

        Returns:
           str: name of the parameter

        """
        if self.is_parameter:
            pval = ParameterFinder().find(self.txt_value)
            return pval.name
        return ""

    def int_str(self) -> str:
        """
        Print as a string or integer value in C format.

        If the value is a parameter, return the parameter name as a string
        (along with any modifications). If the value is an integer, return
        the value as a string in C hex format (0x<value>).

        Returns:
           String representation of the value

        """
        if self.is_parameter:
            pval = ParameterFinder().find(self.txt_value)
            if pval:
                if self.offset > 0:
                    return f"{pval.name}+{self.offset}"
                if self.offset < 0:
                    return f"{pval.name}{self.offset}"
                return f"{pval.name}"
            return ""
        return f"0x{self.int_value:x}"

    def int_decimal_str(self) -> str:
        """
        Print as a string or integer value.

        If the value is a parameter, return the parameter name as a string
        (along with any modifications). If the value is an integer, return
        the value as a string in decimal format.

        Returns:
           String representation of the value

        """
        if self.is_parameter:
            pval = ParameterFinder().find(self.txt_value)
            if pval:
                if self.offset > 0:
                    return f"{pval.name}+{self.offset}"
                if self.offset < 0:
                    return f"{pval.name}{self.offset}"
                return f"{pval.name}"
            return ""
        return f"{self.int_value}"

    def int_vstr(self) -> str:
        """
        Print as a string or integer value in Verilog format.

        If the value is a parameter, return the parameter name as a string
        (along with any modifications). If the value is an integer, return
        the value as a string in Verilog hex format ('h<value>).

        Returns:
           String representation of the value

        """

        if self.is_parameter:
            pval = ParameterFinder().find(self.txt_value)
            if pval:
                if self.offset > 0:
                    return f"{pval.name}+{self.offset}"
                if self.offset < 0:
                    return f"{pval.name}{self.offset}"
                return f"{pval.name}"
            return ""
        return f"'h{self.int_value:x}"

    def set_int(self, value: int) -> None:
        """
        Set the value as an integer value.

        Sets the value and marks it as not being a parameter.

        Parameters:
           value (int): Integer value to assign

        """
        self.int_value = value
        self.is_parameter = False

    def set_param(self, uuid: Uuid, offset: int = 0) -> None:
        """
        Set the value as a parameter.

        Sets the value and marks it as being a parameter.

        Parameters:
           uuid (Uuid): UUID of the associated parameter
           offset (int): Integer offset for the parameter

        """
        self.txt_value = uuid
        self.offset = offset
        self.is_parameter = True

    def resolve(self) -> int:
        """
        Return the integer value that the value represents.

        If the value is not a parameter, return the integer value. If the value
        is a parameter, resolve the value. If the value is overridden at the
        block or top level, resolve the value. If it is not, take the default
        value of the parameter.

        Returns:
           int: Resolved value of the object

        """

        if not self.is_parameter:
            return self.int_value

        finder = ParameterFinder()
        value = finder.find(self.txt_value)
        if value:
            resolver = ParameterResolver()
            return resolver.resolve(value) + self.offset
        return 0

    def json_decode(self, data):
        "Decode from a JSON compatible dictionary"

        self.is_parameter = data["is_parameter"]
        self.offset = data["offset"]
        self.func = ParamFunc(data.get("func", 0))
        if self.is_parameter:
            self.txt_value = data["value"]
            self.int_value = 0
        else:
            self.txt_value = ""
            self.int_value = int(data["value"], 0)

    def json(self):
        "Convert to JSON compatible dictionary"

        val = {
            "is_parameter": self.is_parameter,
            "offset": self.offset,
            "func": int(self.func),
        }
        if self.is_parameter:
            val["value"] = self.txt_value
        else:
            val["value"] = f"{self.int_value}"
        return val


class ParameterResolver:
    """
    Parameter Resolver.

    Resolves parameters into their final integer value, based on default
    values and overriding.

    """

    top_overrides: Dict[str, Dict[str, Any]] = {}
    reginst_overrides: Dict[str, Dict[str, Any]] = {}
    blkinst_id = Uuid("")
    reginst_id = Uuid("")

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(ParameterResolver, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        ...

    def set_reginst(self, uuid: Uuid) -> None:
        "Set the instance name."

        self.reginst_id = uuid

    def set_blkinst(self, uuid: Uuid) -> None:
        "Set the instance name."

        self.blkinst_id = uuid

    def clear(self) -> None:
        """
        Clear out all overrides.

        Typically called when a new project is loaded.
        """
        self.top_overrides = {}
        self.reginst_overrides = {}

    def __repr__(self) -> str:
        """
        Display the text representation of the BlockInst.

        Returns:
           str: Representation of the object

        """
        return "ParameterResolver()"

    def add_regset_override(
        self, reginst_id: Uuid, param_id: Uuid, data: "ParameterValue"
    ) -> None:
        """
        Add an override for a parameter in a register set.

        Parameters:
            reginst_id (Uuid): Register set that contains the parameter
            param_id (Uuid): ID of the parameter to override
            data (ParameterValue): value for the override

        """
        if reginst_id not in self.reginst_overrides:
            self.reginst_overrides[reginst_id] = {param_id: data}
        else:
            self.reginst_overrides[reginst_id][param_id] = data

    def add_blockinst_override(
        self, blkinst_id: Uuid, param_id: Uuid, data: "ParameterValue"
    ) -> None:
        """
        Add an override for a parameter in a block.

        Parameters:
            blkinst_id (Uuid): Register set that contains the parameter
            param_id (Uuid): ID of the parameter to override
            data (ParameterValue): value for the override

        """

        if blkinst_id not in self.top_overrides:
            self.top_overrides[blkinst_id] = {param_id: data}
        else:
            self.top_overrides[blkinst_id][param_id] = data

    def resolve_reg(
        self, param: "ParameterDefinition"
    ) -> Union[int, "ParameterDefinition"]:
        """
        Resolve a parameter looking for overrides in the register set.

        If the reginst_id not use, use the param data. If it is set,
        search that register set's overrides.

        Parameters:
            param (ParamData): default parameter value if not overridden

        Returns:
            Union[int, ParameterDefinition]: resolved value

        """
        if not self.reginst_id:
            return param.value
        if (
            self.reginst_id in self.reginst_overrides
            and param.uuid in self.reginst_overrides[self.reginst_id]
        ):
            val = self.reginst_overrides[self.reginst_id][param.uuid]
            return val
        return param.value

    def resolve_blk(self, value) -> Union[int, "ParameterDefinition"]:
        """
        Resolve a parameter looking for overrides in the block.

        If the blkinst_id not use, use the param data. If it is set, search
        that block's overrides.

        Parameters:
            param (ParamData): default parameter value if not overridden

        Returns:
            Union[int, ParameterDefinition]: resolved value

        """
        if not self.blkinst_id:
            return _resolve_blk_value(value)
        if (
            self.blkinst_id in self.top_overrides
            and value.is_parameter
            and value.txt_value in self.top_overrides[self.blkinst_id]
        ):
            new_val = self.top_overrides[self.blkinst_id][value.txt_value]
            return _resolve_blk_value(new_val)
        return value.value

    def resolve(self, param: "ParameterDefinition") -> int:
        """
        Resolve a parameter looking for overrides in the block.

        If the blkinst_id not use, use the param data. If it is set, search
        that block's overrides.

        Parameters:
            param (ParamData): default parameter value if not overridden

        Returns:
            int: resolved value

        """
        val = self.resolve_reg(param)
        if isinstance(val, int):
            return val
        new_val = self.resolve_blk(val)
        return new_val


def _resolve_blk_value(value):
    """
    Return the parameter value if a parameter, otherwise return the integer.

    Parameters:
       value (Union[int, ParameterValue]): Source value for the data

    """
    if value.is_parameter:
        new_param = ParameterFinder().find(value.txt_value)
        if new_param:
            return new_param.value
        return 0
    return value.int_value


class ParameterFinder:
    """
    Finds a parameter in the project based on its UUID.

    Serves as a singleton.

    """

    data_map: Dict[Uuid, "ParameterDefinition"] = {}

    def __new__(cls):
        """
        Class method new function.

        Creates a new class instance.
        """
        if not hasattr(cls, "instance"):
            cls.instance = super(ParameterFinder, cls).__new__(cls)
        return cls.instance

    def find(self, uuid: Uuid) -> Optional["ParameterDefinition"]:
        """
        Look up the UUID in the data map.

        Parameters:
            uuid (Uuid): UUID of the parameter that is to be found

        Returns:
            Optional[ParameterDefinition]: parameter data or None if not found

        """
        return self.data_map.get(uuid)

    def register(self, parameter: "ParameterDefinition") -> None:
        """
        Register a parameter with the system.

        Parameter:
            parameter (ParameterDefinition): parameter to register

        """
        self.data_map[parameter.uuid] = parameter

    def unregister(self, parameter: "ParameterDefinition") -> None:
        """
        Remove the parameter with the system.

        Parameter:
            parameter (ParameterDefinition): parameter to remove

        """
        if parameter.uuid in self.data_map:
            del self.data_map[parameter.uuid]


class ParameterDefinition(NameBase):
    """
    Parameter data.

    Parameters consist of min, max, and default values.

    """

    def __init__(
        self,
        name: str = "",
        value: int = 1,
        min_val: int = 0,
        max_val: int = 0xFFFF_FFFF,
    ):
        """
        Initialize the object.

        Parameters:
            name (str): Parameter name
            value (int): default value
            min_val (int): minimum value the parameter can hold
            max_val (int): maximum value the parameter can hold

        """
        super().__init__(name, Uuid(""))
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.finder = ParameterFinder()
        self.finder.register(self)

    def __repr__(self) -> str:
        """
        Return the string representation of the object.

        Returns:
            str: string describing the object

        """
        return f'ParameterDefinition(name="{self.name}", uuid="{self.uuid}", value={self.value})'

    def json(self) -> Dict[str, Any]:
        """
        Encode the object to a JSON dictionary.

        Returns:
            Dict[str, Any]: JSON-ish dictionary

        """
        return {
            "uuid": self.uuid,
            "name": self.name,
            "value": self.value,
            "min_val": self.min_val,
            "max_val": self.max_val,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Decode the JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data to decode

        """
        self.finder.unregister(self)
        self.uuid = Uuid(data["uuid"])
        self.name = data["name"]
        self.value = data["value"]
        self.min_val = data["min_val"]
        self.max_val = data["max_val"]
        self.finder.register(self)


class ParameterContainer:
    """
    Class that manages parameters.

    Allows the adding, removing, and searching for parameters.

    """

    def __init__(self):
        """
        Initialize the object.

        Sets the list to an empty list.

        """
        self._parameters: List[ParameterDefinition] = []

    def get(self) -> List[ParameterDefinition]:
        """
        Return the parameter list.

        Returns:
            List[ParameterDefinition]: list of parameters

        """
        return self._parameters

    def add(self, parameter: ParameterDefinition) -> None:
        """
        Add a parameter to the list.

        Parameter:
            parameter (ParameterDefinition): Parameter to add

        """
        self._parameters.append(parameter)

    def remove(self, name: str) -> None:
        """
        Remove a parameter from the list if it exists.

        Parameter:
            name (str): Name of the parameter to remove

        """
        self._parameters = [p for p in self._parameters if p.name != name]

    def remove_by_uuid(self, uuid: Uuid) -> None:
        """
        Remove a parameter from the list if it exists.

        Parameter:
            name (str): Name of the parameter to remove

        """
        self._parameters = [p for p in self._parameters if p.uuid != uuid]

    def set(self, parameter_list: List[ParameterDefinition]) -> None:
        """
        Set the parameter list.

        Parameters:
            parameter_list (List[ParameterDefinition]): parameter list

        """
        self._parameters = parameter_list

    def find(self, name: str) -> Optional[ParameterDefinition]:
        """
        Find a parameter from its name.

        Parameters:
            name (str): name to search for

        Returns:
            Optional[ParameterDefinition]: the parameter data, if found

        """
        for param in self._parameters:
            if param.name == name:
                return param
        return None

    def json(self):
        """
        Encode the object to a JSON dictionary.

        Returns:
            Dict[str, Any]: JSON-ish dictionary

        """
        return [parameter.json() for parameter in self._parameters]

    def json_decode(self, data):
        """
        Decode the JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data to decode

        """
        self._parameters = []
        for item_json in data:
            item = ParameterDefinition()
            item.json_decode(item_json)
            self._parameters.append(item)


class ParameterOverrides:
    """
    Stores the override information.

    This includes the ParameterFinder, the path UUID, parameter UUID,
    and the parameter's value.

    """

    def __init__(self):
        """
        Initialize the object.

        Set the values to their default values.

        """
        self.finder = ParameterFinder()
        self.path: Uuid = Uuid("")
        self.parameter: Uuid = Uuid("")
        self.value = ParameterValue()
        self.temp_name = ""

    def __repr__(self) -> str:
        """
        Provide the string representation of the object.

        Returns:
            str: string representation

        """
        param = self.finder.find(self.parameter)
        pval_str = str(self.value)
        if param:
            return f'ParameterOverrides(path="{self.path}", parameter="{param.name}", value="{pval_str}")'
        return f'ParameterOverrides(path="{self.path}", parameter=<unknown>, value="{pval_str}")'

    def json(self) -> Dict[str, Any]:
        """
        Encode the object to a JSON dictionary.

        Returns:
            Dict[str, Any]: JSON-ish dictionary

        """
        return {
            "path": self.path,
            "parameter": self.parameter,
            "value": self.value,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Decode the JSON data.

        Parameters:
            data (Dict[str, Any]): JSON data to decode

        """
        self.path = Uuid(data["path"])
        self.parameter = Uuid(data["parameter"])
        val = data["value"]
        if isinstance(val, int):
            self.value = ParameterValue(val)
        else:
            self.value = ParameterValue()
            self.value.json_decode(val)
