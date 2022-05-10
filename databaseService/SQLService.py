import mysql.connector
from os import getenv
from dotenv import load_dotenv

class SQLService:
    mycursor = None

    def __init__(self):
        load_dotenv()
        passwd = getenv('MYSQL_PASSWORD')
        if passwd == None:
            # set MYSQL_PASSWORD in .env or set below
            passwd = ''

        mydb = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            passwd = passwd
        )

        mycursor = mydb.cursor()
        
        mycursor.execute('SHOW DATABASES LIKE \'chatserverdb\';')

        if self.is_empty(mycursor):
            mycursor.execute('CREATE DATABASE chatserverdb;')

        mydb = mysql.connector.connect(
            host = 'localhost',
            user = 'root',
            passwd = passwd,
            database = 'chatserverdb'
        )
        
        mycursor = mydb.cursor()

        self.mydb = mydb
        self.mycursor = mycursor

    def create_table(self):
        mycursor = self.mycursor
        mycursor.execute('SHOW TABLES LIKE \'Main\';')
        if self.is_empty(mycursor):
            mycursor.execute('CREATE TABLE Main(id INT PRIMARY KEY AUTO_INCREMENT, summary VARCHAR(99) NOT NULL, time VARCHAR(99), message VARCHAR(99) NOT NULL);')

    def add_table(self, summary, time, message):
        insertFormula = 'INSERT INTO Main (summary, time, message) VALUES (%s, %s, %s);'
        mycursor = self.mycursor
        self.create_table()
        mycursor.execute(insertFormula, (summary, time, message))
        self.update_table()

    def delete_table(self):
        mycursor = self.mycursor
        mycursor.execute('SHOW TABLES LIKE \'Main\';')
        
        if not self.is_empty(mycursor):
            mycursor.execute('DELETE from Main')
            self.update_table()
            self.print_table()

    def update_table(self):
        self.mydb.commit()

    def show_databases(self):
        mycursor = self.mycursor
        mycursor.execute('SHOW DATABASES;')
        print(mycursor.fetchall())
        
    def print_table(self):
        mycursor = self.mycursor
        mycursor.execute('SELECT * FROM Main;')
        for i in mycursor:
            print(i)

    def get_table(self):
        mycursor = self.mycursor
        mycursor.execute('SHOW TABLES LIKE \'Main\';')
        if self.is_empty(mycursor):
            return []
        
        mycursor.execute('SELECT * FROM Main ORDER BY id ASC;')
        table_rows = []
        for r in mycursor:
            table_rows.append(r)

        return table_rows

    def is_empty(self, mycursor):
        return self.len(mycursor) == 0

    def len(self, mycursor):
        counter = 0
        for _ in mycursor:
            counter += 1
        return counter