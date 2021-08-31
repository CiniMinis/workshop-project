"""
    A flask-session based user caching solution which encrypts the function
    inputs and outputs with AES.
"""

from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from .lru_session_cache import LRUSessionCache
import os

class AesLRUSessionCache(LRUSessionCache):
    """Decorator, an AES encrypted LRU caching solution for functions.
    
    Attributes:
        key (bytes, optional): an AES private key to be used. If missing or
            None, attempts to fetch an AES key from the file specified in the
            `AES_SESSION_KEY_FILE` environment variable, and if all fails, randomly
            generate a key.
        mode: an AES mode of operation ot be used. Defaults to CTR.

    Note:
        This class extends the LRUSessionCache solution, and all attributes
        and requirements there apply too.
    """
    DEFAULT_KEY_LENGTH = 32     # the byte length of a generated AES key
    SEPARATOR = b','    # The seperator used between the IV and ciphertext

    def __init__(self, key=None, mode=AES.MODE_CTR, *args, **kwargs):
        key_path = os.environ.get('AES_SESSION_KEY_FILE')
        if key is not None:
            self.key = key
        elif key_path is not None:
            with open(key_path, 'rb') as key_file:
                self.key = key_file.read()
        else:
            key = os.urandom(self.DEFAULT_KEY_LENGTH)
        
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
