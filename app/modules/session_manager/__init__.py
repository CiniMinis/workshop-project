from .events import SessionHandler
from .garbage_collector import SessionGarbageCollector
from instance import DEFAULT_CLEAN_INTERVAL

def create_sessions(app, session_duration=None, clean_interval=DEFAULT_CLEAN_INTERVAL):
    SessionHandler.attach_app(app)
    
    if session_duration is not None:
        with app.app_context():
            SessionGarbageCollector(session_duration, clean_interval)
