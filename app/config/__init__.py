import os
from abc import ABC, abstractmethod

from flask import config
from instance import session_key

FILE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(FILE_DIR, '../../instance')

# general config consts
class AppConfig(ABC):
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = session_key

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

# TODO: make configurations for testing and production

class AppConfigFactory:
    DEV_NAMES = ['dev', 'development']  # names for development

    def make(self, config_type):
        if config_type in self.DEV_NAMES:
            return AppDevConfig()
        
        raise ValueError("Invalid Config Type")