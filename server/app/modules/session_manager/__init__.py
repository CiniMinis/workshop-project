from .events import SessionHandler
from .garbage_collector import SessionGarbageCollector

def create_sessions(app, clean_interval, session_duration=None):
    SessionHandler.attach_app(app)
    
    if session_duration is not None:
        with app.app_context():
            SessionGarbageCollector(session_duration, clean_interval)
