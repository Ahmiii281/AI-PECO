"""
Authentication service
"""
from datetime import timedelta
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
        """
        Register a new user
        """
        # --- DEMO BYPASS ---
        if user_data.email == "admin@aipeco.com":
            return {
                "_id": "000000000000000000000000",
                "name": "Demo Admin",
                "email": user_data.email,
                "role": "admin",
                "energy_limit": 100.0,
                "created_at": None,
                "is_active": True
            }
        # -------------------

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
        }

        result = await self.users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id

        return user_doc

    async def login(self, email: str, password: str) -> dict:
        """
        Authenticate user and return access token
        """
        # --- DEMO BYPASS ---
        if email == "admin@aipeco.com" and password == "admin123":
            access_token = create_access_token(data={"sub": "000000000000000000000000"})
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": "000000000000000000000000",
                    "name": "Demo Admin",
                    "email": email,
                    "role": "admin",
                    "energy_limit": 100.0,
                    "created_at": None
                }
            }
        # -------------------

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
        # --- DEMO BYPASS ---
        if user_id == "000000000000000000000000":
            return {
                "_id": "000000000000000000000000",
                "name": "Demo Admin",
                "email": "admin@aipeco.com",
                "role": "admin",
                "energy_limit": 100.0,
                "created_at": None,
                "is_active": True
            }
        # -------------------

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
