import os
from abc import ABC, abstractmethod
from instance import session_key, APP_SESSION_DURATION

FILE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(FILE_DIR, '../../instance')

# deployment configurations for the app
class DeploymentConfig(ABC):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = session_key
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

# configuration for testing
class TestDeployment(DeploymentConfig):
    DB_NAME = 'development.db'
    TESTING = True
    TEMPLATES_AUTO_RELOAD = True

class ProductionDeployment(DeploymentConfig):
    DB_NAME = 'genetwork-users.db'

# abstract cache configuration
class CacheConfig(ABC):
    @abstractmethod
    def cache_setup(self, app):
        raise NotImplementedError()

    def init_app(self, app):
        from app.modules.session_manager import create_sessions
        create_sessions(app, session_duration=APP_SESSION_DURATION)
        
        self.cache_setup(app)

# configuration for easy mode- flask session cache
class EasyCacheConfig(CacheConfig):
    def cache_setup(self, app):
        from app.modules.user_cache import LRUSessionCache
        app.config['CACHING_TYPE'] = LRUSessionCache

# configuration for medium mode- aes session cache
class MediumCacheConfig(CacheConfig):
    def cache_setup(self, app):
        from app.modules.user_cache import AesLRUSessionCache
        app.config['CACHING_TYPE'] = AesLRUSessionCache

# configuration for hard mode- sql session cache
class HardCacheConfig(CacheConfig):
    def cache_setup(self, app):
        from app.modules.user_cache import SqlLRUSessionCache
        app.config['CACHING_TYPE'] = SqlLRUSessionCache

class AppConfigFactory:
    DEV_CONFIG_NAMES = ['dev', 'development']  # names for development
    TEST_CONFIG_NAMES = ['test', 'testing']
    PRODUCTION_CONFIG_NAMES = ['production', None, 'prod', 'ctf', 'challenge']

    EASY_CACHE_NAMES = ['flask', 'default', 'cookie', 'easy']
    MEDIUM_CACHE_NAMES = ['aes', 'encrypt', 'encrypted', 'medium', 'normal']
    HARD_CACHE_NAMES = ['sql', 'sqlalchemy', 'hard']

    def make(self, deploy_type, difficulty=None):
        if deploy_type in self.DEV_CONFIG_NAMES:
            deploy_config = DevelopmentDeployment
        elif deploy_type in self.TEST_CONFIG_NAMES:
            deploy_config = TestDeployment
        elif deploy_type in self.PRODUCTION_CONFIG_NAMES:
            deploy_config = ProductionDeployment
        else:
            raise ValueError("Invalid Config Type")
        
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