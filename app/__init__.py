from flask import Flask
from os import urandom
import app.config as config
from app.api import api
from app.views import views

app = Flask(__name__)
app.register_blueprint(api)
app.register_blueprint(views)
app.secret_key = urandom(config.SESSION_KEY_BYTES)