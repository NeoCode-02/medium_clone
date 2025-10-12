import redis
from celery import Celery

from app import models
from app.core.config import settings
from app.database import SessionLocal

celery = Celery(
    "sync_metrics",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)


try:
    REDIS_URL = settings.REDIS_URL
except Exception:
    REDIS_URL = None

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


@celery.task(name="sync_article_metrics")
def sync_article_metrics():
    session = SessionLocal()
    try:
        # sync views
        for key in r.scan_iter("views:*"):
            # redis-py returns str when decode_responses=True; if not, decode bytes
            k = key if isinstance(key, str) else key.decode()
            _, article_id_s = k.split(":", 1)
            try:
                article_id = int(article_id_s)
            except ValueError:
                continue
            views = int(r.get(k) or 0)
            if views == 0:
                r.delete(k)
                continue
            article = (
                session.query(models.Article)
                .filter(models.Article.id == article_id)
                .first()
            )
            if article:
                # persist incrementally
                article.views_count = (getattr(article, "views_count", 0) or 0) + views
                session.add(article)
                r.delete(k)
        # sync likes
        for key in r.scan_iter("likes:*"):
            k = key if isinstance(key, str) else key.decode()
            _, article_id_s = k.split(":", 1)
            try:
                article_id = int(article_id_s)
            except ValueError:
                continue
            likes = int(r.get(k) or 0)
            if likes == 0:
                r.delete(k)
                continue
            article = (
                session.query(models.Article)
                .filter(models.Article.id == article_id)
                .first()
            )
            if article:
                article.likes_count = (getattr(article, "likes_count", 0) or 0) + likes
                session.add(article)
                r.delete(k)
        session.commit()
    finally:
        session.close()
