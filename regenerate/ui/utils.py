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
Cleans the code select if needed.
"""

import os
from gi.repository import Gtk

from regenerate.db import LOGGER


def find_next_free(base, current_list):
    """Find the next free name that is not in the list"""

    index = 0
    name = f"{base}{index}"
    while name in current_list:
        index += 1
        name = f"{base}{index}"
    return name


def clean_format_if_needed(obj):
    """
    Gets the selection and removes newlines
    """

    buf = obj.get_buffer()
    bounds = buf.get_selection_bounds()
    if bounds:
        old_text = buf.get_text(bounds[0], bounds[1])
        new_text = " ".join(old_text.replace("\n", " ").split())
        if old_text != new_text:
            buf.delete(bounds[0], bounds[1])
            buf.insert(bounds[0], new_text)
            return True
    return False


def check_hex(new_text):
    """Check to see if a valid hex value"""

    try:
        int(new_text, 16)
        return True
    except ValueError:
        LOGGER.warning('Illegal hexidecimal value: "%s"', new_text)
        return False


def get_new_filename():
    """
    Opens up a file selector, and returns the selected file. The
    selected file is added to the recent manager.
    """

    name = None
    choose = Gtk.FileChooserDialog(
        "New",
        None,
        Gtk.FileChooserAction.SAVE,
        (
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE,
            Gtk.ResponseType.OK,
        ),
    )
    choose.set_current_folder(os.curdir)
    choose.show()

    response = choose.run()
    if response == Gtk.ResponseType.OK:
        name = choose.get_filename()
    choose.destroy()
    return name
