from .events import SessionHandler

def create_sessions(app, expiration_time=None):
    SessionHandler.attach_app(app)