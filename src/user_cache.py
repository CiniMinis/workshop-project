from flask import session
from functools import wraps
import time

# consts for lru_cached operation
CACHE_NAME_TEMPLATE = "cache_for_{}"
DEFAULT_SIZE = 64


def lru_cached(max_size=DEFAULT_SIZE):
    def decorator(func):
        cache_name = CACHE_NAME_TEMPLATE.format(func.__name__)

        @wraps(func)
        def cached_func(*args, **kwargs):
            cache_name = cached_func.cache_name
            if cache_name not in session:
                user_cache = {}
            else:
                user_cache = session[cache_name]

            parameters = str(args + tuple(kwargs.items()))
            if parameters in user_cache:
                _, result = user_cache[parameters]
                user_cache[parameters] = (time.time(), result)
                session[cache_name] = user_cache
                return result

            result = func(*args, **kwargs)
            if len(user_cache) == max_size:
                # finds the oldest cache entry
                evicted = min(
                    user_cache, key=lambda param: user_cache[param][0])
                user_cache.pop(evicted)

            user_cache[parameters] = list((time.time(), result))
            session[cache_name] = user_cache

            return result

        cached_func.cache_name = cache_name
        return cached_func

    return decorator
