"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db
from services.auth_service import AuthService
from schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    ResetPasswordWithToken,
    PasswordResetRequest,
    ForgotPasswordRequest,
)
from utils.jwt import decode_token, create_access_token
from utils.rate_limit import limiter
from utils.email import send_password_reset_email
from utils.logger import setup_logger
from datetime import datetime, timedelta
import secrets

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()
logger = setup_logger(__name__)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get current authenticated user from JWT token.
    """
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return user_id


async def get_current_admin(user_id: str = Depends(get_current_user)):
    """
    Dependency to enforce admin-only access.
    """
    db = get_db()
    auth_service = AuthService(db)

    try:
        user = await auth_service.get_user(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )

    return user_id


# ─── Register ────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister):
    """Register a new user account."""
    db = get_db()
    auth_service = AuthService(db)

    try:
        user = await auth_service.register(user_data)

        # Auto-login: create access token so client can be authenticated immediately
        access_token = create_access_token(data={"sub": str(user["_id"])})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"],
                "role": user.get("role", "user"),
                "energy_limit": user.get("energy_limit", 50.0),
                "created_at": user.get("created_at"),
            },
            "message": "User registered successfully. You can now login.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Login ───────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    """Authenticate and return a JWT access token."""
    db = get_db()
    auth_service = AuthService(db)

    try:
        token_data = await auth_service.login(credentials.email, credentials.password)
        return token_data
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ─── Profile ──────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_profile(user_id: str = Depends(get_current_user)):
    """Get the current user's profile."""
    db = get_db()
    auth_service = AuthService(db)

    try:
        user = await auth_service.get_user(user_id)
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "energy_limit": user["energy_limit"],
            "created_at": user.get("created_at"),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─── Admin: List users ────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
async def get_all_users(admin_id: str = Depends(get_current_admin)):
    """Admin: retrieve all registered users."""
    db = get_db()
    users = await db.users.find().to_list(100)
    return [
        {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user.get("role", "user"),
            "energy_limit": user.get("energy_limit", 50.0),
            "created_at": user.get("created_at", datetime.utcnow()),
        }
        for user in users
    ]


# ─── Admin: Delete user ───────────────────────────────────────────────────────

@router.delete("/users/{target_user_id}")
async def delete_user(target_user_id: str, admin_id: str = Depends(get_current_admin)):
    """Admin: permanently delete a user account."""
    db = get_db()
    from bson import ObjectId

    result = await db.users.delete_one({"_id": ObjectId(target_user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


# ─── Forgot Password ──────────────────────────────────────────────────────────

@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, payload: ForgotPasswordRequest):
    """
    Initiate a password reset flow.

    Always returns HTTP 200 regardless of whether the email exists — this
    prevents user-enumeration attacks. The reset token is sent via email
    and is NEVER included in the API response.
    """
    db = get_db()
    auth_service = AuthService(db)
    email = payload.email.lower().strip()

    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)

    if await auth_service.request_password_reset(email, token, expiry):
        # Send via email (SMTP or log-only fallback in dev)
        email_sent = await send_password_reset_email(email, token, expiry_hours=1)
        if not email_sent:
            logger.error("Failed to dispatch reset email for user %s", email)

    return {"message": "If this email is registered, a reset link has been sent."}


# ─── Reset Password ───────────────────────────────────────────────────────────

@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, payload: ResetPasswordWithToken):
    """
    Reset a user password using a valid, non-expired reset token.
    """
    db = get_db()
    auth_service = AuthService(db)

    try:
        user = await auth_service.reset_password(payload.token, payload.new_password)
        return {
            "message": "Password reset successfully. You can now log in with your new password.",
            "email": user["email"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
