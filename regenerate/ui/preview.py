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
Provides a function to convert restructuredText to HTML
"""

try:
    from docutils.core import publish_string
except ImportError:
    from regenerate.db import LOGGER
    LOGGER.warning("docutils is not installed, preview of formatted "
                   "comments will not be available")

    def publish_string(text, writer_name):
        """
        Provides an alternative publish_string function if docutils is
        not available. Simply returns the text.
        """
        return text


__CSS = '''
<style type="text/css">
table.docutils td{
    padding: 3pt;
}
table.docutils th{
    padding: 3pt;
}
table.docutils {
    border-spacing: 0pt;
}
h1{
    font-family: Arial,Helvetica,Sans;
    font-size: 14pt;
}
h2{
    font-family: Arial,Helvetica,Sans;
    font-size: 12pt;
}
body{
    font-size: 10pt;
    font-family: Arial,Helvetica,Sans;
}
</style>
'''


def html_string(text):
    """
    Converts the strng from restructuredText to HTML and prepends
    the CSS string.
    """
    try:
        return __CSS + publish_string(
            text,
            writer_name="html",
            settings_overrides={'report_level': 'quiet'}, )
    except TypeError:
        return __CSS + publish_string(text, writer_name="html")
