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

import config
from database import Database

def list_monitors() -> None:
    with mss.mss() as sct:
        print("Available screens:")
        for i, monitor in enumerate(sct.monitors):
            print(i, "->", monitor)

def capture(monitor_index) -> (np.array, str):
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)

    # TODO: improve image processing before running OCR
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(thresholded)

    return (frame, text)

def hash_image(cv2_image) -> int:
    return imagehash.average_hash(Image.fromarray(cv2_image))

"""
Saves the image to disk and add an entry for it in the database
"""
# TODO: do the logging here and just call it (plus pass the context)
def save_capture(ctx, image, image_text) -> None:
    db = Database(ctx.database_path)
    last_capture = db.get_last_capture()
    if last_capture is not None:
        img_hash = hash_image(image)

        last_img_path = f"{ctx.screenshots_directory}/{last_capture.filename}"
        last_img_hash = hash_image(cv2.imread(last_img_path))

        difference = img_hash - last_img_hash
        if difference < 5:
            logging.info("Captured image and last capture too similar, aborting capture")
            return

    timestamp = int(time.time())

    filename = f"{timestamp}.jpg"
    img_path = f"{ctx.screenshots_directory}/{filename}"
    img_abs_path = os.path.abspath(img_path)

    cv2.imwrite(img_abs_path, image)
    db.insert_capture(filename, image_text, timestamp)

    logging.info('Screen capture persisted')

def setup_screenshots_directory(directory: Path) -> None:
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        logging.info("Screenshots directory does not exist, creating it")

# TODO: find a better way to deal with this
def do_capture(ctx: config.Context):
    def inner():
        logging.info(f'Starting screen capture')
        (image, content) = capture(ctx.monitor_index)
        save_capture(ctx, image, content)

    job_thread = threading.Thread(target=inner)
    job_thread.start()

def main():
    parser = argparse.ArgumentParser(
        prog='recallfin',
        description='Supercharge your memory using OCR, SQLite and HTML'
    )
    parser.add_argument('-i', '--interval', help='interval in seconds to capture the screen', type=int, default=10)
    parser.add_argument('-d', '--data-directory', help='directory to store the database and screenshots', type=str, default=config.get_directory())
    parser.add_argument('-l', '--list-monitors', help='list available screens', action='store_true')
    parser.add_argument('-m', '--monitor-index', help='monitor index, see --list-monitors', type=int, default=0)
    args = parser.parse_args()

    if args.list_monitors:
        list_monitors()
        return

    root_directory = os.path.expanduser(args.data_directory)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(root_directory, "recallfin.log")),
            logging.StreamHandler()
        ]
    )

    ctx = config.Context(
        root_directory,
        config.screenshots_directory(root_directory),
        config.db_path(root_directory),
        args.monitor_index
    )
    logging.info(f"Root directory is {root_directory}")

    setup_screenshots_directory(ctx.screenshots_directory)
    db = Database(ctx.database_path)
    db.setup()
    del db

    logging.info(f'Starting schedule, capturing every {args.interval} seconds')
    schedule.every(args.interval).seconds.do(lambda: do_capture(ctx))

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
