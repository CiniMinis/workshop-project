from flask import send_from_directory, render_template, Blueprint

# directory constants
STATIC_DIR = "static"
IMAGE_DIR = "static/img"

views = Blueprint('views', __name__)


@views.route('/img/<path:image>')
def images(image):
    return send_from_directory(IMAGE_DIR, image)


@views.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


@views.route('/')
def home():
    return render_template("index.html")


@views.route('/draw')
def draw_page():
    return render_template("draw.html")
