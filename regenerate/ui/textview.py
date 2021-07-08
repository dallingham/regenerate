
from gi.repository import Pango, GtkSource

class RstEditor(GtkSource.View):

    def __init__(self):
        super().__init__()
        manager = GtkSource.LanguageManager()
        self.get_buffer().set_language(manager.get_language('rst'))
        self.modify_font(Pango.FontDescription("monospace"))
