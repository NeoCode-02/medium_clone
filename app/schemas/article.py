from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.user import UserOut
from app.schemas.tag import TagOut


class ArticleBase(BaseModel):
    title: str = Field(..., max_length=150)
    description: Optional[str] = None
    body: str
    tags: Optional[List[str]] = []


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None


class ArticleOut(BaseModel):
    id: int
    title: str
    slug: str
    description: Optional[str]
    body: str
    likes_count: int
    views_count: int
    author: UserOut
    tags: List[TagOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
