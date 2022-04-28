import socket

PORT = 6062
DISCONNECT = 0
MESSAGE = 1
NAME = 2
RESPONSE = 3
COMPOUND = 4  # transfer NAME and MESSAGE


class Message:
    def __init__(self, _type, _text):
        self.type = _type
        self.text = _text


def get_address() -> any:
    HOST = socket.gethostname()
    SERVER = socket.gethostbyname(HOST)
    return (SERVER, PORT)


def display_address(address):
    return f'{address[0]} ({address[1]})'
