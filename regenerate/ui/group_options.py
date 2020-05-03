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

from gi.repository import Gtk

DEF_DIALOG_FLAGS = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
DEF_DIALOG_BUTTONS = (
    Gtk.STOCK_CANCEL,
    Gtk.ResponseType.REJECT,
    Gtk.STOCK_OK,
    Gtk.ResponseType.ACCEPT,
)


class GroupOptions(Gtk.Dialog):
    def __init__(self, instance, modified, parent, width=600, height=260):

        super().__init__(
            title="Instance Options (%s)" % instance.inst,
            parent=parent,
            flags=DEF_DIALOG_FLAGS,
            buttons=DEF_DIALOG_BUTTONS,
        )
        self.instance = instance
        self.val_no_uvm = False
        self.val_no_decode = False
        self.val_single_decode = False
        self.val_array = False

        self.set_size_request(width, height)
        self.build_window(instance.inst)

        changed = False
        response = self.run()
        if response in (Gtk.ResponseType.ACCEPT, Gtk.ResponseType.OK):
            if self.force_arrays.get_active() != self.instance.array:
                self.instance.array = self.force_arrays.get_active()
                changed = True
            if self.decode_exclude.get_active() != self.instance.no_decode:
                self.instance.no_decode = self.decode_exclude.get_active()
                changed = True
            if self.uvm_exclude.get_active() != self.instance.no_uvm:
                self.instance.no_uvm = self.uvm_exclude.get_active()
                changed = True
            if self.single_decode.get_active() != self.instance.single_decode:
                self.instance.single_decode = self.single_decode.get_active()
                changed = True
        if changed:
            modified(True)
        self.hide()
        self.destroy()

    def build_window(self, title):

        area = self.get_content_area()
        title_label = Gtk.Label()
        title_label.set_xalign(0.5)
        title_label.set_markup("<b>%s</b>" % title)

        table = Gtk.Table(4, 5)
        table.set_row_spacings(6)
        table.set_col_spacings(6)

        self.uvm_exclude = Gtk.CheckButton(
            "Exclude the instance from the UVM register package")
        self.uvm_exclude.set_active(self.instance.no_uvm)
        self.val_no_uvm = self.instance.no_uvm

        table.attach(
            self.uvm_exclude,
            1,
            3,
            1,
            2,
            xoptions=Gtk.AttachOptions.FILL,
            yoptions=Gtk.AttachOptions.FILL,
        )

        self.decode_exclude = Gtk.CheckButton(
            "Exclude from register decode"
        )
        self.decode_exclude.set_active(self.instance.no_decode)
        self.val_no_decode = self.instance.no_decode

        table.attach(
            self.decode_exclude,
            1,
            3,
            2,
            3,
            xoptions=Gtk.AttachOptions.FILL,
            yoptions=Gtk.AttachOptions.FILL,
        )

        self.force_arrays = Gtk.CheckButton(
            "Force array notation even for scalar instances"
        )
        self.force_arrays.set_active(self.instance.array)
        self.val_array = self.instance.array

        table.attach(
            self.force_arrays,
            1,
            3,
            3,
            4,
            xoptions=Gtk.AttachOptions.FILL,
            yoptions=Gtk.AttachOptions.FILL,
        )

        self.single_decode = Gtk.CheckButton(
            "Use a single decode for arrays"
        )
        self.single_decode.set_active(self.instance.single_decode)
        self.val_single_decode = self.instance.single_decode

        table.attach(
            self.single_decode,
            1,
            3,
            4,
            5,
            xoptions=Gtk.AttachOptions.FILL,
            yoptions=Gtk.AttachOptions.FILL,
        )

        box = Gtk.VBox(spacing=6)
        box.pack_start(title_label, fill=True, expand=True, padding=12)
        box.pack_start(table, fill=True, expand=True, padding=12)
        area.add(box)

        self.show_all()
