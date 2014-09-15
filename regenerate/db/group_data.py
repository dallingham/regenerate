
class GroupData(object):
    """Basic group information"""
    def __init__(self, name="", base=0, hdl="", repeat=1,
                 repeat_offset=0x10000):
        self.name = name
        self.base = base
        self.hdl = hdl
        self.repeat = repeat
        self.repeat_offset = repeat_offset
        self.register_sets = []
        self.docs = ""
