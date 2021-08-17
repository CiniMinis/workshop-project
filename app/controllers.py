from flask import send_from_directory, render_template, Blueprint, abort, request
from sqlalchemy.sql.expression import func
from app.models import SessionUsers, User

# directory constants
STATIC_DIR = "static"
IMAGE_DIR = "static/img"

# display constants
INITIAL_EXPLORE_COUNT = 16

controllers = Blueprint('controllers', __name__, template_folder="views")


@controllers.route('/img/<path:image>')
def images(image):
    return send_from_directory(IMAGE_DIR, image)


@controllers.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


@controllers.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template("index.html")
    
    # get initial search matches
    search_term = request.form.get('search')
    query = SessionUsers.query.filter(User.name.like(f"%{search_term}%"))

    # enforce privacy select
    privacy_select = request.form.get('privacySelect')
    if privacy_select == "private":
        query = query.filter_by(is_private=True)
    elif privacy_select == "public":
        query = query.filter_by(is_private=False)

    # enforce specified values
    if 'forceJob' in request.form:
        query = query.filter(SessionUsers.job.isnot(None))
    if 'forceLocation' in request.form:
        query = query.filter(SessionUsers.location.isnot(None))

    return render_template("search.html", users=query.all())


@controllers.route('/explore')
def explore():
    explore_users = SessionUsers.query.order_by(func.random()).limit(INITIAL_EXPLORE_COUNT).all()
    return render_template("explore.html", users=explore_users)

@controllers.route('/user/<int:uid>')
def show_user(uid):
    user = SessionUsers.query.filter_by(user_id=uid).first()
    if user is None:
        abort(404)
    return render_template("profile.html", user=user)


@controllers.route('/draw')
def draw_page():
    return render_template("draw.html")
