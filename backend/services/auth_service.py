"""
Authentication service
"""
from datetime import timedelta, datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils.password import hash_password, verify_password
from utils.jwt import create_access_token
from schemas import UserRegister, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users if db is not None else None

    async def register(self, user_data: UserRegister) -> dict:

        # Check if user exists
        existing_user = await self.users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise ValueError("User with this email already exists")

        # Create new user
        user_doc = {
            "name": user_data.name,
            "email": user_data.email,
            "password_hash": hash_password(user_data.password),
            "role": "user",
            "energy_limit": 50.0,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }

        result = await self.users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        return user_doc

    async def login(self, email: str, password: str) -> dict:
        """
        Authenticate user and return access token
        """

        user = await self.users_collection.find_one({"email": email})

        if not user or not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password")

        if not user.get("is_active", True):
            raise ValueError("User account is disabled")

        # Create access token
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
                "created_at": user.get("created_at")
            }
        }

    async def get_user(self, user_id: str) -> dict:
        """
        Get user by ID
        """

        user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")
        return user

    async def update_user(self, user_id: str, update_data: dict) -> dict:
        """
        Update user information
        """
        allowed_fields = {"name", "energy_limit"}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        result = await self.users_collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            raise ValueError("User not found")

        return result

    async def request_password_reset(self, email: str, reset_token: str, token_expiry: datetime) -> bool:
        """
        Store password reset token for a user
        Returns True if email exists, False otherwise
        """
        result = await self.users_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "reset_token": reset_token,
                    "reset_token_expiry": token_expiry
                }
            }
        )
        return result.matched_count > 0

    async def reset_password(self, reset_token: str, new_password: str) -> dict:
        """
        Reset user password using a reset token
        """
        # Find user with valid reset token
        user = await self.users_collection.find_one({
            "reset_token": reset_token,
            "reset_token_expiry": {"$gt": datetime.utcnow()}
        })

        if not user:
            raise ValueError("Invalid or expired reset token")

        # Update password and clear reset token
        updated_user = await self.users_collection.find_one_and_update(
            {"_id": user["_id"]},
            {
                "$set": {
                    "password_hash": hash_password(new_password),
                    "reset_token": None,
                    "reset_token_expiry": None
                }
            },
            return_document=True
        )

        return updated_user
