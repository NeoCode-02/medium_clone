from starlette_admin.contrib.sqla import ModelView
from starlette_admin import action
from starlette_admin.exceptions import FormValidationError
from starlette.requests import Request
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.article import Article, Tag
from app.models.comment import Comment
from app.utils.password import hash_password


class UserAdmin(ModelView):
    """Admin view for User model"""

    exclude_fields_from_list = ["hashed_password"]
    exclude_fields_from_detail = ["hashed_password"]
    exclude_fields_from_create = ["hashed_password", "created_at", "updated_at"]
    exclude_fields_from_edit = ["hashed_password", "created_at", "updated_at"]

    searchable_fields = ["username", "email"]
    sortable_fields = ["id", "username", "email", "created_at", "is_active", "is_admin"]
    page_size = 25
    page_size_options = [10, 25, 50, 100]

    fields = [
        "id",
        "username",
        "email",
        "bio",
        "avatar",
        "is_active",
        "is_verified",
        "is_admin",
        "created_at",
        "updated_at",
    ]

    @action(
        name="activate_users",
        text="Activate Selected",
        confirmation="Are you sure you want to activate selected users?",
        submit_btn_text="Yes, activate",
        submit_btn_class="btn-success",
    )
    async def activate_users(self, request: Request, pks: list) -> str:
        """Bulk activate users"""
        db: Session = request.state.db
        users = db.query(User).filter(User.id.in_(pks)).all()

        for user in users:
            user.is_active = True

        db.commit()
        return f"{len(users)} users activated successfully"

    @action(
        name="deactivate_users",
        text="Deactivate Selected",
        confirmation="Are you sure you want to deactivate selected users?",
        submit_btn_text="Yes, deactivate",
        submit_btn_class="btn-warning",
    )
    async def deactivate_users(self, request: Request, pks: list) -> str:
        """Bulk deactivate users"""
        db: Session = request.state.db
        users = db.query(User).filter(User.id.in_(pks)).all()

        for user in users:
            user.is_active = False

        db.commit()
        return f"{len(users)} users deactivated successfully"

    async def before_create(self, request: Request, data: dict, obj: User) -> None:
        """Hash password before creating user"""
        if "password" in data:
            obj.hashed_password = hash_password(data["password"])


class ArticleAdmin(ModelView):
    """Admin view for Article model"""

    exclude_fields_from_list = ["body", "created_at", "updated_at"]
    exclude_fields_from_create = [
        "created_at",
        "updated_at",
        "likes_count",
        "views_count",
    ]
    exclude_fields_from_edit = ["created_at", "updated_at", "slug"]

    searchable_fields = ["title", "description", "slug"]
    sortable_fields = ["id", "title", "created_at", "likes_count", "views_count"]
    page_size = 25
    page_size_options = [10, 25, 50, 100]

    fields = [
        "id",
        "title",
        "slug",
        "description",
        "body",
        "author",
        "tags",
        "likes_count",
        "views_count",
        "created_at",
        "updated_at",
    ]

    @action(
        name="reset_views",
        text="Reset Views",
        confirmation="Are you sure you want to reset views for selected articles?",
        submit_btn_text="Yes, reset",
        submit_btn_class="btn-warning",
    )
    async def reset_views(self, request: Request, pks: list) -> str:
        """Reset view counts for selected articles"""
        db: Session = request.state.db
        articles = db.query(Article).filter(Article.id.in_(pks)).all()

        for article in articles:
            article.views_count = 0

        db.commit()
        return f"Views reset for {len(articles)} articles"

    @action(
        name="reset_likes",
        text="Reset Likes",
        confirmation="Are you sure you want to reset likes for selected articles?",
        submit_btn_text="Yes, reset",
        submit_btn_class="btn-warning",
    )
    async def reset_likes(self, request: Request, pks: list) -> str:
        """Reset like counts for selected articles"""
        db: Session = request.state.db
        articles = db.query(Article).filter(Article.id.in_(pks)).all()

        for article in articles:
            article.likes_count = 0

        db.commit()
        return f"Likes reset for {len(articles)} articles"


class TagAdmin(ModelView):
    """Admin view for Tag model"""

    searchable_fields = ["name"]
    sortable_fields = ["id", "name"]
    page_size = 50
    page_size_options = [25, 50, 100, 200]

    fields = ["id", "name", "articles"]

    @action(
        name="merge_tags",
        text="Merge into First Selected",
        confirmation="This will merge all selected tags into the first one. Continue?",
        submit_btn_text="Yes, merge",
        submit_btn_class="btn-danger",
    )
    async def merge_tags(self, request: Request, pks: list) -> str:
        """Merge multiple tags into the first selected tag"""
        if len(pks) < 2:
            raise FormValidationError(
                {"error": "Please select at least 2 tags to merge"}
            )

        db: Session = request.state.db

        # Get all tags
        tags = db.query(Tag).filter(Tag.id.in_(pks)).all()
        target_tag = tags[0]
        tags_to_merge = tags[1:]

        # Move all articles to target tag
        for tag in tags_to_merge:
            for article in tag.articles:
                if article not in target_tag.articles:
                    target_tag.articles.append(article)
            db.delete(tag)

        db.commit()
        return f"{len(tags_to_merge)} tags merged into '{target_tag.name}'"


class CommentAdmin(ModelView):
    """Admin view for Comment model"""

    exclude_fields_from_list = ["created_at", "updated_at"]
    exclude_fields_from_create = ["created_at", "updated_at"]
    exclude_fields_from_edit = ["created_at", "updated_at", "user", "article"]

    searchable_fields = ["body"]
    sortable_fields = ["id", "created_at"]
    page_size = 50
    page_size_options = [25, 50, 100, 200]

    fields = ["id", "body", "user", "article", "created_at", "updated_at"]

    @action(
        name="delete_comments",
        text="Delete Selected",
        confirmation="Are you sure you want to delete selected comments?",
        submit_btn_text="Yes, delete",
        submit_btn_class="btn-danger",
    )
    async def delete_comments(self, request: Request, pks: list) -> str:
        """Bulk delete comments"""
        db: Session = request.state.db
        comments = db.query(Comment).filter(Comment.id.in_(pks)).all()

        count = len(comments)
        for comment in comments:
            db.delete(comment)

        db.commit()
        return f"{count} comments deleted successfully"
