from .events import SessionEvent, SessionHandler
from sqlalchemy.sql import func
from flask import copy_current_request_context
from datetime import datetime, timezone
from threading import Thread
import os.path
import time

_DB_BIND_TEMPLATE = "active_sessions_{}"

class SessionGarbageCollector(SessionHandler):
    _next_gc_id = 0
    DEFAULT_DB_FORMAT = 'GarbageCollector_{}.db'
    
    def __init__(self, session_duration, clean_interval, db_uri=None):
        self.session_duration = session_duration
        self.clean_interval = clean_interval
        self._gc_id = SessionGarbageCollector._next_gc_id 
        SessionGarbageCollector._next_gc_id += 1
        self.bind_name = _DB_BIND_TEMPLATE.format(self._gc_id)
        
        # call super for app register
        super().__init__()
        
        if db_uri is None:
            # default is to make the session db in the default db's directory
            db_prefix = os.path.dirname(self.app.config['SQLALCHEMY_DATABASE_URI'])
            db_uri = os.path.join(db_prefix, self.DEFAULT_DB_FORMAT.format(self._gc_id)) 
        
        self._make_db(db_uri)
        
        # deactivates changing the event handlers
        self.on_session_create = self.on_session_connect = self.on_session_delete = lambda func: func
        
        # sets the event handlers to the bound functions
        setattr(self, SessionEvent.CREATE.value, self._add_session)
        setattr(self, SessionEvent.CONNECT.value, self._update_session)
        
        self.started = False
    
    def _make_db(self, db_uri):
        class SessionId(self.app.db.Model):
            __bind_key__ = self.bind_name
            ssid = self.app.db.Column(self.app.db.String(SessionHandler.UUID_LEN), primary_key=True)
            last_connection = self.app.db.Column(self.app.db.DateTime)
            
            def __repr__(self) -> str:
                return f"SSID: {self.ssid} (last {self.last_connection})"
        
        self.SessionTable = SessionId
        new_bind = {self.bind_name: db_uri}
        
        if self.app.config['SQLALCHEMY_BINDS'] is None:
            self.app.config['SQLALCHEMY_BINDS'] = {}
        
        self.app.config['SQLALCHEMY_BINDS'].update(new_bind)
        
        self.app.db.create_all(bind=self.bind_name)   
        
    
    def start(self):
        self.started = True
        # start the garbage collection thread with the context of the first request
        loop_with_context = copy_current_request_context(SessionGarbageCollector._loop_collector)
        self.worker = Thread(target=loop_with_context, args=(self,))
        self.worker.start()
    
    def _add_session(self, ssid):
        if not self.started:
            self.start()
        try:
            self.app.db.session.add(
                self.SessionTable(
                    ssid=ssid,
                    last_connection=func.now()
                )
            )
            self.app.db.session.commit()
        except Exception as e:
            # If race occurred, another thread inserted, which is fine
            print(f'GC: Exception on add {ssid}:', e)
            self.app.db.session.rollback()
                
    def _update_session(self, ssid):
        connection_row = self.SessionTable.query.filter_by(ssid=ssid).first()
        if connection_row is None:
            self._add_session(ssid)
            return

        try:
            connection_row.last_connection=func.now()
            self.app.db.session.commit()
        except Exception as e:
            # If race occurred, another thread updated the time at the same time
            # this means the time is up to date
            print(f'GC: Exception on update {ssid}:', e)
            self.app.db.session.rollback()
    
    @staticmethod
    def _loop_collector(collector):
        while True:
            time.sleep(collector.clean_interval)
            collector._collect_garbage()
    
    def _collect_garbage(self):
        age_threshold = datetime.now(timezone.utc) - self.session_duration
        remove_targets = self.SessionTable.query.filter(
                    self.SessionTable.last_connection < age_threshold
                ).all()      
        for session in remove_targets:
            try:
                self.app.db.session.delete(session)
                self.app.db.session.commit()
            except Exception as e:
                # handle race condition by trying to collect next time
                print(f'GC: Exception on delete:', e)
                self.app.db.session.rollback()
            else:
                SessionHandler.trigger_event(SessionEvent.DELETE, session.ssid)
