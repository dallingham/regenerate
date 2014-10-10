
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

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if self.name != other.name:
            return False
        if self.base != other.base:
            return False
        if self.hdl != other.hdl:
            return False
        if self.repeat != other.repeat:
            return False
        if self.repeat_offset != other.repeat_offset:
            return False
        if self.docs != other.docs:
            return False
        if self.register_sets != other.register_sets:
            return False
        return True
