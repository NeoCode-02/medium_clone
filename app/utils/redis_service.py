import redis
import random
from app.core.config import settings


r = redis.Redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)

CODE_TTL_SECONDS = 120  # 2 minutes


def _make_key(prefix: str, identifier: str) -> str:
    """Return standardized Redis key."""
    return f"{prefix}:{identifier}"


def _gen_code() -> str:
    """Generate a 6-digit random verification code."""
    return f"{random.randint(0, 999999):06d}"


def set_code(email: str, code_type: str, ttl: int = CODE_TTL_SECONDS) -> str:
    """
    Generate and store a 6-digit code in Redis for a given email and code type.
    - code_type: "verify" | "pwdreset"
    """
    key = _make_key(code_type, email)
    code = _gen_code()
    r.setex(key, ttl, code)
    return code


def get_code(email: str, code_type: str) -> str | None:
    """Retrieve a stored verification or password-reset code."""
    key = _make_key(code_type, email)
    return r.get(key)


def delete_code(email: str, code_type: str) -> None:
    """Delete a stored verification or password-reset code."""
    key = _make_key(code_type, email)
    r.delete(key)



# Article Views and Likes Counting
def increment_view(article_id: int) -> int:
    """Increment and return the current view count for an article."""
    key = _make_key("views", str(article_id))
    return r.incr(key)


def get_views(article_id: int) -> int:
    """Retrieve the current view count for an article."""
    key = _make_key("views", str(article_id))
    value = r.get(key)
    return int(value) if value else 0


def increment_like(article_id: int) -> int:
    """Increment and return the like count for an article."""
    key = _make_key("likes", str(article_id))
    return r.incr(key)


def decrement_like(article_id: int) -> int:
    """Decrement and return the like count for an article (if greater than 0)."""
    key = _make_key("likes", str(article_id))
    current = get_likes(article_id)
    if current > 0:
        return r.decr(key)
    return 0


def get_likes(article_id: int) -> int:
    """Retrieve the current like count for an article."""
    key = _make_key("likes", str(article_id))
    value = r.get(key)
    return int(value) if value else 0
