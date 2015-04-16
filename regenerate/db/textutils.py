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

__convert = [(u"\u2013", "-"),
             (u"\u2018", "'"),
             (u"\u2019", "'"),
             (u"\u201c", "\""),
             (u"\u201d", "\""),
             (u"\u201f", "\""),
             (u"\u2022", "*"),
             (u"\ue280a2", "*"), ]


def clean_text(text):
    for (s, d) in __convert:
        text = text.replace(s, d)
    return text.encode('ascii', 'replace')
