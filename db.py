# TODO: make DB class to encapsulate setup and getting conn

import sqlite3
from dataclasses import dataclass

@dataclass
class Capture:
    id: int
    timestamp: int
    filename: str
    text: str

class Database:
    conn = None

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)

    def query(self, query):
        c = self.conn.cursor()
        c.execute("""
            SELECT id, timestamp, filename, text FROM captures
            WHERE text MATCH ?
            ORDER BY timestamp DESC;
        """, (query,))

        return [Capture(*row) for row in c.fetchall()]

    def insert_capture(self, filename, text, timestamp):
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO captures (filename, text, timestamp)
            VALUES (?, ?, ?);
        """, (filename, text, timestamp))
        self.conn.commit()

    def setup(self):
        c = self.conn.cursor()
        c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS captures USING fts5(id, filename, timestamp, text);")
        c.execute("""
            CREATE TABLE IF NOT EXISTS captures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                timestamp TIMESTAMP,
                text TEXT
            );
        """)
        self.conn.commit()


    def __del__(self):
        if self.conn is not None:
            self.conn.close()
