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
Logging functionality for regenerate.

Provides the logger, with the setup format.

"""

import logging

LOGGER = logging.getLogger("regenerate")

__CH = logging.StreamHandler()
__FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - " "%(levelname)s - %(message)s"
)
__CH.setFormatter(__FORMATTER)
LOGGER.addHandler(__CH)


def remove_default_handler():
    """
    Removes the default log handler.
    """
    LOGGER.removeHandler(__CH)
