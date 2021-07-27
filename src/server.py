from flask import *
from functools import lru_cache

STATIC_DIR = "static"
IMAGE_DIR = "static/img"

app = Flask(__name__)


@app.route('/img/<path:image>')
def images(image):
    return send_from_directory(IMAGE_DIR, image)


@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


@app.route('/')
def home():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
