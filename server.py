import socket
import threading
from helpers import *
from constants import *
from encryption import send_compound, send_simple_message, all_connections_send, send_message, receive_message
from getpass import getpass
from Sockets import Sockets

sockets = Sockets()
menu_thread = threading.Event()
menu_thread.clear()
disconnected_server = False
close_server_thread = threading.Event()
close_server_thread.clear()
long_time = get_long_time()
server = create_socket()
count_connection_creation = 0

### MENU

# get server to choose client to disconnect
def kick_client():
    valid_connections_count = len(sockets.connections)

    if valid_connections_count == 0:
        print(f'[ERROR][{long_time}] No clients in server')
        return True

    header(' client list ')
    print('[INPUT] Choose a client to kick:')
    for i in range(valid_connections_count):
        name = sockets.get_name_from_index(i)

        print(f'[OPTION] {i + 1} - {name}')

    print()
    client_index = input('> ')

    if client_index.isdigit():
        client_index = int(client_index) - 1
    else:
        client_index = -1

    if client_index >= 0 and client_index < valid_connections_count:
        name = sockets.get_name_from_index(client_index)
        return sockets.get_connection(name)
    else:
        print(f'[ERROR][{long_time}] Client index is not recognized')
        return None


# send message to tell client to disconnect
def disconnect_all_users():
    restart_clients()

    for c in sockets.connections:
        try:
            send_simple_message(c, DISCONNECT_SERVER)
        except:
            sockets.remove_socket(c)

    global disconnected_server
    disconnected_server = True

    for c in sockets.connections:
        sockets.remove_socket(c)

    print()
    print(
        f'[SUCCESS][{long_time}] All clients have been disconnected')

#  menu options only activated from settings when send/receive threads are paused
def server_menu():
    header('menu')
    print("[OPTION] 1 - Kick a client")
    print("[OPTION] 2 - Disconnect all clients")
    print("[OPTION] 3 - Send a message to all clients")
    print("[OPTION] 4 - Shutdown server")
    print("[OPTION] 5 - Exit menu\n")
    option = input('> ')

    if option == '1':
        print()
        client_kicked = kick_client()

        if client_kicked == None:
            server_menu()
        else:
            restart_clients()
            
            if client_kicked in sockets.connections:
                send_simple_message(client_kicked, DISCONNECT_SERVER)
                broadcast(sockets.get_name(client_kicked), 'has been kicked out', False)
            else:
                send_message(client, RESPONSE, '[ERROR] Client has already left')
    elif option == '2':
        disconnect_all_users()
    elif option == '3':
        print('[INPUT] Enter message to send:')
        server_message = input('> ')

        if server_message == '':
            print(f'[ERROR][{long_time}] Message must not be empty\n')
            server_menu()

        restart_clients()
        broadcast('', server_message, False)
        print(f'[SUCCESS][{long_time}] Message has been sent out\n')
    elif option == '4':
        disconnect_all_users()
        close_server_thread.set()
        server.close()
    elif option == '5' or option == '*':
        restart_clients()
    else:
        print(f'[ERROR][{long_time}] Invalid Input. Choose from 1 to 5\n')
        server_menu()


# call receive thread again
def restart_clients():
    menu_thread.clear()
    for c in sockets.connections:
        try:
            receive_thread = threading.Thread(
                target=client_observe, args=(c, sockets.get_address(c), True))
            receive_thread.start()

            send_message(c, RESPONSE, '[CONTINUE] Server is unpaused')
        except:
            sockets.remove_socket(c)


### SEND AND RECEIVE

# send text to all clients
def broadcast(name, text, is_message):
    time = get_short_time()

    for c in sockets.connections:
        try:
            send_compound(c, name, text, time, is_message)
        except:
            sockets.remove_socket(c)


# thread for each client used when something is received to server socket
def client_observe(connection, address, already_joined):
    name = sockets.get_name(connection)

    if not already_joined:
        print(f'[USER][{long_time}] {name} joined')
        for c in sockets.connections:
            try:
                send_compound(c, name, 'joined', get_short_time(), False)
            except:
                sockets.remove_socket(c)

    while True:
        if menu_thread.is_set():
            return

        try:
            message = receive_message(connection)
        except:
            sockets.remove_socket(connection)
            return

        if message:
            if isinstance(message, list):
                # format: all connections confirm (client_index, message)
                client_name = message[0].text
                private_message = message[1].text
                try:
                    send_message(sockets.get_connection(client_name),
                                 RESPONSE, f'[PRIVATE][{long_time}] {name}: {private_message}')
                    send_message(connection, RESPONSE,
                                 f'[SUCCESS] Private message was sent')
                    print(
                        f'[PRIVATE][{long_time}] {private_message} [from {name} to {client_name}] ')
                except:
                    print(
                        f'[ERROR][{long_time}] Private message from {name} failed')
                    send_message(connection, RESPONSE,
                                 f'[ERROR][{long_time}] Private message failed')

            elif message.type == MESSAGE:
                if message.text == '':
                    print(
                        f'[ERROR][{long_time}] {name} sent empty message')
                    send_message(connection, RESPONSE,
                                 '[ERROR] Message must not be empty')
                else:
                    print(f'[RECEIVED][{long_time}] {name}: {message.text}')
                    broadcast(name, message.text, True)
            elif message.type == NAME:
                if message.text == '':
                    print(
                        f'[ERROR][{long_time}] {name} renamed empty string')
                    send_message(connection, RESPONSE,
                                 f'[ERROR][{long_time}] New name must not be empty')
                elif sockets.has_name(message.text):
                    print(
                        f'[ERROR][{long_time}] {name} renamed to existing name')
                    send_message(connection, RESPONSE,
                                 f'[ERROR][{long_time}] Name already exists')
                else:
                    old_name = name
                    name = message.text
                    sockets.change_name(connection, name)

                    print(f'[USER][{long_time}] {old_name} renamed as {name}')
                    broadcast(old_name, f'renamed as {name}', False)
            elif message.type == MENU:
                print(f'[USER][{long_time}] {name} accessed menu')
                send_simple_message(connection, MENU)
            elif message.type == VOID:
                pass
            elif message.type == STOP_SERVER:
                return
            elif message.type == STOP_CLIENT:
                send_simple_message(connection, STOP_CLIENT)
            elif message.type == PAUSED:
                return
            elif message.type == ALL_CONNECTIONS_REQUEST:
                names = []
                for i in range(min(99, len(sockets.connections))):
                    names.append(sockets.get_name_from_index(i))

                all_connections_send(connection, names)
            elif message.type == DISCONNECT_REQUEST:
                print(f'[USER][{long_time}] {name} is disconnecting')
                broadcast(name, 'disconnected', False)
                send_simple_message(connection, DISCONNECT_REQUEST)
            elif message.type == DISCONNECT_CONFIRM:
                sockets.remove_socket(connection)
                connection.close()

# receive thread continuously checks if menu should be activated
def read_input():
    user_input = getpass('')

    if len(user_input) > 0 and (user_input == '*' or user_input[len(user_input) - 1] == '*'):
        menu_thread.set()
        for c in sockets.connections:
            try:
                send_simple_message(c, PAUSED)
            except:
                sockets.remove_socket(c)

        server_menu()
        print()
        header(' chat server ')

    if not close_server_thread.is_set():
        read_input()


### INITIALIZE SOCKETS AND THREADS

# initialize server socket
def create_socket():
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # for destroying server
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return server
    except socket.error as err:
        print(
            f'[ERROR][{long_time}] Socket creation failed: {str(err)}')
        exit()


def create_client_connection():
    global count_connection_creation, disconnected_server
    connection, address = server.accept()
    server.setblocking(True)

    count_connection_creation += 1

    sockets.add_socket(connection, address)

    for c in sockets.connections:
        try:
            send_simple_message(c, VOID)
        except:
            sockets.remove_socket(c)

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

def boot_server():
    try:
        server = create_socket()
        address = get_address()
        server.bind(address)
        server.listen()
        clear_console()
        header('instructions')
        print(f'[SUCCESS][{long_time}] Server is Running on {address[0]} ({address[1]}')
        print(
            f'[CONTROL][{long_time}] Type and enter "*" anytime to access menu\n')
        header(' chat server ')

        menu_thread = threading.Thread(target=read_input)
        menu_thread.start()
        create_client_connection()
    except socket.error as err:
        if close_server_thread.is_set():
            print(f'[SUCCESS][{long_time}] Server has been shutdown')
        else:
            print(f'[ERROR][{long_time}] Socket binding failed: {str(err)}')
            print(f'[FIX][{long_time}] Try changing port number in shared.py')


boot_server()
