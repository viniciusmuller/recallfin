import cv2
import pytesseract
import numpy as np
import mss

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
import os

IMAGES_DIRECTORY = "screenshots/"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def capture():
    with mss.mss() as sct:
        monitor = sct.monitors[1] # TODO: maybe select monitor?
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(thresholded)

    return (frame, text)

def setup_database(conn):
    c = conn.cursor()
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS captures USING fts5(id, image_path, timestamp, text);")
    c.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT,
            timestamp TIMESTAMP,
            text TEXT
        );
    """)
    conn.commit()

def insert_capture(conn, image, content):
    c = conn.cursor()

    timestamp = datetime.now()

    img_relative_path = f"{IMAGES_DIRECTORY}/{timestamp}.jpg"
    img_abs_path = os.path.abspath(img_relative_path)

    cv2.imwrite(img_abs_path, image)

    c.execute("""
        INSERT INTO captures (image_path, text, timestamp)
        VALUES (?, ?, ?);
    """, (img_abs_path, content, timestamp))

    conn.commit()
    logging.debug('Inserted capture')

def query_database(conn, query):
    c = conn.cursor()
    c.execute("""
        SELECT id, timestamp, image_path, text FROM captures
        WHERE text MATCH ?;
    """, (query,))

    # todo: maybe map to dataclass
    return c.fetchall()

def show_image(image_path, timestamp):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    cv2.imshow(f"Screenshot at {timestamp}", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def setup_images_directory(directory_path):
    directory = Path(directory_path)

    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)


def main():
    conn = sqlite3.connect('database.db')

    setup_images_directory(IMAGES_DIRECTORY)
    setup_database(conn)

    (image, content) = capture()
    insert_capture(conn, image, content)

    query = input("your query here: ")
    for row in query_database(conn, query):
        image_path = row[2]
        timestamp = row[1]

        print(image_path, timestamp)
        if input("show image?") == "y":
            show_image(image_path, timestamp)

    conn.close()

if __name__ == '__main__':
    main()
