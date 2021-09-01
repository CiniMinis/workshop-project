"""
    The application's API
    Handles all queries with prefix /api/ which are responses to javascript
    ajax from the user for updating pages.
    Primarily uses a json format.
"""
from app.models import SessionUsers, Villain
from flask import jsonify, request, Blueprint, render_template, current_app
from app.config.avatar import Avatar
from functools import wraps
from sqlalchemy.sql.expression import func
import asyncio
import json
import os.path

api = Blueprint('api', __name__, url_prefix='/api', template_folder="views/snippets")
caching_function = current_app.config['CACHING_TYPE']   # the configured application page

# general API consts
URL_PART_TEMPLATE = "/img/avatar/{}/"   # string template for the url for part assets
FILE_DIR = os.path.abspath(os.path.dirname(__file__))   # the current directory
URL_TO_PATH_PREFIX = os.path.join(FILE_DIR, 'static')
"""Prefix which convers URL part assets to concrete files in the system"""

USERS_TO_ADD = 8    # The number of users sent on a deck request

def make_json_api(*args, **kwargs):
    """Decorator for turning functions and async coroutines to an API format
    
    This decorates the functions/coroutines to return a JSON with two fields,
    a `status` field which handles wether the request failed or not, and a
    a `content` field which stores the response on success and the error message
    if failed.
    
    Args:
        *args:  args for flask routing within the api
        **kwargs:   keyword args for flask routing within the api
    """
    def decorator(func):
        CAUGHT_ERRORS = (ValueError, AssertionError, KeyError, TypeError)
        
        # handles the sync case
        @wraps(func)
        def sync_decorated(*args, **kwargs):
            resp = {'status': 'success'}
            try:
                resp['content'] = func(*args, **kwargs)
            except CAUGHT_ERRORS as e:
                resp['status'] = 'fail'
                resp['content'] = str(e)
            
            return jsonify(**resp)

        # handles the async case
        @wraps(func)
        async def async_decorated(*args, **kwargs):
            resp = {'status': 'success'}
            try:
                resp['content'] = await func(*args, **kwargs)
            except CAUGHT_ERRORS as e:
                resp['status'] = 'fail'
                resp['content'] = str(e)
            
            return jsonify(**resp)
        
        # return the matching case
        if asyncio.iscoroutinefunction(func):
            decorated = async_decorated
        else:
            decorated = sync_decorated
        
        # add routing to function
        api.add_url_rule(*args, **kwargs, view_func=decorated)

        return decorated
    return decorator

@caching_function(serializer=json)
def part_to_dict(part):
    """Converts a body part to a dict of drawing properties for the js
    
    This is indended to be used in a make_json_api context where the dicts
    will be converted to JSON, making the response solid JSON.
    
    Note:
        This function is cached.
    """
    part_name = part.__class__.__name__.lower()
    part_url = URL_PART_TEMPLATE.format(part_name)

    border_image = os.path.join(part_url, f"border{part.variation}.png")
    assert os.path.isfile(URL_TO_PATH_PREFIX + border_image), f'Missing draw resource for part {URL_TO_PATH_PREFIX + border_image}'
    part_dict = {'border_image': border_image}

    color_image = os.path.join(part_url, f"color{part.variation}.png")
    if part.IS_COLORABLE:
        assert os.path.isfile(URL_TO_PATH_PREFIX + color_image), f'Missing draw resource for part {color_image}'
        color_dict = {'image': color_image,
                      'color': part.color}
    else:
        color_dict = None
    part_dict['color_image'] = color_dict
    return part_dict


@make_json_api('part_from_dna', methods=['POST'])
def part_from_dna():
    """API call which returns part_dict of a part from given DNA

    Note:
        Parameters `dna` and `part` are posted to the request

    Raises:
        ValueError: Missing parameters from API request

    Returns:
        dict: part_dict of drawing details for the requested body part
    """
    if 'dna' not in request.form:
        raise ValueError("Missing dna parameter")
    if 'part' not in request.form:
        raise ValueError("Missing part parameter")
    dna = request.form['dna']
    part_name = request.form['part']
    avatar = Avatar.from_dna(dna)
    return part_to_dict(avatar[part_name])


async def fetch_part_from_user(uid, part_name):
    """gets a body part data from a user

    Args:
        uid (int): the id of the requested user
        part_name (str): the name of the body part for which data is requested

    Raises:
        ValueError: Missing parameters from API request

    Returns:
        dict: part_dict of drawing details for the requested body part
    """
    user = SessionUsers.query.filter_by(user_id=uid).first()
    current_app.db.session.commit()
    if user is None:
        raise ValueError("User id not found")
    avatar = Avatar.from_dna(user.dna)
    return part_to_dict(avatar[part_name])


async def is_user_visible(uid):
    """Checks if the requester is permitted to view a user's DNA


    Args:
        uid (int): the id of the requested user

    Returns:
        bool: True if requester is allowed, False otherwise
    """
    user = SessionUsers.query.filter_by(user_id=uid).first()
    # This Raven Darksomething asked us to let her know when she is being queried
    # weird, but she pays well...
    if Villain.is_villain(user):
        villain = Villain.get_session_villain()
        villain.notify_detection()
    if not user.is_private:
        return True
    # GENETWORK: add user whitelisting before full release of genetwork
    return False


@make_json_api('part_from_user', methods=['POST'])
async def part_from_user():
    """API call which returns part_dict of a users part
    
    Gets a userid and body part from form

    Raises:
        ValueError: Bad parameters or forbidden

    Returns:
        dict: dictionary of drawing instructions for the part
    """
    if 'id' not in request.form:
        raise ValueError("Missing user id parameter")
    if 'part' not in request.form:
        raise ValueError("Missing part parameter")
    user_id = int(request.form['id'])
    part_name = request.form['part']
    is_visible, part = await asyncio.gather(
        is_user_visible(user_id),
        fetch_part_from_user(user_id, part_name)
    )
    if not is_visible:
        raise ValueError("You are not allowed to view this user")

    return part


@api.route('get_user_deck')
def get_user_deck():
    """Returns html for new users being add to a list"""
    new_users = SessionUsers.query.order_by(func.random()).limit(USERS_TO_ADD).all()
    return render_template("users_as_list_items.jinja", users=new_users)
