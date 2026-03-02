"""
Device management service
"""
from bson import ObjectId
from motor.motor_asyncio import AsyncDatabase
from datetime import datetime, timedelta
from typing import List


class DeviceService:
    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.devices_collection = db.devices
        self.energy_collection = db.energy_data

    async def create_device(self, user_id: str, device_data: dict) -> dict:
        """
        Create a new device
        """
        device_doc = {
            "user_id": ObjectId(user_id),
            "name": device_data["name"],
            "location": device_data["location"],
            "relay_pin": device_data.get("relay_pin", 5),
            "status": "offline",
            "is_relay_on": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_seen": None,
        }

        result = await self.devices_collection.insert_one(device_doc)
        device_doc["_id"] = result.inserted_id

        return device_doc

    async def get_user_devices(self, user_id: str) -> List[dict]:
        """
        Get all devices for a user
        """
        devices = await self.devices_collection.find(
            {"user_id": ObjectId(user_id)}
        ).to_list(100)

        return devices

    async def get_device(self, device_id: str, user_id: str = None) -> dict:
        """
        Get device by ID, optionally check ownership
        """
        query = {"_id": ObjectId(device_id)}
        if user_id:
            query["user_id"] = ObjectId(user_id)

        device = await self.devices_collection.find_one(query)
        if not device:
            raise ValueError("Device not found")

        return device

    async def update_device(self, device_id: str, user_id: str, update_data: dict) -> dict:
        """
        Update device information
        """
        allowed_fields = {"name", "location", "relay_pin"}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        update_data["updated_at"] = datetime.utcnow()

        result = await self.devices_collection.find_one_and_update(
            {"_id": ObjectId(device_id), "user_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            raise ValueError("Device not found")

        return result

    async def delete_device(self, device_id: str, user_id: str) -> bool:
        """
        Delete a device
        """
        result = await self.devices_collection.delete_one({
            "_id": ObjectId(device_id),
            "user_id": ObjectId(user_id)
        })

        if result.deleted_count == 0:
            raise ValueError("Device not found")

        return True

    async def update_device_status(self, device_id: str, status: str, last_seen: datetime = None):
        """
        Update device online/offline status
        """
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow(),
        }

        if last_seen:
            update_data["last_seen"] = last_seen

        await self.devices_collection.update_one(
            {"_id": ObjectId(device_id)},
            {"$set": update_data}
        )

    async def set_relay_command(self, device_id: str, command: str) -> dict:
        """
        Set relay command (ON/OFF) for device
        """
        relay_state = command.upper() == "ON"

        device = await self.devices_collection.find_one_and_update(
            {"_id": ObjectId(device_id)},
            {"$set": {
                "is_relay_on": relay_state,
                "updated_at": datetime.utcnow()
            }},
            return_document=True
        )

        if not device:
            raise ValueError("Device not found")

        return device

    async def get_relay_command(self, device_id: str) -> dict:
        """
        Get current relay command for device
        """
        device = await self.devices_collection.find_one({"_id": ObjectId(device_id)})

        if not device:
            raise ValueError("Device not found")

        return {
            "device_id": str(device["_id"]),
            "command": "ON" if device.get("is_relay_on", False) else "OFF",
            "relay_pin": device.get("relay_pin", 5)
        }
