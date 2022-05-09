import threading
from helpers import get_long_time, clear_console, header
from DatabaseService import DatabaseService

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

        print_str = ''
        if summary == 'HEADING':
            print_str = message
        elif summary == 'OPTION':
            print_str = f'[OPTION] {message}'
        else:
            print_str = f'[{summary}][{self.__time}] {message}'

        print(print_str)

    def save(self):
        while len(self.__queue_list) > 0:
            top = self.pop(self.__queue_list)
            self.database_service.add_table(top.summary, top.time, top.message)

    def restore(self):
        clear_console()
        header('Saved Server')
        rows = self.database_service.get_table()
        for i in rows:
            print(i)

    def clear(self):
        self.database_service.delete_table()
        clear_console()

    def push_empty(self):
        print()


    def pop(self, queue):
        if len(queue) == 0:
            return None
        return queue.pop(0)