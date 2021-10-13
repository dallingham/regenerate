from gi.repository import Gtk
from regenerate.db import RegProject
from regenerate.writers import (
    EXPORTERS,
    GRP_EXPORTERS,
    PRJ_EXPORTERS,
    ProjectType,
)
from .columns import ReadOnlyColumn


class Assistant(Gtk.Assistant):
    def __init__(self, project: RegProject):
        Gtk.Assistant.__init__(self)
        self.set_title("Assistant")
        self.set_default_size(1150, 600)
        self.connect("cancel", self.on_cancel_clicked)
        self.connect("close", self.on_close_clicked)
        self.connect("apply", self.on_apply_clicked)
        self.connect("prepare", self.on_prepare_clicked)

        self.project = project
        self.format_list = Gtk.TreeView()
        self.format_model = Gtk.ListStore(str, str, object, int)

        self.build_intro()
        self.build_format_content()
        self.build_source_content()
        self.build_confirm()

    def build_intro(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.INTRO)
        self.set_page_title(box, "Introduction")
        label = Gtk.Label(
            label="This rule builder will guide you in creating "
            "rules that will build output files from the data "
            "in this database."
        )
        label.set_line_wrap(True)
        box.pack_start(label, True, True, 0)
        self.set_page_complete(box, True)

    def build_format_content(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.CONTENT)
        self.set_page_title(box, "Select Output Format")
        label = Gtk.Label(label="Select the output format")
        label.set_line_wrap(True)
        box.pack_start(label, False, False, 12)

        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)
        self.build_format_list()
        scroll.add(self.format_list)
        box.pack_start(scroll, True, True, 12)
        self.set_page_complete(box, True)

    def build_source_content(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.CONTENT)
        self.set_page_title(box, "Select Data Source")
        self.source_label = Gtk.Label(
            label="Select the data source of the file"
        )
        self.source_label.set_line_wrap(True)
        box.pack_start(self.source_label, False, False, 12)

        scroll = Gtk.ScrolledWindow()
        select_list = self.build_source_list()
        scroll.add(select_list)
        box.pack_start(scroll, True, True, 12)
        self.set_page_complete(box, True)

    def build_source_list(self):
        source_list = Gtk.TreeView()
        self.source_model = Gtk.ListStore(str, str, object)
        source_list.set_model(self.source_model)
        column = ReadOnlyColumn("Source", 0)
        column.set_min_width(250)
        source_list.append_column(column)
        column = ReadOnlyColumn("Description", 0)
        source_list.append_column(column)
        return source_list

    def build_format_list(self):
        self.format_list.set_model(self.format_model)
        column = ReadOnlyColumn("Format", 0)
        column.set_min_width(250)
        self.format_list.append_column(column)
        column = ReadOnlyColumn("Description", 1)
        self.format_list.append_column(column)

        for exp in EXPORTERS:
            self.format_model.append(
                row=[
                    exp.type[1],
                    exp.full_description,
                    exp,
                    ProjectType.REGSET,
                ]
            )
        for exp in GRP_EXPORTERS:
            self.format_model.append(
                row=[exp.type[1], exp.full_description, exp, ProjectType.BLOCK]
            )
        for exp in PRJ_EXPORTERS:
            self.format_model.append(
                row=[
                    exp.type[1],
                    exp.full_description,
                    exp,
                    ProjectType.PROJECT,
                ]
            )

    def build_complete(self):

        self.complete = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(self.complete)
        self.set_page_type(self.complete, Gtk.AssistantPageType.PROGRESS)
        self.set_page_title(self.complete, "Page 3: Progress")
        label = Gtk.Label(
            label="A 'Progress' page is used to prevent changing pages "
            "within the Assistant before a long-running process has "
            "completed. The 'Continue' button will be marked as insensitive "
            "until the process has finished. Once finished, the button will "
            "become sensitive."
        )
        label.set_line_wrap(True)
        self.complete.pack_start(label, True, True, 0)
        checkbutton = Gtk.CheckButton(label="Mark page as complete")
        checkbutton.connect("toggled", self.on_complete_toggled)
        self.complete.pack_start(checkbutton, False, False, 0)

    def build_confirm(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.CONFIRM)
        self.set_page_title(box, "Page 4: Confirm")
        label = Gtk.Label(
            label="The 'Confirm' page may be set as the final page in "
            "the Assistant, however this depends on what the Assistant "
            "does. This page provides an 'Apply' button to explicitly "
            "set the changes, or a 'Go Back' button to correct any mistakes."
        )
        label.set_line_wrap(True)
        box.pack_start(label, True, True, 0)
        self.set_page_complete(box, True)

    def get_exporter(self):
        selection = self.format_list.get_selection()
        model, node = selection.get_selected()
        print(model.get_value(node, 0))
        print(model.get_value(node, 1))
        print(model.get_value(node, 2))
        print(model.get_value(node, 3))
        return (model.get_value(node, 2), model.get_value(node, 3))

    def on_apply_clicked(self, *_args):
        print("The 'Apply' button has been clicked")

    def on_close_clicked(self, *_args):
        print("The 'Close' button has been clicked")
        Gtk.main_quit()

    def on_cancel_clicked(self, *_args):
        print("The Assistant has been cancelled.")
        Gtk.main_quit()

    def on_complete_toggled(self, checkbutton):
        self.set_page_complete(self.complete, checkbutton.get_active())

    def on_prepare_clicked(self, _assistant: Gtk.Assistant, _page):
        PRJ_SOURCE = ("register set", "block", "project")
        page = self.get_current_page()
        if page == 1:
            exp, category = self.get_exporter()
            if category == ProjectType.REGSET:
                rsets = sorted(
                    self.project.regsets.values(), key=lambda x: x.name
                )
                self.source_model.clear()
                for regset in rsets:
                    self.source_model.append(
                        row=[regset.name, regset.descriptive_title, regset]
                    )
        elif page == 2:
            exp, category = self.get_exporter()
            format = exp.type[1]
            source = PRJ_SOURCE[category]
            self.source_label.set_text(
                f"The {format} format requires that you select a {source} as the data source"
            )

        print(self.get_current_page())


# Gtk.main()
