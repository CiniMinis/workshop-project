from uuid import uuid4
from flask import session, current_app
from enum import Enum

class SessionEvent(Enum):
    """Enum which specifies session event types.
    
    Declares session event types and the values of each declaration is the
    name of the handler functions for the event.
    """
    CREATE = "create_handler"   # first connection by user (no session set)
    CONNECT = "connect_handler" # a session connected (made a request form the server)
    DELETE = "delete_handler"   # a session should be deleted (triggered by garbage collector)
    
class SessionHandler:
    """Session event handlers.

    Instances of this class access session relevant data and allow event
    listener definitions for the different session events.

    Attributes:
        app (Flask): the flask app to which the handler is bound.
        Set to the app in context during the instance definition.
    """
    SESSION_ID_FIELD = "SessionId"
    """the name of the internal session id in the flask session"""
    UUID_LEN = 36
    """the length of the UUID generated for sessions"""
    _clients = []
    _apps = []
    
    def __init__(self):
        SessionHandler._clients.append(self)
        self.app = current_app
        
    @staticmethod
    def _manage_request():
        is_new = SessionHandler.generate_session()
        ssid = SessionHandler.get_ssid()
        event_type = SessionEvent.CREATE if is_new else SessionEvent.CONNECT
        SessionHandler.trigger_event(event_type, ssid)
    
    @staticmethod
    def attach_app(app):
        """Attaches the event manager to an app.
        
        This adds creation and connection triggers for the app

        Args:
            app (Flask): a flask application which requires session management
        """
        if app in SessionHandler._apps:
            return
        
        SessionHandler._apps.append(app)
        app.before_request(SessionHandler._manage_request)
    
    @staticmethod
    def generate_session():
        """Attempts to create a new session if one doesn't exist

        Returns:
            bool: True if a new session was created, False otherwise
        """
        if SessionHandler.SESSION_ID_FIELD not in session:
            new_ssid = str(uuid4())
            session[SessionHandler.SESSION_ID_FIELD] = new_ssid
            return True
        return False
    
    @staticmethod
    def trigger_event(session_event, ssid):
        """Triggers a session event

        Args:
            session_event (SessionEvent): The session event to trigger
            ssid (str): The ssid for which the event is triggered
        """
        for client in SessionHandler._clients:
            if client.app == current_app:
                client._handle_event(session_event, ssid)
    
    def on_session_create(self, func):
        """Decorator which sets a function as the create event handler"""
        self.create_handler = func
        return func
    
    def on_session_connect(self, func):
        """Decorator which sets a function as the connect event handler"""
        self.connect_handler = func
        return func
    
    def on_session_delete(self, func):
        """Decorator which sets a function as the delete event handler"""
        self.delete_handler = func
        return func
    
    def _handle_event(self, session_event, ssid):
        handler_name = session_event.value
        if hasattr(self, handler_name):
           handler = getattr(self, handler_name)
           handler(ssid)
    
    @property
    def ssid(self):
        """str: the current running session id.
            Raises ValueError if no session exists
        """
        return self.get_ssid()
    
    @staticmethod
    def get_ssid():
        """gets the current session id

        Raises:
            ValueError: no session is currently defined

        Returns:
            str: the session id for the running session
        """
        if SessionHandler.SESSION_ID_FIELD not in session:
            raise ValueError("No Session Present")
        
        return session[SessionHandler.SESSION_ID_FIELD]
