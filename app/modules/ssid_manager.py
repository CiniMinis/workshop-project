from uuid import uuid4
from flask import session
from utils.singleton import Singleton

class SessionIdManager(metaclass=Singleton):
    CLIENT_ID_FIELD = "SessionId"  
    UUID_LEN = 36
    _INITIALIZED_APPS = []
    _CREATION_HANDLERS = []

    @staticmethod
    def _init_ssid():
        if SessionIdManager.CLIENT_ID_FIELD not in session:
            new_ssid = str(uuid4())
            session[SessionIdManager.CLIENT_ID_FIELD] = new_ssid
            for handler in SessionIdManager._CREATION_HANDLERS:
                handler(new_ssid)
    
    @staticmethod
    def init_app(app):
        # don't initialize the same app twice
        if app in SessionIdManager._INITIALIZED_APPS:
            return
        
        # add session giving after each requests
        app.before_request(SessionIdManager._init_ssid)

    @property
    def current_ssid(self):
        if self.CLIENT_ID_FIELD not in session:
            raise ValueError("No Session Present")
        
        ssid = session[self.CLIENT_ID_FIELD]

        return ssid
    
    @staticmethod
    def call_on_new(func):
        SessionIdManager._CREATION_HANDLERS.append(func)
        return func
