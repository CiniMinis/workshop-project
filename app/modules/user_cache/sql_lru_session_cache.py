from flask import session
from app import db
from sqlalchemy.sql import func
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError
from .lru_session_cache import LRUSessionCache
from uuid import uuid4
import os

UUID_LEN = 36


class SqlLRUSessionCache(LRUSessionCache):
    DEFAULT_DB_NAME = "SqlSessions.db"
    DEFAULT_SIZE = 64
    CLIENT_ID_FIELD = "SqlLRUSessionCache-ClientID"
    BIND_NAME_TEMPLATE = "sql_session_cache: {}"
    _DECLARED_SESSION_CACHES = []

    def __init__(self, db_uri=None, *args, **kwargs):
        self.db_uri = db_uri

        self.index = len(self._DECLARED_SESSION_CACHES)
        self._DECLARED_SESSION_CACHES.append(self)
        
        class CacheClient(db.Model):
            __bind_key__ = self.bind_name
            id = db.Column(db.String(UUID_LEN), primary_key=True)
        
        self.CacheClient = CacheClient

        class CacheRecord(db.Model):
            __bind_key__ = self.bind_name
            id = db.Column(db.Integer, primary_key=True)
            client_id = db.Column(db.String(UUID_LEN), db.ForeignKey('cache_client.id'), nullable=False)
            cache_key = db.Column(db.PickleType)
            cache_value = db.Column(db.PickleType)
            last_access = db.Column(db.DateTime)
            __table_args__ = (
                # Makes sure users can't store the same key twice
                db.UniqueConstraint('client_id', 'cache_key'),
            )
        
        self.CacheRecord = CacheRecord

        super().__init__(*args, **kwargs)
    
    @staticmethod
    def _init_ssid(response):
        if SqlLRUSessionCache.CLIENT_ID_FIELD not in session:
            session[SqlLRUSessionCache.CLIENT_ID_FIELD] = str(uuid4())
        
        return response
    
    @staticmethod
    def make_databases():
        for cache in SqlLRUSessionCache._DECLARED_SESSION_CACHES:
            db.create_all(bind=cache.bind_name)
    
    @classmethod
    def init_app(cls, app):
        # default is to make the session db in the default db's directory
        db_prefix = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'])
        default_db_uri = os.path.join(db_prefix, cls.DEFAULT_DB_NAME)

        new_binds = {}
        for cache in cls._DECLARED_SESSION_CACHES:
            if cache.db_uri is not None:
                new_binds[cache.bind_name] = cache.db_uri
            else:
                new_binds[cache.bind_name] = default_db_uri
        
        if app.config['SQLALCHEMY_BINDS'] is None:
            app.config['SQLALCHEMY_BINDS'] = {}
        
        app.config['SQLALCHEMY_BINDS'].update(new_binds)

        with app.app_context():
            cls.make_databases()

        app.after_request(cls._init_ssid)
    
    @property
    def bind_name(self):
        return self.BIND_NAME_TEMPLATE.format(self.index)
    
    @property
    def current_ssid(self):
        if self.CLIENT_ID_FIELD not in session:
            raise ValueError("No Session ID Given")
        ssid = session[self.CLIENT_ID_FIELD]

        if self.CacheClient.query.filter_by(id=ssid).first() is None:
            try:
                db.session.add(self.CacheClient(id=ssid))
                db.session.commit()
            except IntegrityError:
                # another thread committed this ssid, no need to retry
                db.session.rollback()
        
        return ssid
    
    @property
    def _cache(self):
        user_records = self.CacheRecord.query.filter_by(client_id=self.current_ssid).all()
        cache = {record.cache_key: (record.last_access, record.cache_value) for record in user_records}
        return cache
    
    def _store(self, key, value):
        record = self.CacheRecord.query.filter_by(client_id=self.current_ssid, cache_key=key).first()
        if record is None:
            db.session.add(
                self.CacheRecord(
                    client_id=self.current_ssid,
                    cache_key=key,
                    cache_value=value,
                    last_access=func.now()
                )
            )

            if len(self._cache) > self.max_size:
                self._evict()
            
            db.session.commit()
        else:
            record.last_access = func.now()

        try:
            db.session.commit()
        except (StaleDataError, IntegrityError):
            # record was evicted! Retry to store.
            db.session.rollback()
            self._store(key, value)
    
    def _evict(self):
        eviction_target = self.CacheRecord.query.filter_by(client_id=self.current_ssid).order_by(self.CacheRecord.last_access).first()
        db.session.delete(eviction_target)
    
    def __getitem__(self, key):
        record = self.CacheRecord.query.filter_by(client_id=self.current_ssid, cache_key=key).first()
        if record is None:
            return None
        return (record.last_access, record.cache_value)
    
    def set_modified(self):
        pass