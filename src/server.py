from flask import *
from avatar import AvatarBase, BodyPart

STATIC_DIR = "static"
IMAGE_DIR = "static/img"

app = Flask(__name__)

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

@app.route('/img/<path:image>')
def images(image):
    return send_from_directory(IMAGE_DIR, image)


@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(STATIC_DIR, path)


@app.route('/')
def home():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
