try:
    from docutils.core import publish_string
except ImportError:
    LOGGER.warning("docutils is not installed, preview of formatted "
                   "comments will not be available")
    def publish_string (text):
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
    return __CSS + publish_string(text, writer_name="html")
