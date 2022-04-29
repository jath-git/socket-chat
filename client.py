import socket
from shared import *
import threading
from getpass import getpass

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
stop_request_thread = threading.Event()
stop_request_thread.clear()
close_client_thread = threading.Event()
close_client_thread.clear()
end_receive = True


def receive():
    messages = receive_message(client)

    if messages:
        if isinstance(messages, list):
            if messages[1].get_type() == MESSAGE:
                print(
                    f'[{messages[2].text}] {messages[0].text}: {messages[1].text}')
            else:
                print(f'[{messages[2].text}] {messages[0].text} {messages[1].text}')
        elif messages.type == RESPONSE:
            print(messages.text)
        elif messages.type == VOID:
            pass
        elif messages.type == DISCONNECT_CONFIRM:
            close_client_thread.set()
            print('[SUCCESS] You are now unable to send/receive. Press any key to exit')
            return

    if stop_request_thread.is_set():
        global end_receive
        end_receive = True
    else:
        receive()


def send():
    if close_client_thread.is_set():
        send_disconnect_confirm(client)
        return

    user_input = getpass('')
    if user_input == '':
        send()

    if user_input == '*':
        stop_request_thread.set()
    else:
        send_message(client, MESSAGE, user_input)

    if stop_request_thread.is_set():
        send_void(client)
        menu()
    else:
        send()


def menu():
    header('menu')
    print("[OPTION] 1 - Change your name")
    # print("[OPTION] 2 - Send a private message")
    print("[OPTION] 2 - Disconnect from chat room")
    print("[OPTION] 3 - Exit menu\n")

    option = input('> ')

    if option == '1':
        print('[INPUT] Enter new name:')
        text = input('> ')

        send_message(client, NAME, text)
        menu()
    # elif option == '2':
    #     pass
    #     menu()
    elif option == '2':
        print()
        send_disconnect_request(client)
    elif option == '3' or option == '*':
        print()
        header('chat room')
    else:
        print('[ERROR] Invalid Input. Choose from 1 to 4\n')
        menu()

    start_transfer()


def start_transfer():
    global end_receive

    stop_request_thread.clear()

    send_thread = threading.Thread(target=send)
    send_thread.start()

    if end_receive:
        end_receive = False
        receive_thread = threading.Thread(target=receive)
        receive_thread.start()


def boot_client():
    ADDRESS = get_address()
    client.connect(ADDRESS)
    id = display_address(ADDRESS)
    clear_console()
    header('instructions')
    print(f'[SUCCESS] Joining from {id}')
    print('[CONTROL] Enter "*" anytime to access menu\n')
    print('[NOTE] You will not see your input')
    print('[NOTE] Press ENTER to submit message\n')
    header('chat room')

    start_transfer()


boot_client()
