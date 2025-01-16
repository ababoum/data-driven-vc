from functools import wraps
from diskcache import Cache

cache = Cache("cache")


def memorize(ttl=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{args}:{kwargs}"
            result = cache.get(key)
            if result is None:
                result = await func(*args, **kwargs)
                cache.set(key, result, expire=ttl)
            return result
        return wrapper
    return decorator
