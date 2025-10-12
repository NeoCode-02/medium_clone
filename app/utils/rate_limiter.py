import redis
from fastapi import HTTPException, status

from app.core.config import settings

r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)


def rate_limit(key: str, limit: int, window: int):
    current = r.incr(key)
    if current == 1:
        r.expire(key, window)
    elif current > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, please try again later",
        )
