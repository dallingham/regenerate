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
Handle the module tab
"""

from gi.repository import Gtk, Gdk
from typing import Callable, List

from regenerate.db import RegProject
from regenerate.ui.base_doc import BaseDoc
from .entry import EntryText, EntryWord


class ProjectTabs:
    """Handles the project tabs"""

    def __init__(self, builder: Gtk.Builder, modified: Callable):

        item_list = [
            ("project_name", "name", EntryText, "Missing project name"),
            ("short_name", "short_name", EntryWord, "Missing short name"),
            (
                "company_name",
                "company_name",
                EntryText,
                "Missing company name",
            ),
        ]

        self.object_list = []

        for (widget_name, db_name, class_type, placeholder) in item_list:
            if placeholder is not None:
                self.object_list.append(
                    class_type(
                        builder.get_object(widget_name),
                        db_name,
                        self.after_modified,
                        placeholder=placeholder,
                    )
                )
            else:
                self.object_list.append(
                    class_type(
                        builder.get_object(widget_name),
                        db_name,
                        self.after_modified,
                    )
                )

        self.preview = ProjectDoc(
            builder.get_object("prj_doc_notebook"),
            self.after_modified,
            builder.get_object("add_top_doc"),
            builder.get_object("del_top_doc"),
        )

        self.dbase = None
        self.set_modified = modified
        self.icon = builder.get_object("mod_def_warn")

    def change_db(self, dbase) -> None:
        self.dbase = dbase
        self.preview.set_project(dbase)
        for obj in self.object_list:
            obj.change_db(dbase)

    def after_modified(self) -> None:
        self.set_modified()


class ProjectDoc(BaseDoc):
    def __init__(
        self,
        notebook: Gtk.Notebook,
        modified,
        add_btn: Gtk.Button,
        del_btn: Gtk.Button,
    ):
        super().__init__(notebook, modified, add_btn, del_btn)
        self.changing = False

    def set_project(self, project: RegProject) -> None:
        """Change the database so the preview window can resolve references"""
        self.changing = True

        self.project = project
        self.remove_pages()

        for page in project.doc_pages.get_page_names():
            text = self.project.doc_pages.get_page(page)
            if text is not None:
                self.add_page(page, text)

        self.changing = False

    def remove_page_from_doc(self, title: str) -> None:
        if not self.changing and self.project:
            self.project.doc_pages.remove_page(title)

    def update_page_from_doc(
        self, title: str, text: str, tags: List[str]
    ) -> None:
        if not self.changing and self.project:
            self.project.doc_pages.update_page(title, text, tags)
