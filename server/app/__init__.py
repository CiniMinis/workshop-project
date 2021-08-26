from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import AppConfigFactory, USER_COUNT

db = SQLAlchemy(session_options={"autoflush": False})
config_factory = AppConfigFactory()

def create_app(deploy_type=None, challenge_type=None):
    app = Flask(__name__)
    # configuration for development
    app_config = config_factory.make(deploy_type, challenge_type)
    app.config.from_object(app_config)

    with app.app_context():
        db.init_app(app)
        app.db = db
        app_config.init_app(app)
                    
        from app.api import api
        from app.controllers import controllers
        app.register_blueprint(api)
        app.register_blueprint(controllers)
    
    @app.before_first_request
    def initialize_databases():   
        from app.models import UserFactory, User
        db.create_all() # create all db tables
        existing_user_count = User.query.count()
        
        # if user db isn't filled
        if existing_user_count == 0:
            print("Making DB:")
            from app.config.avatar import Avatar
            user_factory = UserFactory(Avatar)

            # populate db with users
            for _ in range(USER_COUNT):
                db.session.add(user_factory.randomize())
            
            db.session.commit()

    return app