from flask import *
from avatar import AvatarBase, BodyPart
import os
import json
from user_cache import *
from db import UserFactory

# directory constants
STATIC_DIR = "static"
IMAGE_DIR = "static/img"
PART_URL_TEMPLATE = "/img/avatar/{}/"

# session constants
SESSION_KEY_BYTES = 32

app = Flask(__name__)
app.secret_key = os.urandom(SESSION_KEY_BYTES)

class Avatar(AvatarBase):
    pass


@Avatar.register_part
class Body(BodyPart):
    VARIATIONS = 1
    IS_COLORABLE = True


@Avatar.register_part
class Head(BodyPart):
    VARIATIONS = 4
    IS_COLORABLE = True


@Avatar.register_part
class Eyes(BodyPart):
    VARIATIONS = 4
    IS_COLORABLE = True


@Avatar.register_part
class Nose(BodyPart):
    VARIATIONS = 2
    IS_COLORABLE = False


@Avatar.register_part
class Ears(BodyPart):
    VARIATIONS = 2
    IS_COLORABLE = True


@Avatar.register_part
class Mouth(BodyPart):
    VARIATIONS = 4
    IS_COLORABLE = True

user_factory = UserFactory(Avatar)
for _ in range(10):
    print(user_factory.randomize())

secret_avatar = Avatar.randomize()

def make_json_response(func):
    def decorated(*args, **kwargs):
        resp = {'status': 'success'}
        try:
            resp['content'] = func(*args, **kwargs)
        except Exception as e:
            resp['status'] = 'fail'
            resp['content'] = str(e)
        return jsonify(**resp)
    return decorated

@app.route('/img/<path:image>')
def images(image):
    return send_from_directory(IMAGE_DIR, image)


@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


@app.route('/')
def home():
    return render_template("index.html")

def rgb_to_hex(color):
    return '#' + ''.join([f"{col:x}" for col in color])

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

@app.route('/api/part_from_dna', methods=['POST'])
@make_json_response
def part_from_dna():
    if 'dna' not in request.form:
        raise ValueError("Missing dna parameter")
    if 'part' not in request.form:
        raise ValueError("Missing part parameter")
    dna = request.form['dna']
    part_name = request.form['part']
    avatar = Avatar.from_dna(dna)
    return json.loads(part_to_dict(avatar[part_name]))

@app.route('/draw')
def draw_page():
    return render_template("draw.html")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
