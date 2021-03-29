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

from .json_base import JSONEncodable


class DocPages:
    def __init__(self):
        self.pages = {}

    def update_page(self, name: str, text: str):
        self.pages[name] = text

    def remove_page(self, name: str):
        if name in self.pages:
            del self.pages[name]

    def get_page_names(self):
        return list(self.pages.keys())

    def get_page(self, name: str):
        return self.pages[name]

    def json(self):
        return self.pages

    def json_decode(self, data):
        self.pages = data
