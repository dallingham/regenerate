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
Manages document pages, which are simply name to string dictionaries.
"""

from typing import Dict, Any, List, Optional


class DocPages:
    """
    Manages the documenation pages, allowing pages to be updated,
    deleted, or interated over.
    """

    def __init__(self):
        self.pages: Dict[str, str] = {}

    def update_page(self, name: str, text: str) -> None:
        "Adds or updates the page specified by the name"
        self.pages[name] = text

    def remove_page(self, name: str) -> None:
        "Removes the page with the specified name"
        if name in self.pages:
            del self.pages[name]

    def get_page_names(self) -> List[str]:
        "Returns a list of the page names"
        return list(self.pages.keys())

    def get_page(self, name: str) -> Optional[str]:
        "Get the page associated with the name"
        return self.pages.get(name)

    def json(self) -> Dict[str, Any]:
        "Convert to a dictionary for JSON"
        return self.pages

    def json_decode(self, data: Dict[str, Any]) -> None:
        "Decode the JSON data"
        self.pages = data
