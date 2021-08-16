from app import db
from sqlalchemy.sql import func
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError
from .lru_session_cache import LRUSessionCache
from ..ssid_manager import SessionIdManager
import os


class SqlLRUSessionCache(LRUSessionCache):
    DEFAULT_DB_FORMAT = "SqlSessions_{}.db"
    DEFAULT_SIZE = 64
    BIND_NAME_TEMPLATE = "sql_session_cache: {}"
    _DECLARED_SESSION_CACHES = []
    _SSID_MANAGER = SessionIdManager()

    def __init__(self, db_uri=None, *args, **kwargs):
        self.db_uri = db_uri

        self.index = len(self._DECLARED_SESSION_CACHES)
        self._DECLARED_SESSION_CACHES.append(self)

        class CacheRecord(db.Model):
            __bind_key__ = self.bind_name
            id = db.Column(db.Integer, primary_key=True)
            ssid = db.Column(db.String(self._SSID_MANAGER.UUID_LEN), nullable=False)
            cache_key = db.Column(db.PickleType)
            cache_value = db.Column(db.PickleType)
            last_access = db.Column(db.DateTime)
            __table_args__ = (
                # Makes sure users can't store the same key twice
                db.UniqueConstraint('ssid', 'cache_key'),
            )
        
        self.CacheRecord = CacheRecord

        super().__init__(*args, **kwargs)
    
    @staticmethod
    def make_databases():
        for cache in SqlLRUSessionCache._DECLARED_SESSION_CACHES:
            db.create_all(bind=cache.bind_name)
    
    @classmethod
    def init_app(cls, app):
        # default is to make the session db in the default db's directory
        db_prefix = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'])
        default_db_uri = os.path.join(db_prefix, cls.DEFAULT_DB_FORMAT)

        new_binds = {}
        for cache in cls._DECLARED_SESSION_CACHES:
            if cache.db_uri is not None:
                new_binds[cache.bind_name] = cache.db_uri
            else:
                new_binds[cache.bind_name] = default_db_uri.format(cache.cache_name)
        
        if app.config['SQLALCHEMY_BINDS'] is None:
            app.config['SQLALCHEMY_BINDS'] = {}
        
        app.config['SQLALCHEMY_BINDS'].update(new_binds)

        with app.app_context():
            cls.make_databases()

        cls._SSID_MANAGER.init_app(app)
    
    @property
    def bind_name(self):
        return self.BIND_NAME_TEMPLATE.format(self.index)
    
    @property
    def current_ssid(self):
        return self._SSID_MANAGER.current_ssid
    
    @property
    def _cache(self):
        user_records = self.CacheRecord.query.filter_by(ssid=self.current_ssid).all()
        cache = {record.cache_key: (record.last_access, record.cache_value) for record in user_records}
        return cache
    
    def _store(self, key, value):
        # NOTE: for some reason, the following NORMAL query issues a delete failure somehow?
        # This is just a query and the bug seems to relate to many parallel queries somehow
        record = self.CacheRecord.query.filter_by(ssid=self.current_ssid, cache_key=key).first()
        if record is None:
            db.session.add(
                self.CacheRecord(
                    ssid=self.current_ssid,
                    cache_key=key,
                    cache_value=value,
                    last_access=func.now()
                )
            )

            if len(self._cache) > self.max_size:
                self._evict()
            
        else:
            record.last_access = func.now()

        try:
            db.session.commit()
        except (StaleDataError, IntegrityError):
            # record was modified while operating! Retry to store.
            db.session.rollback()
            self._store(key, value)
    
    def _evict(self):
        eviction_target = self.CacheRecord.query.filter_by(ssid=self.current_ssid).order_by(self.CacheRecord.last_access).first()
        deleted = db.session.delete(eviction_target)
        if deleted == 0:
            # if deleted item was deleted by another thread, retry
            self._evict()
    
    def __getitem__(self, key):
        record = self.CacheRecord.query.filter_by(ssid=self.current_ssid, cache_key=key).first()
        if record is None:
            return None
        return (record.last_access, record.cache_value)
    
    def set_modified(self):
        pass