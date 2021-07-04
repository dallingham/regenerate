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
Provides the export rules for the builder
"""
from typing import Dict, Any
from .json_base import JSONEncodable


class ExportData(JSONEncodable):
    """
    Provides the export rules for the builder. This includes
    the exporter name (option) and the destination file (path).
    """

    def __init__(self, exporter: str = "", target: str = ""):
        self.exporter: str = exporter
        self.target: str = str(target)
        self.options: Dict[str, str] = {}

    def json(self) -> Dict[str, Any]:
        "Convert object into a Dict for json export"
        return {
            "exporter": self.exporter,
            "target": str(self.target),
            "options": self.options,
        }

    def json_decode(self, data: Dict[str, Any]) -> None:
        """Convert JSON data back into an ExportData instance"""
        self.exporter = data["exporter"]
        self.target = str(data["target"])
        self.options = data["options"]
