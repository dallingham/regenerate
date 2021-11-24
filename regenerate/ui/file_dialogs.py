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
Provide common file dialogs
"""

import os
from typing import Union, List, Optional

from gi.repository import Gtk


def get_new_filename() -> Optional[str]:
    "Creates a new file selector dialog to save a new file"

    filelist = create_file_selector(
        "New", None, None, None, Gtk.FileChooserAction.SAVE, Gtk.STOCK_SAVE
    )
    return filelist[0] if filelist else None


def create_file_selector(
    title: str,
    top_window: Optional[Gtk.Window],
    name: Optional[str],
    regex: Optional[Union[str, List[str]]],
    action: Gtk.FileChooserAction,
    icon: str,
) -> List[str]:
    """
    Creates a file save selector, using the mime type and regular
    expression to control the selector.
    """

    choose = Gtk.FileChooserDialog(
        title,
        top_window,
        action,
        (
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            icon,
            Gtk.ResponseType.OK,
        ),
    )

    choose.set_select_multiple(False)
    choose.set_current_folder(os.curdir)

    if name and regex:
        mime_filter = Gtk.FileFilter()
        mime_filter.set_name(name)
        if isinstance(regex, str):
            mime_filter.add_pattern(regex)
        else:
            for val in regex:
                mime_filter.add_pattern(val)

        choose.add_filter(mime_filter)
    choose.show()

    name = None
    if choose.run() == Gtk.ResponseType.OK:
        name = choose.get_filenames()
    choose.destroy()
    return name
