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

import os
from pathlib import Path


class project_path_not_found(Exception):
    pass


__regenerate_data_directory__ = "../data/"


def getdatapath() -> Path:
    """Retrieve regenerate data path

    This path is by default <regenerate_lib_path>/../data/ in trunk
    and /usr/share/regenerate in an installed version but this path
    is specified at installation time.
    """

    # get pathname absolute or relative
    if __regenerate_data_directory__.startswith("/"):
        pathname = __regenerate_data_directory__
    else:
        pathname = os.path.join(
            os.path.dirname(__file__), __regenerate_data_directory__
        )

    return Path(os.path.abspath(pathname))


INSTALL_PATH = getdatapath()
GLADE_TOP = INSTALL_PATH / "ui" / "regenerate.ui"
GLADE_GTXT = INSTALL_PATH / "ui" / "group_text.ui"
GLADE_BIT = INSTALL_PATH / "ui" / "bitfield.ui"
GLADE_CHK = INSTALL_PATH / "ui" / "check.ui"
GLADE_PROP = INSTALL_PATH / "ui" / "properties.ui"
GLADE_PREF = INSTALL_PATH / "ui" / "preferences.ui"
GLADE_GRP = INSTALL_PATH / "ui" / "groupings.ui"
ODTFILE = INSTALL_PATH / "extra" / "template.odt"
USERODTFILE = INSTALL_PATH / ".." / "site_local" / "template.odt"
HELP_PATH = INSTALL_PATH / "help"
