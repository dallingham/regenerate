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
from regenerate.ui.spell import Spell
from regenerate.ui.preview_editor import PreviewEditor, PREVIEW_ENABLED
from regenerate.settings.paths import GLADE_GTXT
from regenerate.ui.utils import clean_format_if_needed


class GroupDocEditor(object):
    def __init__(self, group_inst, callback, parent):

        builder = gtk.Builder()
        builder.add_from_file(GLADE_GTXT)
        self.callback = callback
        self.group_doc = builder.get_object('group_text')
        self.group_title = builder.get_object('group_title')
        self.group_inst = group_inst
        self.text_buf = builder.get_object('overview1').get_buffer()

        builder.get_object('overview1').modify_font(
            pango.FontDescription("monospace")
        )

        preview = PreviewEditor(
            self.text_buf,
            builder.get_object('scroll_webkit1')
        )

        self.text_buf.set_text(group_inst.docs)
        self.group_title.set_text(group_inst.title)

        builder.get_object("overview1").connect(
            "key-press-event",
            self.on_key_press_event
        )
        builder.get_object("button2").connect(
            "button-press-event",
            self._save
        )
        builder.get_object("button3").connect(
            "button-press-event",
            self._cancel
        )

        builder.get_object('title').set_text(group_inst.name)
        if PREVIEW_ENABLED:
            preview.enable()
        else:
            preview.disable()
        self.__spell = Spell(builder.get_object('overview1'))

        self.group_doc.connect('delete-event', self.on_delete_event)
        self.group_doc.connect('destroy-event', self.on_destroy_event)
        self.group_doc.set_transient_for(parent)
        self.group_doc.show()

    def on_key_press_event(self, obj, event):
        if event.keyval == gtk.keysyms.F12:
            clean_format_if_needed(obj)
            return True
        return False

    def on_destroy_event(self, obj):
        self.__spell.detach()

    def on_delete_event(self, obj, event):
        self.__spell.detach()

    def _cancel(self, obj, data):
        self.group_doc.destroy()

    def _save(self, obj, data):

        new_docs = self.text_buf.get_text(
            self.text_buf.get_start_iter(),
            self.text_buf.get_end_iter(),
            False
        )

        if self.group_inst.docs != new_docs:
            self.group_inst.docs = new_docs
            self.callback(True)

        new_title = self.group_title.get_text()
        if self.group_inst.title != new_title:
            self.group_inst.title = new_title
            self.callback(True)

        self.group_doc.destroy()
