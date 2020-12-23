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
Manages the search filter
"""

from regenerate.db import LOGGER
from regenerate.ui.enums import FilterField


class FilterManager:
    """
    Manages the search filter.
    """

    def __init__(self, obj, model=None):
        self._obj = obj
        self._model = model
        self._text = ""
        self._fields = (FilterField.ADDR, FilterField.NAME, FilterField.TOKEN)
        self._obj.connect("changed", self._filter_changed)

    def get_model(self):
        """Get the assocated model"""
        return self._model

    def text(self):
        """Get the search text"""
        return self._text.upper()

    def set_search_fields(self, fields):
        """Set the search fields and refilters the model"""
        self._fields = fields
        self._model.refilter()

    def refilter(self):
        """Applies the filter to the model"""
        self._model.refilter()

    def change_filter(self, model, set_func=False):
        """Changes the filter function"""
        self._model = model
        if set_func:
            model.set_visible_func(self.visible_cb)

    def _filter_changed(self, _obj):
        """Callback when the object emits 'changed'"""
        self._text = self._obj.get_text()
        self._model.refilter()

    def visible_cb(self, model, *obj):
        """Determines if the current cell should be visible"""
        node = obj[0]

        if self._text == "":
            return True
        try:
            search_text = self._text.upper()
            for i in self._fields:
                text = model.get_value(node, i).upper()
                if text.find(search_text) != -1:
                    return True
            return False
        except:
            LOGGER.error("Error filtering")
            return False
