import socket
import threading
from shared import *

connections = []
id_name = {}
name_id = {}


def create_socket():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return server
    except socket.error as err:
        print(f'[ERROR] Socket creation failed: {str(err)}')
        exit()


server = create_socket()


def send(client, message):
    client.send(message.text.encode())


def receive(connection):
    message_code = connection.recv(3).decode()

    if not message_code:
        return None

    message_type = int(message_code[0])

    if message_type == DISCONNECT:
        return Message(DISCONNECT, '')

    message_len = int(message_code[1:])
    text = connection.recv(message_len).decode()
    return Message(message_type, text)


def client_observe(client, address):
    id = display_address(address)
    connected = True
    message_success = True
    name = id

    print(f'[UPDATE] {id} joined')

    if id in id_name:
        name = id_name[id]

    while connected:
        message = receive(client)
        if message:
            message_success = True
            if message.type == MESSAGE:
                if message.text == '':
                    message_success = False
                else:
                    print(f'[RECEIVED] {name}: {message.text}')
            elif message.type == NAME:
                if message.text == '' or message.text in name_id:
                    message_success = False
                else:
                    name = message.text
                    if id in id_name:
                        old_name = id_name[id]
                        del name_id[old_name]
                        id_name[id] = name
                        name_id[name] = id
                        print(f'[UPDATE] {old_name} renamed as {name}')
                    else:
                        id_name[id] = name
                        name_id[name] = id
                        print(f'[UPDATE] {id} renamed as {name}')
            else:
                connected = False

            client.send(f'{RESPONSE}02'.encode())
            client.send(
                f'{message.type}{1 if message_success else 0}'.encode())
            # send(client, Message(
            #     RESPONSE, f'{message.type}{1 if message_success else 0}'))

    if id in id_name:
        del name_id[name], id_name[id]
    print(f'[UPDATE] {name} left')
    client.close()


def create_client_connection():
    connection, address = server.accept()
    server.setblocking(True)

    active_threads = threading.activeCount()
    if active_threads == 1:
        print('[UPDATE] 1 Active Connection\n')
    else:
        print(f'[UPDATE] {active_threads} Active Connections\n')

    connections.append(connection)
    thread = threading.Thread(
        target=client_observe, args=(connection, address))
    thread.start()
    create_client_connection()


def boot_server():
    try:
        ADDRESS = get_address()
        server.bind(ADDRESS)
        server.listen()
        id = display_address(ADDRESS)
        print(f'[SUCCESS] Server is Running on {id}')

        for c in connections:
            c.close()
            del c

        create_client_connection()
    except socket.error as err:
        print(f'[ERROR] Socket binding failed: {str(err)}')
        exit()


boot_server()
