# Attempt to load the GTK spell package to provide basic spell checking.
# If the import fails (gtkspell not installed), then create a dummy
# spell object that does nothing.

from regenerate.db import LOGGER

try:

    from gtkspellcheck import SpellChecker

    class Spell(SpellChecker):
        def __init__(self, obj):
            super().__init__(obj)
            self.enable()

        def detach(self):
            pass


except ImportError:

    try:

        from gtkspell import Spell

    except ImportError:

        class Spell(object):
            "Empty class for compatiblity if the spell checker is not found"

            def __init__(self, obj):
                pass

            def detach(self):
                pass

            LOGGER.warning(
                "gtkspell/gtkspellcheck is not installed, "
                "spell checking will not be available"
            )
