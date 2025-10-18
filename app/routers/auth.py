from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import Token
from app.schemas.auth_verification import (
    EmailVerificationConfirm,
    PasswordResetConfirm,
    PasswordResetRequest,
)
from app.schemas.user import UserCreate, UserOut
from app.tasks.email import send_email_code_email
from app.utils.dependencies import get_current_user, get_db
from app.utils.jwt_token import create_access_token, create_refresh_token, decode_token
from app.utils.password import hash_password, verify_password
from app.utils.rate_limiter import rate_limit
from app.utils.redis_service import delete_code, get_code, set_code

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and send verification email"""

    is_first_user = db.query(User).count() == 0

    # Check if user already exists
    existing_user = (
        db.query(User)
        .filter((User.email == user.email) | (User.username == user.username))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    # Create new user
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.hashed_password),
        bio=user.bio,
        avatar=user.avatar,
        is_active=True,
        is_verified=is_first_user,
        is_admin=is_first_user,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate and send verification code
    if not is_first_user:
        code = set_code(user.email, "verify")
        send_email_code_email.delay(user.email, code, "verify")

    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Login with username/email and password"""

    # Rate limiting
    rate_limit(f"login:{form_data.username}", limit=5, window=300)

    # Find user by username or email
    user = (
        db.query(User)
        .filter(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
        .first()
    )

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(verification: EmailVerificationConfirm, db: Session = Depends(get_db)):
    """Verify email with 6-digit code"""

    # Rate limiting
    rate_limit(f"verify:{verification.email}", limit=5, window=300)

    # Get stored code
    stored_code = get_code(verification.email, "verify")

    if not stored_code or stored_code != verification.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    # Find and verify user
    user = db.query(User).filter(User.email == verification.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_verified = True
    db.commit()

    # Delete code after successful verification
    delete_code(verification.email, "verify")

    return {"message": "Email verified successfully"}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(email: str, db: Session = Depends(get_db)):
    """Resend verification code"""

    # Rate limiting
    rate_limit(f"resend:{email}", limit=3, window=300)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
        )

    # Generate and send new code
    code = set_code(email, "verify")
    send_email_code_email.delay(email, code, "verify")

    return {"message": "Verification code sent"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset code"""

    # Rate limiting
    rate_limit(f"reset:{request.email}", limit=3, window=300)

    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset code has been sent"}

    # Generate and send reset code
    code = set_code(request.email, "pwdreset")
    send_email_code_email.delay(request.email, code, "reset")

    return {"message": "If the email exists, a reset code has been sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(reset: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password with verification code"""

    # Rate limiting
    rate_limit(f"resetconfirm:{reset.email}", limit=5, window=300)

    # Verify code
    stored_code = get_code(reset.email, "pwdreset")
    if not stored_code or stored_code != reset.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code",
        )

    # Find user and update password
    user = db.query(User).filter(User.email == reset.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.hashed_password = hash_password(reset.new_password)
    db.commit()

    # Delete code after successful reset
    delete_code(reset.email, "pwdreset")

    return {"message": "Password reset successfully"}


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """Get new access token using refresh token"""

    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    # Create new tokens
    access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserOut)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user
