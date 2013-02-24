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

from regenerate.db import LOGGER

ADDR_FIELD = 1
NAME_FIELD = 2
TOKEN_FIELD = 3


class FilterManager(object):

    def __init__(self, obj, model=None):
        self._obj = obj
        self._model = model
        self._text = ""
        self._fields = (ADDR_FIELD, NAME_FIELD, TOKEN_FIELD)

        self._obj.connect('changed', self._filter_changed)

    def get_model(self):
        return self._model

    def text(self):
        return self._text.upper()

    def set_search_fields(self, fields):
        self._fields = fields
        self._model.refilter()

    def refilter(self):
        self._model.refilter()

    def change_filter(self, model, set_func=False):
        self._model = model
        if set_func:
            model.set_visible_func(self.visible_cb)

    def _filter_changed(self, obj):
        self._text = self._obj.get_text()
        self._model.refilter()

    def visible_cb(self, model, iter):
        if self._text == "":
            return True
        try:
            search_text = self._text.upper()
            for i in self._fields:
                text = model.get_value(iter, i).upper()
                if text.find(search_text) != -1:
                    return True
            return False
        except:
            LOGGER.error("Error filtering")
            return False
