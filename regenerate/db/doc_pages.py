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
Manages document pages.

Document pages consist of the page (a text string holding the documentation),
a list of labels or tags, and a title.

"""

from typing import Dict, List, Optional
from .json_base import JSONEncodable


class Page(JSONEncodable):
    """
    Data associated with a page.

    Include text, title, and labels.
    """

    def __init__(self):
        """
        Initialize the object with empty values.

        Sets page and title to empty strings, labels to an empty list.

        """
        self.page: str = ""
        self.labels: List[str] = []
        self.title: str = ""


class DocPages:
    """
    Manages the documenation pages.

    Allow pages to be updated, deleted, or interated over.
    """

    def __init__(self):
        """
        Initialize the object with empty values.

        Creates an empty list of pages.
        """
        self.pages: List[Page] = []

    def update_page(self, page_name: str, text: str, tags: List[str]) -> None:
        """
        Add or update the page specified by the page_name.

        Parameters:
            page_name (str): name of the page

            text (str): text associated with the page

            tags (List[str]): list of tags associated with the page

        """
        for page in self.pages:
            if page.title == page_name:
                page.labels = tags
                page.page = text
                return
        page = Page()
        page.title = page_name
        page.labels = tags
        page.page = text
        self.pages.append(page)

    def remove_page(self, name: str) -> None:
        """
        Remove the page with the specified name.

        Parameters:
            name (str): Name of the page to remove

        """
        if self.pages:
            index = 0
            for index, page in enumerate(self.pages):
                if page.title == name:
                    break
            self.pages.pop(index)

    def get_page_names(self) -> List[str]:
        """
        Return a list of the page names.

        Returns:
            List[str]: list of page names in order of display

        """
        return [page.title for page in self.pages]

    def get_page(self, name: str) -> Optional[Page]:
        """
        Return the page associated with the name.

        Parameters:
            name (str): Name of the page to retrieve

        Returns:
            Page: Page associated with the name, or None if it does not exist

        """
        for page in self.pages:
            if page.title == name:
                return page
        return None

    def update_page_order(self, order: List[str]) -> None:
        """
        Rearrange the pages so that they match the order passed.

        Parameter:
            order (List[str]): new order of the pages

        """
        page_dict = {page.title: page for page in self.pages}
        self.pages = [page_dict[item] for item in order]

    def json(self) -> List[Dict[str, str]]:
        """
        Encode the class variables into a dictionary for JSON encoding.

        Returns:
           JSON data (Dict[str, Any]): Dictionary of data in JSON format

        """
        return [page.json() for page in self.pages]

    def json_decode(self, data) -> None:
        """
        Convert the incoming JSON data to the class variables.

        Parameters:
           data (Dict[str, Any]) - JSON data

        """
        self.pages = []
        if isinstance(data, dict):
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
