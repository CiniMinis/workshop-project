from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import AppConfigFactory, USER_COUNT

db = SQLAlchemy(session_options={"autoflush": False})
config_factory = AppConfigFactory()


def create_app(**kwargs):
    """Factory method for creating a server application of the ctf challenge.

    Args:
        **kwargs: keyword arguments passed forward to the configuration factory with which the app is initialized.
            May containe 'deploy_type' and 'challenge_type' keywords. See app.config.__init__.py for more information.

    Returns:
        Flask: the created flask application with the given configuration
    """
    app = Flask(__name__)
    # configuration for development
    app_config = config_factory.make(**kwargs)
    app.config.from_object(app_config)

    # adds all components to the app
    with app.app_context():
        db.init_app(app)
        app.db = db
        app_config.init_app(app)

        from app.api import api
        from app.controllers import controllers
        app.register_blueprint(api)
        app.register_blueprint(controllers)

    # This method creates and initializes (if required) the database tables
    # upon the first request.
    @app.before_first_request
    def initialize_databases():
        from app.models import UserFactory, User
        db.create_all()  # create all db tables
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
