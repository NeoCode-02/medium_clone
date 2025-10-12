from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.time_mixin import TimeMixin


class User(Base, TimeMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str] = mapped_column(String(300), nullable=True)
    avatar: Mapped[str] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    articles = relationship("Article", back_populates="author", cascade="all, delete")
    comments = relationship("Comment", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"

    __table_args__ = (Index("ix_users_username_email", username, email),)
