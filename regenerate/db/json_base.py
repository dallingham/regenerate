class JSONEncodable:
    def json(self):
        data = vars(self)
        return data

    def json_decode(self, data):
        for key, value in data:
            self.__setattr__(key, value)
