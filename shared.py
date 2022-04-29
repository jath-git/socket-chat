import socket
import os

PORT = 6062
DISCONNECT_REQUEST = 10
MESSAGE = 0
NAME = 2
RESPONSE = 3
COMPOUND = 4  # transfer NAME and MESSAGE/RESPONSE
VOID = 5
MENU = 6
TIME = 7
DISCONNECT_CONFIRM = 11
DISCONNECT = 1
DISCONNECT_SERVER = 12
PAUSED = 8


def header(heading):
    print(f'---------------{heading.upper()}---------------')


def clear_console():
    command = 'cls' if os.name in ('nt', 'dos') else 'clear'
    os.system(command)


class Message:
    def __init__(self, _type, _text):
        self.type = _type
        self.text = _text

    def get_type(self):
        return self.type

    def get_text(self):
        return self.text


def send_compound(connection, name, message_or_response, time, is_message):
    compound_code = str(MESSAGE if is_message else RESPONSE).zfill(2)

    send_message(connection, COMPOUND, compound_code)
    send_message(connection, NAME, name)
    send_message(connection, MESSAGE if is_message else RESPONSE,
                 message_or_response)
    send_message(connection, TIME, time)


def send_disconnect_request(connection):
    send_message(connection, DISCONNECT_REQUEST, '')


def send_disconnect_confirm(connection):
    send_message(connection, DISCONNECT_CONFIRM, '')


def send_disconnect_server(connection):
    send_message(connection, DISCONNECT_SERVER, '')


def send_menu(connection):
    send_message(connection, MENU, '')


def send_void(connection):
    send_message(connection, VOID, '')


def send_paused(connection):
    send_message(connection, PAUSED, '')


def send_message(connection, message_type, message_text):
    def encode_send(message_str):
        connection.send(message_str.encode())

    def trim_message(message_text):
        MESSAGE_LIMIT = 99
        return message_text[: MESSAGE_LIMIT]

    message_text = trim_message(message_text)

    if message_type == DISCONNECT_REQUEST or message_type == DISCONNECT_CONFIRM or message_type == DISCONNECT_SERVER:
        encode_send(f'{message_type}0')
    elif message_type == MENU or message_type == VOID or message_type == PAUSED:
        encode_send(f'{message_type}00')
    elif message_type == COMPOUND:
        encode_send(f'{message_type}{message_text}')
    elif message_type == NAME or message_type == MESSAGE or message_type == RESPONSE:
        encode_send(f'{message_type}{str(len(message_text)).zfill(2)}')
        encode_send(message_text)
    elif message_type == COMPOUND:
        encode_send(f'{COMPOUND}02')
    elif message_type == TIME:
        encode_send(f'{TIME}05')
        encode_send(message_text)


def receive_message(client):
    def decode_receive(message_len):
        return client.recv(message_len).decode()

    code = decode_receive(3)

    if not code:
        return None

    type = int(code[0])

    if type == DISCONNECT:
        return Message(int(code[:2]), '')
    elif type == MENU or type == VOID or type == PAUSED:
        return Message(type, '')
    elif type == NAME or type == MESSAGE or type == RESPONSE:
        message_len = int(code[1:])
        message_text = decode_receive(message_len)
        return Message(type, message_text)
    elif type == COMPOUND:
        name = receive_message(client)
        message_or_response = receive_message(client)
        time = receive_message(client)
        return [name, message_or_response, time]
    elif type == TIME:
        message_text = decode_receive(5)
        return Message(TIME, f'{"" if message_text[0] == "0" else "1"}{message_text[1]}:{message_text[2:4]} {message_text[4]}M')


def get_address():
    HOST = socket.gethostname()
    SERVER = socket.gethostbyname(HOST)
    return (SERVER, PORT)


def display_address(address):
    return f'{address[0]} ({address[1]})'
