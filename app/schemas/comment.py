from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class CommentBase(BaseModel):
    body: str = Field(..., min_length=1, max_length=255)


class CommentCreate(CommentBase):
    pass


class CommentOut(CommentBase):
    id: int
    user: UserOut
    article_id: int
    created_at: datetime

    class Config:
        from_attributes = True
