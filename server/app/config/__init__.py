import os
from abc import ABC, abstractmethod

# file system consts, finding the init dir if environs are missing
FILE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(FILE_DIR, '../../instance')

# no. of bytes in the application session key by default
SESSION_KEY_BYTES = 32

# session garbage collector consts, configures it's execution
_SECONDS_IN_MINUTE = 60
GARBAGE_COLLECTOR_CLEAN_INTERVAL = 15 * _SECONDS_IN_MINUTE
APP_SESSION_DURATION = 20 * _SECONDS_IN_MINUTE

# amount of users expected in db
USER_COUNT = 128

class DeploymentConfig(ABC):
    """Abstract base class for deployment configuration.
    
    Defines global configurations and abstract properties for inheriting deployments.
    """
    # Disables flask-sqlalchemy modification tracking (inefficient)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # For development & testing or as a fallback, use a random secret key for each run
    SECRET_KEY = os.urandom(SESSION_KEY_BYTES)
    # enables flask sessions and flask cookie signing
    SESSION_USE_SIGNER = True

    @property
    @abstractmethod
    def DB_NAME():
        """name of the sqlite db file in an instance subdirectory."""
        pass

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        """SQLALCHEMY Default/Fallback database uri is a local sqlite database"""
        return f'sqlite:///{ os.path.join(INSTANCE_DIR, self.DB_NAME) }'


class DevelopmentDeployment(DeploymentConfig):
    """Defines app configuration for development and debug."""
    DB_NAME = 'development.db'
    ENV = 'development'
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True

class TestDeployment(DeploymentConfig):
    """Defines app configuration for app testing."""
    DB_NAME = 'development.db'
    TESTING = True
    TEMPLATES_AUTO_RELOAD = True

class ProductionDeployment(DeploymentConfig):
    """Defines the production configuration for real deployment

    This configuration attempts to use a remote postgres database at a container named "db".
    
    Note:
        The config attempts to load the db password for the connection from a file specified in
        the environment variable 'DB_PASSWORD_FILE'. The password specifies the password for a
        genetwork account and expects the required database to exist. If the variable is missing,
        falls back to a local file sqlite db.
        Additionally, it similarly attempts to load a secret key for flask sessions from the
        file specified in the environment variable 'SESSION_KEY_FILE', and falls-back to using
        a random session key on failure.
        
        If the setup is containerized (via docker) it is highly reccommended to use docker secrets
        for these two file.
    """
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

class CacheConfig(ABC):
    """Abstract base class for configuration of the different user caches

    Defines general functions and abstract methods/properties for inheriting deployments.
    """
    @abstractmethod
    def cache_setup(self, app):
        """Sets up an application with a user cache.
        
        Sets an app config variable 'CACHING_TYPE' to the cache object the app should use.

        Args:
            app (Flask): the app to initialize with the cache
        """
        pass
    
    @property
    @abstractmethod
    def INDEX_PAGE_TEMPLATE(self):
        """The template page to embed within the app's homepage.
        
        The app's views are configured to use a dynamic home page according to the difficulty (cache)."""
        pass

    def init_app(self, app):
        """Initializes an application.
        
        Enables custom sessions (app.modules.session_manager) on the app
        and initializes the app's cache using cache_setup.

        Args:
            app (Flask): the app to initialize
        """
        from app.modules.session_manager import create_sessions
        create_sessions(app,
                        session_duration=APP_SESSION_DURATION,
                        clean_interval=GARBAGE_COLLECTOR_CLEAN_INTERVAL)
        
        self.cache_setup(app)

class EasyCacheConfig(CacheConfig):
    """configuration for easy mode- flask session cache"""
    def cache_setup(self, app):
        from app.modules.user_cache import LRUSessionCache
        app.config['CACHING_TYPE'] = LRUSessionCache
    
    INDEX_PAGE_TEMPLATE = 'index_easy.jinja'

class MediumCacheConfig(CacheConfig):
    """configuration for medium mode- AES session cache"""
    def cache_setup(self, app):
        from app.modules.user_cache import AesLRUSessionCache
        app.config['CACHING_TYPE'] = AesLRUSessionCache
        
    INDEX_PAGE_TEMPLATE = 'index_medium.jinja'


class HardCacheConfig(CacheConfig):
    """configuration for hard mode- SQL server-side session cache"""
    def cache_setup(self, app):
        from app.modules.user_cache import SqlLRUSessionCache
        app.config['CACHING_TYPE'] = SqlLRUSessionCache
    
    INDEX_PAGE_TEMPLATE = 'index_hard.jinja'

class AppConfigFactory:
    """Factory class for making combined deployment + difficulty configs.

    Creates a combined configuration object which inherits from both
    DeploymentConfig and CacheConfig.
    """
    # Possible names for each deployment type
    DEV_CONFIG_NAMES = ['dev', 'development']
    TEST_CONFIG_NAMES = ['test', 'testing']
    PRODUCTION_CONFIG_NAMES = ['production', None, 'prod', 'ctf', 'challenge']

    # Possible names for each challenge difficulty
    EASY_CACHE_NAMES = ['flask', 'default', 'cookie', 'easy']
    MEDIUM_CACHE_NAMES = ['aes', 'encrypt', 'encrypted', 'medium', 'normal']
    HARD_CACHE_NAMES = ['sql', 'sqlalchemy', 'hard']

    def make(self, deploy_type=None, difficulty=None):
        """Factory method for creating complete app configurations

        Args:
            deploy_type (str, optional): String name for the deployment type.
                Defaults to None. If None, will attempt to get a string form
                the environment variable 'DEPLOYMENT_TYPE', and if fails stay
                as None. Should be all lowercase.
            difficulty (str, optional): String name for the challenge difficulty.
                Defaults to None. If None, will attempt to get a string form
                the environment variable 'DIFFICULTY'. Should be all lowercase.

        Raises:
            ValueError: if an invalid configuration string is supplied in any way.
            KeyError: if difficulty is None/missing and environment variable
                'DIFFICULTY' is not set.

        Returns:
            DeploymentConfig & CacheConfig: An instance which inherits from both
                DeploymentConfig and CacheConfig to be used as a flask app config.
        """
        # get the deployment type
        if deploy_type is None:
            deploy_type = os.environ.get('DEPLOYMENT_TYPE')
        
        if deploy_type in self.DEV_CONFIG_NAMES:
            deploy_config = DevelopmentDeployment
        elif deploy_type in self.TEST_CONFIG_NAMES:
            deploy_config = TestDeployment
        elif deploy_type in self.PRODUCTION_CONFIG_NAMES:
            deploy_config = ProductionDeployment
        else:
            raise ValueError("Invalid Config Type")
        
        # get the difficulty cache config
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