"""
Authentication service
"""
import hashlib
from datetime import timedelta, datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils.password import hash_password, verify_password
from utils.jwt import create_access_token
from schemas import UserRegister, TokenResponse, UserResponse


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users if db is not None else None

    async def register(self, user_data: UserRegister) -> dict:

        # Normalize email and check if user exists
        email = user_data.email.lower().strip()
        existing_user = await self.users_collection.find_one({"email": email})
        if existing_user:
            raise ValueError("User already exists")

        # Create new user
        user_doc = {
            "name": user_data.name,
            "email": email,
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

        email = email.lower().strip()
        user = await self.users_collection.find_one({"email": email})

        if not user:
            raise ValueError("User not registered")

        if not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid credentials")

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
        Store password reset token for a user.
        Returns True if the email exists, False otherwise.
        """
        hashed_token = _hash_reset_token(reset_token)
        result = await self.users_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "reset_token": hashed_token,
                    "reset_token_expiry": token_expiry
                }
            }
        )
        return result.matched_count > 0

    async def reset_password(self, reset_token: str, new_password: str) -> dict:
        """
        Reset a user's password using a reset token.
        """
        hashed_token = _hash_reset_token(reset_token)

        # Find user with valid reset token
        user = await self.users_collection.find_one({
            "$and": [
                {"reset_token_expiry": {"$gt": datetime.utcnow()}},
                {
                    "$or": [
                        {"reset_token": hashed_token},
                        {"reset_token": reset_token}
                    ]
                }
            ]
        })

        if not user:
            raise ValueError("Invalid or expired reset token")

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
