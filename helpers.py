import socket
import os
from math import floor
from datetime import datetime

# code for time in format HH:MM AM/PM
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


def get_long_time():
    short_time = get_short_time()
    return f'{"" if short_time[0] == "0" else "1"}{short_time[1]}:{short_time[2:4]} {short_time[4]}M'


def pad_dash(str):
    str = str.upper()
    total_length = 50
    dash_length = floor((total_length - len(str)) / 2)

    dashes = ''
    for _ in range(dash_length):
        dashes += '-'

    return f'{dashes}{str}{dashes}'

# pad string with hyphens, symmetrically
def header(heading):
    print(pad_dash(heading))

# clear user shell
def clear_console():
    command = 'cls' if os.name in ('nt', 'dos') else 'clear'
    os.system(command)

def get_address():
    SERVER = socket.gethostbyname('localhost')
    PORT = 6002
    return (SERVER, PORT)
