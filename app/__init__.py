from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app import config
from instance import app_config_type
from app.config import AppConfigFactory
from app.api import api
from app.controllers import controllers

db = SQLAlchemy()
config_factory = AppConfigFactory()

def create_app(config_type=app_config_type):
    app = Flask(__name__)
    # configuration for development
    app_config = config_factory.make(config_type)
    app.config.from_object(app_config)
    app.register_blueprint(api)
    app.register_blueprint(controllers)
    db.init_app(app)

    return app