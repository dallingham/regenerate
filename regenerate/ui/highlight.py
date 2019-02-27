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

try:
    from pygments.lexers import VerilogLexer
    from pygments.styles import get_style_by_name
    import pango

    def highlight_text(text, buf):

        styles = {}
        STYLE = get_style_by_name('emacs')
        for token, value in VerilogLexer().get_tokens(text):
            while not STYLE.styles_token(token) and token.parent:
                token = token.parent
            if token not in styles:
                styles[token] = buf.create_tag()
            start = buf.get_end_iter()
            buf.insert_with_tags(start, value, styles[token])

            for token in styles:
                tag = styles[token]
                style = STYLE.style_for_token(token)
                if style['bgcolor']:
                    tag.set_property('background', '#' + style['bgcolor'])
                if style['color']:
                    tag.set_property('foreground', '#' + style['color'])
                if style['bold']:
                    tag.set_property('weight', pango.WEIGHT_BOLD)
                if style['italic']:
                    tag.set_property('style', pango.STYLE_ITALIC)
                if style['underline']:
                    tag.set_property('underline', pango.UNDERLINE_SINGLE)

except ImportError:

    def highlight_text(text, buf):
        buf.set_text(text)
