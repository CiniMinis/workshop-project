"""
    Small script for dropping all app tables and users and
    recreating them.
    Supplied as a utility but no longer necessary for user generation.
"""
from app.models import UserFactory, User
from app.config.avatar import Avatar
from app.config import USER_COUNT
from app import db, create_app

# debugging consts
SHOULD_DISPLAY = False
DISPLAY_COUNT = 5

if __name__ == '__main__':
    # make application
    app = create_app()

    user_factory = UserFactory(Avatar)

    # destroy all tables and remake them
    with app.app_context():
        db.drop_all()
        db.create_all()

        # populate db with users
        for _ in range(USER_COUNT):
            db.session.add(user_factory.randomize())
        
        db.session.commit()
    
    # shows first few users
    if SHOULD_DISPLAY:
        with app.app_context():
            display_users = User.query.limit(DISPLAY_COUNT).all()
            for user in display_users:
                print(user)