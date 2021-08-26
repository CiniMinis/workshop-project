from flask import send_from_directory, render_template, Blueprint, abort, request, current_app
from sqlalchemy.sql.expression import func
from app.models import SessionUsers, Villain
import os

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
        if 'INDEX_PAGE_TEMPLATE' in current_app.config:
            return render_template(current_app.config['INDEX_PAGE_TEMPLATE'])
        return render_template('index_base.jinja')
    
    # get initial search matches
    search_term = request.form.get('search')
    query = SessionUsers.query.filter(SessionUsers.name.ilike(f"%{search_term}%"))

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

    return render_template("search.jinja", users=query.all())


@controllers.route('/explore')
def explore():
    explore_users = SessionUsers.query.order_by(func.random()).limit(INITIAL_EXPLORE_COUNT).all()
    return render_template("explore.jinja", users=explore_users)

@controllers.route('/user/<int:uid>')
def show_user(uid):
    user = SessionUsers.query.filter_by(user_id=uid).first()
    if user is None:
        abort(404)
    return render_template("profile.jinja", user=user)


@controllers.route('/draw')
def draw_page():
    return render_template("draw.jinja")

@controllers.route('/check_challenge', methods=['GET', 'POST'])
def check_villain_dna():
    if request.method == 'GET':
        return render_template("check_challenge.jinja")
    
    submitted_dna = request.form.get('dna')
    if submitted_dna is not None:
        submitted_dna = submitted_dna.strip()
    
    session_villain = Villain.get_session_villain()
    
    if session_villain.dna == submitted_dna:
        flag = os.environ.get('FLAG')
        if flag is None:
            from instance import FLAG
            flag = FLAG
        return render_template("check_challenge.jinja", win=True, message="The Flag Is: {}".format(flag))
    else:
        session_villain.shapeshift()
        return render_template("check_challenge.jinja", win=False)
