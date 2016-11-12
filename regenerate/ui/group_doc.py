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
Provides a preview editor, tying a text buffer to a webkit display. All
changes to the buffer cause an update on the webkit display, after the
text is converted from restructuredText to HTML.
"""

import gtk
import pango
from spell import Spell
from preview_editor import PreviewEditor, PREVIEW_ENABLED
from regenerate.settings.paths import GLADE_GTXT


class GroupDocEditor(object):
    def __init__(self, group_inst):

        builder = gtk.Builder()
        builder.add_from_file(GLADE_GTXT)
        self.group_doc = builder.get_object('group_text')
        self.group_title = builder.get_object('group_title')
        self.group_inst = group_inst
        self.buffer = builder.get_object('overview1').get_buffer()
        pango_font = pango.FontDescription("monospace")
        builder.get_object('overview1').modify_font(pango_font)

        self.__prj_preview = PreviewEditor(
            self.buffer, builder.get_object('scroll_webkit1'))

        self.buffer.set_text(group_inst.docs)
        self.group_title.set_text(group_inst.title)

        builder.get_object("button2").connect("button-press-event", self._save)
        builder.get_object("button3").connect("button-press-event",
                                              self._cancel)
        builder.get_object('title').set_text(group_inst.name)
        if PREVIEW_ENABLED:
            self.__prj_preview.enable()
        else:
            self.__prj_preview.disable()
        self.__spell = Spell(builder.get_object('overview1'))

        self.group_doc.connect('delete-event', self.on_delete_event)
        self.group_doc.connect('destroy-event', self.on_destroy_event)
        self.group_doc.show()

    def on_destroy_event(self, obj):
        self.__spell.detach()

    def on_delete_event(self, obj, event):
        self.__spell.detach()

    def _cancel(self, obj, data):
        self.group_doc.destroy()

    def _save(self, obj, data):
        self.group_inst.docs = self.buffer.get_text(
            self.buffer.get_start_iter(), self.buffer.get_end_iter(), False)
        self.group_inst.title = self.group_title.get_text()
        self.group_doc.destroy()
