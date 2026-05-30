"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db
from services.auth_service import AuthService
from schemas import UserRegister, UserLogin, TokenResponse, UserResponse, ResetPasswordWithToken, PasswordResetRequest
from utils.jwt import decode_token
from utils.rate_limit import limiter
from datetime import datetime
from datetime import timedelta
import secrets
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get current authenticated user
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
            detail="Invalid token",
        )

    return user_id


async def get_current_admin(user_id: str = Depends(get_current_user)):
    """
    Dependency to get current admin user
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

    
@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserRegister):
    """
    Register a new user
    """
    db = get_db()
    auth_service = AuthService(db)

    try:
        user = await auth_service.register(user_data)
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "energy_limit": user["energy_limit"],
            "created_at": user.get("created_at"),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, credentials: UserLogin):
    """
    Login and get access token
    """
    db = get_db()
    auth_service = AuthService(db)

    try:
        token_data = await auth_service.login(credentials.email, credentials.password)
        return token_data
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_profile(user_id: str = Depends(get_current_user)):
    """
    Get current user profile
    """
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


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(admin_id: str = Depends(get_current_admin)):
    """
    Admin: Get all users
    """
    db = get_db()
    users = await db.users.find().to_list(100)
    return [
        {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user.get("role", "user"),
            "energy_limit": user.get("energy_limit", 50.0),
            "created_at": user.get("created_at", datetime.utcnow())
        }
        for user in users
    ]


@router.delete("/users/{target_user_id}")
async def delete_user(target_user_id: str, admin_id: str = Depends(get_current_admin)):
    """
    Admin: Delete a user
    """
    db = get_db()
    from bson import ObjectId
    result = await db.users.delete_one({"_id": ObjectId(target_user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/forgot-password")
async def forgot_password(request: Request, payload: ForgotPasswordRequest):
    """
    Initiate a password reset flow. Always return 200 and do not reveal
    whether the email exists in the system.
    """
    db = get_db()
    email = payload.email

    user = await db.users.find_one({"email": email})
    if user:
        token = secrets.token_urlsafe(32)
        expiry = datetime.utcnow() + timedelta(hours=1)
        await db.users.update_one({"_id": user["_id"]}, {"$set": {"reset_token": token, "reset_token_expiry": expiry}})
        print(f"Password reset token for {email}: {token}")

    return {"message": "If this email is registered, a reset link has been sent."}


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, payload: ResetPasswordWithToken):
    """
    Reset user password using a reset token
    """
    db = get_db()
    auth_service = AuthService(db)

    try:
        user = await auth_service.reset_password(payload.token, payload.new_password)
        return {
            "message": "Password reset successfully",
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

