from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.tag import TagOut
from app.schemas.user import UserOut


class ArticleBase(BaseModel):
    title: str = Field(..., max_length=150)
    description: str | None = None
    body: str
    tags: list[str] | None = []


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    body: str | None = None
    tags: list[str] | None = None


class ArticleOut(BaseModel):
    id: int
    title: str
    slug: str
    description: str | None
    body: str
    likes_count: int
    views_count: int
    author: UserOut
    tags: list[TagOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
