"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from database import get_db
from services.auth_service import AuthService
from schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from utils.jwt import decode_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
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


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister):
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
async def login(credentials: UserLogin):
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
