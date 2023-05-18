import cv2
import pytesseract
import numpy as np
import mss
import schedule
import imagehash
from PIL import Image

from pathlib import Path
import argparse
import threading
import logging
import time
import os

from constants import IMAGES_DIRECTORY, DATABASE_PATH
from database import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

def list_monitors():
    with mss.mss() as sct:
        print("Available screens:")
        for i, monitor in enumerate(sct.monitors):
            print(i, "->", monitor)

def capture(monitor_index):
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)

    # TODO: improve image processing before running OCR
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(thresholded)

    return (frame, text)

def hash_image(cv2_image):
    return imagehash.average_hash(Image.fromarray(cv2_image))

"""
Saves the image to disk and add an entry for it in the database
"""
def save_capture(db, image, image_text):
    last_capture = db.get_last_capture()
    if last_capture is not None:
        img_hash = hash_image(image)

        last_img_path = f"{IMAGES_DIRECTORY}/{last_capture.filename}"
        last_img_hash = hash_image(cv2.imread(last_img_path))

        difference = img_hash - last_img_hash
        if difference < 5:
            logging.info("Captured image and last capture too similar, aborting capture")
            return

    timestamp = int(time.time())

    filename = f"{timestamp}.jpg"
    img_path = f"{IMAGES_DIRECTORY}/{filename}"
    img_abs_path = os.path.abspath(img_path)

    cv2.imwrite(img_abs_path, image)
    db.insert_capture(filename, image_text, timestamp)

    logging.info('Image capture persisted')

def setup_images_directory(directory_path):
    directory = Path(directory_path)

    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        logging.info("Screenshots directory does not exist, creating it")

def do_capture(monitor_index):
    def inner():
        db = Database(DATABASE_PATH)
        logging.info(f'Starting image capture')
        (image, content) = capture(monitor_index)
        save_capture(db, image, content)

    job_thread = threading.Thread(target=inner)
    job_thread.start()

def main():
    parser = argparse.ArgumentParser(
        prog='recallfin',
        description='Supercharge your memory using OCR, SQLite and HTML'
    )
    parser.add_argument('-i', '--interval', help='interval in seconds to capture the screen', type=int, default=10)
    parser.add_argument('-l', '--list-monitors', help='list available screens', action='store_true')
    parser.add_argument('-m', '--monitor-index', help='monitor index, see --list-monitors', type=int, default=0)
    args = parser.parse_args()

    if args.list_monitors:
        list_monitors()
        return

    db = Database(DATABASE_PATH)
    db.setup()
    del db
    setup_images_directory(IMAGES_DIRECTORY)

    logging.info(f'Starting schedule, capturing every {args.interval} seconds')
    schedule.every(args.interval).seconds.do(lambda: do_capture(args.monitor_index))

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
