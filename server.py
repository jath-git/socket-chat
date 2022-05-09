import socket
import threading
import sys
from helpers import *
from constants import *
from encryption import send_compound, send_simple_message, all_connections_send, send_message, receive_message
from getpass import getpass

sys.path.insert(0, './classes')
from Queue import Queue
from Sockets import Sockets


sockets = Sockets()
menu_thread = threading.Event()
menu_thread.clear()
disconnected_server = False
close_server_thread = threading.Event()
close_server_thread.clear()
long_time = get_long_time()
count_connection_creation = 0
queue = Queue()

### MENU

# get server to choose client to disconnect
def kick_client():
    valid_connections_count = len(sockets.connections)

    if valid_connections_count == 0:
        queue.push('ERROR', 'No clients in server')
        return True

    queue.push('HEADING', pad_dash(' client list '))
    queue.push('INPUT', 'Choose a client to kick:')
    for i in range(valid_connections_count):
        name = sockets.get_name_from_index(i)

        queue.push('OPTION', f'{i + 1} - {name}')

    queue.push_empty()
    client_index = input('> ')

    if client_index.isdigit():
        client_index = int(client_index) - 1
    else:
        client_index = -1

    if client_index >= 0 and client_index < valid_connections_count:
        name = sockets.get_name_from_index(client_index)
        return sockets.get_connection(name)
    else:
        queue.push('ERROR', 'Client index is not recognized')
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

    queue.push_empty()
    queue.push('SUCCESS', 'All clients have been disconnected')

def database_menu():
    queue.push('HEADING', pad_dash(' database menu '))
    queue.push('OPTION', '1 - Save server messages')
    queue.push('OPTION', '2 - Restore server messages')
    queue.push('OPTION', '3 - Clear server messages')
    queue.push('OPTION', '4 - Exit database menu')
    queue.push_empty()

    option = input('> ')

    if option == '1':
        queue.save()
        queue.push('DATABASE', 'Server has been saved successfully')
    elif option == '2':
        queue.restore()
    elif option == '3':
        queue.clear()
        queue.push('DATABASE', 'Server has been cleared successfully')
    elif option == '4':
        pass
    else:
        queue.push('ERROR', 'Invalid Input. Choose from 1 to 4')
        database_menu()

#  menu options only activated from settings when send/receive threads are paused
def server_menu():
    console_colour_change('blue')
    queue.push('HEADING', pad_dash('menu'))
    queue.push('OPTION', '1 - Kick a client')
    queue.push('OPTION', '2 - Disconnect all clients')
    queue.push('OPTION', '3 - Send a message to all clients')
    queue.push('OPTION', '4 - Shutdown server')
    queue.push('OPTION', '5 - Access database')
    queue.push('OPTION', '6 - Exit menu')
    queue.push_empty()

    option = input('> ')

    if option == '1':
        queue.push_empty()
        client_kicked = kick_client()

        if client_kicked == None:
            server_menu()
        else:
            restart_clients()
            
            if client_kicked in sockets.connections:
                send_simple_message(client_kicked, DISCONNECT_SERVER)
                broadcast(sockets.get_name(client_kicked), 'has been kicked out', False)
    elif option == '2':
        disconnect_all_users()
    elif option == '3':
        queue.push('INPUT', 'Enter message to send:')
        server_message = input('> ')

        if server_message == '':
            queue.push('ERROR', 'Message must not be empty')
            queue.push_empty()
            server_menu()

        restart_clients()
        broadcast('', server_message, False)
        queue.push('SUCCESS', 'Message has been sent out')
        queue.push_empty()
    elif option == '4':
        disconnect_all_users()
        close_server_thread.set()
        server.close()
    elif option == '5':
        database_menu()
    elif option == '6' or option == '*':
        restart_clients()
    else:
        queue.push('ERROR', 'Invalid Input. Choose from 1 to 6')
        queue.push_empty()
        server_menu()
        
    console_colour_change('black')


# call receive thread again
def restart_clients():
    menu_thread.clear()
    for c in sockets.connections:
        receive_thread = threading.Thread(
            target=client_observe, args=(c, sockets.get_address(c), True))
        receive_thread.start()

        try:
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
        queue.push('USER', f'{name} joined')
        for c in sockets.connections:
            try:
                send_compound(c, name, 'joined', get_short_time(), False)
            except:
                sockets.remove_socket(c)

    while True:
        if menu_thread.is_set():
            send_simple_message(connection, PAUSED)
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
                    queue.push('PRIVATE', f'{private_message} [from {name} to {client_name}]')
                except:
                    queue.push('ERROR', f'Private message from {name} failed')
                    send_message(connection, RESPONSE,
                                 f'[ERROR][{long_time}] Private message failed')

            elif message.type == MESSAGE:
                if message.text == '':
                    queue.push('ERROR', f'{name} sent empty message')
                    send_message(connection, RESPONSE,
                                 '[ERROR] Message must not be empty')
                else:
                    queue.push('RECEIVED', f'{name}: {message.text}')
                    broadcast(name, message.text, True)
            elif message.type == NAME:
                if message.text == '':
                    queue.push('ERROR', f'{name} renamed empty string')
                    send_message(connection, RESPONSE,
                                 f'[ERROR][{long_time}] New name must not be empty')
                elif sockets.has_name(message.text):
                    queue.push('ERROR', f'{name} renamed to existing name')
                    send_message(connection, RESPONSE,
                                 f'[ERROR][{long_time}] Name already exists')
                else:
                    old_name = name
                    name = message.text
                    sockets.change_name(connection, name)

                    queue.push('USER', f'{old_name} renamed as {name}')
                    broadcast(old_name, f'renamed as {name}', False)
            elif message.type == MENU:
                queue.push('USER', f'{name} accessed menu')
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
                queue.push('USER', f'{name} has disconnected')
                broadcast(name, 'disconnected', False)
                send_simple_message(connection, DISCONNECT_REQUEST)
            elif message.type == DISCONNECT_CONFIRM:
                sockets.remove_socket(connection)

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
        queue.push_empty()
        queue.push('HEADING', pad_dash(' chat server '))


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
        queue.push('ERROR', f'Socket creation failed: {str(err)}')
        exit()

server = create_socket()


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
        queue.push('UPDATE', 'Connection has been created')
    else:
        queue.push('UPDATE', f'{count_connection_creation} Connections have been created')

    receive_thread = threading.Thread(
        target=client_observe, args=(connection, address, False))
    receive_thread.start()

    if not disconnected_server:
        create_client_connection()

def boot_server():
    def get_address():
        SERVER = socket.gethostbyname('localhost')
        PORT = 6002
        return (SERVER, PORT)

    try:
        address = get_address()
        server.bind(address)
        server.listen()
        clear_console()
        console_colour_change('black')
        queue.push('HEADING', pad_dash(' instructions '))
        queue.push(f'SUCCESS', f'Server is Running on {address[0]} ({address[1]})')
        queue.push('CONTROL', 'Type and enter "*" anytime to access menu\n')
        queue.push('HEADING', pad_dash(' chat server '))

        read_thread = threading.Thread(target=read_input)
        read_thread.start()
        create_client_connection()
    except socket.error as err:
        if close_server_thread.is_set():
            queue.push('SUCCESS', 'Server has been shutdown')
        else:
            queue.push('ERROR', f'Socket binding failed: {str(err)}')
            queue.push('FIX', 'Try changing port number in shared.py')


boot_server()