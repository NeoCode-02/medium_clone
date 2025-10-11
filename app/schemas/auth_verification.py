from pydantic import BaseModel, EmailStr, Field

# --- EMAIL VERIFICATION ---


class EmailVerificationConfirm(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


# --- PASSWORD RESET (forgot password) ---


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6)
