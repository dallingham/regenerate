from gi.repository import Gtk

from .preview import html_string
from .html_display import HtmlDisplay
from .base_window import BaseWindow


class PreviewDisplay(BaseWindow):
    def __init__(
        self,
        textbuf: Gtk.TextBuffer,
    ):
        super().__init__()

        self.window = Gtk.Window()
        self.window.set_resizable(True)
        self.window.set_default_size(800, 600)
        self.configure(self.window)
        self.textbuf = textbuf
        self.container = HtmlDisplay()

        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        refresh = Gtk.ToolButton()
        refresh.set_stock_id(Gtk.STOCK_REFRESH)
        refresh.set_label("Refresh")
        toolbar.insert(refresh, 0)

        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC
        )
        scroll_window.add(self.container)

        vbox = Gtk.VBox(spacing=0)
        vbox.pack_start(toolbar, False, False, 0)
        vbox.pack_start(scroll_window, True, True, 0)

        self.window.add(vbox)
        self.window.show_all()
        refresh.connect("clicked", self.on_refresh_button_clicked)
        self.update()

    def on_refresh_button_clicked(self, _button: Gtk.Button):
        self.update()

    def update(self):
        text = self.textbuf.get_text(
            self.textbuf.get_start_iter(),
            self.textbuf.get_end_iter(),
            False,
        )
        self.container.load_html(html_string(text), "text/html")
