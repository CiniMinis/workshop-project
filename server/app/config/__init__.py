import os
from abc import ABC, abstractmethod

# file system consts
FILE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(FILE_DIR, '../../instance')

# secret key consts
SESSION_KEY_BYTES = 32

# session garbage collector consts
_SECONDS_IN_MINUTE = 60
GARBAGE_COLLECTOR_CLEAN_INTERVAL = 15 * _SECONDS_IN_MINUTE
APP_SESSION_DURATION = 20 * _SECONDS_IN_MINUTE

# amount of users expected in db
USER_COUNT = 128

# deployment configurations for the app
class DeploymentConfig(ABC):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # for dev and test, secret key only needs to be random
    SECRET_KEY = os.urandom(SESSION_KEY_BYTES)
    SESSION_USE_SIGNER = True

    @property
    @abstractmethod
    def DB_NAME():
        pass

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return f'sqlite:///{ os.path.join(INSTANCE_DIR, self.DB_NAME) }'


# configuration for development
class DevelopmentDeployment(DeploymentConfig):
    DB_NAME = 'development.db'
    ENV = 'development'
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True

# configuration for testing
class TestDeployment(DeploymentConfig):
    DB_NAME = 'development.db'
    TESTING = True
    TEMPLATES_AUTO_RELOAD = True

class ProductionDeployment(DeploymentConfig):
    DB_NAME = 'genetwork_users'
    
    # if a session key secret is specified, use it instead of the random one
    _session_key_path = os.environ.get('SESSION_KEY_FILE')
    if _session_key_path is not None:
        with open(_session_key_path, 'rb') as _sess_key_file:
            SECRET_KEY = _sess_key_file.read()
                
    # if a db password is given, update sqlalchemy to use the remote db
    _db_pass_path = os.environ.get('DB_PASSWORD_FILE')
    if _db_pass_path is not None:
        with open(_db_pass_path, 'r') as _db_pass_file:
            _db_pass = _db_pass_file.read()
        SQLALCHEMY_DATABASE_URI = f'postgresql://genetwork:{_db_pass}@db/{DB_NAME}'     

# abstract cache configuration
class CacheConfig(ABC):    
    @abstractmethod
    def cache_setup(self, app):
        raise NotImplementedError()
    
    @property
    @abstractmethod
    def INDEX_PAGE_TEMPLATE(self):
        raise NotImplementedError()

    def init_app(self, app):
        from app.modules.session_manager import create_sessions
        create_sessions(app,
                        session_duration=APP_SESSION_DURATION,
                        clean_interval=GARBAGE_COLLECTOR_CLEAN_INTERVAL)
        
        self.cache_setup(app)

# configuration for easy mode- flask session cache
class EasyCacheConfig(CacheConfig):
    def cache_setup(self, app):
        from app.modules.user_cache import LRUSessionCache
        app.config['CACHING_TYPE'] = LRUSessionCache
    
    INDEX_PAGE_TEMPLATE = 'index_easy.jinja'

# configuration for medium mode- aes session cache
class MediumCacheConfig(CacheConfig):
    def cache_setup(self, app):
        from app.modules.user_cache import AesLRUSessionCache
        app.config['CACHING_TYPE'] = AesLRUSessionCache
        
    INDEX_PAGE_TEMPLATE = 'index_medium.jinja'


# configuration for hard mode- sql session cache
class HardCacheConfig(CacheConfig):
    def cache_setup(self, app):
        from app.modules.user_cache import SqlLRUSessionCache
        app.config['CACHING_TYPE'] = SqlLRUSessionCache
    
    INDEX_PAGE_TEMPLATE = 'index_hard.jinja'

class AppConfigFactory:
    DEV_CONFIG_NAMES = ['dev', 'development']  # names for development
    TEST_CONFIG_NAMES = ['test', 'testing']
    PRODUCTION_CONFIG_NAMES = ['production', None, 'prod', 'ctf', 'challenge']

    EASY_CACHE_NAMES = ['flask', 'default', 'cookie', 'easy']
    MEDIUM_CACHE_NAMES = ['aes', 'encrypt', 'encrypted', 'medium', 'normal']
    HARD_CACHE_NAMES = ['sql', 'sqlalchemy', 'hard']

    def make(self, deploy_type, difficulty):
        if deploy_type is None:
            deploy_type = os.environ['DEPLOYMENT_TYPE']
        
        if deploy_type in self.DEV_CONFIG_NAMES:
            deploy_config = DevelopmentDeployment
        elif deploy_type in self.TEST_CONFIG_NAMES:
            deploy_config = TestDeployment
        elif deploy_type in self.PRODUCTION_CONFIG_NAMES:
            deploy_config = ProductionDeployment
        else:
            raise ValueError("Invalid Config Type")
        
        if difficulty is None:
            difficulty = os.environ['DIFFICULTY']
        
        if difficulty in self.EASY_CACHE_NAMES:
            difficulty = EasyCacheConfig
        elif difficulty in self.MEDIUM_CACHE_NAMES:
            difficulty = MediumCacheConfig
        elif difficulty in self.HARD_CACHE_NAMES:
            difficulty = HardCacheConfig
        else:
            raise ValueError("Invalid Session Type")

        class MyConfig(deploy_config, difficulty):
            pass

        return MyConfig()