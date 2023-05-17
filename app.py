from flask import Flask, render_template, send_from_directory, request, url_for

from datetime import datetime

from constants import DATABASE_PATH, IMAGES_DIRECTORY
from db import Database

app = Flask(__name__)

def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

initial_db = Database(DATABASE_PATH)
initial_db.setup()
del initial_db

@app.route("/")
def list_captures():
    db = Database(DATABASE_PATH)
    captures = []
    # TODO: tolerate typos
    query = request.args.get('query')

    print(query)
    if query is not None and len(query) > 0:
        captures = db.query(query)

    return render_template('index.html', captures=captures)

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
    return send_from_directory(IMAGES_DIRECTORY, filename)

app.run()
