from starlette_admin.contrib.sqla import Admin

from app.admin.auth import CustomAuthProvider
from app.admin.views import ArticleAdmin, CommentAdmin, TagAdmin, UserAdmin
from app.database import engine
from app.models.article import Article, Tag
from app.models.comment import Comment
from app.models.user import User

admin = Admin(
    engine,
    title="MediumClone Admin",
    base_url="/admin",
    auth_provider=CustomAuthProvider(),
    middlewares=[],
)

admin.add_view(UserAdmin(User, icon="fa fa-users"))
admin.add_view(ArticleAdmin(Article, icon="fa fa-newspaper"))
admin.add_view(TagAdmin(Tag, icon="fa fa-tags"))
admin.add_view(CommentAdmin(Comment, icon="fa fa-comments"))
