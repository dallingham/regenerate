import os
from typing import Union, List, Optional

from gi.repository import Gtk


def get_new_filename():
    return create_file_selector(
        "New", None, None, None, Gtk.FileChooserAction.SAVE, Gtk.STOCK_SAVE
    )


def create_file_selector(
    title: str,
    top_window: Optional[Gtk.Window],
    name: Optional[str],
    regex: Optional[Union[str, List[str]]],
    action: Gtk.FileChooserAction,
    icon: str,
    multiple=False,
) -> Optional[Union[str, List[str]]]:
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

    choose.set_select_multiple(multiple)

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

    response = choose.run()

    name = None
    if response == Gtk.ResponseType.OK:
        if multiple:
            name = choose.get_filenames()
        else:
            name = choose.get_filename()
    choose.destroy()
    return name
