from flask import send_from_directory, render_template, Blueprint
from app.models import User

# directory constants
STATIC_DIR = "static"
IMAGE_DIR = "static/img"

# display constants
EXPLORE_COUNT = 5

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


@controllers.route('/explore')
def explore():
    explore_users = User.query.limit(EXPLORE_COUNT).all()
    return render_template("explore.html", users=explore_users)


@controllers.route('/draw')
def draw_page():
    return render_template("draw.html")
