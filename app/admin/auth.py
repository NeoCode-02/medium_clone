from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import LoginFailed

from app.models.user import User
from app.utils.password import verify_password


class CustomAuthProvider(AuthProvider):
    """Custom authentication provider for admin panel"""

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        """Handle admin login"""
        # Get database session
        db: Session = request.state.db

        # Find user by username or email
        user = (
            db.query(User)
            .filter((User.username == username) | (User.email == username))
            .first()
        )

        # Verify credentials and admin status
        if not user or not verify_password(password, user.hashed_password):
            raise LoginFailed("Invalid username or password")

        if not user.is_active:
            raise LoginFailed("Account is inactive")

        if not user.is_admin:
            raise LoginFailed("You don't have admin privileges")

        # Store user info in session
        request.session.update(
            {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
            }
        )

        return response

    async def is_authenticated(self, request: Request) -> bool:
        """Check if user is authenticated"""
        user_id = request.session.get("user_id")
        if not user_id:
            return False

        # Verify user still exists and is admin
        db: Session = request.state.db
        user = db.query(User).filter(User.id == user_id).first()
        return user is not None and user.is_admin and user.is_active

    def get_admin_user(self, request: Request) -> AdminUser:
        """Get current admin user"""
        username = request.session.get("username", "Admin")
        return AdminUser(username=username)

    async def logout(self, request: Request, response: Response) -> Response:
        """Handle admin logout"""
        request.session.clear()
        return response
