from constants import *
import sys
sys.path.insert(0, './classes')
from Message import Message

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

    if not (message_type == DISCONNECT_REQUEST or message_type == DISCONNECT_CONFIRM or message_type == DISCONNECT_SERVER or message_type == ALL_CONNECTIONS_REQUEST or message_type == ALL_CONNECTIONS_SEND or message_type == MENU or message_type == VOID or message_type == PAUSED or message_type == COMPOUND or message_type == STOP_SERVER or message_type == STOP_CLIENT):
        return

    if message_type == COMPOUND:
        encode_send(f'{message_type}00')
    else:
        encode_send(f'{message_type}0')


def all_connections_send(connection, names):
    def encode_send(message_str): encode_sender(connection, message_str)
    client_count = len(names)
    if client_count > 99:
        client_count = 99

    send_simple_message(connection, ALL_CONNECTIONS_SEND)
    encode_send(str(client_count).zfill(3))

    for i in range(client_count):
        send_message(connection, NAME, names[i])


def all_connections_confirm(connection, name, message):
    def encode_send(message_str): encode_sender(connection, message_str)

    encode_send(f'{ALL_CONNECTIONS_CONFIRM}0')
    send_message(connection, RESPONSE, name)
    send_message(connection, RESPONSE, message)


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

    if type == DISCONNECT or type == SIMPLE:
        actual_type = int(code[:2])
        return Message(actual_type, '')
    elif type == COMPOUND:
        def parse_time(
            message_text): return f'{"" if message_text[0] == "0" else "1"}{message_text[1]}:{message_text[2:4]} {message_text[4]}M'
        name = receive_message(client)
        message_or_response = receive_message(client)
        time = receive_message(client)
        return [name, message_or_response, Message(RESPONSE, parse_time(time.text))]
    elif type == NAME or type == MESSAGE or type == RESPONSE:
        message_len = int(code[1:])
        message_text = decode_receive(message_len)
        return Message(type, message_text)
    elif type == ALL_CONNECTIONS:
        actual_type = int(code[:2])

        if actual_type == ALL_CONNECTIONS_REQUEST:
            return Message(actual_type, '')
        elif actual_type == ALL_CONNECTIONS_SEND:
            names = []
            count = int(decode_receive(3))
            for _ in range(count):
                name = receive_message(client)
                names.append(name)
            return names
        elif actual_type == ALL_CONNECTIONS_CONFIRM:
            name = receive_message(client)
            message = receive_message(client)
            return [Message(name.type, name.text), Message(message.type, message.text)]
