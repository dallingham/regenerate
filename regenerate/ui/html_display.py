
try:
    import gi
    gi.require_version('WebKit2', '4.0')
    from gi.repository import WebKit2 as webkit
    WEBKIT = True
    
except ValueError:

    try:
        gi.require_version("WebKit", "3.0")
        from gi.repository import WebKit as webkit
        WEBKIT = True
    except ImportError:
        
        WEBKIT = False
        PREVIEW_ENABLED = False
        LOGGER.warning("Webkit is not installed, preview of formatted "
                       "comments will not be available")


        
class HtmlDisplay(webkit.WebView):

    def __init__(self):
        super(HtmlDisplay, self).__init__()


    def show_html(self, data):
        try:
            self.load_html(data, "text/html")
        except:
            self.load_html_string(data, "text/html")

            
