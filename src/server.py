from flask import *
from avatar import AvatarBase, BodyPart
import os
from user_cache import LRUSessionCache

# directory constants
STATIC_DIR = "static"
IMAGE_DIR = "static/img"

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


secret_avatar = Avatar.randomize()


@app.route('/img/<path:image>')
def images(image):
    return send_from_directory(IMAGE_DIR, image)


@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


@app.route('/')
def home():
    return render_template("index.html")


@LRUSessionCache(16)
def get_secret(part):
    try:
        selected = secret_avatar[part]
        return (selected.variation, selected.color)
    except KeyError:
        return None


@app.route('/secret/<part>')
def secret(part):
    secret = get_secret(part)
    print(secret)
    return """<html>
                <body>
                    <h1>NOPE</h1>
                <body>
            </html>"""


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
