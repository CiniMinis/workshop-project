from flask import send_from_directory, render_template, Blueprint

# directory constants
STATIC_DIR = "static"
IMAGE_DIR = "static/img"

controllers = Blueprint('controllers', __name__)


@controllers.route('/img/<path:image>')
def images(image):
    return send_from_directory(IMAGE_DIR, image)


@controllers.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


@controllers.route('/')
def home():
    return render_template("index.html")


@controllers.route('/draw')
def draw_page():
    return render_template("draw.html")
