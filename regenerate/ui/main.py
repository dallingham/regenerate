#! /usr/bin/env python3
#
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
Actual program. Parses the arguments, and initiates the main window
"""

import os
import sys
import logging
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gtk

from regenerate.ui.regenerate_top import MainWindow
from regenerate.settings import ini


def run_gui(args):
    """
    Actually runs the program
    """

    edit = MainWindow()
    if args.project_file:
        try:
            edit.open_project(
                args.project_file, "file:///" + args.project_file
            )
        except IOError as msg:
            sys.stderr.write("regenerate: error: could not project file: ")
            sys.stderr.write("%s\n" % str(msg))
            sys.exit(1)
    elif ini.get("user", "last_project", False):
        filename = ini.get("user", "last_project", None)
        if filename and os.path.exists(filename):
            edit.open_project(filename, None)

    # Windows seems to have a real problem with threads. This little trick
    # allows us to get around it. Fortunately, Linux doesn't appear to be
    # broken in the same way.

    if os.name == "nt":
        from gi.repository import GObject

        GObject.threads_init()
        Gtk.threads_enter()
        Gtk.main()
        Gtk.threads_leave()
    else:
        Gtk.main()


def main():
    """
    main program
    """
    from argparse import ArgumentParser

    parser = ArgumentParser(
        description="Manages the registers in an ASIC or FPGA design"
    )

    parser.add_argument(
        "project_file", nargs="?", default=None, help="Regenerate project file"
    )
    parser.add_argument(
        "--log", type=str, default="WARN", help="logging level"
    )

    args = parser.parse_args()

    if args.log:
        numeric_level = getattr(logging, args.log.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError("Invalid log level: %s" % args.log)
        logging.basicConfig(
            level=numeric_level, format="%(levelname)s: %(message)s"
        )

    if "DISPLAY" in os.environ:
        run_gui(args)
    else:
        sys.stderr.write(
            'ERROR: Display not available. Did you forget to give ssh the "-X" option?\n'
        )
        sys.exit(1)
