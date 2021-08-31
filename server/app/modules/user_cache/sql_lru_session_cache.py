"""
    A server side, SQL based per-user caching solution.
    Assumes a SessionHandler is attached to the flask app (SessionIDs are required).
"""

from app import db
from flask import current_app
from sqlalchemy.sql import func
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.exc import IntegrityError
from .lru_session_cache import LRUSessionCache
from ..session_manager import SessionHandler
import os


class SqlLRUSessionCache(LRUSessionCache):
    """A decorator, an server side LRU per-session caching solution.

    Attributes:
        index (int): a unique index for the SQL table.
            Used for table identification within the database.
        CacheRecord (db.Model): the flask-sqlalchemy table object
            which stores all cached values.

    Note:
        This class extends the LRUSessionCache solution, and all attributes
        and requirements there apply too.
    """
    DEFAULT_SIZE = 64   # The default LRU cache size
    DB_NAME = "sql_sessions"    # the name for the sessions' database
    BIND_NAME = "sql_sessions"  # the flask-sqlalchemy bind name for the sessions' database
    TABLE_NAME_TEMPLATE = "sql_session_cache_{}"    # a string format template for table names
    _DECLARED_SESSION_CACHES = []
    _SESSION_HANDLER = SessionHandler()

    def __init__(self, *args, **kwargs):
        self.index = len(self._DECLARED_SESSION_CACHES)
        self._DECLARED_SESSION_CACHES.append(self)

        class CacheRecord(db.Model):
            __bind_key__ = self.BIND_NAME
            __tablename__ = self.table_name
            id = db.Column(db.Integer, primary_key=True)
            ssid = db.Column(db.String(self._SESSION_HANDLER.UUID_LEN), nullable=False)
            cache_key = db.Column(db.PickleType)
            cache_value = db.Column(db.PickleType)
            last_access = db.Column(db.DateTime)
            __table_args__ = (
                # Makes sure users can't store the same key twice
                db.UniqueConstraint('ssid', 'cache_key'),
            )
        
        self.CacheRecord = CacheRecord

        super().__init__(*args, **kwargs)
    
    def _register_cache(self, app):
        # default is to make the session db in the default db's directory
        db_prefix = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'])
        db_uri = os.path.join(db_prefix, self.DB_NAME)
        new_bind = {self.BIND_NAME: db_uri}
        
        if app.config['SQLALCHEMY_BINDS'] is None:
            app.config['SQLALCHEMY_BINDS'] = {}
        
        app.config['SQLALCHEMY_BINDS'].update(new_bind)
    
    @staticmethod
    @_SESSION_HANDLER.on_session_delete
    def _delete_session(ssid):
        for cache in SqlLRUSessionCache._DECLARED_SESSION_CACHES:
            cache.CacheRecord.query.filter_by(ssid=ssid).delete()
        db.session.commit()
    
    @property
    def table_name(self):
        """str: the name of the table used for caching in the database"""
        return self.TABLE_NAME_TEMPLATE.format(self.index)
    
    @property
    def current_ssid(self):
        """str: the current userid being handled, used for clearness only"""
        return self._SESSION_HANDLER.ssid
    
    @property
    def _cache(self):
        user_records = self.CacheRecord.query.filter_by(ssid=self.current_ssid).all()
        cache = {record.cache_key: (record.last_access, record.cache_value) for record in user_records}
        return cache
    
    def _store(self, key, value):
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
        """Disabling the inherited set_modified function. Not required."""
        pass
    
    def __call__(self, func):
        decorated = super().__call__(func)
        self._register_cache(current_app)
        return decorated