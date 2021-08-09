import os
from abc import ABC, abstractmethod
from flask_sessionstore import Session
from instance import session_key

FILE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(FILE_DIR, '../../instance')

# general config consts
class AppConfig(ABC):
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @property
    @abstractmethod
    def DB_NAME():
        pass

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return f'sqlite:///{ os.path.join(INSTANCE_DIR, self.DB_NAME) }'


# configuration for development
class AppDevConfig(AppConfig):
    DB_NAME = 'development.db'
    DEBUG = True

# configuration for testing
class AppTestConfig(AppConfig):
    DB_NAME = 'development.db'
    TESTING = True

# TODO: make configurations for production


# configuration for default flask sessions
class SessionConfig:
    SECRET_KEY = session_key
    SESSION_USE_SIGNER = True   # for sessionstore child classes

    def init_session(self, app):
        pass

# configuration for sqlalchemy flask session
class SQLSessionConfig(SessionConfig):
    SESSION_TYPE = 'sqlalchemy'

    def init_session(self, app):
        session = Session(app)
        session.app.session_interface.db.create_all()

class AppConfigFactory:
    DEV_CONFIG_NAMES = ['dev', 'development']  # names for development
    TEST_CONFIG_NAMES = ['test', 'testing']

    DEFAULT_SESSION_NAME = [None, 'default', 'cookie']
    SQL_SESSION_NAME = ['sql', 'sqlalchemy']

    def make(self, config_type, session_type=None):
        if config_type in self.DEV_CONFIG_NAMES:
            app_config = AppDevConfig
        elif config_type in self.TEST_CONFIG_NAMES:
            app_config = AppTestConfig
        else:
            raise ValueError("Invalid Config Type")
        
        if session_type in self.DEFAULT_SESSION_NAME:
            session_config = SessionConfig
        elif session_type in self.SQL_SESSION_NAME:
            session_config = SQLSessionConfig
        else:
            raise ValueError("Invalid Session Type")

        class MyConfig(app_config, session_config):
            pass

        return MyConfig()