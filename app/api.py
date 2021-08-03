from flask import jsonify, request, Blueprint
from app.modules.user_cache import AesLRUSessionCache
from app.config.avatar import Avatar
from functools import wraps
import json

api = Blueprint('api', __name__, url_prefix='/api')

PART_URL_TEMPLATE = "/img/avatar/{}/"


def rgb_to_hex(color):
    return '#' + ''.join([f"{col:x}" for col in color])


def make_json_api(*args, **kwargs):
    def decorator(func):
        @api.route(*args, **kwargs)
        @wraps(func)
        def decorated(*args, **kwargs):
            resp = {'status': 'success'}
            try:
                resp['content'] = func(*args, **kwargs)
            except Exception as e:
                resp['status'] = 'fail'
                resp['content'] = str(e)
            return jsonify(**resp)
        return decorated
    return decorator


@AesLRUSessionCache(max_size=16)
def part_to_dict(part):
    part_name = part.__class__.__name__.lower()
    part_path = PART_URL_TEMPLATE.format(part_name)

    border_image = f"{part_path}border{part.variation}.png"
    part_dict = {'border_image': border_image}

    if part.IS_COLORABLE:
        color_image = f"{part_path}color{part.variation}.png"
        color_dict = {'image': color_image,
                      'rgb': rgb_to_hex(part.color)}
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
