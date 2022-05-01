import socket
import os
from math import floor
from datetime import datetime

PORT = 6000 + int(datetime.now().minute)


def header(heading):
    def pad_dash(str):
        total_length = 50
        dash_length = floor((total_length - len(str)) / 2)

        dashes = ''
        for _ in range(dash_length):
            dashes += '-'

        return f'{dashes}{str}{dashes}'

    print(pad_dash(heading.upper()))


def comment(str):
    write_comment = True

    if write_comment:
        return
    print(str)


def clear_console():
    command = 'cls' if os.name in ('nt', 'dos') else 'clear'
    os.system(command)


def get_address():
    HOST = socket.gethostname()
    SERVER = socket.gethostbyname(HOST)
    return (SERVER, PORT)


def display_address(address):
    return f'{address[0]} ({address[1]})'
