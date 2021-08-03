"""
    A simple utility script which decodes the session data from the given cookie.
    Session data is signed but not encrypted, similar to a JWT!
"""
from itsdangerous.exc import *
from itsdangerous.url_safe import URLSafeTimedSerializer
from flask.sessions import session_json_serializer

s = URLSafeTimedSerializer("random-key-which-is-wrong", serializer=session_json_serializer)

cookie = ".eJyrVkpOTM5IjU_LL4pPTy2JL05NLkotUbKqVtJQd61MLVbX0QRxFIBC0YZmRuYWhuYWFiZ6JgbGFqbmRjpQGQMYw8jQQMfIxEjH1DS2FgR1gMbk5Rengo2BGWBpYKpnamBkbgrTZaiTV5qTA1JfCwCvhyf9.YQaHsQ.D6ZvcO16FSM3BIgUXNXLj0UUOjQ"

_, payload = s.loads_unsafe(cookie)

print(payload)