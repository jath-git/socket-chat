# use class for encryption and decryption of messages

class Message:
    def __init__(self, _type, _text):
        self.type = _type
        self.text = _text

    def get_type(self):
        return self.type

    def get_text(self):
        return self.text