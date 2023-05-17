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
            SELECT c.id, c.timestamp, c.filename, c.text
            FROM captures c
            JOIN captures_fts cfts
            ON c.id = cfts.capture_id
            WHERE cfts.text MATCH ?
            ORDER BY c.timestamp DESC;
        """, (query,))

        result = c.fetchall()
        return [Capture(*row) for row in result]

    def get_last_capture(self):
        c = self.conn.cursor()
        c.execute("""
            SELECT id, timestamp, filename, text 
            FROM captures 
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        if (row := c.fetchone()) is None:
            return None

        return Capture(*row)

    def get_previous_n(self, capture, n):
        c = self.conn.cursor()
        c.execute("""
            SELECT id, timestamp, filename, text FROM captures 
            LIMIT ?1
            OFFSET ?2 - ?1 - 1
        """, (n, capture.id))

        result = c.fetchall()
        return [Capture(*row) for row in result]

    def get_next_n(self, capture, n):
        c = self.conn.cursor()
        c.execute("""
            SELECT id, timestamp, filename, text FROM captures 
            LIMIT ?1
            OFFSET ?2
        """, (n, capture.id))

        result = c.fetchall()
        return [Capture(*row) for row in result]

    def get_capture_by_id(self, id):
        c = self.conn.cursor()
        c.execute("""
            SELECT id, timestamp, filename, text 
            FROM captures WHERE id = ?
        """, (id,))

        if (row := c.fetchone()) is None:
            return None

        return Capture(*row)

    def insert_capture(self, filename, text, timestamp):
        with self.conn:
            c = self.conn.cursor()

            c.execute("""
                INSERT INTO captures (filename, text, timestamp)
                VALUES (?, ?, ?);
            """, (filename, text, timestamp))

            rowid = c.lastrowid
            c.execute("""
                INSERT INTO captures_fts (capture_id, text)
                VALUES (?, ?);
            """, (rowid, text))

    def setup(self):
        c = self.conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS captures (
                id INTEGER PRIMARY KEY,
                filename TEXT,
                timestamp TIMESTAMP,
                text TEXT
            );
        """)
        c.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS captures_fts
            USING fts5(capture_id, text);
        """)
        self.conn.commit()


    def __del__(self):
        if self.conn is not None:
            self.conn.close()
