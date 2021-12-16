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

from typing import Dict, Any, List, Optional, Tuple
from .json_base import JSONEncodable


class Page(JSONEncodable):
    def __init__(self):
        self.page: str = ""
        self.labels: List[str] = []
        self.title: str = ""


class DocPages:
    """
    Manages the documenation pages, allowing pages to be updated,
    deleted, or interated over.
    """

    def __init__(self):
        self.pages: List[Page] = []

    def update_page(self, name: str, text: str, tags: List[str]) -> None:
        "Adds or updates the page specified by the name"
        for page in self.pages:
            if page.title == name:
                page.labels = tags
                page.page = text
                return
        page = Page()
        page.title = name
        page.labels = tags
        page.page = text
        self.pages.append(page)

    def remove_page(self, name: str) -> None:
        "Removes the page with the specified name"
        for index, page in enumerate(self.pages):
            if page.title == name:
                break
        self.pages.pop(index)

    def get_page_names(self) -> List[str]:
        "Returns a list of the page names"
        return [page.title for page in self.pages]

    def get_page(self, name: str) -> Optional[Page]:
        "Get the page associated with the name"
        for page in self.pages:
            if page.title == name:
                return page
        return None

    def update_page_order(self, order: List[str]) -> None:
        page_dict = {}
        for page in self.pages:
            page_dict[page.title] = page

        new_list = []
        for item in order:
            new_list.append(page_dict[item])

        self.pages = new_list

    def json(self) -> List[Dict[str, str]]:
        "Convert to a dictionary for JSON"
        return [page.json() for page in self.pages]

    def json_decode(self, data) -> None:
        "Decode the JSON data"
        self.pages = []
        if type(data) == dict:
            for page_name, value in data.items():
                page = Page()
                page.title = page_name
                if isinstance(value, str):
                    page.page = value
                    page.labels = ["Confidential"]
                else:
                    page.page = value[0]
                    page.labels = value[1]
                self.pages.append(page)
        else:
            for item in data:
                page = Page()
                page.json_decode(item)
                self.pages.append(page)
