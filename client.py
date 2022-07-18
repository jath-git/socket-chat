from ast import Return
import socket
from helpers import header, clear_console
from constants import *
from encryption import send_simple_message, send_message, receive_message, all_connections_confirm

import threading
from getpass import getpass

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
stop_request_thread = threading.Event()
stop_request_thread.clear()
close_client_thread = threading.Event()
close_client_thread.clear()
end_receive = True

### SEND AND RECEIVE THREADS

def receive():
    messages = receive_message(client)

    if messages:
        if isinstance(messages, list):
            if len(messages) == 3 and (messages[1].get_type() == MESSAGE or messages[1].get_type() == RESPONSE):
                if messages[1].get_type() == MESSAGE:
                    print(
                        f'[{messages[2].text}] {messages[0].text}: {messages[1].text}')
                else:
                    print(
                        f'[{messages[2].text}] {messages[0].text} {messages[1].text}')
            else:
                if len(messages) < 1:
                    print('[CAUTION] No clients in server')
                else:
                    stop_receive()

                    header(' client list ')
                    print('[INPUT] Choose a client to send privately')
                    valid_connections_count = len(messages)
                    for i in range(valid_connections_count):
                        print(f'[OPTION] {i + 1} - {messages[i].text}')
                    client_index = input('> ')

                    if client_index.isdigit():
                        client_index = int(client_index) - 1
                    else:
                        client_index = -1

                    if client_index >= 0 and client_index < valid_connections_count:
                        print('[INPUT] Enter a message to send privately')
                        message_input = input('> ')
                        message_input = message_input[:99]

                        if message_input == '':
                            print('[ERROR] Message must not be empty')
                        else:
                            all_connections_confirm(
                                client, messages[client_index].text, message_input)
                    else:
                        print('[ERROR] Client index is not recognized')

                    start_transfer()
        elif messages.type == RESPONSE:
            print(messages.text)
        elif messages.type == STOP_CLIENT:
            return
        elif messages.type == STOP_SERVER:
            send_simple_message(client, STOP_SERVER)
        elif messages.type == VOID:
            pass
        elif messages.type == PAUSED:
            print(
                '[PAUSED] The server is paused')
            print('[NOTE] Future messages will be pending until unpaused')
            send_simple_message(client, PAUSED)
        elif messages.type == DISCONNECT_REQUEST:
            close_client_thread.set()
            send_simple_message(client, DISCONNECT_CONFIRM)
            print('[DISCONNECTED] You have been disconnected')
            print('[INPUT] Press any key to exit')
            return
        elif messages.type == DISCONNECT_SERVER:
            send_simple_message(client, DISCONNECT_REQUEST)

    receive()


def send():
    if close_client_thread.is_set() or stop_request_thread.is_set():
        return

    user_input = getpass('')

    if close_client_thread.is_set() or stop_request_thread.is_set():
        return

    if user_input == '':
        send()

    if user_input == '*':
        stop_receive()
        send_simple_message(client, MENU)
        menu()
    else:
        send_message(client, MESSAGE, user_input)
        send()

### MENU

def menu():
    header('menu')
    print("[OPTION] 1 - Change your name")
    print("[OPTION] 2 - Send a private message")
    print("[OPTION] 3 - Disconnect from chat room")
    print("[OPTION] 4 - Exit menu\n")

    option = input('> ')

    if option == '1':
        print('[INPUT] Enter new name:')
        text = input('> ')
        send_message(client, NAME, text)
    elif option == '2':
        send_simple_message(client, ALL_CONNECTIONS_REQUEST)
        start_receive()
        return
    elif option == '3':
        print()
        send_simple_message(client, DISCONNECT_REQUEST)
    elif option == '4' or option == '*':
        pass
    else:
        print('[ERROR] Invalid Input. Choose from 1 to 4\n')
        menu()

    start_transfer()

### INITALIZE THREADS AND CONNECT CLIENT

def stop_receive():
    global end_receive
    end_receive = True
    stop_request_thread.set()
    send_simple_message(client, STOP_CLIENT)


def start_send():
    stop_request_thread.clear()
    send_thread = threading.Thread(target=send)
    send_thread.start()


def start_transfer():
    global end_receive
    end_receive = True

    start_send()
    start_receive()
    print()
    header(' chat room ')


def start_receive():
    stop_request_thread.clear()

    global end_receive
    if end_receive or True:
        end_receive = False
        receive_thread = threading.Thread(target=receive)
        receive_thread.start()


def boot_client():
    def get_address():
        SERVER = socket.gethostbyname('localhost')
        PORT = 6002
        return (SERVER, PORT)
    ADDRESS = get_address()
    client.connect(ADDRESS)
    clear_console()
    header('instructions')
    print(f'[SUCCESS] Joining {ADDRESS[0]} ({ADDRESS[1]})')
    print('[CONTROL] Type and enter "*" anytime to access menu\n')
    print('[NOTE] You will not see your input')
    print('[NOTE] Press ENTER to submit message\n')

    start_transfer()


boot_client()
