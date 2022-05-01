import socket
import os
from math import floor

PORT = 6061
DISCONNECT_REQUEST = 10
MESSAGE = 0
NAME = 2
RESPONSE = 3
COMPOUND = 4  # transfer NAME, MESSAGE/RESPONSE, RESPONSE
VOID = 5
MENU = 6
PRIVATE = 7
DISCONNECT_CONFIRM = 11
DISCONNECT = 1
DISCONNECT_SERVER = 12
PAUSED = 8
ALL_CONNECTIONS = 9
ALL_CONNECTIONS_REQUEST = 90
ALL_CONNECTIONS_SEND = 91
ALL_CONNECTIONS_CONFIRM = 92


def pad_dash(str):
    total_length = 45
    dash_length = floor((total_length - len(str)) / 2)

    dashes = ''
    for _ in range(dash_length):
        dashes += '-'

    return f'{dashes}{str}{dashes}'


def header(heading):
    print(pad_dash(heading.upper()))


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
    send_simple_message(connection, COMPOUND)
    send_message(connection, NAME, name)
    send_message(connection, MESSAGE if is_message else RESPONSE,
                 message_or_response)
    send_message(connection, RESPONSE, time)


def encode_sender(connection, message_str):
    connection.send(message_str.encode())


def send_simple_message(connection, message_type):
    def encode_send(message_str): encode_sender(connection, message_str)
    # or message_type == ALL_CONNECTIONS_REQUEST:
    if message_type == DISCONNECT_REQUEST or message_type == DISCONNECT_CONFIRM or message_type == DISCONNECT_SERVER:
        encode_send(f'{message_type}0')
    elif message_type == MENU or message_type == VOID or message_type == PAUSED or message_type == COMPOUND:
        encode_send(f'{message_type}00')

# def all_connections_send(connection, names):
#     def encode_send(message_str): encode_sender(connection, message_str)
#     client_count = len(names)
#     if client_count > 99:
#         client_count = 99

#     encode_send(f'{ALL_CONNECTIONS}{str(client_count).zfill(2)}')
#     for i in range(client_count):
#         send_message(connection, NAME, names[i])


# def all_connections_confirm(connection, index, message):
#     def encode_send(message_str): encode_sender(connection, message_str)
#     encode_send(f'{ALL_CONNECTIONS_CONFIRM}0')
#     send_message(connection, RESPONSE, str(index).zfill(2))
#     send_message(connection, RESPONSE, message)

def send_message(connection, message_type, message_text):
    def encode_send(message_str): encode_sender(connection, message_str)

    def trim_message(message_text):
        MESSAGE_LIMIT = 99
        return message_text[: MESSAGE_LIMIT]

    message_text = trim_message(message_text)

    if message_type == NAME or message_type == MESSAGE or message_type == RESPONSE:
        encode_send(f'{message_type}{str(len(message_text)).zfill(2)}')
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
        def parse_time(
            message_text): return f'{"" if message_text[0] == "0" else "1"}{message_text[1]}:{message_text[2:4]} {message_text[4]}M'
        name = receive_message(client)
        message_or_response = receive_message(client)
        time = receive_message(client)
        return [name, message_or_response, Message(RESPONSE, parse_time(time.text))]
    # elif type == ALL_CONNECTIONS:
    #     actual_type = int(code[:2])

    #     if actual_type == ALL_CONNECTIONS_REQUEST:
    #         return Message(actual_type, '')
    #     elif actual_type == ALL_CONNECTIONS_SEND:
    #         names = []
    #         count = int(code[1:])
    #         for i in range(count):
    #             name = receive_message(client)
    #             names.append(name)
    #         return names
    #     else:
    #         client_index = receive_message(client)
    #         message = receive_message(client)
    #         return Message(client_index.type, client_index.text), Message(client_index.type, message.text)


def get_address():
    HOST = socket.gethostname()
    SERVER = socket.gethostbyname(HOST)
    return (SERVER, PORT)


def display_address(address):
    return f'{address[0]} ({address[1]})'
