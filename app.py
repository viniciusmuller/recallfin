from flask import Flask, render_template, send_from_directory, request

from datetime import datetime

from constants import DATABASE_PATH, IMAGES_DIRECTORY
from db import Database

app = Flask(__name__)

def timestamp_to_date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

initial_db = Database(DATABASE_PATH)
initial_db.setup()

@app.route("/")
def hello_world():
    db = Database(DATABASE_PATH)
    results = []
    query = request.args.get('query')

    if query is not None:
        results = db.query(query)
        if len(results) > 0:
            print(results[0])

    return render_template('index.html', results=results)

@app.route('/images/<filename>')
def get_image(filename):
    return send_from_directory(IMAGES_DIRECTORY, filename)

app.run()
