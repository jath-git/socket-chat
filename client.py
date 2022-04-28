import socket
from shared import *
import threading
from queue import Queue
import atexit

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
response_map = {
    f'{DISCONNECT}1': '[SUCCESS] You disconnected',
    f'{MESSAGE}1': '[SUCCESS] Message sent',
    f'{MESSAGE}0': '[ERROR] Message must not be empty',
    f'{NAME}1': f'[SUCCESS] You joined',
    f'{NAME}0': '[ERROR] Name is empty or already exists',
}
client_connected = True
queue = Queue()
READ_INPUT = 0
RECEIVE = 1


def receive_response():
    response = client.recv(2).decode()
    print(f'{response_map[response]}')


def receive():
    message = client.recv(3).decode()

    if not message:
        return None

    message_code = message[0]
    if message_code == RESPONSE:
        receive_response()


def send(message):
    max_data = 99
    message_len = len(message.text)

    if message_len > 99:
        message_len = max_data
        message.text = message.text[0:max_data]

    client.send(f'{message.type}{str(message_len).zfill(2)}'.encode())

    if message.type != DISCONNECT:
        client.send(message.text.encode())

    response = ''
    if message.type == DISCONNECT:
        response = f'{DISCONNECT}1'
        global client_connected
        client_connected = False
        print(f'{response_map[response]}\n')


def read_input():
    continue_read = True
    print("[OPTION] 1 - Change your name")
    print("[OPTION] 2 - Send a message")
    print("[OPTION] 3 - Disconnect from chat room\n")
    option = input('> ')
    if option == '1':
        print('[INPUT] Enter new name:')
        text = input('> ')

        send(Message(NAME, text))
        response_map[f'{NAME}1'] = f'[SUCCESS] You renamed as {text}'
        queue.put(RECEIVE)
    elif option == '2':
        print('[INPUT] Enter message:')
        text = input('> ')
        send(Message(MESSAGE, text))
        queue.put(RECEIVE)
    elif option == '3':
        send(Message(DISCONNECT, ''))
        queue.put(RECEIVE)
        continue_read = False
    else:
        print('[ERROR] Invalid Input. Choose from 1 to 3\n')

    if continue_read:
        queue.put(READ_INPUT)


def work():
    top = queue.get()
    if top == READ_INPUT:
        read_input()
    if top == RECEIVE:
        receive()

    queue.task_done()
    work()


def create_work():
    queue.put(READ_INPUT)

    work_thread = threading.Thread(target=work)
    work_thread.start()


def boot_client():
    ADDRESS = get_address()
    client.connect(ADDRESS)
    id = display_address(ADDRESS)

    print(f'[SUCCESS] Joining from {id}\n')
    create_work()


boot_client()


def terminate_client():
    pass
    if client_connected:
        send(Message(DISCONNECT, ''))


atexit.register(terminate_client)
