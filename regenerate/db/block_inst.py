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
Holds the information for a BlockInst.

The block instance describes the instantiation of a block. It contains:

  * name - name of the block instance
  * uuid - unique ID
  * blkid - the UUID of the corresponding block
  * address_base - address base of the block instance
  * hdl_path - HDL path segment from the top level to the block instance
  * repeat - repeat count (array dimension)
"""

from typing import Dict, Any
from .name_base import NameBase, Uuid


class BlockInst(NameBase):
    """
    BlockInst contains the information to describe the instantion of a block.

    A block instance adds the uuid of the block it instantiates, the base
    address, hdl path, and the repeat count.
    """

    def __init__(self, name: str = "", blkid: Uuid = Uuid("")) -> None:
        """
        Initialize the object.

        Parameters:
           name (str): name of the block instance
           blkid (Uuid): uuid of the block the instance references

        """
        super().__init__(name, Uuid(""))
        self.blkid = blkid
        self.address_base = 0
        self.hdl_path = ""
        self.repeat = 1

    def __repr__(self) -> str:
        """
        Display the text representation of the BlockInst.

        Returns:
           str: Representation of the object

        """
        return f'BlockInst(name="{self.name}", uuid="{self.uuid}", blkid="{self.blkid}")'

    def json_decode(self, data: Dict[str, Any]) -> None:
        """
        Decode the JSON compatible dictionary into the object.

        Parameters:
           data (Dict[str, Any]): JSON data

        """
        self.name = data["name"]
        self.uuid = Uuid(data["id"])
        self.blkid = data["blkid"]
        self.address_base = int(data["address_base"], 0)
        self.hdl_path = data["hdl_path"]
        self.description = data["description"]
        self.repeat = data["repeat"]

    def json(self) -> Dict[str, Any]:
        """
        Convert the object to a JSON compatible dictionary.

        Returns:
           Dict[str, Any]: Dictionary of JSON compatible data

        """
        return {
            "name": self.name,
            "id": self.uuid,
            "blkid": self.blkid,
            "address_base": f"{self.address_base}",
            "hdl_path": self.hdl_path,
            "description": self.description,
            "repeat": self.repeat,
        }
