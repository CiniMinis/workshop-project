from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from instance import app_config_type, session_config_type
from app.config import AppConfigFactory

db = SQLAlchemy()
config_factory = AppConfigFactory()

def create_app(app_type=app_config_type, session_type=session_config_type):
    app = Flask(__name__)
    # configuration for development
    app_config = config_factory.make(app_type, session_type)
    app.config.from_object(app_config)

    # imports inside create_app to avoid circular import
    from app.api import api
    from app.controllers import controllers

    app.register_blueprint(api)
    app.register_blueprint(controllers)

    db.init_app(app)
    app_config.init_session(app)

    return app