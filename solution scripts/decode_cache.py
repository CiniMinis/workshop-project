"""
    A simple utility script which decodes the session data from the given cookie.
    Session data is signed but not encrypted, similar to a JWT!
"""
from itsdangerous.exc import *
from itsdangerous.url_safe import URLSafeTimedSerializer
from flask.sessions import session_json_serializer

s = URLSafeTimedSerializer("random-key-which-is-wrong", serializer=session_json_serializer)

cookie = input("Cookie to decode: ")

# using unsafe to ignore the signing mismatch
_, payload = s.loads_unsafe(cookie)

if payload is None:
    print("Bad decoding")
else:
    print(payload)
