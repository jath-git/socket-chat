# use class to maintain all valid connections connected to server

class Sockets:
    # public fields
    connections = []

    # private fields
    __connection_address_map = {}
    __connection_name_map = {}
    __name_connection_map = {}

    def display_address(self, address):
        return f'{address[0]} ({address[1]})'

    def add_socket(self, _connection, _address):
        self.connections.append(_connection)
            
        self.__connection_address_map[_connection] = _address
        
        name = self.display_address(_address)
        self.__connection_name_map[_connection] = name
        self.__name_connection_map[name] = _connection

    def remove_socket(self, c):
        if c in self.connections:
            if c in self.__connection_name_map:
                name = self.__connection_name_map[c]
                if name in self.__name_connection_map:
                    del self.__name_connection_map[name]
                del self.__connection_name_map[c]

            if c in self.__connection_address_map:
                del self.__connection_address_map[c]

            self.connections.remove(c)
        c.close()

    def get_name(self, connection):
        return self.__connection_name_map[connection]

    def get_address(self, connection):
        return self.__connection_address_map[connection]

    def get_name_from_index(self, index):
        return self.get_name(self.get_connection_from_index(index))

    def has_name(self, name):
        return name in self.__name_connection_map

    def get_connection(self, name):
        return self.__name_connection_map[name]

    def has_connection(self, connection):
        return connection in self.connections

    def get_connection_from_index(self, index):
        return self.connections[index]

    def change_name(self, connection, new_name):
        old_name = self.__connection_name_map[connection]
        self.__connection_name_map[connection] = new_name
        self.__name_connection_map[new_name] = connection
        del self.__name_connection_map[old_name]