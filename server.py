import socket
import threading
from shared import *
from datetime import datetime
from getpass import getpass
import atexit


def exit_handler():
    print('My application is ending!')


atexit.register(exit_handler)

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
            remove_connection(c)
            return

        if message:
            long_time = get_long_time()
            if message.type == MESSAGE:
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
                send_menu(client)
            elif message.type == VOID:
                send_void(client)
            elif message.type == PAUSED:
                return
            elif message.type == DISCONNECT_REQUEST:
                broadcast(name, 'disconnected', False)
                send_disconnect_request(client)
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
    connections_address_map[connection] = address
    count_connection_creation += 1

    for c in connections:
        try:
            send_void(c)
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

    if disconnected_server:
        create_client_connection()


def server_menu():
    header('menu')
    print("[OPTION] 1 - Kick a player")
    print("[OPTION] 2 - Disconnect server")
    print("[OPTION] 3 - Exit menu\n")
    option = input('> ')

    if option == '1':
        pass
    elif option == '2':
        for c in connections:
            global disconnected_server
            send_disconnect_server(c)
            remove_connection(c)
            c.close()
            disconnected_server = True
        return False
    elif option == '3' or option == '*':
        pass
    else:
        print('[ERROR] Invalid Input. Choose from 1 to 3\n')
        server_menu()

    return True


def read_input():
    user_input = getpass('')

    if len(user_input) > 0 and (user_input == '*' or user_input[len(user_input) - 1] == '*'):
        menu_thread.set()
        for c in connections:
            try:
                send_paused(c)
            except:
                remove_connection(c)

        boot_server = server_menu()

        if not boot_server:
            return

        menu_thread.clear()
        for c in connections:
            try:
                receive_thread = threading.Thread(
                    target=client_observe, args=(c, connections_address_map[c], True))
                receive_thread.start()

                send_message(c, RESPONSE, '[CONTINUE] Server is unpaused')
            except:
                remove_connection(c)


def boot_server():
    try:
        ADDRESS = get_address()
        server.bind(ADDRESS)
        server.listen()
        id = display_address(ADDRESS)
        clear_console()
        header('instructions')
        print(f'[SUCCESS] Server is Running on {id}')
        print('[CONTROL] Enter "*" anytime to access menu\n')
        header(' chat server ')

        menu_thread = threading.Thread(target=read_input)
        menu_thread.start()
        create_client_connection()
    except socket.error as err:
        print(f'[ERROR][{get_long_time()}] Socket binding failed: {str(err)}')


boot_server()
