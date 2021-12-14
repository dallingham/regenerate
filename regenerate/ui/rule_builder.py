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
Provides the rule builder for the build tool.
"""

import os
from enum import IntEnum
from typing import Callable, Tuple

from gi.repository import Gtk

from regenerate.db import RegProject
from regenerate.writers import (
    EXPORTERS,
    GRP_EXPORTERS,
    PRJ_EXPORTERS,
    ProjectType,
)
from regenerate.writers.export_info import ExportInfo
from .columns import ReadOnlyColumn, ToggleColumn


class PageId(IntEnum):
    "Page names for the Assistant pages"

    INTRO = 0
    EXPORTER = 1
    SOURCE = 2
    OPTIONS = 3
    FILENAME = 4
    CONFIRM = 5


def add_row_to_grid(grid: Gtk.Grid, row: int, str1: str, str2: str) -> None:
    "Adds a row of two labels to the grid"

    label1 = Gtk.Label(label=str1)
    label1.set_alignment(1.0, 0.5)
    label2 = Gtk.Label(label=str2)
    label2.set_alignment(0, 0.5)
    grid.attach(label1, 0, row, 1, 1)
    grid.attach(label2, 1, row, 1, 1)


class RuleBuilder(Gtk.Assistant):
    """
    Guides the user through the process of creating a builder by using
    a Gtk.Assistant and information in the Exporter's ExportInfo
    structure.
    """

    def __init__(self, project: RegProject, callback: Callable):
        Gtk.Assistant.__init__(self)
        self.callback = callback
        self.set_title("Rule Builder")
        self.set_default_size(1150, 600)

        self._project = project
        self._widgets = {}
        self._format_list = Gtk.TreeView()
        self._format_mdl = Gtk.ListStore(str, str, object, int, str)
        self._source_mdl = Gtk.ListStore(str, str, object)
        self._reginst_mdl = Gtk.ListStore(bool, str, str, object)
        self._addrmap_mdl = Gtk.ListStore(str, str, object)
        self._addrmaps_mdl = Gtk.ListStore(bool, str, str, object)
        self._addrmap_table = Gtk.TreeView()
        self._addrmaps_table = Gtk.TreeView()

        self._setup_buttons()
        self._build_intro()
        self._build_format_content()
        self._build_source_content()
        self._build_options_content()
        self._build_filename_content()
        self._build_confirm()

    def _setup_buttons(self) -> None:
        """
        Connects buttons to the callback functions, and establishes the forward
        function to control the flow.
        """

        self.connect("cancel", self._on_cancel_clicked)
        self.connect("close", self._on_close_clicked)
        self.connect("apply", self._on_apply_clicked)
        self.connect("prepare", self._on_prepare_clicked)
        self.set_forward_page_func(self._on_page_forward)

    def _build_intro(self) -> None:
        """
        Builds the introduction page, which does nothing by provide some
        information on how to use the rule builder.
        """

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.INTRO)
        self.set_page_title(box, "Introduction")
        label = Gtk.Label(
            label="This rule builder will guide you in creating "
            "rules that will build output files from the data "
            "in this database.\n\nThere are three types of rules "
            "based off their data source. They can use a single "
            "register set, a single block, or the entire project."
        )
        label.set_line_wrap(True)
        box.pack_start(label, True, True, 0)
        self.set_page_complete(box, True)

    def _build_format_content(self) -> None:
        """
        The first thing we need is the exporter. So we build a page which
        allows them to select the exporter.
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.CONTENT)
        self.set_page_title(box, "Select Output Format")
        label = Gtk.Label(label="Select the output format")
        label.set_line_wrap(True)
        box.pack_start(label, False, False, 9)

        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)

        self._build_format_list()
        scroll.add(self._format_list)

        box.pack_start(scroll, True, True, 9)
        self.set_page_complete(box, True)

    def _build_source_content(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.CONTENT)
        self.set_page_title(box, "Select Data Source")
        self.source_label = Gtk.Label(
            label="Select the data source of the file"
        )
        self.source_label.set_line_wrap(True)
        box.pack_start(self.source_label, False, False, 9)

        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)

        self.source_list = self._build_source_list()
        scroll.add(self.source_list)
        self.source_list.get_selection().select_path((0,))
        box.pack_start(scroll, True, True, 9)
        self.set_page_complete(box, True)

    def _build_options_content(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.CONTENT)
        self.set_page_title(box, "Select Available Options")
        self.set_page_complete(box, True)

    def _create_default_filename(self) -> None:
        exporter, level = self._get_exporter()

        if level == ProjectType.REGSET:
            source = self._project.regsets[self._get_source()]
            filename = exporter.default_path.format(source.name)
        elif level == ProjectType.BLOCK:
            source = self._project.blocks[self._get_source()]
            filename = exporter.default_path.format(source.name)
        else:
            filename = exporter.default_path.format(self._project.short_name)
        self.choose.set_current_name(filename)
        file_filter = Gtk.FileFilter()
        file_filter.set_name(exporter.description)
        file_filter.add_pattern(f"*{exporter.file_extension}")
        self.choose.set_filter(file_filter)

    def _build_filename_content(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.CONTENT)
        self.set_page_title(box, "Select Filename")
        self.filename_label = Gtk.Label(
            label="Select the filename for the rule"
        )
        self.filename_label.set_line_wrap(True)
        box.pack_start(self.filename_label, False, False, 9)

        self.choose = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.SAVE)
        self.choose.set_current_folder(os.curdir)
        self.choose.set_local_only(True)
        self.choose.show()
        self.choose.set_border_width(0)

        box.pack_start(self.choose, True, True, 9)
        self.set_page_complete(box, True)

    def _build_source_list(self) -> Gtk.TreeView:
        source_list = Gtk.TreeView()
        source_list.set_model(self._source_mdl)
        column = ReadOnlyColumn("Source", 0)
        column.set_min_width(250)
        source_list.append_column(column)
        column = ReadOnlyColumn("Description", 1)
        source_list.append_column(column)
        return source_list

    def _build_format_list(self) -> None:
        self._format_list.set_model(self._format_mdl)
        column = ReadOnlyColumn("Format", 0)
        column.set_min_width(225)
        self._format_list.append_column(column)
        column = ReadOnlyColumn("Level", 4)
        column.set_min_width(120)
        self._format_list.append_column(column)
        column = ReadOnlyColumn("Description", 1)
        self._format_list.append_column(column)

        for exp in EXPORTERS:
            self._format_mdl.append(
                row=[
                    exp.description,
                    exp.full_description,
                    exp,
                    ProjectType.REGSET,
                    "Register Set",
                ]
            )
        for exp in GRP_EXPORTERS:
            self._format_mdl.append(
                row=[
                    exp.description,
                    exp.full_description,
                    exp,
                    ProjectType.BLOCK,
                    "Block",
                ]
            )
        for exp in PRJ_EXPORTERS:
            self._format_mdl.append(
                row=[
                    exp.description,
                    exp.full_description,
                    exp,
                    ProjectType.PROJECT,
                    "Project",
                ]
            )
        self._format_list.get_selection().select_path((0,))

    def _build_confirm(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.append_page(box)
        self.set_page_type(box, Gtk.AssistantPageType.CONFIRM)
        self.set_page_title(box, "Confirm")

        label = Gtk.Label(label="")
        label.set_line_wrap(True)
        box.pack_start(label, True, True, 0)
        self.set_page_complete(box, True)

    def _get_exporter(self) -> Tuple[ExportInfo, int]:
        selection = self._format_list.get_selection()
        model, node = selection.get_selected()
        return (model.get_value(node, 2), model.get_value(node, 3))

    def _reginst_toggle_changed(
        self, _cell: Gtk.CellRendererToggle, path: str, _source: int
    ) -> None:
        """Called when enable changed"""
        self._reginst_mdl[path][0] = not self._reginst_mdl[path][0]

    def _addrmaps_toggle_changed(
        self, _cell: Gtk.CellRendererToggle, path: str, _source: int
    ) -> None:
        """Called when enable changed"""
        self._addrmaps_mdl[path][0] = not self._addrmaps_mdl[path][0]

    def _build_options_reginsts(self) -> Gtk.Box:
        exporter, _ = self._get_exporter()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label=exporter.options["reginsts"])
        box.pack_start(label, False, False, 6)
        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)

        table = Gtk.TreeView()
        table.append_column(
            ToggleColumn("Select", self._reginst_toggle_changed, 0)
        )
        table.append_column(ReadOnlyColumn("Register Set Instance", 1))
        table.append_column(ReadOnlyColumn("Register Set", 2))
        box.pack_start(table, True, True, 6)

        blkid = self._get_source()
        block = self._project.blocks[blkid]

        for reginst in block.regset_insts:
            self._reginst_mdl.append(
                row=[
                    True,
                    reginst.name,
                    self._project.regsets[reginst.regset_id].name,
                    reginst,
                ]
            )
        table.set_model(self._reginst_mdl)
        box.show_all()
        return box

    def _build_options_addrmap(self) -> Gtk.Box:
        exporter, _ = self._get_exporter()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label=exporter.options["addrmaps"])
        box.pack_start(label, False, False, 6)
        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)

        self._addrmap_table.get_selection().set_mode(Gtk.SelectionMode.BROWSE)
        column = ReadOnlyColumn("Address Map", 0)
        column.set_min_width(300)
        self._addrmap_table.append_column(column)
        self._addrmap_table.append_column(ReadOnlyColumn("Base Address", 1))
        scroll.add(self._addrmap_table)
        box.pack_start(scroll, True, True, 6)

        for addrmap in self._project.get_address_maps():
            self._addrmap_mdl.append(
                row=[
                    addrmap.name,
                    f"0x{addrmap.base:x}",
                    addrmap,
                ]
            )
        self._addrmap_table.set_model(self._addrmap_mdl)
        box.show_all()
        return box

    def _build_options_addrmaps(self) -> Gtk.Box:
        exporter, _ = self._get_exporter()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label=exporter.options["addrmaps"])
        box.pack_start(label, False, False, 6)
        scroll = Gtk.ScrolledWindow()
        scroll.set_shadow_type(Gtk.ShadowType.IN)

        column = ToggleColumn("Select", self._addrmaps_toggle_changed, 0)
        column.set_min_width(100)
        self._addrmaps_table.append_column(column)

        column = ReadOnlyColumn("Address Map", 1)
        column.set_min_width(300)
        self._addrmaps_table.append_column(column)
        self._addrmaps_table.append_column(ReadOnlyColumn("Base Address", 2))
        scroll.add(self._addrmaps_table)
        box.pack_start(scroll, True, True, 6)

        for addrmap in self._project.get_address_maps():
            self._addrmaps_mdl.append(
                row=[
                    True,
                    addrmap.name,
                    f"0x{addrmap.base:x}",
                    addrmap,
                ]
            )
        self._addrmaps_table.set_model(self._addrmaps_mdl)
        box.show_all()
        return box

    def _get_source(self) -> str:
        selection = self.source_list.get_selection()
        model, node = selection.get_selected()
        return model.get_value(node, 2).uuid

    def _on_apply_clicked(self, *_args) -> None:
        "Saves the rule"

        # pylint: disable=E1133

        info, level = self._get_exporter()

        uuid = self._get_source() if level != ProjectType.PROJECT else ""
        filename = self.choose.get_filename()
        options = {}
        if "reginsts" in info.options:
            options["reginsts"] = [
                row[3].uuid for row in self._reginst_mdl if row[0]
            ]
        if "addrmap" in info.options:
            model, node = self._addrmap_table.get_selection().get_selected()
            selected = model.get_value(node, 2)
            options["addrmap"] = [selected.uuid]
        if "addrmaps" in info.options:
            options["addrmaps"] = []
            for row in self._addrmaps_mdl:
                if row[0]:
                    options["addrmaps"].append(row[-1].uuid)
        for option in info.options:
            if option.startswith("bool:"):
                options[option] = self._widgets[option].get_active()
        self.callback(filename, info, uuid, level, options)

    def _on_page_forward(self, page_num: int) -> int:
        """
        Controls the next page selection.

        If the exporter is a Project Level, then we do not need a source
        of the data. So we go to the Options page if options are needed,
        otherwise we go the Filename.

        If we are on the source page, and there are not options, we go to
        the Filename page.

        Otherwise, we just advance to the next page.
        """
        exporter, level = self._get_exporter()

        if page_num == PageId.EXPORTER and level == ProjectType.PROJECT:
            if exporter.options:
                return PageId.OPTIONS
            return PageId.FILENAME
        if page_num == PageId.SOURCE and not exporter.options:
            return PageId.FILENAME
        return page_num + 1

    def _on_close_clicked(self, *_args) -> None:
        self.destroy()

    def _on_cancel_clicked(self, *_args) -> None:
        self.destroy()

    def _on_prepare_clicked(
        self, _assistant: Gtk.Assistant, _page: Gtk.Box
    ) -> None:
        page = self.get_current_page()
        exporter, category = self._get_exporter()
        if page == PageId.SOURCE:
            self._prepare_source(exporter, category)
        elif page == PageId.OPTIONS:
            self._prepare_options(exporter)
        elif page == PageId.FILENAME:
            self._create_default_filename()
        elif page == PageId.CONFIRM:
            self._prepare_confirm()

    def _prepare_confirm(self) -> None:
        box = self.get_nth_page(PageId.CONFIRM)
        for child in box.get_children():
            box.remove(child)

        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)
        grid.set_hexpand(True)
        title = Gtk.Label()
        title.set_markup(
            '<span weight="bold" size="large">Summary of new rule</span>'
        )
        title.set_hexpand(True)
        title.set_justify(Gtk.Justification.CENTER)
        grid.attach(title, 0, 0, 2, 1)

        filename = self.choose.get_filename()
        exporter, level = self._get_exporter()

        if level == ProjectType.PROJECT:
            source = "Project"
        elif level == ProjectType.BLOCK:
            block = self._get_source()
            name = self._project.blocks[block].name
            source = f"Block ({name})"
        else:
            regset = self._get_source()
            name = self._project.regsets[regset].name
            source = f"Register Set ({name})"

        add_row_to_grid(grid, 1, "Filename:", filename)
        add_row_to_grid(grid, 2, "Exporter:", exporter.description)
        add_row_to_grid(grid, 3, "Source:", source)

        box.pack_start(grid, True, True, 12)
        grid.show_all()

    def _prepare_options(self, exporter: ExportInfo) -> None:
        box = self.get_nth_page(PageId.OPTIONS)
        for child in box.get_children():
            box.remove(child)
        if "reginsts" in exporter.options:
            widget = self._build_options_reginsts()
            box.pack_start(widget, True, True, 6)
        if "addrmaps" in exporter.options:
            widget = self._build_options_addrmaps()
            box.pack_start(widget, True, True, 6)
        if "addrmap" in exporter.options:
            widget = self._build_options_addrmap()
            box.pack_start(widget, True, True, 6)
        for option in exporter.options:
            if option.startswith("bool:"):
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                label = Gtk.Label(label=exporter.options[option])
                hbox.pack_start(label, False, False, 12)
                self._widgets[option] = Gtk.Switch()
                hbox.pack_start(self._widgets[option], False, False, 12)
                hbox.show_all()
                box.pack_start(hbox, True, True, 12)

    def _prepare_source(
        self, exporter: ExportInfo, category: ProjectType
    ) -> None:
        if category == ProjectType.REGSET:
            self._prepare_regset_source()
            source = "register set"
        elif category == ProjectType.BLOCK:
            self._prepare_block_source()
            source = "block"
        else:
            source = "project"

        fmt = exporter.description
        self.source_label.set_text(
            f"The {fmt} format requires that you select a "
            f"{source} as the data source"
        )

    def _prepare_block_source(self) -> None:
        blocks = sorted(self._project.blocks.values(), key=lambda x: x.name)
        self._source_mdl.clear()
        for block in blocks:
            self._source_mdl.append(row=[block.name, block.description, block])

    def _prepare_regset_source(self) -> None:
        rsets = sorted(self._project.regsets.values(), key=lambda x: x.name)
        self._source_mdl.clear()
        for regset in rsets:
            self._source_mdl.append(
                row=[regset.name, regset.descriptive_title, regset]
            )
