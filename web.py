from flask import Flask, render_template, send_from_directory, request, url_for

from datetime import datetime
import argparse
import itertools
import logging
import os

from database import Database
import config

parser = argparse.ArgumentParser(prog='recallfin-web', description='Supercharge your memory using OCR, SQLite and HTML')
parser.add_argument('-d', '--data-directory', help="recallfin's data directory", type=str, default=config.get_directory())
args = parser.parse_args()

root_directory = os.path.expanduser(args.data_directory)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(root_directory, "recallfin-web.log")),
        logging.StreamHandler()
    ]
)

SCREENSHOTS_DIRECTORY = config.screenshots_directory(root_directory)
DATABASE_PATH = config.db_path(root_directory)

app = Flask(__name__)

def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

def get_day(capture):
    return datetime.utcfromtimestamp(capture.timestamp).strftime('%Y-%m-%d')

def group_captures_by_date(captures):
    return itertools.groupby(captures, get_day)

@app.route("/")
def list_captures():
    db = Database(DATABASE_PATH)
    captures = {}
    # TODO: tolerate typos
    query = request.args.get('query') or ""

    if len(query) > 0:
        result = db.query(query)
        captures = group_captures_by_date(result)

    return render_template('index.html', captures=captures, query=query)

@app.route('/captures/<identifier>')
def show_capture(identifier):
    db = Database(DATABASE_PATH)
    # TODO: parse links and add them to capture (as tags)
    capture = db.get_capture_by_id(identifier)
    previous = db.get_previous_n(capture, 2)
    next = db.get_next_n(capture, 2)
    return render_template('show.html', capture=capture, previous=previous, next=next)

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(SCREENSHOTS_DIRECTORY, filename)

app.run()
