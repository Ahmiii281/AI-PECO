"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from services.auth_service import AuthService
from schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from utils.jwt import decode_token

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
async def register(user_data: UserRegister):
    """
    Register a new user
    """
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
async def login(credentials: UserLogin):
    """
    Login and get access token
    """
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
    from bson import ObjectId
    result = await db.users.delete_one({"_id": ObjectId(target_user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

