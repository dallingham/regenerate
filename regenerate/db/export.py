from .json_base import JSONEncodable


class ExportData(JSONEncodable):
    def __init__(self, option: str = "", path: str = ""):
        self.option: str = option
        self.path: str = path

    def json_decode(self, data):
        self.option = data["option"]
        self.path = data["path"]
