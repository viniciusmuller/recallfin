import cv2
import pytesseract
import numpy as np
import mss

from pathlib import Path
import logging
import time
import os

from constants import IMAGES_DIRECTORY, DATABASE_PATH
from database import Database

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

    # TODO: improve image processing before running OCR
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(thresholded)

    return (frame, text)

"""
Saves the image to disk and add an entry for it in the database
"""
def save_capture(db, image, image_text):
    timestamp = int(time.time())

    filename = f"{timestamp}.jpg"
    img_path = f"{IMAGES_DIRECTORY}/{filename}"
    img_abs_path = os.path.abspath(img_path)

    cv2.imwrite(img_abs_path, image)
    db.insert_capture(filename, image_text, timestamp)

    logging.debug('Inserted capture')

def setup_images_directory(directory_path):
    directory = Path(directory_path)

    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)


def main():
    db = Database(DATABASE_PATH)
    db.setup()

    setup_images_directory(IMAGES_DIRECTORY)

    (image, content) = capture()
    save_capture(db, image, content)

if __name__ == '__main__':
    main()
