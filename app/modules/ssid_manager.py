from uuid import uuid4
from flask import session
from utils.singleton import Singleton

class SessionIdManager(metaclass=Singleton):
    CLIENT_ID_FIELD = "SessionId"  
    UUID_LEN = 36
    _INITIALIZED_APPS = []

    @staticmethod
    def _init_ssid(response):
        if SessionIdManager.CLIENT_ID_FIELD not in session:
            session[SessionIdManager.CLIENT_ID_FIELD] = str(uuid4())
        
        return response
    
    @staticmethod
    def init_app(app):
        # don't initialize the same app twice
        if app in SessionIdManager._INITIALIZED_APPS:
            return
        
        # add session giving after each requests
        app.after_request(SessionIdManager._init_ssid)

    @property
    def current_ssid(self):
        if self.CLIENT_ID_FIELD not in session:
            raise ValueError("No Session Present")
        
        ssid = session[self.CLIENT_ID_FIELD]

        return ssid