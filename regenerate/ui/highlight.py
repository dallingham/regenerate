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
Highlight the selected text in the buffer.
"""

try:
    from gi.repository import Pango
    from pygments.lexers import VerilogLexer
    from pygments.styles import get_style_by_name

    def highlight_text(text, buf):
        """Highlight the text in the buffer"""

        styles = {}
        emacs_style = get_style_by_name("emacs")
        for token, value in VerilogLexer().get_tokens(text):
            while not emacs_style.styles_token(token) and token.parent:
                token = token.parent
            if token not in styles:
                styles[token] = buf.create_tag()
            start = buf.get_end_iter()
            buf.insert_with_tags(start, value, styles[token])

            for token0, tag in styles.items():
                style = emacs_style.style_for_token(token0)
                if style["bgcolor"]:
                    tag.set_property("background", "#" + style["bgcolor"])
                if style["color"]:
                    tag.set_property("foreground", "#" + style["color"])
                if style["bold"]:
                    tag.set_property("weight", Pango.Weight.BOLD)
                if style["italic"]:
                    tag.set_property("style", Pango.Style.ITALIC)
                if style["underline"]:
                    tag.set_property("underline", Pango.Underline.SINGLE)


except ImportError:

    def highlight_text(text, buf):
        """Pass through the text if pygments not installed"""
        buf.set_text(text)
