from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from instance import deploy_type, challenge_type
from app.config import AppConfigFactory

db = SQLAlchemy(session_options={"autoflush": False})
config_factory = AppConfigFactory()

def create_app(deploy_type=deploy_type, challenge_type=challenge_type):
    app = Flask(__name__)
    # configuration for development
    app_config = config_factory.make(deploy_type, challenge_type)
    app.config.from_object(app_config)

    # imports inside create_app to avoid circular import
    with app.app_context():
        db.init_app(app)
        app.db = db
        app_config.init_app(app)
        
        from app.api import api
        from app.controllers import controllers
        app.register_blueprint(api)
        app.register_blueprint(controllers)


    return app