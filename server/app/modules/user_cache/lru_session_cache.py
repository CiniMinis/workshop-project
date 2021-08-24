from flask import session
from functools import wraps
import time



class LRUSessionCache:
    CACHE_NAME_TEMPLATE = "cache_for_{}"
    DEFAULT_SIZE = 10

    def __init__(self, max_size=None, serializer=None):
        if max_size is None:
            max_size = self.DEFAULT_SIZE
        
        self.max_size = max_size
        self.serializer = serializer

    @property
    def _cache(self):
        if self.cache_name not in session:
            session[self.cache_name] = {}
        return session[self.cache_name]

    @staticmethod
    def _encode_params(*args, **kwargs):
        return str(args + tuple(kwargs.items()))

    def _evict(self):
        evicted = min(self._cache, key=lambda param: self._cache[param][0])
        self._cache.pop(evicted)

    def _store(self, key, value):
        self._cache[key] = (time.time(), value)

    def __getitem__(self, key):
        if key in self._cache:
            return self._cache[key]
        return None

    def set_modified(self):
        session[self.cache_name] = self._cache

    def __call__(self, func):
        self.cache_name = self.CACHE_NAME_TEMPLATE.format(func.__name__)

        @wraps(func)
        def cached_func(*args, **kwargs):
            self.set_modified()     # makes sure the cache update flows to user
            parameters = self._encode_params(*args, **kwargs)
            fetched = self[parameters]
            if fetched is not None:
                _, result = fetched
                self._store(parameters, result)

                if self.serializer is None:
                    return result
                return self.serializer.loads(result)

            result = func(*args, **kwargs)
            if self.serializer is None:
                to_store = result
            else:
                to_store = self.serializer.dumps(result)
            
            if len(self._cache) >= self.max_size:
                self._evict()

            self._store(parameters, to_store)
            return result

        return cached_func