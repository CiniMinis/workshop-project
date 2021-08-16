from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from .lru_session_cache import LRUSessionCache
import os

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
