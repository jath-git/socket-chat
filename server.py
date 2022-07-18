import socket
import threading
import sys
from helpers import *
from constants import *
from encryption import send_compound, send_simple_message, all_connections_send, send_message, receive_message
from getpass import getpass

sys.path.insert(0, './classes')
sys.path.insert(0, './databaseService')
from Queue import Queue
from Sockets import Sockets
from FirebaseService import FirebaseService
import firebase_admin
from firebase_admin import credentials, firestore

sockets = Sockets()
menu_thread = threading.Event()
menu_thread.clear()
disconnected_server = False
close_server_thread = threading.Event()
close_server_thread.clear()
long_time = get_long_time()
count_connection_creation = 0
notifications_counter = 0
queue = Queue()

# initialize db
cred = credentials.Certificate('./FirebaseKey.json')
app = firebase_admin.initialize_app(cred)
db = firebase_admin.firestore.client()
firebase_service = FirebaseService(db)

### MENU

# get server to choose client to disconnect
def kick_client():
    valid_connections_count = len(sockets.connections)

    if valid_connections_count == 0:
        push_and_print('ERROR', 'No clients in server')
        return True

    push_and_print('HEADING', pad_dash(' client list '))
    push_and_print('INPUT', 'Choose a client to kick:')
    for i in range(valid_connections_count):
        name = sockets.get_name_from_index(i)

        push_and_print('OPTION', f'{i + 1} - {name}')

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
        push_and_print('ERROR', 'Client index is not recognized')
        return None


# send message to tell client to disconnect
def disconnect_all_users():
    restart_clients()

    while len(sockets.connections) > 0:
        try:
            send_simple_message(sockets.connections[0], DISCONNECT_SERVER)
            sockets.connections.pop(0)
        except:
            sockets.connections.pop(0)

    global disconnected_server
    disconnected_server = True

    queue.push_empty()
    push_and_print('SUCCESS', 'All clients have been disconnected')

def database_menu():
    push_and_print('HEADING', pad_dash(' database menu '))
    push_and_print('OPTION', '1 - Save server messages')
    push_and_print('OPTION', '2 - Restore server messages')
    push_and_print('OPTION', '3 - Clear server messages')
    push_and_print('OPTION', '4 - Exit database menu')
    queue.push_empty()

    option = input('> ')

    database_message = ''
    if option == '1':
        queue.save()
        database_message = 'Server has been saved'
    elif option == '2':
        if queue.restore():
            database_message = 'Server has been restored'
        else:
            database_message = 'No server data to restore'
    elif option == '3':
        queue.clear()
        database_message = 'Server has been cleared'
    elif option == '4':
        return
    else:
        push_and_print('ERROR', 'Invalid Input. Choose from 1 to 4')
        database_menu()

    console_colour_change('black')
    push_and_print('DATABASE', database_message)
    

#  menu options only activated from settings when send/receive threads are paused
def server_menu():
    console_colour_change('blue')
    push_and_print('HEADING', pad_dash('menu'))
    push_and_print('OPTION', '1 - Kick a client')
    push_and_print('OPTION', '2 - Disconnect all clients')
    push_and_print('OPTION', '3 - Send a message to all clients')
    push_and_print('OPTION', '4 - Shutdown server')
    # push_and_print('OPTION', '5 - Access database')
    push_and_print('OPTION', '5 - Exit menu')
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
        push_and_print('INPUT', 'Enter message to send:')
        server_message = input('> ')

        if server_message == '':
            push_and_print('ERROR', 'Message must not be empty')
            queue.push_empty()
            server_menu()

        restart_clients()
        broadcast('', server_message, False)
        push_and_print('SUCCESS', 'Message has been sent out')
        queue.push_empty()
    elif option == '4':
        disconnect_all_users()
        close_server_thread.set()
        server.close()
        firebase_service.update_document('active', False)
        firebase_service.update_document('approxnotifications', notifications_counter)
        return
    # elif option == '5':
    #     database_menu()
    elif option == '5' or option == '*':
        restart_clients()
    else:
        push_and_print('ERROR', 'Invalid Input. Choose from 1 to 6')
        queue.push_empty()
        server_menu()
        
    console_colour_change('black')
    firebase_service.update_document('approxnotifications', notifications_counter)


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
        push_and_print('USER', f'{name} joined')
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
                    push_and_print('PRIVATE', f'{private_message} [from {name} to {client_name}]')
                except:
                    push_and_print('ERROR', f'Private message from {name} failed')
                    send_message(connection, RESPONSE,
                                 f'[ERROR][{long_time}] Private message failed')

            elif message.type == MESSAGE:
                if message.text == '':
                    push_and_print('ERROR', f'{name} sent empty message')
                    send_message(connection, RESPONSE,
                                 '[ERROR] Message must not be empty')
                else:
                    push_and_print('RECEIVED', f'{name}: {message.text}')
                    broadcast(name, message.text, True)
            elif message.type == NAME:
                if message.text == '':
                    push_and_print('ERROR', f'{name} renamed empty string')
                    send_message(connection, RESPONSE,
                                 f'[ERROR][{long_time}] New name must not be empty')
                elif sockets.has_name(message.text):
                    push_and_print('ERROR', f'{name} renamed to existing name')
                    send_message(connection, RESPONSE,
                                 f'[ERROR][{long_time}] Name already exists')
                else:
                    old_name = name
                    name = message.text
                    sockets.change_name(connection, name)

                    push_and_print('USER', f'{old_name} renamed as {name}')
                    broadcast(old_name, f'renamed as {name}', False)
            elif message.type == MENU:
                push_and_print('USER', f'{name} accessed menu')
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
                push_and_print('USER', f'{name} has disconnected')
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
        push_and_print('HEADING', pad_dash(' chat server '))


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
        push_and_print('ERROR', f'Socket creation failed: {str(err)}')
        exit()

server = create_socket()


def create_client_connection():
    global count_connection_creation, disconnected_server
    connection, address = server.accept()
    server.setblocking(True)

    count_connection_creation += 1
    firebase_service.update_document_int('connections', 1)

    sockets.add_socket(connection, address)

    for c in sockets.connections:
        try:
            send_simple_message(c, VOID)
        except:
            sockets.remove_socket(c)

    if count_connection_creation == 1:
        push_and_print('UPDATE', 'Connection has been created')
    else:
        push_and_print('UPDATE', f'{count_connection_creation} Connections have been created')

    receive_thread = threading.Thread(
        target=client_observe, args=(connection, address, False))
    receive_thread.start()

    if not disconnected_server:
        create_client_connection()

def push_and_print(summary, message):
    queue.push(summary, message)
    if summary != 'OPTION' and summary != 'HEADING':
        global notifications_counter
        notifications_counter += 1

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

        firebase_service.create_document(f'{address[0]} ({address[1]})')
        firebase_service.set_document({
            'active': True,
            'connections': 0,
            'approxnotifications': 0,
            'datecreated': get_date()
        })
        
        console_colour_change('black')
        push_and_print('HEADING', pad_dash(' instructions '))
        push_and_print(f'SUCCESS', f'Server is Running on {address[0]} ({address[1]})')
        push_and_print('CONTROL', 'Type and enter "*" anytime to access menu\n')
        push_and_print('HEADING', pad_dash(' chat server '))

        read_thread = threading.Thread(target=read_input)
        read_thread.start()
        create_client_connection()
    except socket.error as err:
        if close_server_thread.is_set():
            push_and_print('SUCCESS', 'Server has been shutdown')
        else:
            push_and_print('ERROR', f'Socket binding failed: {str(err)}')
            push_and_print('FIX', 'Try changing port number in shared.py')


boot_server()