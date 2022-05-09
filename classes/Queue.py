import threading
from helpers import get_long_time, clear_console, header, console_colour_change
from DatabaseService import DatabaseService
import json

class ServerMessage:
    def __init__(self, _summary, _time, _message):
        self.summary = _summary
        self.time = _time
        self.message = _message

class Queue:
    # private field
    __queue_list = None
    __time = None
    database_service = None

    def __init__(self):
        self.__queue_list = []
        self.update_time()
    database_service = DatabaseService()

    def update_time(self):
        self.__time = get_long_time()


    def push(self, summary, message):
        self.update_time()
        summary = summary.upper()
        self.__queue_list.append(ServerMessage(summary, self.__time, message))

        print_str = self.get_print_str(summary, self.__time, message)

        print(print_str)

    def get_print_str(self, summary, time, message):
        if summary == 'HEADING':
            return message
        elif summary == 'OPTION':
            return f'[{summary}] {message}'
        else:
            return f'[{summary}][{time}] {message}'

    def save(self):
        while len(self.__queue_list) > 0:
            top = self.pop(self.__queue_list)
            self.database_service.add_table(top.summary, top.time, top.message)

    def print_row(self, row):
        row_obj = {"id": row[0], "summary": row[1], "time": row[2], "message": row[3]}
        print_str = self.get_print_str(row_obj['summary'], row_obj['time'], row_obj['message'])
        print(print_str)


    def restore(self):
        clear_console()
        rows = self.database_service.get_table()
        if len(rows) > 0:
            header('Saved Server')
            print()
            console_colour_change('green')
            for i in rows:
                self.print_row(i)
            console_colour_change('black')
        else:
            self.push('CAUTION', 'No server data is saved')


    def clear(self):
        self.database_service.delete_table()
        clear_console()

    def push_empty(self):
        print()


    def pop(self, queue):
        if len(queue) == 0:
            return None
        return queue.pop(0)