#  Copyright (c) 2024. Jonas Zellweger, University of Zurich (jonas.zellweger@uzh.ch)
#  All rights reserved.

import sys
import psycopg
from psycopg.rows import dict_row
from helpers.io_handler import IOHandler, Color


class Database:

    def __init__(self, database):
        self.connection = None
        self.cursor = None
        self.database = database

    def open(self):
        if not self.connection:
            try:
                self.connection = psycopg.connect(
                    host="localhost",
                    port=5432,
                    dbname=self.database,
                    row_factory=dict_row,
                )
                self.cursor = self.connection.cursor()
                IOHandler.print_color(f"--- Connection to database {self.database} established")
            except psycopg.OperationalError as err:
                IOHandler.print_color(
                    message=f"--- Error while connecting to database '{self.database}':\n=> {err}",
                    color=Color.RED
                )
                sys.exit()
        else:
            IOHandler.print_color(f"--- Already connected to database '{self.database}'")
    
    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            IOHandler.print_color(f"--- Closed connection to database '{self.database}'")
    
    def fetch_one(self, query):
        if self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchone()

    def fetch_many(self, size=0):
        if self.connection:
            return self.cursor.fetchmany(size)

    def fetch_all(self, query):
        if self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def execute(self, query, values=None):
        if self.connection:
            try:
                if values:
                    result = self.cursor.execute(query, values)
                else:
                    result = self.cursor.execute(query)
                self.connection.commit()
                return True, result
            except Exception as e:
                return False, e
