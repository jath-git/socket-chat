import socket
import threading
from helpers import *
from constants import *
from encryption import *
from datetime import datetime
from getpass import getpass
from constants import *

connections = []
connections_id_map = {}
connections_address_map = {}
id_name_map = {}
name_id_map = {}
menu_thread = threading.Event()
menu_thread.clear()
disconnected_server = False


def get_long_time():
    short_time = get_short_time()
    return f'{"" if short_time[0] == "0" else "1"}{short_time[1]}:{short_time[2:4]} {short_time[4]}M'


def get_short_time():
    now = datetime.now()
    hour = now.hour
    min = now.minute
    section = 'AM'

    if hour == 0:
        hour = 12
    elif hour == 12:
        section = 'PM'
    elif hour > 12:
        hour -= 12
        section = 'PM'

    return f'{str(hour).zfill(2)}{str(min).zfill(2)}{section[0]}'


def broadcast(name, text, is_message):
    time = get_short_time()

    for c in connections:
        try:
            send_compound(c, name, text, time, is_message)
        except:
            remove_connection(c)


def remove_connection(c):
    if c in connections:
        if c in connections_id_map:
            id = connections_id_map[c]
            if id in id_name_map:
                name = id_name_map
                if name in name_id_map:
                    del name_id_map[name]
                del id_name_map[id]
            del connections_id_map[c]

        if c in connections_address_map:
            del connections_address_map[c]

        connections.remove(c)
        c.close()


def client_observe(client, address, already_joined):
    id = display_address(address)
    old_name = id_name_map[id] if id in id_name_map else id
    name = old_name

    connections_address_map[client] = address
    connections_id_map[client] = id

    if not already_joined:
        print(f'[USER][{get_long_time()}] {name} joined')
        for c in connections:
            try:
                send_compound(c, name, 'joined', get_short_time(), False)
            except:
                remove_connection(c)

    while True:
        if menu_thread.is_set():
            return

        try:
            message = receive_message(client)
        except:
            remove_connection(client)
            return

        if message:
            long_time = get_long_time()
            if isinstance(message, list):
                # all connections confirm (client_index, message)
                client_index = int(message[0].text)
                private_message = message[1].text
                try:
                    send_message(connections[client_index],
                                 RESPONSE, f'[PRIVATE][{long_time}] {name}: {private_message}')
                    send_message(client, RESPONSE,
                                 f'[SUCESS] Private message was sent')
                    print(f'[RECEIVED][{long_time}] {name}: {private_message}')
                except:
                    print(
                        f'[ERROR][{long_time}] Private message from {name} failed')
                    send_message(client, RESPONSE,
                                 f'[ERROR][{long_time}] Private message failed')

            elif message.type == MESSAGE:
                if message.text == '':
                    print(
                        f'[ERROR][{long_time}] {name} sent empty message')
                    send_message(client, RESPONSE,
                                 '[ERROR] Message must not be empty')
                else:
                    print(f'[RECEIVED][{long_time}] {name}: {message.text}')
                    broadcast(name, message.text, True)
            elif message.type == NAME:
                if message.text == '':
                    print(
                        f'[ERROR][{long_time}] {name} renamed empty string')
                    send_message(client, RESPONSE,
                                 f'[ERROR][{long_time}] New name must not be empty')
                elif message.text in name_id_map:
                    print(
                        f'[ERROR][{long_time}] {name} renamed to existing name')
                    send_message(client, RESPONSE,
                                 f'[ERROR][{long_time}] Name already exists')
                else:
                    old_name = name
                    name = message.text
                    if id in id_name_map:
                        del name_id_map[old_name]
                        id_name_map[id] = name
                        name_id_map[name] = id
                    else:
                        id_name_map[id] = name
                        name_id_map[name] = id

                    print(f'[USER][{long_time}] {old_name} renamed as {name}')
                    broadcast(old_name, f'renamed as {name}', False)
            elif message.type == MENU:
                print(f'[USER][{long_time}] {name} accessed menu')
                send_simple_message(client, MENU)
            elif message.type == VOID:
                send_simple_message(client, VOID)
            elif message.type == PAUSED:
                return
            elif message.type == ALL_CONNECTIONS_REQUEST:
                comment('reached 1')
                names = []
                for i in range(min(99, len(connections))):
                    name = get_name(connections[i])
                    names.append(name)

                all_connections_send(client, names)
            elif message.type == DISCONNECT_REQUEST:
                print(f'[USER][{long_time}] {name} disconnected')
                broadcast(name, 'disconnected', False)
                send_simple_message(client, DISCONNECT_REQUEST)
            elif message.type == DISCONNECT_CONFIRM:
                remove_connection(client)
                client.close()


def create_socket():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return server
    except socket.error as err:
        print(
            f'[ERROR][{get_long_time()}] Socket creation failed: {str(err)}')
        exit()


server = create_socket()
count_connection_creation = 0


def create_client_connection():
    global count_connection_creation, disconnected_server
    connection, address = server.accept()
    server.setblocking(True)

    connections.append(connection)
    connections_id_map[connection] = display_address(get_address())
    count_connection_creation += 1

    for c in connections:
        try:
            send_simple_message(c, VOID)
        except:
            remove_connection(c)

    long_time = get_long_time()
    if count_connection_creation == 1:
        print(f'[UPDATE][{long_time}] 1 Connection has been created')
    else:
        print(
            f'[UPDATE][{long_time}] {count_connection_creation} Connections have been created')

    receive_thread = threading.Thread(
        target=client_observe, args=(connection, address, False))
    receive_thread.start()

    if not disconnected_server:
        create_client_connection()


def kick_client():
    print()

    valid_connections_count = len(connections)

    if valid_connections_count == 0:
        print('[ERROR] No clients in server')
        return True

    header(' client list ')
    print('[INPUT] Choose a client to kick:')
    for i in range(valid_connections_count):
        c = connections[i]
        name = connections_id_map[c]

        if name in id_name_map:
            name = id_name_map[name]

        print(f'[OPTION] {i + 1} - {name}')

    print()
    client_index = input('> ')

    if client_index.isdigit():
        client_index = int(client_index) - 1
    else:
        client_index = -1

    if client_index >= 0 and client_index < valid_connections_count:
        return connections[client_index]
    else:
        print('[ERROR] Client index is not recognized')
        return None


def get_name(connection):
    name = 'unknown'

    if connection in connections_id_map:
        name = connections_id_map[connection]

        if name in id_name_map:
            name = id_name_map[name]

    return name


def server_menu():
    header('menu')
    print("[OPTION] 1 - Kick a client")
    print("[OPTION] 2 - Disconnect all clients")
    print("[OPTION] 3 - Send a message to all clients")
    print("[OPTION] 4 - Exit menu\n")
    option = input('> ')

    if option == '1':
        client_kicked = kick_client()

        if client_kicked == None:
            server_menu()
        else:
            restart_clients()
            broadcast(get_name(client_kicked), 'has been kicked out', False)
            send_simple_message(client_kicked, DISCONNECT_SERVER)
    elif option == '2':
        restart_clients()

        for c in connections:
            try:
                send_simple_message(c, DISCONNECT_SERVER)
            except:
                remove_connection(c)

        global disconnected_server
        disconnected_server = True

        print('\n[SUCCESS] All clients have been disconnected')

        return
    elif option == '3':
        print('[INPUT] Enter message to send:')
        server_message = input('> ')

        if server_message == '':
            print('[ERROR] Message must not be empty\n')
            server_menu()

        restart_clients()
        broadcast('', server_message, False)
    elif option == '4' or option == '*':
        restart_clients()
    else:
        print('[ERROR] Invalid Input. Choose from 1 to 4\n')
        server_menu()


def restart_clients():
    menu_thread.clear()
    for c in connections:
        try:
            receive_thread = threading.Thread(
                target=client_observe, args=(c, connections_address_map[c], True))
            receive_thread.start()

            send_message(c, RESPONSE, '[CONTINUE] Server is unpaused')
        except:
            remove_connection(c)


def read_input():
    user_input = getpass('')

    if len(user_input) > 0 and (user_input == '*' or user_input[len(user_input) - 1] == '*'):
        menu_thread.set()
        for c in connections:
            try:
                send_simple_message(c, PAUSED)
            except:
                remove_connection(c)

        server_menu()
        print()
        header(' chat server ')
    read_input()


def boot_server():
    try:
        ADDRESS = get_address()
        server.bind(ADDRESS)
        server.listen()
        id = display_address(ADDRESS)
        clear_console()
        header('instructions')
        print(f'[SUCCESS] Server is Running on {id}')
        print('[CONTROL] Type and enter "*" anytime to access menu\n')
        header(' chat server ')

        menu_thread = threading.Thread(target=read_input)
        menu_thread.start()
        create_client_connection()
    except socket.error as err:
        print(f'[ERROR][{get_long_time()}] Socket binding failed: {str(err)}')
        print(f'[FIX][{get_long_time()}] Try changing port number in shared.py')


boot_server()
