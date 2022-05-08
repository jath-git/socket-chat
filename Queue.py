import threading
from helpers import get_long_time

class Queue:
    # private field
    __queue_list = None
    __time = None

    def __init__(self):
        self.__queue_list = []
        self.update_time()

    def update_time(self):
        self.__time = get_long_time()

    def push_simple(self, print_str):
        self.__queue_list.append(print_str)
        print(print_str)


    def push(self, summary, message):
        self.update_time()
        print_str = f'[{summary.upper()}][{self.__time}] {message}'
        self.push_simple(print_str)

    def push_empty(self):
        self.push_simple('')


    def pop(self, queue):
        if len(queue) == 0:
            return None
        return queue.pop(0)