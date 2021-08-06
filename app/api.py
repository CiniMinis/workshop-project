from app.models import User
from flask import jsonify, request, Blueprint
from app.modules.user_cache import AesLRUSessionCache
from app.config.avatar import Avatar
from functools import wraps
import asyncio
import json

api = Blueprint('api', __name__, url_prefix='/api', template_folder="api_snippets")

PART_URL_TEMPLATE = "/img/avatar/{}/"


def make_json_api(*args, **kwargs):
    def decorator(func):
        @wraps(func)
        def sync_decorated(*args, **kwargs):
            resp = {'status': 'success'}
            try:
                resp['content'] = func(*args, **kwargs)
            except Exception as e:
                resp['status'] = 'fail'
                resp['content'] = str(e)
            
            return jsonify(**resp)

        @wraps(func)
        async def async_decorated(*args, **kwargs):
            resp = {'status': 'success'}
            try:
                resp['content'] = await func(*args, **kwargs)
            except Exception as e:
                resp['status'] = 'fail'
                resp['content'] = str(e)
            
            return jsonify(**resp)
        
        if asyncio.iscoroutinefunction(func):
            decorated = async_decorated
        else:
            decorated = sync_decorated
        
        api.add_url_rule(*args, **kwargs, view_func=decorated)

        return decorated
    return decorator


@AesLRUSessionCache(max_size=10)
def part_to_dict(part):
    part_name = part.__class__.__name__.lower()
    part_path = PART_URL_TEMPLATE.format(part_name)

    border_image = f"{part_path}border{part.variation}.png"
    part_dict = {'border_image': border_image}

    if part.IS_COLORABLE:
        color_image = f"{part_path}color{part.variation}.png"
        color_dict = {'image': color_image,
                      'rgb': part.color}
    else:
        color_dict = None
    part_dict['color_image'] = color_dict
    # return part_dict
    # TODO: make me return normally!
    return json.dumps(part_dict)


@make_json_api('part_from_dna', methods=['POST'])
def part_from_dna():
    if 'dna' not in request.form:
        raise ValueError("Missing dna parameter")
    if 'part' not in request.form:
        raise ValueError("Missing part parameter")
    dna = request.form['dna']
    part_name = request.form['part']
    avatar = Avatar.from_dna(dna)
    return json.loads(part_to_dict(avatar[part_name]))


async def fetch_part_from_user(uid, part_name):
    user = User.query.filter_by(user_id=uid).first()
    if user is None:
        raise ValueError("User id not found")
    avatar = Avatar.from_dna(user.dna)
    return json.loads(part_to_dict(avatar[part_name]))


async def is_user_visible(uid):
    user = User.query.filter_by(user_id=uid).first()
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
    user_id = request.form['id']
    part_name = request.form['part']
    is_visible, part = await asyncio.gather(
        is_user_visible(user_id),
        fetch_part_from_user(user_id, part_name)
    )
    if not is_visible:
        raise ValueError("You are not allowed to view this user")

    return part
