"""
    A session management module which provides an event-based
    framework for handling sessions.
"""

from .events import SessionHandler
from .garbage_collector import SessionGarbageCollector

def create_sessions(app, clean_interval=None, session_duration=None):
    """Attaches session management to an application

    Note:
        the supplied app should support flask-sessions
    
    Args:
        app (Flask): The flask app to which the module attaches
        clean_interval (int, optional): the time in seconds between session
            garbage collector activations. If None, disables garbage collection.
            Defaults to None.
        session_duration (int, optional): the maximal lifetime of an inactive session in seconds.
            Defines the time an app needs to be inactive in order for it to be garbage collected.
            If None, disables garbase collection. Defaults to None.
    """
    SessionHandler.attach_app(app)
    
    if session_duration is not None and clean_interval is not None:
        with app.app_context():
            SessionGarbageCollector(session_duration, clean_interval)
