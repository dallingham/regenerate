#
# Manage registers in a hardware design
#
# Copyright (C) 2009  Donald N. Allingham
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

import os
from gi.repository import Gtk, Gdk
from regenerate.ui.enums import ExportPages


class TextCombo(Gtk.ComboBox):
    def __init__(self):
        super().__init__()

        self.model = Gtk.ListStore(str, str)
        cell = Gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 0)
        self.set_model(self.model)
        self.set_active(0)

    def append_text(self, item, value=""):
        self.model.append(row=[item, value])
        self.set_active(0)

    def get_active_text(self):
        node = self.get_active_iter()
        try:
            val = self.model.get_value(node, 0)
        except:
            val = None
        return val

    def get_active_value(self):
        node = self.get_active_iter()
        try:
            val = self.model.get_value(node, 1)
        except:
            val = None
        return val


class ExportAssistant(Gtk.Assistant):
    def __init__(
        self,
        project_name,
        optlist,
        register_sets,
        group_names,
        save_callback,
        parent,
    ):
        super().__init__()

        self.set_transient_for(parent)
        self.project_name = project_name
        self.save_callback = save_callback
        self.connect("delete_event", self.cb_on_delete)
        self.connect("close", self.cb_close)
        self.connect("cancel", self.cb_cancel)
        self.connect("prepare", self.prepare)
        self.set_forward_page_func(self.forward)
        self.set_default_size(600, 500)

        self.page0 = self.build_page_0(optlist)
        self.page1 = self.build_page_1(register_sets)
        self.page2 = self.build_page_2(group_names)
        self.page3 = self.build_page_3()
        self.sum = self.build_summary()

    def selected_export(self):
        model = self.export_combo.get_model()
        return model.get_value(self.export_combo.get_active_iter(), 0)

    def selected_export_is_project(self):
        model = self.export_combo.get_model()
        return model.get_value(self.export_combo.get_active_iter(), 1) == 2

    def selected_export_is_group(self):
        model = self.export_combo.get_model()
        return model.get_value(self.export_combo.get_active_iter(), 1) == 1

    def selected_extension(self):
        model = self.export_combo.get_model()
        return model.get_value(self.export_combo.get_active_iter(), 2)

    def selected_register_set(self):
        return self.register_combo.get_active_text()

    def prepare(self, _obj, page):
        self.set_page_complete(page, True)
        if page == self.sum:
            self.populate_summary()
        if page == self.page3:
            filename = self.choose.get_filename()
            if not filename:
                if self.selected_export_is_project():
                    value = self.project_name
                elif self.selected_export_is_group():
                    value = self.group_combo.get_active_text() + "_reg_decode"
                else:
                    value = self.register_combo.get_active_text()

                filename = value + self.selected_extension()
                self.choose.set_current_name(filename)

    def forward(self, current_page):
        if current_page == 0:
            if self.selected_export_is_project():
                return ExportPages.FILE_SELECT
            if self.selected_export_is_group():
                return ExportPages.GROUP_SELECT
            return ExportPages.REGSET_SELECT
        if current_page == ExportPages.REGSET_SELECT:
            return ExportPages.GROUP_SELECT
        if current_page == ExportPages.GROUP_SELECT:
            return ExportPages.FILE_SELECT
        return current_page + 1

    def cb_on_delete(self, widget, event):
        self.destroy()

    def cb_cancel(self, assistant):
        self.destroy()

    def cb_close(self, assistant):
        filename = self.choose.get_filename()

        model = self.export_combo.get_model()
        sel_fmt = model.get_value(self.export_combo.get_active_iter(), 0)

        sel_set = self.register_combo.get_active_value()
        sel_grp = self.group_combo.get_active_value()

        if filename:
            self.save_callback(filename, sel_fmt, sel_set, sel_grp)
        self.emit("delete_event", Gdk.Event(Gdk.EventType.NOTHING))

    def build_page_0(self, optlist):
        # Construct page 0
        table = Gtk.Table(3, 3)
        table.set_border_width(3)
        table.show()

        label = Gtk.Label(
            "There are many different types of files that can "
            "be exported. Some files are based on a selected "
            "register set, some are based on a group of "
            "registers, others are based on the entire "
            "project.\n\nSelect the type file that you "
            "wish to generate."
        )
        label.set_line_wrap(True)
        label.show()
        table.attach(
            label,
            0,
            3,
            0,
            1,
            Gtk.AttachOptions.FILL | Gtk.AttachOptions.EXPAND,
            Gtk.AttachOptions.SHRINK,
        )

        self.export_combo = Gtk.ComboBox()
        self.export_combo.show()

        cell = Gtk.CellRendererText()
        model = Gtk.ListStore(str, int, str)

        for item in optlist:
            model.append(row=item)
        self.export_combo.pack_start(cell, True)
        self.export_combo.add_attribute(cell, "text", 0)
        self.export_combo.set_active(0)
        self.export_combo.set_model(model)

        table.attach(
            self.export_combo,
            1,
            2,
            1,
            2,
            Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL,
            Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL,
        )

        self.append_page(table)
        self.set_page_title(table, "Choose the export type")
        self.set_page_type(table, Gtk.AssistantPageType.CONTENT)
        self.set_page_complete(table, True)
        return table

    def build_page_1(self, register_sets):
        # Construct page 0
        table = Gtk.Table(3, 3)
        table.set_border_width(3)
        table.show()

        label = Gtk.Label(
            "The selected export file is requires that "
            "you select a register set as the source of "
            "your data.\n\n"
        )
        label.set_line_wrap(True)
        label.show()
        table.attach(label, 0, 3, 0, 1)

        self.register_combo = TextCombo()
        self.register_combo.show()
        for item in register_sets:
            self.register_combo.append_text(item[0], item[1])
        table.attach(
            self.register_combo, 1, 2, 1, 2, 0, Gtk.AttachOptions.EXPAND
        )

        self.append_page(table)
        self.set_page_title(table, "Choose the register set")
        self.set_page_type(table, Gtk.AssistantPageType.CONTENT)
        return table

    def build_page_2(self, groups):
        # Construct page 0
        table = Gtk.Table(3, 3)
        table.set_border_width(3)
        table.show()

        label = Gtk.Label(
            "The selected export file is requires that "
            "you select a block as the source of "
            "your data.\n\n"
        )
        label.set_line_wrap(True)
        label.show()
        table.attach(label, 0, 3, 0, 1)

        self.group_combo = TextCombo()
        self.group_combo.show()
        for item in groups:
            self.group_combo.append_text(item[0], item[1])
        table.attach(self.group_combo, 1, 2, 1, 2, 0, Gtk.AttachOptions.EXPAND)

        self.append_page(table)
        self.set_page_title(table, "Choose the block")
        self.set_page_type(table, Gtk.AssistantPageType.CONTENT)
        return table

    def build_page_3(self):
        # Construct page 0
        self.choose = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.SAVE)
        self.choose.set_current_folder(os.curdir)
        self.choose.show()
        self.choose.set_border_width(12)
        self.append_page(self.choose)
        self.set_page_title(self.choose, "Choose the destination file")
        self.set_page_type(self.choose, Gtk.AssistantPageType.CONTENT)
        return self.choose

    def populate_summary(self):
        msg = "Added to the builder"
        destination = self.choose.get_filename()
        model = self.export_combo.get_model()
        export_iter = self.export_combo.get_active_iter()
        export_project = model.get_value(export_iter, 1)
        export_type = model.get_value(export_iter, 0)
        register_set = self.register_combo.get_active_text()

        self.export_obj.set_text(export_type)
        if export_project:
            self.register_obj.set_text("Entire Project")
        else:
            self.register_obj.set_text(register_set)
        self.dest_obj.set_text(destination)
        self.execute_obj.set_text(msg)

    def build_summary(self):
        self.sum = Gtk.Table(4, 5)
        self.sum.set_row_spacings(6)
        self.sum.set_col_spacings(6)
        self.sum.attach(
            MyLabel("Export type:"), 1, 2, 0, 1, Gtk.AttachOptions.FILL, 0
        )
        self.sum.attach(
            MyLabel("Register set:"), 1, 2, 1, 2, Gtk.AttachOptions.FILL, 0
        )
        self.sum.attach(
            MyLabel("Output file:"), 1, 2, 2, 3, Gtk.AttachOptions.FILL, 0
        )
        self.sum.attach(
            MyLabel("Execute status:"), 1, 2, 3, 4, Gtk.AttachOptions.FILL, 0
        )
        self.sum.set_border_width(12)
        self.export_obj = MyLabel()
        self.register_obj = MyLabel()
        self.dest_obj = MyLabel()
        self.execute_obj = MyLabel()
        self.sum.attach(
            self.export_obj,
            2,
            3,
            0,
            1,
            Gtk.AttachOptions.FILL | Gtk.AttachOptions.EXPAND,
            0,
        )
        self.sum.attach(
            self.register_obj,
            2,
            3,
            1,
            2,
            Gtk.AttachOptions.FILL | Gtk.AttachOptions.EXPAND,
            0,
        )
        self.sum.attach(
            self.dest_obj,
            2,
            3,
            2,
            3,
            Gtk.AttachOptions.FILL | Gtk.AttachOptions.EXPAND,
            0,
        )
        self.sum.attach(
            self.execute_obj,
            2,
            3,
            3,
            4,
            Gtk.AttachOptions.FILL | Gtk.AttachOptions.EXPAND,
            0,
        )
        self.sum.show_all()

        self.append_page(self.sum)
        self.set_page_title(self.sum, "Completion")
        self.set_page_type(self.sum, Gtk.AssistantPageType.CONFIRM)
        self.show()
        return self.sum


class MyLabel(Gtk.Label):
    def __init__(self, text=""):
        if text is None:
            text = ""
        super().__init__(text)
        self.set_alignment(0, 0)

    def set_text(self, text):
        if text is None:
            text = ""
        Gtk.Label.set_text(self, text)
