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

import gtk


class ExportAssistant(gtk.Assistant):

    def __init__(self, project_name, optlist, register_sets, save_callback, run_callback):
        gtk.Assistant.__init__(self)

        self.project_name = project_name
        self.save_callback = save_callback
        self.run_callback = run_callback
        self.connect('delete_event', self.cb_on_delete)
        self.connect('close', self.cb_close)
        self.connect('cancel', self.cb_close)
        self.connect('prepare', self.prepare)
        self.set_forward_page_func(self.forward)
        self.set_default_size(600, 500)

        self.page0 = self.build_page_0(optlist)
        self.page1 = self.build_page_1(register_sets)
        self.page2 = self.build_page_2()
        self.page3 = self.build_page_3()
        self.summary = self.build_summary()

    def selected_export(self):
        model = self.export_combo.get_model()
        return model.get_value(self.export_combo.get_active_iter(), 0)

    def selected_export_is_project(self):
        model = self.export_combo.get_model()
        return model.get_value(self.export_combo.get_active_iter(), 1)

    def selected_extension(self):
        model = self.export_combo.get_model()
        return model.get_value(self.export_combo.get_active_iter(), 2)

    def selected_register_set(self):
        model = self.register_combo.get_model()
        return model.get_value(self.register_combo.get_active_iter(), 0)

    def prepare(self, obj, page):
        self.set_page_complete(page, True)
        if page == self.summary:
            self.populate_summary()
        if page == self.page2:
            filename = self.choose.get_filename()
            if not filename:
                model = self.register_combo.get_model()
                value = model.get_value(self.register_combo.get_active_iter(), 0)
                ext = self.selected_extension()
                filename = value + ext
                self.choose.set_current_name(filename)

    def forward(self, current_page):
        if current_page == 0:
            value = self.selected_export_is_project()
            if value:
                return 1
            else:
                return 2
        else:
            return current_page + 1

    def cb_on_delete(self, widget, event):
        self.destroy()

    def cb_close(self, assistant):
        filename = self.choose.get_filename()

        model = self.export_combo.get_model()
        sel_fmt = model.get_value(self.export_combo.get_active_iter(), 0)

        model = self.register_combo.get_model()
        sel_set = model.get_value(self.register_combo.get_active_iter(), 0)

        if filename:
            if self.check_box.get_active():
                self.save_callback(filename, sel_fmt, sel_set)
            else:
                self.run_callback(filename, sel_fmt, sel_set)
        self.emit('delete_event', gtk.gdk.Event(gtk.gdk.NOTHING))

    def build_page_0(self, optlist):
        # Construct page 0
        table = gtk.Table(3, 3)
        table.set_border_width(3)
        table.show()

        label = gtk.Label("There are many different types of files that can "
                          "be exported. Some files are based on a selected "
                          "register set, others are based on the entire "
                          "project.\n\nSelect the type file that you "
                          "wish to generate.")
        label.set_line_wrap(True)
        label.show()
        table.attach(label, 0, 3, 0, 1)

        self.export_combo = gtk.ComboBox()
        self.export_combo.show()

        cell = gtk.CellRendererText()
        model = gtk.ListStore(str, bool, str)
        for item in optlist:
            model.append(row=item)
        self.export_combo.pack_start(cell, True)
        self.export_combo.add_attribute(cell, 'text', 0)
        self.export_combo.set_active(0)
        self.export_combo.set_model(model)

        table.attach(self.export_combo, 1, 2, 1, 2, 0, gtk.EXPAND)

        self.append_page(table)
        self.set_page_title(table, 'Choose the export type')
        self.set_page_type(table, gtk.ASSISTANT_PAGE_CONTENT)
        self.set_page_complete(table, True)
        return table

    def build_page_1(self, register_sets):
        # Construct page 0
        table = gtk.Table(3, 3)
        table.set_border_width(3)
        table.show()

        label = gtk.Label("The selected export file is requires that "
                          "you select a register set as the source of "
                          "your data.\n\n")
        label.set_line_wrap(True)
        label.show()
        table.attach(label, 0, 3, 0, 1)

        self.register_combo = gtk.ComboBox()
        self.register_combo.show()
        cell = gtk.CellRendererText()
        model = gtk.ListStore(str)
        for item in register_sets:
            model.append(row=[item])
        self.register_combo.pack_start(cell, True)
        self.register_combo.add_attribute(cell, 'text', 0)
        self.register_combo.set_active(0)
        self.register_combo.set_model(model)
        table.attach(self.register_combo, 1, 2, 1, 2, 0, gtk.EXPAND)

        self.append_page(table)
        self.set_page_title(table, 'Choose the register set')
        self.set_page_type(table, gtk.ASSISTANT_PAGE_CONTENT)
        return table

    def build_page_2(self):
        # Construct page 0
        self.choose = gtk.FileChooserWidget(action=gtk.FILE_CHOOSER_ACTION_SAVE)
        self.choose.show()
        self.choose.set_border_width(12)
        self.append_page(self.choose)
        self.set_page_title(self.choose, 'Choose the destination file')
        self.set_page_type(self.choose, gtk.ASSISTANT_PAGE_CONTENT)
        return self.choose

    def build_page_3(self):
        # Construct page 0
        table = gtk.Table(3, 3)
        table.set_border_width(3)
        table.show()

        label = gtk.Label("You can add this export rule to the export "
                          "builder. If you add it to the builder, you can "
                          "rebuild this file directly from the builder "
                          "without having to rerun this assistant. The "
                          "builder will remember add the details, including "
                          "the destination file, and will let you know when "
                          "it needs to be rebuilt due to changes in the "
                          "selected register set or project.")
        label.set_line_wrap(True)
        label.show()
        table.attach(label, 0, 3, 0, 1)

        self.check_box = gtk.CheckButton("Add this rule to the builder")
        self.check_box.show()
        table.attach(self.check_box, 1, 2, 1, 2, 0, gtk.EXPAND)

        self.append_page(table)
        self.set_page_title(table, 'Add to the builder')
        self.set_page_type(table, gtk.ASSISTANT_PAGE_CONTENT)
        return table

    def populate_summary(self):
        if self.check_box.get_active():
            msg = "Added to the builder"
        else:
            msg = "Immediately executed"
        destination = self.choose.get_filename()
        model = self.export_combo.get_model()
        export_project = model.get_value(self.export_combo.get_active_iter(), 1)
        export_type = model.get_value(self.export_combo.get_active_iter(), 0)
        model = self.register_combo.get_model()
        register_set = model.get_value(self.register_combo.get_active_iter(), 0)

        self.export_obj.set_text(export_type)
        if export_project:
            self.register_obj.set_text(register_set)
        else:
            self.register_obj.set_text("Entire Project")
        self.dest_obj.set_text(destination)
        self.execute_obj.set_text(msg)

    def build_summary(self):
        self.summary = gtk.Table(4, 5)
        self.summary.set_row_spacings(6)
        self.summary.set_col_spacings(6)
        self.summary.attach(MyLabel('Export type:'), 1, 2, 0, 1, gtk.FILL, 0)
        self.summary.attach(MyLabel('Register set:'), 1, 2, 1, 2, gtk.FILL, 0)
        self.summary.attach(MyLabel('Output file:'), 1, 2, 2, 3, gtk.FILL, 0)
        self.summary.attach(MyLabel('Execute status:'), 1, 2, 3, 4, gtk.FILL, 0)
        self.summary.set_border_width(12)
        self.export_obj = MyLabel()
        self.register_obj = MyLabel()
        self.dest_obj = MyLabel()
        self.execute_obj = MyLabel()
        self.summary.attach(self.export_obj, 2, 3, 0, 1, gtk.FILL|gtk.EXPAND, 0)
        self.summary.attach(self.register_obj, 2, 3, 1, 2, gtk.FILL|gtk.EXPAND, 0)
        self.summary.attach(self.dest_obj, 2, 3, 2, 3, gtk.FILL|gtk.EXPAND, 0)
        self.summary.attach(self.execute_obj, 2, 3, 3, 4, gtk.FILL|gtk.EXPAND, 0)
        self.summary.show_all()

        self.append_page(self.summary)
        self.set_page_title(self.summary, 'Completion')
        self.set_page_type(self.summary, gtk.ASSISTANT_PAGE_CONFIRM)
        self.show()
        return self.summary

class MyLabel(gtk.Label):

    def __init__(self, text=""):
        if text == None:
            text = ""
        gtk.Label.__init__(self, text)
        self.set_alignment(0, 0)

    def set_text(self, text):
        if text == None:
            text = ""
        gtk.Label.set_text(self, text)
    
