"""
    The application's controllers (MVC)
    Gets all incoming html page requests and processes them.
    
    Note:
        This module does not handle the api calls to the module.
"""
from flask import send_from_directory, render_template, Blueprint, abort, request, current_app
from sqlalchemy.sql.expression import func
from app.models import SessionUsers, Villain, User
import os
import time

# directory constants
STATIC_DIR = "static"   # path for static files folder
IMAGE_DIR = "static/img"    # path for images folder

INITIAL_EXPLORE_COUNT = 16  # The initial number of users shown in the explore view

controllers = Blueprint('controllers', __name__, template_folder="views")


@controllers.route('/img/<path:image>')
def images(image):
    """Handles image queries"""
    return send_from_directory(IMAGE_DIR, image)


@controllers.route('/static/<path:path>')
def static_files(path):
    """Handles queries for static files"""
    return send_from_directory(STATIC_DIR, path)


@controllers.route('/', methods=['GET', 'POST'])
def home():
    """Homepage
    
    POST requests are user search requests from the search bar
    """
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
        query = query.filter(User.is_private==True)
    elif privacy_select == "public":
        query = query.filter(User.is_private==False)

    # enforce specified values
    if 'forceJob' in request.form:
        query = query.filter(SessionUsers.job.isnot(None))
    if 'forceLocation' in request.form:
        query = query.filter(SessionUsers.location.isnot(None))

    return render_template("search.jinja", users=query.all())


@controllers.route('/explore')
def explore():
    """The explore users page"""
    explore_users = SessionUsers.query.order_by(func.random()).limit(INITIAL_EXPLORE_COUNT).all()
    return render_template("explore.jinja", users=explore_users)

@controllers.route('/user/<int:uid>')
def show_user(uid):
    """The profile pages of users"""
    user = SessionUsers.query.filter(User.user_id==uid).first()
    if user is None:
        abort(404)
    return render_template("profile.jinja", user=user)


@controllers.route('/draw')
def draw_page():
    """The draw from DNA page"""
    return render_template("draw.jinja")

@controllers.route('/check_challenge', methods=['GET', 'POST'])
def check_villain_dna():
    """Handles challenge submition checking"""
    if request.method == 'GET':
        return render_template("check_challenge.jinja")
    
    time.sleep(1)   # ensures this method can't be bruteforced realistically
    submitted_dna = request.form.get('dna')
    if submitted_dna is not None:
        submitted_dna = submitted_dna.strip()
    
    session_villain = Villain.get_session_villain()
    
    if session_villain.dna == submitted_dna:
        flag_path = os.environ.get('CTF_FLAG_FILE')
        if flag_path is None:
            from instance import FLAG
            flag = FLAG
        else:
            with open(flag_path, 'r') as flag_file:
                flag = flag_file.read()
        return render_template("check_challenge.jinja", win=True, message="The Flag Is: {}".format(flag))
    else:
        session_villain.shapeshift()
        return render_template("check_challenge.jinja", win=False)
