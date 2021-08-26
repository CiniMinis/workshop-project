from app.models import SessionUsers, Villain
from flask import jsonify, request, Blueprint, render_template, current_app
from app.config.avatar import Avatar
from functools import wraps
from sqlalchemy.sql.expression import func
import asyncio
import json
import os.path

api = Blueprint('api', __name__, url_prefix='/api', template_folder="views/snippets")
caching_function = current_app.config['CACHING_TYPE']

# general API consts
URL_PART_TEMPLATE = "/img/avatar/{}/"
FILE_DIR = os.path.abspath(os.path.dirname(__file__))
URL_TO_PATH_PREFIX = os.path.join(FILE_DIR, 'static') 


def make_json_api(*args, **kwargs):
    def decorator(func):
        CAUGHT_ERRORS = (ValueError, AssertionError, KeyError, TypeError)
        @wraps(func)
        def sync_decorated(*args, **kwargs):
            resp = {'status': 'success'}
            try:
                resp['content'] = func(*args, **kwargs)
            except CAUGHT_ERRORS as e:
                resp['status'] = 'fail'
                resp['content'] = str(e)
            
            return jsonify(**resp)

        @wraps(func)
        async def async_decorated(*args, **kwargs):
            resp = {'status': 'success'}
            try:
                resp['content'] = await func(*args, **kwargs)
            except CAUGHT_ERRORS as e:
                resp['status'] = 'fail'
                resp['content'] = str(e)
            print(resp)
            return jsonify(**resp)
        
        if asyncio.iscoroutinefunction(func):
            decorated = async_decorated
        else:
            decorated = sync_decorated
        
        api.add_url_rule(*args, **kwargs, view_func=decorated)

        return decorated
    return decorator

@caching_function(serializer=json)
def part_to_dict(part):
    part_name = part.__class__.__name__.lower()
    part_url = URL_PART_TEMPLATE.format(part_name)

    border_image = os.path.join(part_url, f"border{part.variation}.png")
    assert os.path.isfile(URL_TO_PATH_PREFIX + border_image), f'Missing draw resource for part {URL_TO_PATH_PREFIX + border_image}'
    part_dict = {'border_image': border_image}

    if part.IS_COLORABLE:
        color_image = os.path.join(part_url, f"color{part.variation}.png")
        assert os.path.isfile(URL_TO_PATH_PREFIX + border_image), f'Missing draw resource for part {color_image}'
        color_dict = {'image': color_image,
                      'color': part.color}
    else:
        color_dict = None
    part_dict['color_image'] = color_dict
    return part_dict


@make_json_api('part_from_dna', methods=['POST'])
def part_from_dna():
    if 'dna' not in request.form:
        raise ValueError("Missing dna parameter")
    if 'part' not in request.form:
        raise ValueError("Missing part parameter")
    dna = request.form['dna']
    part_name = request.form['part']
    avatar = Avatar.from_dna(dna)
    return part_to_dict(avatar[part_name])


async def fetch_part_from_user(uid, part_name):
    user = SessionUsers.query.filter_by(user_id=uid).first()
    if user is None:
        raise ValueError("User id not found")
    avatar = Avatar.from_dna(user.dna)
    return part_to_dict(avatar[part_name])


async def is_user_visible(uid):
    user = SessionUsers.query.filter_by(user_id=uid).first()
    if Villain.is_villain(user):
        villain = Villain.get_session_villain()
        villain.notify_detection()
    if not user.is_private:
        return True
    # TODO: Implement friend check to show avatar to friends
    return False


@make_json_api('part_from_user', methods=['POST'])
async def part_from_user():
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

# Consts for user deck
USERS_TO_ADD = 8

@api.route('get_user_deck')
def get_user_deck():
    new_users = SessionUsers.query.order_by(func.random()).limit(USERS_TO_ADD).all()
    return render_template("users_as_list_items.jinja", users=new_users)