from docutils.core import publish_parts
from cStringIO import StringIO
from regenerate.db import TYPES

TYPE_STR = {}
for i in TYPES:
    TYPE_STR[i.type] = i.simple_type


CSS = '''
<style type="text/css">
table td{
    padding: 3pt;
    font-size: 10pt;
}
table th{
    padding: 3pt;
    font-size: 11pt;
}
table th.field-name{
    padding-bottom: 0pt;
    padding-left: 5pt;
    font-size: 10pt;
}
table td.field-body{
    padding-bottom: 0pt;
    font-size: 10pt;
}
table {
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


class RegisterRst:

    def __init__(self, register):
        self.reg = register

    def html_css(self):
        return CSS + self.html()

    def html(self):
        o = StringIO()
        rlen = len(self.reg.register_name) + 1
        o.write("\n")
        o.write(self.reg.register_name)
        o.write("\n%s\n" % ("-" * rlen))
        o.write("\n%s\n\n" % self.reg.description)
        o.write(".. list-table::\n")
        o.write("   :widths: 5 15 10 20 50\n")
        o.write("   :header-rows: 1\n\n")
        o.write("   * - Bit(s)\n")
        o.write("     - Reset\n")
        o.write("     - Type\n")
        o.write("     - Name\n")
        o.write("     - Description\n")

        last_index = self.reg.width - 1

        for key in reversed(self.reg.get_bit_field_keys()):
            field = self.reg.get_bit_field(key)
            start = field.start_position
            stop = field.stop_position

            if stop != last_index:
                display_reserved(o, last_index, stop + 1)

            if start == stop:
                o.write("   * - ``%d``\n" % start )
            else:
                o.write("   * - ``%d:%d``\n" % (stop, start))
            o.write("     - ``0x%x``\n" % field.reset_value)
            o.write("     - ``%s``\n" % TYPE_STR[field.field_type])
            o.write("     - ``%s``\n" % field.field_name)
            marked_descr = "\n       ".join(field.description.split("\n"))
            o.write("     - %s\n" % marked_descr)
            if field.values:
                o.write("\n")
                for val in sorted(field.values,
                                  key=lambda x: int(int(x[0], 16))):
                    o.write("       :%d: %s\n" % (int(val[0], 16),
                                                  val[1]))
            last_index = start - 1
        if last_index >= 0:
            display_reserved(o, last_index, 0)

        o.write("\n")
        parts = publish_parts(o.getvalue(), writer_name="html")
        return parts['html_title'] + parts['body']


def display_reserved(o, stop, start):
    if stop == start:
        o.write("   * - ``%d``\n" % stop)
    else:
        o.write("   * - ``%d:%d``\n" % (start, stop))
    o.write('     - ``0x0``\n')
    o.write('     - ``RO``\n')
    o.write('     - \n')
    o.write('     - *reserved*\n')
