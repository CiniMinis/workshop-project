import os
from abc import ABC, abstractmethod
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


# configuration for easy mode- flask session cache
class SessionConfig:
    SECRET_KEY = session_key
    SESSION_USE_SIGNER = True

    def init_sessions(self, app):
        from app.modules.session_manager import create_sessions
        create_sessions(app)
    
    def set_session(self, app):
        self.init_sessions(app)
        from app.modules.user_cache import LRUSessionCache
        app.config['CACHING_TYPE'] = LRUSessionCache

# configuration for medium mode- aes session cache
class AESSessionConfig(SessionConfig):
    def set_session(self, app):
        super().init_sessions(app)
        from app.modules.user_cache import AesLRUSessionCache
        app.config['CACHING_TYPE'] = AesLRUSessionCache

# configuration for hard mode- sql session cache
class SQLSessionConfig(SessionConfig):
    def set_session(self, app):
        super().init_sessions(app)
        from app.modules.user_cache import SqlLRUSessionCache
        app.config['CACHING_TYPE'] = SqlLRUSessionCache

class AppConfigFactory:
    DEV_CONFIG_NAMES = ['dev', 'development']  # names for development
    TEST_CONFIG_NAMES = ['test', 'testing']

    DEFAULT_SESSION_NAME = [None, 'default', 'cookie', 'easy']
    AES_SESSION_NAME = ['aes', 'encrypt', 'encrypted', 'medium', 'normal']
    SQL_SESSION_NAME = ['sql', 'sqlalchemy', 'hard']

    def make(self, config_type, session_type=None):
        if config_type in self.DEV_CONFIG_NAMES:
            app_config = AppDevConfig
        elif config_type in self.TEST_CONFIG_NAMES:
            app_config = AppTestConfig
        else:
            raise ValueError("Invalid Config Type")
        
        if session_type in self.DEFAULT_SESSION_NAME:
            session_config = SessionConfig
        elif session_type in self.AES_SESSION_NAME:
            session_config = AESSessionConfig
        elif session_type in self.SQL_SESSION_NAME:
            session_config = SQLSessionConfig
        else:
            raise ValueError("Invalid Session Type")

        class MyConfig(app_config, session_config):
            pass

        return MyConfig()