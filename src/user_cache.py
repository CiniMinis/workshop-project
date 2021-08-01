from flask import session
from functools import wraps
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
import time
import os


class LRUSessionCache:
    CACHE_NAME_TEMPLATE = "cache_for_{}"
    DEFAULT_SIZE = 64

    def __init__(self, max_size=DEFAULT_SIZE):
        self.max_size = max_size

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
            print(self._cache)
            parameters = self._encode_params(*args, **kwargs)
            fetched = self[parameters]
            if fetched is not None:
                _, result = fetched
                self._store(parameters, result)
                return result

            result = func(*args, **kwargs)
            if len(self._cache) == self.max_size:
                self._evict()

            self._store(parameters, result)
            return result

        return cached_func


class AesLRUSessionCache(LRUSessionCache):
    DEFAULT_KEY_LENGTH = 32
    SEPARATOR = b','

    def __init__(self, key=None, mode=AES.MODE_CTR, *args, **kwargs):
        if key is None:
            key = os.urandom(self.DEFAULT_KEY_LENGTH)
        self.key = key
        self.mode = mode
        super().__init__(*args, **kwargs)

    def _encrypt_and_encode(self, plain):
        aes = AES.new(self.key, self.mode)
        encrypted = aes.encrypt(plain.encode('ascii'))
        encoded_vals = map(b64encode, (aes.nonce, encrypted))
        return self.SEPARATOR.join(encoded_vals).decode('ascii')

    def _decode_and_decrypt(self, encoded):
        encoded_bytes = encoded.encode('ascii')
        encoded_vals = encoded_bytes.split(self.SEPARATOR)
        nonce, cipher = map(b64decode, encoded_vals)
        aes = AES.new(self.key, self.mode, nonce=nonce)
        return aes.decrypt(cipher).decode('ascii')

    def _store(self, cache_key, cache_value):
        enc_cache_key = self._encrypt_and_encode(cache_key)
        enc_cache_value = self._encrypt_and_encode(cache_value)
        for cached in self._cache:
            if self._decode_and_decrypt(cached) == cache_key:
                enc_cache_key = cached
                break
        super()._store(enc_cache_key, enc_cache_value)

    def __getitem__(self, cache_key):
        for cached in self._cache:
            if self._decode_and_decrypt(cached) == cache_key:
                cache_time, result = self._cache[cached]
                return cache_time, self._decode_and_decrypt(result)
        return None
