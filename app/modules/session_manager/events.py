from uuid import uuid4
from flask import session, current_app
from app import db
from enum import Enum

_DB_BIND = "active_sessions"
_UUID_LEN = 36

class SessionId(db.Model):
    __bind_key__ = _DB_BIND
    ssid = db.Column(db.String(_UUID_LEN), primary_key=True)
    last_connection = db.Column(db.DateTime)

class SessionEvent(Enum):
    CREATE = "create_handler"
    CONNECT = "connect_handler"
    DELETE = "delete_handler"
    
class SessionHandler:
    SESSION_ID_FIELD = "SessionId"
    UUID_LEN = _UUID_LEN
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
        if app in SessionHandler._apps:
            return
        
        SessionHandler._apps.append(app)
        app.before_request(SessionHandler._manage_request)
    
    @staticmethod
    def generate_session():
        if SessionHandler.SESSION_ID_FIELD not in session:
            new_ssid = str(uuid4())
            session[SessionHandler.SESSION_ID_FIELD] = new_ssid
            return True
        return False
    
    @staticmethod
    def trigger_event(session_event, ssid):
        for client in SessionHandler._clients:
            if client.app == current_app:
                client._handle_event(session_event, ssid)
    
    def on_session_create(self, func):
        self.create_handler = func
        return func
    
    def on_session_connect(self, func):
        self.connect_handler = func
        return func
    
    def on_session_delete(self, func):
        self.delete_handler = func
        return func
    
    def _handle_event(self, session_event, ssid):
        handler_name = session_event.value
        if hasattr(self, handler_name):
           handler = getattr(self, handler_name)
           handler(ssid)
    
    @property
    def ssid(self):
        return self.get_ssid()
    
    @staticmethod
    def get_ssid():
        if SessionHandler.SESSION_ID_FIELD not in session:
            raise ValueError("No Session Present")
        
        return session[SessionHandler.SESSION_ID_FIELD]
